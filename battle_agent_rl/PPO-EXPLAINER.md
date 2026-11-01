# PPO: what the model sees and chooses

This is the plain-language companion to [PPO.md](PPO.md) and the
[Crossroads contract](../specs/ppo-agent/08-crossroads-environment-policy-contract.md).
Keep it in sync when the game or PPO contract changes; it explains the contract,
not a separate set of rules.

**Current status:** the Crossroads setup below is specified for increment 08,
but not yet implemented or trained. The playable 9×9 demo from 07 is different:
it uses two PPO units, 162 actions, and PPO in the first seat. Its existing
trainer uses `[32, 32]` hidden layers. Do not confuse those artifacts with the
planned Crossroads model.

## The basic loop

```text
Core game → observation + legal-action mask → PPO chooses one action
    ↑                                               ↓
    └──────── core resolves movement/fire ───────────┘
```

- **Environment:** the game plus the adapter that resets it, accepts actions,
  advances turns, and returns observations, rewards, and ending flags.
- **Observation:** numbers describing the current public game state.
- **Action space:** the fixed menu of choices the model can output.
- **Action mask:** which items on that menu are legal right now.
- **Policy:** the neural network that assigns probabilities to those choices.

Core still owns movement, defensive fire, combat, scoring, and completion.
The neural network chooses orders; it does not replace the rules engine.

## Who plays whom?

For Crossroads, **PPO plays Player 2 / Wehrmacht**. The human plays
**Player 1 / Airborne**, and Airborne still moves first. Seeded random or hold
controllers stand in for the human during environment checks.

The board is 18×18, with three objectives and an eight-turn limit. Wehrmacht
starts with three units; two more are scheduled to arrive on turn 3.

## Action space: why `Discrete(1620)`?

There are five permanent Wehrmacht unit slots and 324 board cells:

```text
5 units × (18 × 18 destinations) = 1,620 unit/destination choices
```

`Discrete(1620)` means one integer from **0 through 1,619**. It includes legal
and illegal choices; the mask filters them.

| Slot | Unit | Action IDs |
| --- | --- | --- |
| 0 | A / Inf. Zug | 0–323 |
| 1 | B / Inf. Zug | 324–647 |
| 2 | Crossroads Feldwache | 648–971 |
| 3 | MG Trupp A (reinforcement) | 972–1295 |
| 4 | StuG. III Zug A (reinforcement) | 1296–1619 |

Slots never shift after a death. Reinforcement slots exist from the start but
cannot act before deployment. Airborne units are not in PPO's action space.

### Encoding and decoding an order

Coordinates are zero-based:

```python
action = slot * 324 + row * 18 + column
```

For example, **German B → row 4, column 7** is:

```text
1 × 324 + 4 × 18 + 7 = 403
```

That illustrates the encoding, not a claim that this destination is legal.
Decode the integer with:

```python
slot, cell = divmod(403, 324)  # slot 1, cell 79
row, column = divmod(cell, 18) # row 4, column 7
```

PPO chooses both **which unit goes next** and **its destination**. Core supplies
the legal path and resolves its consequences. Choosing the unit's current hex
means hold; it is not a separate action type.

## The mask: what can I do right now?

The mask is a separate Boolean array with shape `(1620,)`:

```python
mask = [False, False, ..., True, ..., False]
# True = legal now; False = unavailable now
```

Only reachable destinations for deployed units with pending orders are enabled.
Dead, awaiting, and already-ordered units have entirely false action blocks.
The zero-movement Feldwache has a hold-only order.

After one order resolves, including defensive fire and retreat, we rebuild the
mask before choosing again. Each unit gets **one order per friendly movement
phase**, starting with its full movement allowance. It can move less than its
maximum, but cannot split its movement into multiple orders. Hold also spends
the order.

An all-false mask means there are no legal actions. The environment must advance
automatically or finish the episode, not ask PPO to choose from an empty menu.

**Invalid predictions are errors, not silent holds.** Reject them before any
board change or random draw. Drawing from the random-number generator (RNG)
advances its state, even if the result is discarded; an invalid request must
not secretly change the next valid fire or combat roll.

## Observation: what does PPO see?

The model receives a dictionary of NumPy arrays, not prose or a screenshot.
The first five unit rows are Wehrmacht; the next six are Airborne A–F.
Learner-first arrays do **not** change core's Airborne-first turn order.

| Field | Shape | What it tells PPO |
| --- | --- | --- |
| `positions` | `(11, 324)` | One row per unit; a 1 marks its board cell. Separate rows preserve stacks. |
| `unit_status` | `(11,)` | 0 awaiting deployment, 1 on board, 2 eliminated. |
| `unit_stats` | `(11, 4)` | Attack, defense, full movement, defensive-fire modifier. |
| `movement_remaining` | `(11,)` | Live movement points; zero off-board. |
| `fire_flags` | `(11, 4)` | Public readiness relative to Wehrmacht, last-friendly-turn eligibility, forced retreat, fire spent. |
| `pending` | `(5,)` | Which German units still have an order. |
| `terrain` | `(324, 3)` | Movement cost, defensive-fire modifier, combat odds shift per cell. |
| `road_edges` | `(324, 6)` | Road costs in core neighbor-direction order; zero for no road/out-of-bounds. |
| `objective_points` | `(324,)` | Objective locations and point values. |
| `objective_control` | `(3,)` | Whether **Airborne** occupies each objective, in scenario objective order. |
| `scores` | `(2,)` | Wehrmacht score, then Airborne score. |
| `reinforcement` | `(1, 4)` | Arrival turn, entry row, entry column, group status. |
| `remaining_cycles` | `(1,)` | True scenario horizon, including the current cycle. |

No future rolls, RNG state, or hypothetical combat outcomes are exposed.
Roads are observable metadata: **current core movement uses destination terrain
cost, not a road discount**.

### A sample model input

Imagine Airborne has held all its units in place on turn 1. We are now at
Wehrmacht's first decision. This is a **NumPy-style display**, not executable
code: `...` abbreviates array entries that are present in the real input.

```python
obs = {
    "positions": array([                  # (11, 324), int8
        [0, ..., 1, ..., 0],              # German A: 1 at cell 69
        [0, ..., 1, ..., 0],              # German B: 1 at cell 77
        [0, ..., 1, ..., 0],              # Feldwache: 1 at cell 117
        [0, ..., 0],                      # MG: all zero, off-board
        [0, ..., 0],                      # StuG: all zero, off-board
        [0, ..., 1, ..., 0],              # Airborne A: cell 227
        [0, ..., 1, ..., 0],              # Airborne B: cell 223
        [0, ..., 1, ..., 0],              # Airborne C: cell 286
        [0, ..., 1, ..., 0],              # Airborne D: cell 289
        [0, ..., 1, ..., 0],              # Airborne E: cell 288
        [0, ..., 1, ..., 0],              # Airborne F: cell 295
    ], dtype=int8),

    "unit_status": array([1,1,1,0,0,1,1,1,1,1,1], dtype=int8),

    "unit_stats": array([
        [2,2,4,1.00], [2,2,4,1.00], [1,1,0,0.50],
        [1,2,3,1.33], [4,4,7,1.33],
        [3,2,5,1.00], [3,2,5,1.00], [3,2,5,1.00],
        [3,2,5,1.00], [3,2,5,1.00], [3,2,5,1.00],
    ], dtype=float32),

    "movement_remaining": array([4,4,0,0,0,5,5,5,5,5,5], dtype=int8),

    "fire_flags": array([
        [1,1,0,0], [1,1,0,0], [1,1,0,0],
        [0,0,0,0], [0,0,0,0],
        [1,1,0,0], [1,1,0,0], [1,1,0,0],
        [1,1,0,0], [1,1,0,0], [1,1,0,0],
    ], dtype=int8),

    "pending": array([1,1,1,0,0], dtype=int8),
    "terrain": array([[2,0.85,-1], [1,1.00,0], ...], dtype=float32),
    "road_edges": array([[0,0,0,0,0,0], ...], dtype=float32),
    "objective_points": array([0, ..., 1, ..., 0], dtype=int8),
    "objective_control": array([0,0,0], dtype=int8),
    "scores": array([3,0], dtype=int8),
    "reinforcement": array([[3,0,16,0]], dtype=int32),
    "remaining_cycles": array([8], dtype=int32),
}
```

Cell index is `row * 18 + column`; the three objective cells are 39, 69, and 117.
German B's **position cell** is 77, but its **hold action** is `324 + 77 = 401`.
Those numbers have different meanings.

Reinforcement status is 0 scheduled, 1 delayed, or 2 entered. Unit status still
distinguishes a deployed unit that later dies. Zero-filled off-board positions
alone cannot tell those situations apart.

## What does the neural network do with this?

The planned Crossroads baseline is `MaskablePPO` with `MultiInputPolicy`:

```python
policy_kwargs = {"net_arch": {"pi": [64, 64], "vf": [64, 64]}}
```

SB3 converts the arrays to tensors and flattens/concatenates their features.
These board arrays are not automatically processed by a spatial CNN.

- **Policy network:** two 64-neuron hidden layers, then 1,620 scores (logits).
- **Mask and softmax:** give illegal actions zero probability and normalize the
  legal choices to probabilities summing to 1.
- **Choice:** sample during training; choose the highest-probability legal
  action during deterministic play.
- **Value network:** separate two 64-neuron hidden layers and one value estimate
  of expected future return, used during training.

Both networks use `Tanh` hidden activations. The mask is supplied separately;
it is not another field in the observation dictionary. The intended inference
call is:

```python
action, _ = model.predict(obs, action_masks=mask, deterministic=True)
```

The architecture is a modest CPU baseline, not a promise of playing strength.
Training time also depends on how many simulated games are needed and how
quickly core can run them.

## Turns, rewards, and endings

The non-learning environment resolves the opening Airborne turn before returning
its first Wehrmacht decision. Each step applies one German order. After the
last order, it closes Wehrmacht's turn and, unless ended/capped, resolves the
next Airborne turn before the next learner decision. The human driver waits
for actual human commands instead of acting automatically for Airborne.

Reinforcements arrive **before Airborne moves on turn 3**, not immediately
before PPO moves. They can be attacked before their first order and cannot
fire defensively during that intervening Airborne turn. Core handles blocked
entry, retries, movement resets, and fire readiness.

Airborne scores occupied objectives; Wehrmacht scores the rest, even empty
ones. Scores reflect current control, not accumulated captures.

| Core result | PPO reward |
| --- | --- |
| Wehrmacht wins | +1 |
| Airborne wins | -1 |
| Draw | 0 |
| Still playing or externally cut off | 0 |

Reward is delivered once at completion, not for each capture. Eliminating a
side is not automatically victory: core's objective-conditioned rules decide.

An **external cutoff** stops an experiment early; it is not a completed draw.
For example, a cap of two cycles stops after Wehrmacht's turn 2, before the
next Airborne action. Core may already have advanced to turn 3 and deployed
arrivals; `remaining_cycles` is then `[6]`, not zero. A real core ending takes
precedence over a cutoff. Ordinary turn-limit completion is at the end of
Wehrmacht's turn 8.

## Keeping this reference accurate

Update this file in the same change whenever relevant rules, scenario data,
observations, action encoding/masking, turn timing, rewards, model architecture,
or implementation status changes. Recheck the numeric examples against core
and the active contract. Keep planned behavior clearly separate from delivered
behavior; if implementation and specification disagree, flag it rather than
silently documenting a new contract.

For exact bounds, validation requirements, and acceptance criteria, use the
[08 specification](../specs/ppo-agent/08-crossroads-environment-policy-contract.md).
For delivered status and later work, use [PPO.md](PPO.md) and the
[active schedule](../specs/ppo-agent/playable-player-schedule.md).

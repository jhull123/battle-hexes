# PPO Schedule 2 — Playable Crossroads Player

This is the active schedule, beginning at 07. Increments 01–06 are completed
foundation work; their specifications and evidence remain in the
[foundation schedule](implementation-schedule.md). All increments below are
planned. Mark completion only after delivery and verification of the evidence.

The finish line is a trained, evaluated, frozen PPO player that a human can
select and play against through core/API/UI on
[`d_day_crossroads`](../../battle_hexes_core/src/battle_hexes_core/scenarios/d_day_crossroads.json).
One explicitly declared PPO side is sufficient. The fixed 9×9 prototype from
[06](06-multi-unit-design.md) is an intermediate verification environment;
its input contract and weights are not assumed to transfer to Crossroads.
Measured weakness is an acceptable evaluation result. Demonstrated playing
strength belongs to [schedule 3](crossroads-strength-schedule.md), which will
be defined only after this schedule is fully implemented and verified.
Self-play, arbitrary boards, broad scenario expansion, and open-ended policy
tuning are outside this schedule.

## 07 — Supported play contract and live core turns

**Objective:** Make the multi-unit decision contract usable in ordinary games
before committing to a training campaign.

**Bounded scope:** Declare the supported Crossroads version, PPO side, and
human-opponent boundary. Resolve live per-unit decisions versus
`Player.movement()`'s precomputed batch in core execution and the API movement
path, preserving 06's post-movement/fire feedback and once-per-side combat.
Keep core authoritative and independent of trainer dependencies. Establish
execution that can accommodate Crossroads' roster and phases; the 9×9 case
may provide the initial execution evidence.

**Dependencies:** 01–06.

**Observable completion evidence:** A recorded support and execution contract,
plus core/API traces showing that a subsequent decision sees the preceding
move's actual fire/retreat effects, with correct combat and turn handoff.
Existing batch players still work. No speculative batch, game mutation inside
`movement()`, or training cutoff presented as a completed game is used.

## 08 — Crossroads environment and policy contract

**Objective:** Make actual Crossroads the training and inference task before
the main training campaign.

**Bounded scope:** Load the existing scenario through core and establish a
Crossroads-specific observation/action contract and masked environment. Cover
the 18×18 board, six Airborne versus up to five Germans, heterogeneous units,
terrain, roads, stacking, reinforcements, objective control, and eight-turn
limit. Audit policy access to decision-relevant state, stable unit identity,
and live legal actions. Align rewards and remaining-time semantics with core
scoring and completion, keeping external cutoffs distinct. Define a new
versioned contract rather than silently reinterpreting 06's fixed inputs.

**Dependencies:** 07.

**Observable completion evidence:** Audited non-learning Crossroads rollouts
complete under core rules, including reinforcement arrival and objective-based
turn-limit results. Policy inputs and masks track live core state throughout,
including turns with no available orders. A compatible masked policy can make
legal decisions; incompatible prototype artifacts are rejected. The declared
PPO side and human opponent can use the same game semantics.

## 09 — Crossroads training and held-out evaluation

**Objective:** Produce a trained Crossroads checkpoint with an honest,
reproducible baseline comparison for the supported side.

**Bounded scope:** Run a bounded masked-PPO campaign under 08's contract with
durable checkpoints and recorded scenario/configuration. Predeclare opponent/
RNG protocols, training/validation/held-out separation, checkpoint selection,
comparison criteria, and random, hold, and an objective-aware tactical baseline.
Select on validation only, then freeze the checkpoint for held-out reporting.

**Dependencies:** 08.

**Observable completion evidence:** A repeatable run demonstrates parameter
updates and legal live multi-unit decisions on actual Crossroads. Reloadable
artifacts and a held-out report identify the selected checkpoint and PPO side,
report objective scores, outcomes, and cutoffs separately, and quantify paired
baseline differences and uncertainty. The report states improvement,
inconclusive evidence, or weakness without using
held-out results to select or tune the policy. Passing does not require wins
over every baseline or imply generalization beyond the declared task.

## 10 — Frozen-policy Crossroads inference parity

**Objective:** Use the evaluated checkpoint as a frozen Crossroads core player
against a human-controlled opponent.

**Bounded scope:** Load and bind the selected artifact to the declared Crossroads
side using 07's live execution path. Share training/inference observation, mask,
unit identity, reinforcement, horizon, and action conversion semantics; reject
incompatible artifacts and game configurations. Keep learning out of execution.

**Dependencies:** 07–09.

**Observable completion evidence:** Seed/RNG-matched evaluation and ordinary
Crossroads core-player runs agree on observations, masks, choices, resolved
events, scores, and endings, with unchanged policy weights. Legal human turns
alternate with PPO turns through core completion, including the scenario turn
limit; an external cutoff never substitutes for a completed result.

## 11 — Retire or isolate the 5×5 engine

**Objective:** Establish one actively maintained PPO decision engine.

**Bounded scope:** After multi-unit training and inference are proven, decide
and implement retirement of the 5×5 engine or explicitly justify retaining it
solely for legacy checkpoint/evidence replay. Consolidate shared plumbing
where practical and update entry points and documentation to match the choice.

**Dependencies:** 09 and 10.

**Observable completion evidence:** A recorded decision identifies the removed
paths or the exact legacy artifacts and replay purpose that justify retention.
Active training and player workflows use the Crossroads-capable engine;
retained legacy replay is demonstrably isolated and runnable. Crossroads
training, evaluation, and inference evidence remains reproducible after the
change; the 9×9 case remains only as useful verification coverage.

## 12 — Selectable human-versus-PPO Crossroads games

**Objective:** Deliver the evaluated player through the game's normal API/UI.

**Bounded scope:** Expose Crossroads and PPO player selection for the declared
side, provision the frozen artifact for API inference, and enforce scenario/seat
compatibility. Connect creation and persisted-game restoration to the live
player, preserving artifact identity and required decision state. Integrate
movement results, combat, turn handoff, and terminal display with the existing
human/CPU phase flow.

**Dependencies:** 07–11.

**Observable completion evidence:** In a backend-connected run, a human selects
Crossroads and the PPO opponent, starts a game, plays alternating turns,
reloads/resumes it, and reaches a core-confirmed completed result and objective
scores displayed in the UI. Every advertised PPO side has completed-game
evidence; unsupported combinations are unavailable or rejected clearly. The
serving checkpoint matches 09's evaluated artifact, remains frozen, and has
documented availability, supported limits, and measured performance. A 9×9 or
mock-only demo or bounded cutoff does not satisfy this gate.

## Open Questions

No questions.

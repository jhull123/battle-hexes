# PPO Schedule 2 — Playable Crossroads Player

This is the active schedule, beginning at 07. Increments 01–06 are completed
foundation work; their specifications and evidence remain in the
[foundation schedule](implementation-schedule.md). All increments below are
planned. Mark completion only after delivery and verification of the evidence.

The finish line is a trained, evaluated, frozen PPO player that a human can
select and play against through core/API/UI on
[`d_day_crossroads`](../../battle_hexes_core/src/battle_hexes_core/scenarios/d_day_crossroads.json).
One explicitly declared PPO side is sufficient. The fixed 9×9 prototype from
[06](06-multi-unit-design.md) first becomes an explicitly experimental,
human-visible integration slice in 07. That slice uses a **trained, saved and
reloaded** multi-unit checkpoint, not an initialized policy. Smoke training
proves plumbing, not playing strength; its input contract and weights do not
transfer to Crossroads. The 9×9 selection remains visibly experimental until the
Crossroads release in 12, when it is hidden or retired rather than left as a
permanent player option.
Measured weakness is an acceptable evaluation result. Demonstrated playing
strength belongs to [schedule 3](crossroads-strength-schedule.md), which will
be defined only after this schedule is fully implemented and verified.
Self-play, arbitrary boards, broad scenario expansion, and open-ended policy
tuning are outside this schedule.

## 07 — Trained 9×9 human-visible slice

**Objective:** Train and reload a compatible 9×9 multi-unit policy, then prove
live human-versus-PPO play end to end before the Crossroads campaign.

**Bounded scope:** In the fixed 9×9 2v2 scenario from 06, run bounded masked-PPO
smoke training with legal masked rollouts and actual parameter updates. Save a
versioned, validated checkpoint and let a human explicitly select its frozen,
reloaded policy as a clearly labeled experimental opponent in core/API/UI.
Build training, artifact and inference plumbing reusable with a different
Crossroads contract; do not assume 9×9 weights or inputs transfer. Preserve
live per-unit decisions, post-move fire/retreat feedback, once-per-side combat,
persisted pending decisions and checkpoint identity across reload/resume, and
existing batch-player behavior. No 9×9 strength campaign, skill claim or
external cutoff presented as core completion. Leave the API design and supported
seat/execution details to the 07 spec.

**Dependencies:** 01–06.

**Observable completion evidence:** A bounded training run records legal masked
rollouts and changed parameters; its versioned checkpoint reloads with matching
masked choices, rejects incompatible inputs, and remains frozen during play.
A declared, bounded seed set reports win/loss/draw/cutoff counts without a
strength threshold. In a backend-connected UI run, a human selects that
experimental checkpoint, watches live per-unit moves and fire/retreat, reloads
mid-turn with pending orders intact, and reaches a core-confirmed completed
result displayed in the UI. Traces verify once-per-side combat and turn handoff;
existing batch-player games still work. A CLI-only trace, initialized policy
or cutoff does not pass.

## 08 — Crossroads environment and policy contract

**Objective:** Make actual Crossroads the training and inference task before
the main training campaign, using 07's live-play path.

**Bounded scope:** Declare the supported Crossroads version, PPO side and
human-opponent boundary. Load the existing scenario through core and establish
a Crossroads-specific observation/action contract and masked environment. Cover
the 18×18 board, six Airborne versus up to five Germans, heterogeneous units,
terrain, roads, stacking, reinforcements, objective control, and eight-turn
limit. Audit policy access to decision-relevant state, stable unit identity,
and live legal actions. Align rewards and remaining-time semantics with core
scoring and completion, keeping external cutoffs distinct. Define a new
versioned contract rather than silently reinterpreting 06's fixed inputs;
adapt 07's training and artifact interfaces without transferring its weights.

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

**Bounded scope:** Extend 07's masked training and versioned checkpoint plumbing
to a bounded campaign under 08's Crossroads contract, rather than build a second
trainer. Record scenario/configuration; predeclare opponent and RNG protocols,
training/validation/held-out separation, checkpoint selection, comparison
criteria, and random, hold, and an objective-aware tactical baseline.
Select on validation only, then freeze the checkpoint for held-out reporting.

**Dependencies:** 07's training/artifacts and 08's Crossroads contract.

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
against a human-controlled opponent through 07's live execution path.

**Bounded scope:** Load and bind the selected artifact to the declared Crossroads
side using 07's validated loading, frozen inference, live execution and
persisted-decision path, not a second UI integration. Share training/inference
observation, mask, unit identity, reinforcement, horizon, and action conversion
semantics; reject incompatible artifacts and game configurations. Keep learning
out of execution.

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
change; 9×9 can remain useful verification coverage after its experimental
player selection is hidden or retired in 12.

## 12 — Promote Crossroads through the playable path

**Objective:** Make the evaluated Crossroads player the selectable human-versus-
PPO target through the API/UI path proven in 07.

**Bounded scope:** Extend 07's selection, live decision, reload/resume and
terminal display to the declared Crossroads side and 09's evaluated, frozen
artifact; enforce scenario/seat and artifact compatibility. Do not rebuild the
UI integration. At this Crossroads release, hide or retire the experimental
9×9 opponent selection (retaining only useful internal verification coverage).

**Dependencies:** 07–11.

**Observable completion evidence:** In a backend-connected run, a human selects
Crossroads and the PPO opponent, plays alternating turns, reloads/resumes, and
reaches a core-confirmed completed result with objective scores in the UI.
Every advertised PPO side has completed-game evidence; unsupported combinations
are unavailable or rejected clearly, and the experimental 9×9 selection is no
longer offered. The serving checkpoint matches 09's evaluated artifact,
remains frozen, and has documented availability, supported limits, and measured
performance. The 07 demo or an external cutoff does not satisfy this gate.

## Open Questions

No questions.

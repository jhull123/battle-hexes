# PPO Playable Player Implementation Schedule

This is the active schedule, beginning at 07. Increments 01–06 are completed
foundation work; their specifications and evidence remain in the
[foundation schedule](implementation-schedule.md). All increments below are
planned. Mark completion only after delivery and verification of the evidence.

The finish line is a trained, evaluated, frozen PPO player that a human can
select and play against through core/API/UI on explicitly supported scenarios.
Start with the fixed 9×9 2v2 case from [06](06-multi-unit-design.md); padding
support does not automatically qualify other starting rosters for release.
Measured weakness is an acceptable evaluation result, not a strength claim.
Self-play, arbitrary boards, broad scenario expansion, and open-ended policy
tuning are outside this schedule.

## 07 — Supported play contract and live core turns

**Objective:** Make the multi-unit decision contract usable in ordinary games
before committing to a training campaign.

**Bounded scope:** Declare the supported scenario, PPO seat, unit/settings
limits, and human-opponent boundary. Resolve live per-unit decisions versus
`Player.movement()`'s precomputed batch in core execution and the API movement
path, preserving 06's post-movement/fire feedback and once-per-side combat.
Keep core authoritative and independent of trainer dependencies. Settle how
the policy's finite cycle budget relates to human games and core completion
before training; any contract change requires explicit design approval.

**Dependencies:** 01–06.

**Observable completion evidence:** A recorded support and horizon contract,
plus core/API traces showing that a subsequent decision sees the preceding
move's actual fire/retreat effects, with correct combat and turn handoff.
Existing batch players still work. No speculative batch, game mutation inside
`movement()`, or training cutoff presented as a completed game is used.

## 08 — Multi-unit training and held-out evaluation

**Objective:** Produce a trained multi-unit checkpoint with an honest,
reproducible baseline comparison for the supported task.

**Bounded scope:** Run a bounded masked-PPO campaign under 07's contract with
durable checkpoints and recorded configuration. Predeclare opponent/RNG
protocols, training/validation/held-out separation, checkpoint selection,
comparison criteria, and random, hold, and a simple tactical baseline.
Select on validation only, then freeze the checkpoint for held-out reporting.

**Dependencies:** 07.

**Observable completion evidence:** A repeatable run demonstrates parameter
updates and legal live multi-unit decisions. Reloadable artifacts and a
held-out report identify the selected checkpoint, report outcomes and cutoffs
separately, and quantify paired baseline differences and uncertainty. The
report states improvement, inconclusive evidence, or weakness without using
held-out results to select or tune the policy. Passing does not require wins
over every baseline or imply generalization beyond the declared task.

## 09 — Frozen-policy core inference parity

**Objective:** Use the evaluated checkpoint as a frozen multi-unit core player
against a human-compatible opponent.

**Bounded scope:** Load and bind the selected artifact to supported games using
07's live execution path. Share training/inference observation, mask, slot,
budget, and action conversion semantics; reject incompatible artifacts and
game configurations. Keep learning out of player execution.

**Dependencies:** 07 and 08.

**Observable completion evidence:** Seed/RNG-matched evaluation and ordinary
core-player runs agree on observations, masks, choices, resolved events, and
endings, with unchanged policy weights. Legal human-controlled opponent turns
can alternate with PPO turns through core completion; horizon exhaustion is
handled according to 07, never silently reported as a win, loss, or draw.

## 10 — Retire or isolate the 5×5 engine

**Objective:** Establish one actively maintained PPO decision engine.

**Bounded scope:** After multi-unit training and inference are proven, decide
and implement retirement of the 5×5 engine or explicitly justify retaining it
solely for legacy checkpoint/evidence replay. Consolidate shared plumbing
where practical and update entry points and documentation to match the choice.

**Dependencies:** 08 and 09.

**Observable completion evidence:** A recorded decision identifies the removed
paths or the exact legacy artifacts and replay purpose that justify retention.
Active training and player workflows use the multi-unit engine; retained legacy
replay is demonstrably isolated and runnable. Multi-unit training, evaluation,
and inference evidence remains reproducible after the change.

## 11 — Selectable human-versus-PPO games

**Objective:** Deliver the evaluated player through the game's normal API/UI.

**Bounded scope:** Expose the supported scenario and PPO player selection,
provision the frozen artifact for API inference, and enforce scenario/seat
compatibility. Connect creation and persisted-game restoration to the live
player, preserving artifact identity and required decision state. Integrate
movement results, combat, turn handoff, and terminal display with the existing
human/CPU phase flow.

**Dependencies:** 07–10.

**Observable completion evidence:** In a backend-connected run, a human selects
the supported scenario and PPO opponent, starts a game, plays alternating turns,
reloads/resumes it, and reaches a core-confirmed completed result displayed in
the UI. Every advertised scenario/seat combination has completed-game evidence;
unsupported combinations are unavailable or rejected clearly. The serving
checkpoint matches 08's evaluated artifact, remains frozen, and has documented
availability, supported limits, and measured performance. A mock-only demo or
bounded cutoff does not satisfy this gate.

## Open Questions

No questions.

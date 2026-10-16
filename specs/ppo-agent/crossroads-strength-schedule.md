# PPO Schedule 3 — Crossroads Playing Strength (Placeholder)

This is an inactive placeholder, not an implementation schedule. Define its
increments, dependencies, scope, and completion gates only after
[schedule 2](playable-player-schedule.md) is fully implemented and its evidence
verified. Use the delivered Crossroads player, evaluation artifacts, and observed
weaknesses to decide the work; no numbered targets are assigned here.

## High-level objectives

- Define what “good at Crossroads” means through a predeclared, side-specific
  benchmark with objective-aware tactical opponents, held-out evaluation, and
  structured human play. Beating random alone is insufficient.
- Improve measured tactical and objective-control weaknesses through bounded
  experiments in training, representation, rewards, or opponent selection,
  choosing interventions from schedule 2's evidence.
- Demonstrate reproducible improvement with uncertainty estimates and fresh
  held-out evidence, keeping checkpoint selection separate from final reporting.
- Preserve frozen-policy parity and completed human-versus-PPO Crossroads play
  as stronger evaluated checkpoints become available.

Supporting both sides, self-play, or other training extensions should be
considered only when the evidence and chosen strength goal justify them.
Arbitrary boards and broad scenario expansion are not assumed prerequisites.

## Open Questions

No questions.

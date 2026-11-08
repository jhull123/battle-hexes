---
title: API Game-Agent Integration Boundary
version: 1.0
date_created: 2026-10-18
tags: [architecture, ppo, api, persistence]
---

# Introduction

Refactor the experimental 9×9 Proximal Policy Optimization (PPO) game's API
integration so generic saved-game processing and ordinary movement/combat
commands do not implement PPO-specific behavior. This is a behavior-preserving
companion to [increment 07](07-trained-9x9-human-visible-slice.md), not a new
PPO policy contract or a Crossroads implementation.

## 1. Purpose & Scope

This specification is for implementers of the API refactor before adding a
Crossroads agent. It covers API composition, authoritative saved-state
validation/rehydration, and commands executed by the non-PPO opponent. It does
not add a new scenario, player type, training workflow, model, public route, or
browser behavior. Increment 07's durable backend/browser acceptance gate
remains outstanding and is not satisfied by this refactor.

## 2. Definitions

- **Core:** `battle_hexes_core`, the authority for rules, phase transitions,
  scoring, and game completion.
- **Agent integration:** An API-owned collaborator selected for a game's
  supported agent/scenario configuration. It handles only agent-specific
  command policy and saved-state lifecycle, not core rules or inference.
- **Ordinary command:** An existing `/movement`, `/move`, `/end-movement`,
  `/combat`, or `/end-turn` command, as opposed to `/ppo/order`.
- **Saved extension:** The existing optional JSON `ppo_state` field in the
  version-1 authoritative game document. Absence is represented by `null`.
- **Game-bound artifact:** The configured checkpoint validated against the
  digest persisted when the PPO game was created; the current default must not
  replace it on resume.
- **No-op integration:** The implementation selected for ordinary, non-agent
  games; it does not change their authorization or turn execution.

## 3. Requirements, Constraints & Guidelines

- **REQ-001 — Ownership:** Place integration selection and PPO-specific
  command/save-state behavior in API-owned integration modules, separate from
  generic persistence, ordinary command adapters, and RL inference. Generic
  persistence must not import `ppo_state` or perform PPO validation or artifact
  access directly. Ordinary adapters must not import `ppo_state` or
  `ppo_opponent`, inspect `game.ppo_state`, or branch on a PPO player type.
- **REQ-002 — Selection:** Resolve an integration from authoritative scenario
  ID, player type IDs, and presence of the saved extension, never from an HTTP
  request's claim about an existing game. Select the 9×9 integration if any
  of these indicates the experimental PPO configuration; it must reject an
  invalid combination, including a missing required extension. Select the
  no-op integration only if none indicates an agent game. Unknown agent state
  must fail closed rather than be ignored. Keep registration explicit and
  small; no dynamic plugin discovery or fallback policy.
- **REQ-003 — Codec boundary:** The generic document may retain the optional
  wire key `ppo_state` for version-1 compatibility, but must treat its contents
  as opaque until the selected integration strictly validates them. Extract
  the existing `PpoState` field/type checks into the PPO integration, including
  rejection of extra fields. Call integration hooks on **both** encode and
  decode: extract extension data from the live game for encode; validate it
  against the document and scenario after generic validation and before
  hydration; restore it to the detached game only after generic hydration.
  Never restore or inspect unvalidated extension data. Preserve the current
  canonical JSON field names, `null` for ordinary games, schema version 1, and
  existing snapshot readability; do not replace `ppo_state` with a new wire
  format in this refactor.
- **REQ-004 — Artifact and RNG:** Keep existing strict scenario/seat, contract,
  checkpoint path/digest, pending-unit, and JSON RNG-state checks. On decode,
  validate artifact availability against the *saved* digest without loading
  model weights; bind the restored RNG to PPO decisions and defensive fire.
  Load the model only when creating a PPO game or executing a PPO order, as
  today. Capture the shared RNG state after every successful command that can
  consume it, including opponent movement and combat. Never silently replace
  a missing checkpoint, recompute spent pending slots from movement points, or
  consume a random roll on a rejected command or receipt replay.
- **REQ-005 — Command policy:** Ordinary adapters call the integration for
  command/phase/seat authorization, sparse-board safeguards, completed-phase
  closure after movement, optional combat RNG, and post-turn pending/RNG
  bookkeeping. The PPO integration keeps the current rule that only the
  second seat can use ordinary commands, with `/movement` for Random or
  Q-Learning and `/move` for Human; a submitted board cannot move a PPO unit
  or rewrite a resolved phase. It must keep the existing allowed commands and
  409 error behavior. The no-op integration preserves normal batch-player and
  human behavior, including not passing an RNG argument to ordinary combat.
- **REQ-006 — Core authority:** Adapters retain their existing sequence of
  applying plans/boards, invoking core, scoring, and notifying completion.
  The integration may request the existing generic
  `game.finalize_completed_phase()` transition at the current movement
  points, but must not evaluate victory itself, duplicate scoring, or invoke
  `GameStatusEvaluator` from routes or schemas. Preserve the timing of
  combat, end-turn handoff, pending-slot refresh, and terminal-state closure.
- **REQ-007 — Public contracts:** Preserve existing player selection and
  `/ppo/order` inference behavior, `ppoTurn` projections, HTTP routes/statuses,
  idempotency receipts, optimistic version checks, and checkpoint-unavailable
  error translation. No new wire fields or state-schema migration are needed.
- **CON-001:** `battle_hexes_core` must not depend on PPO, API integration
  modules, inference packages, or persistence. The dedicated PPO order adapter
  may continue to import RL inference; it is not an ordinary command.
- **CON-002:** Preserve the numbered 07 specification. If implementation
  requires changing its behavior, explain the proposed deviation and obtain
  a decision before implementing it.
- **GUD-001:** Use one explicit API composition point to supply the integration
  to persistence and ordinary commands. Prefer a small no-op implementation
  and a 9×9 implementation over a general framework. Keep strict PPO state
  parsing, artifact checks, command policy, and serialization in cohesive
  collaborators if one integration module becomes too large.

## 4. Interfaces & Data Contracts

The following are conceptual API-owned contracts; names and exact method
signatures may follow local conventions, but the call sites and semantics are
required. The selector handles both saved documents and live games; the
creation path selects from the scenario and requested player types.

| Operation | Generic caller | Required integration behavior |
| --- | --- | --- |
| `select(scenario_id, player_type_ids, extension_present)` | API composition/codec | Choose 9×9 or no-op; reject unsupported agent configurations. Use `extension_present` to detect stray/tampered data, not to grant authorization. |
| `initial_state(game)` | Game creation | For 9×9, validate/configure the checkpoint, shared RNG, and initial pending IDs; for ordinary games, do nothing. Creation's existing player factory may still construct the experimental player. |
| `encode_state(game)` | Game-state encoder | Return the validated JSON-compatible PPO mapping or `None`; never include a model or executable object. |
| `validate_state(document, scenario)` | Game-state codec, after generic validation | Enforce strict extension shape and existing 9×9 invariants without mutating the game. Reject missing/stray state. |
| `restore_state(game, document)` | Game-state hydrator, after validation | Verify game-bound artifact availability and restore PPO pending state/RNG; no inference or rule evaluation. |
| `authorize(game, command_kind, sparse_board=None)` | Ordinary command, before mutation | Enforce seat/phase/controller permissions and submitted-board constraints for PPO games; no-op otherwise. |
| `finalize_movement_if_completed(game, command_kind) -> bool` | Movement adapters, after core movement | For PPO games call core's generic completion transition at the existing command point; return whether it closed the phase. For ordinary games return `False` without changing status. |
| `combat_rng(game) -> Random | None` | Combat adapter, before constructing combat | Return the restored shared RNG for PPO games or `None` for ordinary games; omit the `rng` constructor argument when `None`. |
| `capture_rng(game)` | Movement/combat adapters, after successful resolution | Snapshot PPO RNG continuation into the saved extension; no-op otherwise. |
| `after_end_turn(game)` | End-turn adapter, after core transition | Refresh PPO pending IDs for the next eligible PPO movement turn (or empty on completion), then capture RNG; no-op otherwise. |

`finalize_movement_if_completed` is called after `/movement` and `/move`
regardless of whether its return value is used. For `/end-movement`, the
adapter skips its existing hold-objective scoring and `end_movement()` only
when the hook returns `True`; otherwise both run in their current order. All
three paths capture RNG after their existing scoring/transition steps. Combat
captures RNG after its existing scoring/completion steps. Authorization runs
before converting or applying a submitted sparse board. The adapter calls
`after_end_turn` only after core `end_turn()` succeeds.

The version-1 document retains these fields (other fields omitted):

```json
{
  "state_schema_version": 1,
  "ppo_state": null
}
```

For a PPO game, `ppo_state` is a JSON object with exactly the existing keys
`contract` (v3 policy contract string), `checkpoint_digest` (game-bound
SHA-256 digest string), `checkpoint_path` (`checkpoint.zip`),
`pending_unit_ids` (ordered list of unspent, living PPO slot IDs), and
`rng_state` (JSON list representation of a valid `random.Random.getstate()`
value). The PPO integration must reject malformed RNG state, not just a
wrongly typed top-level field.

## 5. Acceptance Criteria

- **AC-001:** Given an ordinary game or a pre-refactor version-1 snapshot,
  when it is created, encoded, decoded, and played through ordinary commands,
  then behavior and serialized field names remain unchanged; no model or
  agent-specific validation runs for that game.
- **AC-002:** Given a valid pre-refactor 9×9 snapshot with one pending order,
  when decoded and continued, then its saved digest, remaining slot, RNG
  continuation, core phase, and next command outcome match the existing path.
- **AC-003:** Given missing `ppo_state`, stray `ppo_state`, invalid seat or
  scenario, malformed/extra extension fields, invalid pending IDs, or a
  corrupted RNG state, when encoding or decoding, then the game is rejected
  before an order or mutation; no no-op fallback occurs.
- **AC-004:** Given a valid saved PPO game whose checkpoint is replaced, when
  GET or a command decodes it, then the existing distinct
  `ppoSavedCheckpointUnavailable` response is returned without using the new
  model; ordinary GETs and PPO-opponent commands do not reload model weights.
- **AC-005:** Given a PPO game, when the first seat tries an ordinary command
  or a client submits a board modifying PPO units/resolved phases, then it is
  rejected before core mutation. Given a valid Human, Random, or Q-Learning
  second-seat turn, its existing authorized commands still work.
- **AC-006:** Given completion during movement, combat, or end-turn, when an
  authorized command runs, then core remains the source of the result, terminal
  player/phase fields are consistent, and scoring/combat do not run an extra
  time. The next active PPO turn has only living eligible pending units.
- **AC-007:** Given a successful order/opponent command and a reload or exact
  idempotent retry, when play continues, then the saved RNG and command result
  are stable and no order or random draw is repeated. Non-PPO combat retains
  its old constructor/default-RNG behavior.

## 6. Test Automation Strategy

- **Unit:** Test the integration selector and no-op/PPO hooks through public
  contracts, including mismatched scenario/seat/extension combinations and
  strict extension parsing. Do not assert private hook-call counts or log text.
- **Codec/API:** Decode representative version-1 snapshots from before the
  refactor; check ordinary and PPO round trips, missing/tampered state,
  replaced artifact errors, and GET without model reload. Exercise Human,
  Random, and Q-Learning opponent commands, board tampering, combat RNG,
  terminal phases, receipt replay, and a simulated repository restart.
- **Integration:** Retain the existing increment-07 backend/browser acceptance
  gate separately; this refactor does not claim it. Run
  `./server-side-checks.sh` and the relevant existing API/PPO tests. Run web
  tests only if web files or client-facing behavior change (neither is planned).
- **Data:** Use test-created snapshots and configured test artifacts; do not
  regenerate or replace the tracked trained checkpoints for this refactor.

## 7. Rationale & Context

`Game.finalize_completed_phase()` in core is a general transition, while
`command_adapters/ppo_order.py` is properly specialized for inference. The
unwanted coupling is the generic validator/hydrator calling `ppo_state` and
ordinary movement/combat adapters repeatedly branching on PPO. Centralizing
these policies removes the need to add more such branches as agent contracts
evolve. Preserving the existing `ppo_state` wire key avoids invalidating saved
games or changing receipt serialization just to move code. This boundary does
not make the 9×9 observation, slots, artifact loader, or policy usable on
Crossroads; that scenario needs its own declared contract and evidence.

## 8. Dependencies & External Integrations

- **EXT-001:** Existing core scenario loading, legal movement, combat, scoring,
  and completed-phase transition; only core determines game outcomes.
- **DAT-001:** Version-1 canonical JSON game documents and committed response
  receipts; their format and compatibility remain unchanged.
- **INF-001:** Configured PPO serving artifact and game repository, whether
  in-memory or durable; no additional service or registry is introduced.
- **PLT-001:** Existing API runtime and PPO inference dependencies; neither
  version pins nor trained weights change as part of this refactor.

## 9. Examples & Edge Cases

1. An ordinary Random-versus-Human game has `ppo_state: null`: selection chooses
   no-op, and combat is constructed without an explicit `rng` argument.
2. A 9×9 PPO game with missing `ppo_state` still selects the 9×9 integration
   from its scenario/seat and fails validation. A foreign scenario with
   `ppo_state` also selects it and fails; neither silently becomes ordinary.
3. On a PPO order that kills the last opponent during movement, core closes the
   completed phase; no later combat or prediction runs. A second-seat turn
   ending normally refreshes pending IDs for living PPO units.
4. If the serving artifact has a different digest after restart, decoding the
   saved game fails with the existing checkpoint-unavailable response. A fresh
   non-PPO game must not depend on that artifact.

## 10. Validation Criteria

The refactor is complete only when AC-001–AC-007 pass, the generic persistence
validator/hydrator and ordinary adapters no longer import or branch on PPO
implementation modules, version-1 snapshots still decode, and server-side
checks pass. Review the changed modules for duplicated command sequences and
preserve API/core/schema boundaries. Do not mark increment 07 complete or
change PPO.md/schedule status merely because this refactor passes: its durable
browser demonstration must be verified independently.

## 11. Related Specifications / Further Reading

- [Increment 07: trained 9×9 human-visible slice](07-trained-9x9-human-visible-slice.md)
- [Playable Crossroads schedule](playable-player-schedule.md)
- [PPO implementation schedule](implementation-schedule.md)
- [PPO project status](../../battle_agent_rl/PPO.md)

## Open Questions

No questions.

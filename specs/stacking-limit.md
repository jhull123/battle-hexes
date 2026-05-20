# Stacking Limit (Implementable Spec)

## 1. Overview
Implement scenario-defined **stacking limits** so a hex may contain at most _N friendly units_ when a scenario opts in.

This feature enforces the rulebook behavior in movement validation and execution, while preserving backward compatibility for scenarios that do not define a stacking limit.

## 2. Rulebook Source of Truth
From `HOW_TO_PLAY.md`:
- A scenario may define a stacking limit: the maximum number of friendly units in one hex.
- If a scenario does not define stacking limit, there is no stacking limit.
- A unit may not move into a hex if doing so would exceed the stacking limit.
- Enemy units may not occupy the same hex.

## 3. Goals
- Add an optional scenario-level `stacking_limit` setting.
- Enforce stacking limit consistently in core movement rules.
- Ensure movement plans cannot bypass the limit.
- Keep behavior deterministic and easy to test.
- Preserve existing scenario behavior when `stacking_limit` is omitted.

## 4. Non-goals
- No changes to combat resolution.
- No changes to retreat rules beyond normal occupancy legality checks already present.
- No redesign of API surface beyond fields/errors needed for this rule.
- No UI redesign; only minimal feedback updates for invalid moves.

## 5. Current Behavior (Gap)
- Enemy co-occupancy is already forbidden.
- There is currently no explicit scenario-level cap on friendly units per hex.
- Movement can therefore stack arbitrarily many friendly units in one hex.

## 6. Desired Behavior

### 6.1 Scenario option
- Add optional scenario property: `stacking_limit`.
- Semantics:
  - Integer.
  - Applies globally to all hexes unless a future feature adds per-terrain/per-hex overrides.
  - Represents max friendly units allowed in the same hex at one time.

### 6.2 Default behavior
- If `stacking_limit` is absent (`null`/unset), stacking is unlimited.
- Existing scenarios that omit this field continue to behave exactly as today.

### 6.3 Movement rule
- A movement step into destination hex is legal only if:
  1. destination does not contain enemy unit(s), and
  2. resulting count of moving unit's side in destination is `<= stacking_limit` when limit is configured.

### 6.4 Planned movement execution
- Validation must account for occupancy changes as plans resolve so simultaneous/sequence effects cannot overstack.
- If multiple movement plans target the same hex in one resolution pass:
  - enforce the limit according to existing engine ordering semantics,
  - reject/stop moves that would be the first to exceed the limit under that ordering.

### 6.5 No partial exceptions
- Stacking limit applies to all friendly units equally (including zero-move / special units).
- No terrain, unit-type, or phase-specific exemptions in this feature.

### 6.6 Retreat path and destination legality
- Retreat movement must also respect stacking limits.
- A retreat may not:
  - cross through intermediate hexes that would violate stacking limit constraints, or
  - end on a hex where friendly occupancy would exceed `stacking_limit`.
- If existing retreat resolution already validates enemy occupancy / map bounds, stacking-limit checks must be added alongside those existing legality checks.

## 7. Data Model and Schema Changes

### 7.1 Core scenario model
- Add optional `stacking_limit` field on scenario settings/root model (where other global rules live).
- Represent as optional integer (`int | None`).

### 7.2 Scenario JSON validation
- Accept omitted `stacking_limit`.
- If provided, require integer and value `>= 1`.
  - `0` and negatives are invalid.
  - Non-integer numeric/string values are invalid.
- Provide clear validation error message indicating invalid field and accepted range.

### 7.3 API contracts
- Include `stacking_limit` in scenario payloads returned by API if scenario metadata is exposed there.
- Preserve backward compatibility for clients that ignore unknown fields.

## 8. Core Rules Integration

### 8.1 Legal move check helper
- Centralize occupancy legality check into a reusable helper used by:
  - per-step movement validation,
  - movement-plan execution guardrails.

Pseudo-rule:

```text
can_enter_hex(unit, destination_hex):
  if destination contains enemy: return false
  if scenario.stacking_limit is None: return true
  friendly_count = count friendly units currently in destination
  # entering unit would increase friendly_count by 1 unless already in same hex and no-op
  return (friendly_count + entering_increment) <= scenario.stacking_limit
```

### 8.2 No-op / same-hex edge
- If engine ever allows “move to current hex” as a no-op, this must not artificially fail stacking checks.
- If no-op moves are already invalid, preserve that behavior.

### 8.3 Interaction with adjacency stop rule
- Existing “stop when entering enemy-adjacent hex” remains unchanged.
- Stacking legality is checked before committing entry to a hex.

### 8.4 Retreat resolution integration
- Reuse the same occupancy legality helper (or equivalent shared logic) for retreat-step validation so movement and retreat cannot diverge in stacking behavior.
- If a retreat sequence has multiple candidate hexes, candidate filtering must exclude any option that crosses or ends in a stacking-illegal state.

## 9. Error and Feedback Semantics
- Invalid move due to stacking should produce a specific reason code/message (e.g., `STACKING_LIMIT_EXCEEDED`) where the system currently reports movement invalidity reasons.
- If the engine currently uses generic invalid-move responses, at minimum include enough message text for frontend to display a useful explanation.

## 10. Required Changes by Project

### 10.1 `battle_hexes_core`
- Scenario/domain model: add optional `stacking_limit`.
- Scenario parsing + validation: enforce type/range rules.
- Movement validation/execution: enforce stacking cap using centralized helper.
- Unit tests:
  - unlimited when field missing,
  - legal moves at exactly limit,
  - illegal move when exceeding limit,
  - enemy co-occupancy still illegal,
  - multi-plan contention into same hex respects resolver order + cap.

### 10.2 `battle_hexes_api`
- Ensure request/response models (if scenario serialized here) include `stacking_limit`.
- Ensure movement endpoints surface stacking-limit invalidity reason.
- Add/adjust API tests for invalid move messaging and scenario field passthrough.

### 10.3 `battle-hexes-web`
- If move-invalid reason codes are exposed to UI, map stacking-limit failure to player-facing message.
- Do not draw a movement arrow for a destination hex when the move is currently illegal due to stacking limit.
- Add/update unit tests for displayed invalid-move explanation (if message mapping exists).
- Add/update unit tests for movement-arrow suppression on stacking-illegal destinations.

## 11. Test Plan

### 11.1 Core unit tests
1. **No configured limit**: 3+ friendlies in one hex remains legal.
2. **Limit=1**: moving into friendly-occupied hex fails.
3. **Limit=2**: move that reaches 2 succeeds; move that would reach 3 fails.
4. **Enemy occupancy**: still fails independent of stacking value.
5. **Sequential contention**: two moves into same hex with one remaining slot => first succeeds, second fails per resolver order.
6. **Validation**: `stacking_limit` accepts omitted and positive integers; rejects `0`, negative, float, string.
7. **Retreat destination**: retreat cannot end on a hex that would exceed stacking limit.
8. **Retreat crossing**: retreat path generation/execution excludes intermediate hexes that would violate stacking limit.

### 11.2 API tests
- Scenario payload includes `stacking_limit` when set.
- Movement invalid response includes stacking-limit reason/message.

### 11.3 Web tests
- Invalid move reason renders expected message in UI (if reason rendering is already implemented).
- Move arrow is not rendered for a stacking-illegal destination hex.

## 12. Backward Compatibility
- Existing scenarios without `stacking_limit` are unaffected.
- Existing clients continue to work; new field is additive.
- Existing saved tests expecting unlimited stacking remain valid unless they relied on malformed scenario values that will now be rejected.

## 13. Rollout Notes
- Add at least one scenario fixture using non-null `stacking_limit` for regression coverage.
- Update docs/examples in scenario authoring guidance to show:

```json
{
  "stacking_limit": 2
}
```

## Open Questions
No questions.

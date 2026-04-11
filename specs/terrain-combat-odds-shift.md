# Terrain Modifies Combat Odds (Implementable Spec)

## 1. Overview
- Add terrain-based combat odds shifts to Battle Hexes combat resolution.
- Terrain affects combat by shifting the **final CRT odds column** left/right.
- Only the **defender's terrain** contributes to this shift.
- Scenario terrain definitions already support `combat_odds_shift`; this feature wires that value into validation and combat resolution.

## 2. Goals
- Apply a defender-terrain odds shift during combat in a deterministic, testable way.
- Keep compatibility with existing scenarios where `combat_odds_shift` may be absent.
- Ensure shifts are bounded by CRT column limits.
- Keep behavior explicit and easy to reason about in code and tests.

## 3. Non-goals
- Do not redesign the CRT or add new CRT columns.
- Do not introduce additional combat modifiers (leadership, weather, unit state, etc.) in this change.
- Do not implement stacked/multi-source modifier systems in this change.
- Do not change UI/UX behavior beyond whatever is necessary to reflect resolved combat results.

## 4. Current behavior
- Combat resolution currently:
  1. Totals attacker strength.
  2. Totals defender strength.
  3. Maps ratio to a CRT odds column.
  4. Rolls and reads result from CRT.
- No terrain-based odds shift is applied today.
- Scenario terrain data may already include `combat_odds_shift` (e.g., `d_day_crossroads.json`), but behavior is effectively neutral unless runtime logic consumes it.

## 5. Desired behavior
- The combat flow must apply terrain shift **after** base odds column selection and **before** CRT roll lookup.
- Terrain modifies **odds column index**, not raw attacker/defender strengths.
- Shift direction:
  - Negative shift => move left (favors defender).
  - Positive shift => move right (favors attacker).
- Defender terrain only:
  - Use terrain of the hex occupied by the defending unit(s).
  - Ignore attacker terrain for this feature.
- Missing `combat_odds_shift` on terrain defaults to `0`.

## 6. Scenario schema changes (already decided)
- Continue using `combat_odds_shift` on terrain definitions in scenario JSON.
- Field semantics:
  - Type: integer.
  - Meaning: number of CRT columns to shift from base odds.
- Backward compatibility:
  - Terrain definitions lacking `combat_odds_shift` remain valid and behave as `0`.
  - Existing scenarios must not require edits unless they want non-zero terrain effects.

## 7. Validation rules
- Scenario validation should enforce:
  - `combat_odds_shift` (if present) is an integer.
- `combat_odds_shift` is optional.
- If omitted, system sets/reads it as `0` at model/parsing boundary.
- No hard min/max required at schema layer for this feature; runtime clamping against CRT bounds guarantees safe behavior.

## 8. Combat resolution rules
- Let CRT columns be ordered left-to-right (worst for attacker to best for attacker), e.g.:
  `1:7, 1:6, 1:5, 1:4, 1:3, 1:2, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1`.
- Resolution steps:
  1. Compute base odds column from attacker/defender strengths using existing logic.
  2. Read defender terrain `combat_odds_shift` (default `0` if absent).
  3. Compute shifted index: `shifted = base_index + combat_odds_shift`.
  4. Clamp: `final_index = min(max(shifted, 0), last_column_index)`.
  5. Use `final_index` column for CRT roll result lookup.
- Example (required behavior):
  - Base odds `2:1` (index 6 in the list above), defender terrain shift `-1` => final odds `1:1` (index 5).

## 9. Edge cases
- Very negative shifts clamp to leftmost column (`1:7`).
- Very positive shifts clamp to rightmost column (`7:1`).
- Missing terrain definition field (`combat_odds_shift`) behaves as `0`.
- If attacker and defender occupy different terrain types, only defender terrain applies.
- If defender terrain lookup fails due to invalid scenario state, current engine error-handling behavior should remain unchanged (do not silently fabricate terrain).

## 10. Required code changes by area/module

### A) Scenario parsing / domain model
- Ensure terrain model includes optional `combat_odds_shift` with default `0` when absent.
- Ensure JSON parsing/deserialization maps this field correctly.
- Ensure serialization (if present) preserves explicit non-zero values.

### B) Scenario validation
- Add/update validation for terrain `combat_odds_shift` type correctness (integer when provided).
- Preserve backward compatibility for existing terrain entries without the field.

### C) Combat resolution logic
- In the combat odds-to-CRT path, insert defender-terrain shift application between:
  - base odds determination, and
  - CRT result lookup.
- Implement/centralize CRT index shift + clamp behavior to avoid duplicated ad-hoc logic.
- Ensure code clearly indicates this is a column modifier, not a strength modifier.

### D) Integration points (API / state projection if applicable)
- Ensure any payloads or logs that expose resolved odds reflect the final shifted odds column.
- If API returns combat detail, include whichever odds representation is already standard (base and/or final) without breaking existing contracts.

### E) Tests
- Add/update unit tests in core combat and scenario/model validation layers.
- Add/update API-level tests only where combat detail payload/contract is affected.

## 11. Test plan
- Add unit tests for combat resolution:
  - No terrain shift: base odds and final odds are identical.
  - Negative shift: e.g., base `2:1`, shift `-1`, final `1:1`.
  - Clamp at left boundary: base at/near left edge plus negative shift stays at leftmost column (including `1:7` deterministic outcome behavior).
  - Clamp at right boundary: base at/near right edge plus positive shift stays at rightmost column (including `7:1` deterministic outcome behavior).
  - Defender terrain used instead of attacker terrain.
- Add unit tests for scenario parsing/model:
  - Missing `combat_odds_shift` defaults to `0`.
  - Present integer `combat_odds_shift` is accepted and loaded.
- Add unit tests for validation:
  - Non-integer `combat_odds_shift` is rejected with clear error.
- Update any existing tests that assert odds mapping if they currently assume no terrain effects.

## 12. Questions for Jason
- Should this release expose both **base odds** and **final shifted odds** in combat result APIs/logs, or only final odds?
Answer: base odds and final odds should be included in logs and api for explainability.
- Should we require every terrain type to explicitly declare `combat_odds_shift` in scenario authoring guidelines, even though runtime default is `0`?
Answer: No!
- Do we want to reserve a future extension point for stacking multiple odds shifts (terrain + other effects), and if yes should we shape the internal API now?
Answer: not needed
- Should rulebook/docs include a standard terrain modifier table (example values) as part of this feature rollout?
Answer: no.
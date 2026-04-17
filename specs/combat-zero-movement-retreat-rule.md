# Zero-Movement Units Forced to Retreat (Implementable Spec)

## 1. Overview
Implement the Combat Results note from `HOW_TO_PLAY.md`: units with zero movement cannot retreat and are eliminated whenever a combat result would force them to retreat.

Rule text to implement:
- "Units with zero movement (fixed units such as garrisons) cannot retreat."
- "These units are eliminated when forced to retreat."

This behavior must apply consistently to combat outcomes that include retreat effects.

## 2. Goals
- Enforce zero-movement retreat immunity (cannot actually move as retreat).
- Convert forced-retreat outcomes on zero-movement units into elimination.
- Keep combat resolution deterministic and explicit in logs/API responses.
- Preserve existing retreat behavior for units with movement greater than zero.

## 3. Non-goals
- Do not redesign retreat pathfinding/hex selection rules.
- Do not change CRT probabilities or combat odds calculations.
- Do not change defensive-fire retreat rules unless they already share the same forced-retreat resolution path and inherit this behavior naturally.
- Do not rebalance unit stats/scenarios.

## 4. Current behavior summary
- Combat results can include retreat outcomes (`Defender Retreat 2`, `Attacker Retreat 2`).
- Rulebook note requires a special case for units with movement `0`, but this behavior is not yet fully codified across all resolution layers.

## 5. Desired behavior

### 5.1 Retreat conversion rule
When a unit is forced to retreat by a combat result:
1. Check the unit's base movement stat.
2. If movement is `0`, do not execute retreat movement.
3. Eliminate that unit immediately instead.

### 5.2 Scope of "forced to retreat"
This rule applies to combat result outcomes in the Combat Results section:
- Defender Retreat 2
- Attacker Retreat 2
- Exchange (only for the side(s) where exchange resolution requires retreat under existing game-system rules)

If Exchange for the current system does not require retreat, this rule has no additional effect for that branch.

### 5.3 Multi-unit implications
- If a combat result forces retreat on multiple units, evaluate each unit independently.
- Zero-movement units are eliminated; non-zero-movement units follow normal retreat rules.

### 5.4 Elimination semantics
A zero-movement unit eliminated due to forced retreat is removed exactly as any other elimination result:
- removed from board occupancy/state,
- no further retreat processing for that unit,
- included in combat/event logs as elimination caused by forced retreat conversion.

## 6. Data/model expectations
- Unit movement value is authoritative from unit stats (`movement` / equivalent field).
- "Zero movement" means exactly numeric `0`.
- Negative movement values remain invalid per existing validation (no new behavior introduced).

## 7. Resolution flow changes
Insert an explicit guard in combat retreat resolution:
1. Identify units that must retreat and retreat distance.
2. For each unit, call a shared predicate/helper like `cannot_retreat(unit)` (true for movement `0`).
3. If `cannot_retreat`:
   - emit elimination action/result reason `forced_retreat_no_movement` (name can vary but should be explicit),
   - skip retreat destination selection.
4. Else perform existing retreat resolution logic.

Prefer centralizing this guard in one retreat-resolution path to avoid duplicated checks in attacker/defender branches.

## 8. API and state projection behavior
If combat detail payloads/events expose per-unit outcomes, they should distinguish:
- normal elimination,
- elimination due to forced retreat with zero movement.

Minimum requirement:
- Outcome is unambiguously visible as elimination.

Preferred requirement (for explainability):
- include a machine-readable reason/cause field indicating forced-retreat conversion.

No breaking API contract changes; extend optional metadata where possible.

## 9. Logging/UX expectations
- Combat log text should reflect that the unit was eliminated because it could not retreat.
- If current UI already renders elimination generically, maintain compatibility and optionally add richer message copy in a follow-up.

## 10. Test plan

### 10.1 Core combat tests
Add/update tests to cover:
- Defender retreat result against defender with movement `0` => defender eliminated.
- Attacker retreat result against attacker with movement `0` => attacker eliminated.
- Retreat result against movement `> 0` => normal retreat still occurs.
- Mixed stack/participants (if supported): only zero-movement units convert to elimination.
- Exchange branch: if exchange includes retreat in current implementation, verify zero-movement conversion there too.

### 10.2 API tests (if API exposes combat outcomes)
- Response includes elimination outcome for zero-movement forced-retreat case.
- If reason fields/events exist, assert forced-retreat conversion reason is present.

### 10.3 Regression tests
- Existing elimination and retreat scenarios for mobile units remain unchanged.
- No impact on odds-column selection or CRT lookup behavior.

## 11. Implementation notes by package
- `battle_hexes_core`: primary rules implementation and unit tests.
- `battle_hexes_api`: verify serialized combat outcomes/events remain accurate and (optionally) reason-coded.
- `battle-hexes-web`: only adjust display text if API/log payload gains explicit cause metadata.

## 12. Acceptance criteria
- Any combat result that forces retreat eliminates units whose movement stat is `0`.
- No retreat displacement is attempted for those units.
- Mobile units still retreat per existing rules.
- Automated tests cover attacker and defender retreat conversion cases.
- Rulebook note behavior is represented in implementation and observable outcomes.

## Open Questions
No questions.

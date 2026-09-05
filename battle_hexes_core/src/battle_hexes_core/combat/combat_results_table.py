"""Read-only projection types for the authoritative combat results table."""

from dataclasses import dataclass

from battle_hexes_core.combat.combatresult import CombatResult


@dataclass(frozen=True)
class CombatResultsTableRow:
    """One odds column and either rolled or automatic outcomes."""

    odds: tuple[int, int]
    results: tuple[CombatResult, ...] | None = None
    automatic_result: CombatResult | None = None


@dataclass(frozen=True)
class CombatResultsTable:
    """Ordered, client-independent reference to all combat outcomes."""

    die_rolls: tuple[int, ...]
    rows: tuple[CombatResultsTableRow, ...]

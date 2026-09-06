"""Build and retain authoritative defensive-fire history events."""

from battle_hexes_core.defensivefire.defensive_fire_event import (
    DefensiveFireEvent,
    DefensiveFireUnitSnapshot,
)


class DefensiveFireEventRecorder:
    """Convert resolver results into durable, player-readable history."""

    def __init__(self, board, game_log: list[DefensiveFireEvent]):
        self.board = board
        self.game_log = game_log

    def record(self, results, target_unit, turn_number, player_name) -> None:
        units_by_id = {
            str(unit.get_id()): unit for unit in self.board.get_units()
        }
        for result in results:
            firing_unit = units_by_id[result.firing_unit_id]
            outcome = self._outcome(result)
            self.game_log.append(DefensiveFireEvent(
                turn_number=turn_number,
                player_name=player_name,
                firing_unit=DefensiveFireUnitSnapshot(
                    result.firing_unit_id,
                    firing_unit.get_name(),
                ),
                target_unit=DefensiveFireUnitSnapshot(
                    result.target_unit_id,
                    target_unit.get_name(),
                ),
                success_probability=result.probability,
                random_roll=result.roll,
                outcome=outcome,
                summary=self._summary(
                    firing_unit.get_name(),
                    target_unit.get_name(),
                    outcome,
                ),
            ))

    @staticmethod
    def _outcome(result) -> str:
        if result.outcome == "no_effect":
            return "noEffect"
        if result.retreat_destination is None:
            return "eliminated"
        return "retreated"

    @staticmethod
    def _summary(
        firing_unit_name: str,
        target_unit_name: str,
        outcome: str,
    ) -> str:
        if outcome == "retreated":
            return (
                f"{firing_unit_name} forced {target_unit_name} to retreat."
            )
        if outcome == "eliminated":
            return f"{firing_unit_name} eliminated {target_unit_name}."
        return (
            f"{firing_unit_name} fired at {target_unit_name} with no effect."
        )

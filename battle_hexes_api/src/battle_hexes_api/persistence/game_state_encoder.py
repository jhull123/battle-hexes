"""Encode a live core game into the persistence document."""

from dataclasses import asdict

from battle_hexes_core.scenario.scenario_loader import ScenarioData

from .game_state_document import Document


class GameStateEncoder:
    def __init__(self, schema_version: int) -> None:
        self._schema_version = schema_version

    def encode(
        self, game, scenario: ScenarioData, scenario_version: str
    ) -> Document:
        board_units, all_units, pending_ids = self._unit_indexes(game)
        raw_document = {
            "state_schema_version": self._schema_version,
            "game_id": str(game.id),
            "scenario_id": game.scenario_id,
            "scenario_version": scenario_version,
            "players": self._players(game),
            "current_player_name": (
                game.current_player.name if game.current_player else None
            ),
            "turn_number": game.turn_number,
            "current_phase": game.current_phase,
            "pending_combats": game.pending_combats,
            "terminal": game._terminal,
            "game_status": asdict(game.get_game_status()),
            "scores": self._scores(game),
            "active_unit_ids": list(board_units),
            "units": self._units(
                scenario, board_units, all_units, pending_ids
            ),
            "reinforcements": [
                {"group_id": group.id, "entered": group.entered}
                for group in game.reinforcements_deployer.groups
            ],
            "reinforcement_history": [
                asdict(event)
                for event in game.reinforcements_deployer.game_log
            ],
            "combat_history": [asdict(event) for event in game.combat_log],
            "defensive_fire_history": [
                asdict(event) for event in game.defensive_fire_log
            ],
        }
        return Document.model_validate(raw_document)

    @staticmethod
    def _players(game):
        return [
            {"name": player.name, "type_id": type_id}
            for player, type_id in zip(game.players, game.player_type_ids)
        ]

    @staticmethod
    def _scores(game):
        return [
            {
                "player_name": player.name,
                "points": game.score_tracker.get_score(player),
            }
            for player in game.players
        ]

    @staticmethod
    def _unit_indexes(game):
        board_units = {
            str(unit.get_id()): unit for unit in game.board.get_units()
        }
        all_units = dict(board_units)
        pending_ids = set()
        for group in game.reinforcements_deployer.groups:
            for unit in group.units:
                all_units[str(unit.get_id())] = unit
                if not group.entered:
                    pending_ids.add(str(unit.get_id()))
        return board_units, all_units, pending_ids

    @staticmethod
    def _units(scenario, board_units, all_units, pending_ids):
        units = []
        for definition in scenario.units:
            unit = all_units[definition.id]
            if definition.id in board_units:
                disposition = "active"
            elif definition.id in pending_ids:
                disposition = "reinforcement"
            else:
                disposition = "eliminated"
            coords = unit.get_coords() if disposition == "active" else None
            ended_eligible_key = (
                "ended_last_friendly_turn_with_defensive_fire_eligibility"
            )
            units.append(
                {
                    "unit_id": definition.id,
                    "disposition": disposition,
                    "row": coords[0] if coords else None,
                    "column": coords[1] if coords else None,
                    "movement_points_remaining": (
                        unit.current_turn_movement_points_remaining
                    ),
                    ended_eligible_key: getattr(unit, ended_eligible_key),
                    "forced_to_retreat_since_last_friendly_turn": (
                        unit.forced_to_retreat_since_last_friendly_turn
                    ),
                    "defensive_fire_spent_this_off_turn": (
                        unit.defensive_fire_spent_this_off_turn
                    ),
                    "defensive_fire_available": unit.defensive_fire_available,
                    "defensive_fire_modifier": unit.defensive_fire_modifier,
                }
            )
        return units

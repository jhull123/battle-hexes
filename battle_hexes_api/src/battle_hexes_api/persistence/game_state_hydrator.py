"""Hydrate a detached core game from a validated persistence document."""

import uuid

from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_core.gamecreator.gamecreator import (
    GameCreator as CoreCreator,
)
from battle_hexes_core.scoring.game_status_evaluator import GameStatus

from .game_state_document import Document
from .game_state_events import (
    decode_combat_event,
    decode_defensive_fire_event,
    decode_reinforcement_event,
)


class GameStateHydrator:
    def hydrate(self, document: Document, scenario_data):
        game, players = self._build_baseline(document, scenario_data)
        units = self._index_units(game)
        self._restore_board(game, document, units)
        self._restore_units(document, units)
        self._restore_reinforcements(game, document)
        self._restore_runtime(game, document, players)
        self._restore_histories(game, document)
        self._reconnect_players(game, players)
        return game

    @staticmethod
    def _build_baseline(document, scenario_data):
        players = [
            GameCreator._create_player(player.type_id, player.name, [], None)
            for player in document.players
        ]
        _, players, _, game = CoreCreator().build_game_components(
            scenario_data.to_core(), players
        )
        game.id = uuid.UUID(document.game_id)
        game.scenario_id = document.scenario_id
        game.scenario_version = document.scenario_version
        game.player_type_ids = [player.type_id for player in document.players]
        return game, players

    @staticmethod
    def _index_units(game):
        units = {str(unit.id): unit for unit in game.board.get_units()}
        for group in game.reinforcements_deployer.groups:
            units.update((str(unit.id), unit) for unit in group.units)
        return units

    @staticmethod
    def _restore_board(game, document, units):
        saved_units = {unit.unit_id: unit for unit in document.units}
        game.board.units = {}
        for unit_id in document.active_unit_ids:
            saved = saved_units[unit_id]
            game.board.add_unit(units[unit_id], saved.row, saved.column)

    @staticmethod
    def _restore_units(document, units):
        attributes = (
            "ended_last_friendly_turn_with_defensive_fire_eligibility",
            "forced_to_retreat_since_last_friendly_turn",
            "defensive_fire_spent_this_off_turn",
            "defensive_fire_available",
            "defensive_fire_modifier",
        )
        for saved in document.units:
            unit = units[saved.unit_id]
            if saved.disposition != "active":
                unit.set_coords(None, None)
            unit.current_turn_movement_points_remaining = (
                saved.movement_points_remaining
            )
            for attribute in attributes:
                setattr(unit, attribute, getattr(saved, attribute))

    @staticmethod
    def _restore_reinforcements(game, document):
        for group, saved in zip(
            game.reinforcements_deployer.groups, document.reinforcements
        ):
            group.entered = saved.entered

    @staticmethod
    def _restore_runtime(game, document, players):
        game.turn_number = document.turn_number
        game.current_player = next(
            (
                player
                for player in players
                if player.name == document.current_player_name
            ),
            None,
        )
        game.current_phase = document.current_phase
        game.pending_combats = [
            combat.model_dump() for combat in document.pending_combats
        ]
        game._terminal = document.terminal
        game.game_status = GameStatus(**document.game_status.model_dump())
        game.score_tracker.set_scores(
            (player, score.points)
            for player, score in zip(players, document.scores)
        )

    @staticmethod
    def _restore_histories(game, document):
        game.reinforcements_deployer.game_log = [
            decode_reinforcement_event(value)
            for value in document.reinforcement_history
        ]
        game.combat_log = [
            decode_combat_event(value) for value in document.combat_history
        ]
        game.defensive_fire_log = [
            decode_defensive_fire_event(value)
            for value in document.defensive_fire_history
        ]

    @staticmethod
    def _reconnect_players(game, players):
        for player in players:
            if hasattr(player, "_board"):
                player._board = game.board

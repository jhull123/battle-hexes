"""Explicit API-owned saved-game and ordinary-command integration selection."""

from battle_hexes_api.persistence.errors import SavedGameIncompatibleError

from .ppo_state import TYPE_ID, SCENARIO_ID


class NoAgentIntegration:
    def initial_state(self, game):
        pass

    def encode_state(self, game):
        return None

    def validate_state(self, document, scenario):
        pass

    def restore_state(self, game, document):
        pass

    def authorize(self, game, command_kind, sparse_board=None):
        pass

    def finalize_movement_if_completed(self, game, command_kind):
        return False

    def combat_rng(self, game):
        return None

    def capture_rng(self, game):
        pass

    def after_end_turn(self, game):
        pass


class ExperimentalPpoIntegration(NoAgentIntegration):
    def initial_state(self, game):
        from .ppo_state import initial_state
        initial_state(game)

    def encode_state(self, game):
        from .ppo_state import validate_state
        state = getattr(game, "ppo_state", None)
        validate_state(state, game)
        return state

    def validate_state(self, document, scenario):
        from .ppo_state import validate_state
        validate_state(document.ppo_state, document)

    def restore_state(self, game, document):
        from .ppo_state import restore_state
        restore_state(game, document.ppo_state)

    def authorize(self, game, command_kind, sparse_board=None):
        from .ppo_opponent import (check_opponent_board, require_cpu_opponent,
                                   require_human, require_opponent)
        if command_kind == "movement":
            require_cpu_opponent(game)
        elif command_kind == "move":
            require_human(game, "movement")
        else:
            phase = {"end-movement": "movement", "combat": "combat",
                     "end-turn": "end_turn"}[command_kind]
            require_opponent(game, phase)
        if sparse_board is not None:
            check_opponent_board(game, sparse_board)

    def finalize_movement_if_completed(self, game, command_kind):
        return game.finalize_completed_phase()

    def combat_rng(self, game):
        return game.ppo_rng

    def capture_rng(self, game):
        from .ppo_state import capture_rng
        capture_rng(game)

    def after_end_turn(self, game):
        game.ppo_state["pending_unit_ids"] = (
            [unit.id for unit in game.board.get_units_for_player(
                game.players[0])]
            if game.current_player is game.players[0] else [])
        self.capture_rng(game)


class AgentIntegrations:
    """Select by authoritative scenario, seats and extension presence."""

    def __init__(self):
        self._ordinary = NoAgentIntegration()
        self._experimental = ExperimentalPpoIntegration()

    def select(self, scenario_id, player_type_ids, extension_present):
        if (scenario_id == SCENARIO_ID or TYPE_ID in player_type_ids
                or extension_present):
            if (scenario_id != SCENARIO_ID or len(player_type_ids) != 2
                    or player_type_ids[0] != TYPE_ID
                    or player_type_ids[1] not in
                    ("human", "random", "q-learning")):
                raise SavedGameIncompatibleError("ppo_scenario_or_seat")
            return self._experimental
        return self._ordinary

    def for_game(self, game):
        return self.select(game.scenario_id, game.player_type_ids,
                           getattr(game, "ppo_state", None) is not None)

    def for_document(self, document):
        return self.select(document.scenario_id,
                           [player.type_id for player in document.players],
                           document.ppo_state is not None)


integrations = AgentIntegrations()

"""Adapter for creating an authoritative game."""

from battle_agent_rl.scripted import ScriptedOpening
from battle_hexes_core.scenario.scenario_loader import load_scenario_data

from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import CreatedGame


class CreateGameAdapter:
    """Validate scenario input and construct a game with save metadata."""

    def __init__(
        self,
        request,
        scenario_loader=load_scenario_data,
        game_creator=GameCreator,
    ):
        self._request = request
        self._scenario_loader = scenario_loader
        self._game_creator = game_creator

    def __call__(self):
        scenario = self._scenario_loader(self._request.scenario_id)
        player_types = self._request.player_types
        options = {}
        if "scripted" in player_types:
            options["scripted_opening"] = ScriptedOpening(mode="randomized")
        game = self._game_creator.create_sample_game(
            self._request.scenario_id,
            player_types,
            **options,
        )
        return CreatedGame(
            game=game,
            scenario_id=self._request.scenario_id,
            scenario_version=scenario.version,
        )

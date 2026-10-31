"""Integration selection and version-1 extension validation."""

import json

import pytest

from battle_hexes_api.agent_integrations import (
    AgentIntegrations, ExperimentalPpoIntegration, NoAgentIntegration,
)
from battle_hexes_api.gamecreator import GameCreator
from battle_hexes_api.persistence import (
    GameStateCodec, SavedGameIncompatibleError, StoredGame,
)
from battle_hexes_core.scenario.scenario_loader import load_scenario_data


@pytest.mark.parametrize("scenario,players,present,expected", [
    ("elim_1", ["human", "random"], False, NoAgentIntegration),
    ("ppo_9x9_experimental", ["ppo-9x9-experimental", "human"], False,
     ExperimentalPpoIntegration),
    ("ppo_9x9_experimental", ["ppo-9x9-experimental", "random"], True,
     ExperimentalPpoIntegration),
])
def test_selects_authoritative_configuration(scenario, players, present,
                                             expected):
    assert isinstance(AgentIntegrations().select(scenario, players, present),
                      expected)


@pytest.mark.parametrize("scenario,players,present", [
    ("elim_1", ["human", "random"], True),
    ("elim_1", ["ppo-9x9-experimental", "human"], False),
    ("ppo_9x9_experimental", ["human", "random"], False),
    ("ppo_9x9_experimental", ["human", "ppo-9x9-experimental"], True),
    ("ppo_9x9_experimental", ["ppo-9x9-experimental", "human",
                              "random"], True),
])
def test_rejects_unsupported_agent_configurations(scenario, players, present):
    with pytest.raises(SavedGameIncompatibleError):
        AgentIntegrations().select(scenario, players, present)


def test_ordinary_extension_is_null_and_stray_state_fails():
    game = GameCreator.create_sample_game("elim_1", ["human", "random"])
    version = load_scenario_data("elim_1").version
    codec = GameStateCodec()
    document = json.loads(codec.encode(game, scenario_version=version))
    assert document["ppo_state"] is None
    document["ppo_state"] = {"unknown": True}
    saved = StoredGame(str(game.id), 1, 1, "elim_1", version,
                       json.dumps(document).encode(), 1, 2)
    with pytest.raises(SavedGameIncompatibleError):
        codec.decode(saved)
    game.ppo_state = document["ppo_state"]
    with pytest.raises(SavedGameIncompatibleError):
        codec.encode(game, scenario_version=version)

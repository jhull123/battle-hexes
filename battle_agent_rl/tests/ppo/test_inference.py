import random

import numpy as np
import pytest
import torch

from battle_agent_rl.ppo.artifacts import (
    CONTRACT, read_manifest, write_json,
)
from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)
from battle_agent_rl.ppo.experiment import train_run
from battle_agent_rl.ppo.gym_env import MaskedBattleHexesEnv
from battle_agent_rl.ppo.inference import PPOPlayer
from battle_agent_rl.ppo.local_game import play_local_game
from battle_agent_rl.ppo.scenario import create_game
from battle_agent_rl.ppo.turn_resolution import play_cycle
from battle_hexes_core.unit.faction import Faction


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    run_dir = tmp_path_factory.mktemp("inference") / "run"
    train_run(run_dir, 1, validation=[100], held_out=[200], seed=3,
              step_limit=4, total_timesteps=16, n_steps=8, batch_size=4)
    manifest = read_manifest(run_dir)
    manifest["selected"] = manifest["checkpoints"][0]
    write_json(run_dir / "manifest.json", manifest)
    return run_dir


def player(run, **options):
    return PPOPlayer.from_checkpoint(
        "Learner", [Faction("learner", "Learner", "blue")],
        run, **options,
    )


def budget_player(run, limit):
    loaded = player(run)
    return PPOPlayer(loaded.name, loaded.factions, loaded.model, limit)


def game_for(p, seed=42):
    rng = random.Random(seed)
    game = create_game(p, rng)
    p.bind_game(game)
    return game, rng


def test_manifest_entries_and_invalid_artifacts(run):
    manifest = read_manifest(run)
    manifest["selected"] = None
    write_json(run / "manifest.json", manifest)
    with pytest.raises(ValueError, match="selected"):
        player(run)
    first = manifest["checkpoints"][0]
    assert player(run, checkpoint=first["path"]).step_limit == 4
    with pytest.raises(ValueError, match="step limit"):
        player(run, checkpoint=first["path"], step_limit=5)
    with pytest.raises(ValueError, match="manifest"):
        player(run, checkpoint="other.zip")
    manifest["selected"] = first
    write_json(run / "manifest.json", manifest)
    assert player(run).step_limit == 4
    with pytest.raises(AttributeError):
        player(run).step_limit = 5
    manifest["contract"] = "wrong"
    write_json(run / "manifest.json", manifest)
    with pytest.raises(ValueError, match="contract"):
        player(run)
    manifest["contract"] = CONTRACT
    write_json(run / "manifest.json", manifest)
    archive = run / first["path"]
    original = archive.read_bytes()
    try:
        archive.write_bytes(b"invalid")
        with pytest.raises(ValueError, match="digest"):
            player(run)
    finally:
        archive.write_bytes(original)


@pytest.fixture
def bound(run):
    p = player(run)
    game, rng = game_for(p)
    return p, game, rng


def test_binding_scenario_and_turn_guards(run, bound):
    p, game, rng = bound
    p.bind_game(game)
    with pytest.raises(ValueError, match="another game"):
        p.bind_game(create_game(p, random.Random(1)))
    for mutate in (
        lambda g: g.get_board().get_hex(0, 0).set_terrain(object()),
        lambda g: g.get_board().set_stacking_limit(1),
        lambda g: g.set_defensive_fire_settings(None),
        lambda g: g.next_player(),
        lambda g: g.get_board().get_units()[0].set_coords(1, 0),
    ):
        other = player(run)
        candidate = create_game(other, random.Random(1))
        mutate(candidate)
        with pytest.raises(ValueError, match="Unsupported"):
            other.bind_game(candidate)
    before = [t.detach().clone() for t in p.model.policy.parameters()]
    plans = p.movement()
    assert len(plans) == 1
    unit = game.get_board().get_units_for_player(p)[0]
    assert plans[0].unit is unit
    assert game.get_board().shortest_path(
        unit, game.get_board().get_hex(*unit.get_coords()), plans[0].path[-1]
    ) == plans[0].path
    p.bind_game(game)
    with pytest.raises(RuntimeError, match="already issued"):
        p.movement()
    assert p.decisions_issued == 1
    game.apply_movement_plans(plans)
    with pytest.raises(RuntimeError, match="already issued"):
        p.movement()
    assert p.decisions_issued == 1
    if game.get_game_status().state == "in_progress":
        game.next_player()
        with pytest.raises(RuntimeError, match="turn"):
            p.movement()
    assert all(torch.equal(a, b) for a, b in zip(
        before, p.model.policy.parameters()
    ))
    p.combat_results([])
    p.end_game_cb()


def test_current_state_mask_readiness_and_invalid_prediction(bound):
    p, game, rng = bound
    env = MaskedBattleHexesEnv(step_limit=4)
    obs, _ = env.reset(seed=42)
    from battle_agent_rl.ppo.gym_env import encode_observation
    from battle_agent_rl.ppo.policy_state import action_mask, observation
    encoded = encode_observation(observation(game, p, 4))
    assert all(np.array_equal(obs[key], encoded[key]) for key in obs)
    assert env.action_masks().tolist() == list(action_mask(game, p))
    enemy = game.get_board().get_units_for_player(game.players[1])[0]
    enemy.set_coords(2, 2)
    enemy.ended_last_friendly_turn_with_defensive_fire_eligibility = False
    assert observation(game, p, 4)["defensive_fire_ready"][12] == 0

    class BadModel:
        def predict(self, obs, action_masks, deterministic):
            assert obs["defensive_fire_ready"][12] == 0
            assert deterministic and action_masks[10]
            return 12, None

    p.model = BadModel()
    with pytest.raises(ValueError, match="illegal"):
        p.movement()
    assert p.decisions_issued == 0

    class HoldModel:
        def predict(self, obs, action_masks, deterministic):
            return 10, None

    p.model = HoldModel()
    assert p.movement()[0].path[-1] == (2, 0)
    assert p.decisions_issued == 1


def test_rejects_live_changes_and_bad_actions_before_issuing(bound):
    p, game, rng = bound

    class CountingModel:
        def __init__(self, action):
            self.action = action
            self.calls = 0

        def predict(self, obs, action_masks, deterministic):
            self.calls += 1
            return self.action, None

    model = CountingModel(25)
    p.model = model
    for action in (25, 1.0, True, np.array([10])):
        model.action = action
        with pytest.raises(ValueError, match="Invalid or illegal"):
            p.movement()
        assert p.decisions_issued == 0
    game.get_board().get_hex(1, 0).set_terrain(object())
    with pytest.raises(ValueError, match="board"):
        p.movement()
    assert model.calls == 4
    game.get_board().get_hex(1, 0).set_terrain(None)
    game.set_defensive_fire_settings(DefensiveFireSettings(1))
    with pytest.raises(ValueError, match="rules"):
        p.movement()
    game.set_defensive_fire_settings(DefensiveFireSettings(0.25))
    model.action = 10
    plan = p.movement()[0]
    assert plan.path == [game.get_board().get_hex(2, 0)]
    assert model.calls == 5
    p.bind_game(game)
    with pytest.raises(RuntimeError, match="already issued"):
        p.movement()
    assert model.calls == 5
    game.apply_movement_plans([plan])
    with pytest.raises(RuntimeError, match="already issued"):
        p.movement()
    assert model.calls == 5


def test_no_mask_or_path_does_not_consume_decision(bound, monkeypatch):
    p, game, rng = bound

    class HoldModel:
        calls = 0

        def predict(self, obs, action_masks, deterministic):
            self.calls += 1
            return 10, None

    model = HoldModel()
    p.model = model
    board = game.get_board()
    with monkeypatch.context() as patches:
        patches.setattr(board, "get_reachable_hexes", lambda *args: set())
        with pytest.raises(ValueError, match="No legal"):
            p.movement()
    assert model.calls == 0
    with monkeypatch.context() as patches:
        patches.setattr(board, "shortest_path", lambda *args: [])
        with pytest.raises(RuntimeError, match="Core could not route"):
            p.movement()
    assert p.decisions_issued == 0 and model.calls == 1
    assert p.movement()[0].path == [board.get_hex(2, 0)]


def test_seeded_core_parity_with_checkpoint_evaluation(run):
    for seed in (0, 2, 20, 42):
        p = player(run)
        before = [t.detach().clone() for t in p.model.policy.parameters()]
        trace, ending, status, game = play_local_game(p, seed)
        env = MaskedBattleHexesEnv(step_limit=4)
        obs, _ = env.reset(seed=seed)
        for inputs, mask, action in trace:
            assert all(np.array_equal(obs[key], inputs[key]) for key in obs)
            assert env.action_masks().tolist() == list(mask)
            expected, _ = p.model.predict(
                obs, action_masks=env.action_masks(), deterministic=True
            )
            assert action == int(expected) and mask[action]
            obs, reward, completed, cutoff, info = env.step(action)
        assert ending == ("completed" if completed else "cutoff")
        if seed == 20:
            assert len(trace) == p.step_limit
            assert ending == "completed" and not cutoff
        assert status == info["outcome"]
        assert len(trace) == p.decisions_issued
        assert game.get_turn_number() == env.game_env.game.get_turn_number()
        assert game.combat_log == env.game_env.game.combat_log
        assert game.defensive_fire_log == env.game_env.game.defensive_fire_log
        assert all(torch.equal(a, b) for a, b in zip(
            before, p.model.policy.parameters()
        ))


def test_budget_completion_and_post_resolution_state(run):
    p = budget_player(run, 1)
    trace, ending, status, game = play_local_game(p, 42)
    assert len(trace) == 1
    assert ending == ("completed" if status.state == "completed"
                      else "cutoff")
    with pytest.raises(RuntimeError, match="completed|budget|turn"):
        p.movement()
    # A successful held plan consumes exactly one decision even after combat.
    other = budget_player(run, 2)
    game, rng = game_for(other, 2)
    enemy = game.get_board().get_units_for_player(game.players[1])[0]
    enemy.set_coords(2, 2)
    rng.random = lambda: 0.0  # force a successful fire without changing rules
    # The live encoder is consulted again after resolution, not cached.

    class Recorder:
        def __init__(self):
            self.inputs = []

        def predict(self, obs, action_masks, deterministic):
            self.inputs.append(obs)
            return (11 if len(self.inputs) == 1 else
                    int(np.flatnonzero(obs["occupancy"] == 1)[0])), None

    recorder = Recorder()
    other.model = recorder
    play_cycle(game, other, rng)
    assert game.defensive_fire_log
    assert game.defensive_fire_log[0].outcome == "retreated"
    if game.get_game_status().state == "in_progress":
        plans = other.movement()
        assert recorder.inputs[1]["occupancy"][11] == 0
        assert recorder.inputs[1]["remaining_steps"].tolist() == [1]
        assert plans[0].path[0] == game.get_board().get_hex(
            *plans[0].unit.get_coords()
        )


def test_terminal_and_budget_never_predict(run):
    p = budget_player(run, 1)
    game, rng = game_for(p)

    class CountingModel:
        calls = 0

        def predict(self, *args, **kwargs):
            self.calls += 1
            return 10, None

    model = CountingModel()
    p.model = model
    play_cycle(game, p, rng)
    if game.get_game_status().state == "in_progress":
        with pytest.raises(RuntimeError, match="budget"):
            p.movement()
    assert model.calls == 1
    ended = player(run)
    terminal_game, _ = game_for(ended)
    terminal_game.get_board().remove_units(
        terminal_game.get_board().get_units_for_player(
            terminal_game.players[1]
        )
    )
    terminal_game.update_game_status(finalize=True)
    with pytest.raises(RuntimeError, match="completed"):
        ended.movement()

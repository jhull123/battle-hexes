import json

import pytest
import torch

from battle_agent_rl.ppo.artifacts import (
    check_seed_separation,
    load_checkpoint,
    read_manifest,
)
from battle_agent_rl.ppo.evaluation import evaluate_games, play_game
from battle_agent_rl.ppo.gym_env import MaskedBattleHexesEnv
from battle_agent_rl.ppo.experiment import (
    evaluate_checkpoint,
    select_and_report,
    train_run,
)
from battle_agent_rl.ppo.metrics import bootstrap, select, summarize, table


def test_snapshot_reload_replay_and_selection(tmp_path):
    run = tmp_path / "run"
    config = dict(
        seed=4, step_limit=2, total_timesteps=16, n_steps=8, batch_size=4
    )
    model, recorder = train_run(
        run, 1, validation=[100, 101], held_out=[200, 201], **config
    )
    manifest = read_manifest(run)
    assert len(manifest["checkpoints"]) == 2
    assert [e["training_timesteps"] for e in manifest["checkpoints"]] == [
        8,
        16,
    ]
    assert manifest["training_episode_seeds"] == recorder.episode_seeds
    assert len(recorder.episode_seeds) > len(recorder.episodes)
    entry = manifest["checkpoints"][0]
    loaded = load_checkpoint(run, entry, manifest)
    first = evaluate_games(loaded, "validation", entry, [100, 101], 2)
    assert first == evaluate_games(loaded, "validation", entry, [100, 101], 2)
    final = load_checkpoint(run, manifest["checkpoints"][-1], manifest)
    env = MaskedBattleHexesEnv(step_limit=2)
    for seed in (100, 101, 102):
        obs, _ = env.reset(seed=seed)
        for _ in range(2):
            mask = env.action_masks()
            a, _ = model.predict(obs, action_masks=mask, deterministic=True)
            b, _ = final.predict(obs, action_masks=mask, deterministic=True)
            assert int(a) == int(b) and mask[int(a)]
            obs, _, terminated, truncated, _ = env.step(a)
            if terminated or truncated:
                break
    before = [p.detach().clone() for p in loaded.policy.parameters()]
    select_and_report(run)
    selected = read_manifest(run)["selected"]
    assert selected in manifest["checkpoints"]
    with pytest.raises(ValueError, match="frozen selected"):
        other = next(e for e in manifest["checkpoints"] if e != selected)
        evaluate_checkpoint(run, other["path"], "held_out")
    replay = evaluate_checkpoint(run, entry["path"])
    assert "Outcomes and episode metrics" in replay
    assert (
        json.loads(
            (
                run / f"replay-validation-{entry['path'][:-4]}-episodes.json"
            ).read_text()
        )
        == first
    )
    assert all(
        torch.equal(a, b) for a, b in zip(before, loaded.policy.parameters())
    )
    assert model.num_timesteps == 16


def test_baselines_and_cutoff():
    for policy in ("random", "hold", "center_hold"):
        summary, length, reward = play_game(None, policy, 42, 1)
        assert summary["length"] == length == 1
        assert summary["return"] == reward
        assert summary["outcome"] in ("win", "loss", "draw", "cutoff")
        assert play_game(None, policy, 42, 1) == (summary, length, reward)


def test_seed_separation_and_corrupt_checkpoint(tmp_path):
    run = tmp_path / "run"
    train_run(
        run,
        1,
        validation=[20],
        held_out=[30],
        seed=2,
        step_limit=1,
        total_timesteps=8,
        n_steps=8,
        batch_size=4,
    )
    manifest = read_manifest(run)
    manifest["validation_seeds"] = [manifest["training_episode_seeds"][-1]]
    with pytest.raises(ValueError, match="overlap"):
        check_seed_separation(manifest)
    manifest = read_manifest(run)
    entry = manifest["checkpoints"][0]
    (run / entry["path"]).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="digest"):
        load_checkpoint(run, entry, manifest)


def test_metrics_ties_cutoffs_and_bootstrap():
    records = []
    for seed in (1, 2):
        for policy, outcome in (
            ("ppo", "draw" if seed == 1 else "cutoff"),
            ("random", "loss"),
            ("hold", "draw"),
            ("center_hold", "win"),
        ):
            records.append(
                dict(
                    policy=policy,
                    game_seed=seed,
                    outcome=outcome,
                    length=seed,
                    **{"return": 0.0},
                )
            )
    summary = summarize(records)
    assert summary["ppo"]["counts"] == dict(win=0, loss=0, draw=1, cutoff=1)
    assert summary["ppo"]["score"] == 0.25
    assert summary["ppo"]["median_length"] == 1.5
    intervals, conclusion = bootstrap(records)
    assert intervals["center_hold"]["interval"][1] < 0
    assert conclusion == "worse"
    rendered = table(
        dict(path="candidate.zip", training_timesteps=16), summary
    )
    assert "Outcomes and episode metrics" in rendered
    assert "Paired score difference (PPO − baseline)" in rendered
    assert "center-then-hold" in rendered
    assert "0.0/0.0/50.0/50.0" in rendered
    header = next(line for line in rendered.splitlines()
                  if line.startswith("Policy "))
    ppo_row = next(line for line in rendered.splitlines()
                   if line.startswith("ppo "))
    assert header.index("Score") == ppo_row.index("0.250", 80)
    assert "|" not in header
    separator = rendered.splitlines()[rendered.splitlines().index(header) + 1]
    assert separator.rfind("-----") == header.index("Score")
    first = dict(path="later.zip", training_timesteps=16)
    earlier = dict(path="earlier.zip", training_timesteps=8)
    assert select([(first, records), (earlier, records)]) == earlier
    with pytest.raises(ValueError, match="Incomplete"):
        summarize(records[:-1])

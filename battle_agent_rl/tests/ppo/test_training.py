import pytest
import torch
from sb3_contrib import MaskablePPO

from battle_agent_rl.ppo.gym_env import MaskedBattleHexesEnv
from battle_agent_rl.ppo.training import train, training_report


class HoldOnlyEnv(MaskedBattleHexesEnv):
    def action_masks(self):
        mask = super().action_masks()
        if mask.any():
            mask[:] = False
            learner = self.game_env.game.get_board().get_units_for_player(
                self.game_env.learner
            )[0]
            row, column = learner.get_coords()
            mask[row * 5 + column] = True
        return mask


def weights(model):
    return [value.detach().clone() for value in model.policy.parameters()]


def test_mask_is_applied_during_rollouts_and_prediction():
    env = HoldOnlyEnv(step_limit=2)
    model = MaskablePPO(
        "MultiInputPolicy", env, seed=7, device="cpu", n_steps=8,
        batch_size=4, policy_kwargs={"net_arch": [16, 16]},
    )
    from battle_agent_rl.ppo.training import EpisodeRecorder
    recorder = EpisodeRecorder()
    model.learn(total_timesteps=16, callback=recorder)
    assert recorder.episodes
    obs, _ = env.reset(seed=3)
    for deterministic in (True, False):
        for _ in range(20):
            action, _ = model.predict(
                obs, action_masks=env.action_masks(),
                deterministic=deterministic,
            )
            assert int(action) == 10
    # MaskablePPO's vectorized environment auto-resets after a cutoff.
    assert set(recorder.actions) == {10}
    assert all(e["outcome"] == "cutoff" for e in recorder.episodes)


def test_updates_reproducible_trace_and_legal_predictions():
    config = dict(seed=12, step_limit=2, total_timesteps=32, n_steps=16,
                  batch_size=8, policy_kwargs={"net_arch": [16, 16]})
    initial = MaskablePPO(
        "MultiInputPolicy", MaskedBattleHexesEnv(step_limit=2),
        seed=12, device="cpu", n_steps=16, batch_size=8,
        policy_kwargs={"net_arch": [16, 16]},
    )
    before = weights(initial)
    first, trace = train(**config)
    after = weights(first)
    assert any(not torch.equal(a, b) for a, b in zip(before, after))
    assert first.num_timesteps == 32
    assert trace.episodes
    assert [e["seed"] for e in trace.episodes] == list(
        range(12, 12 + len(trace.episodes))
    )
    report = training_report(first, trace, 12, 2, 32, 16, 8)
    for field in ("collected_timesteps=32", "episodes=", "cutoff=",
                  "mean_length=", "mean_return=", "train/n_updates=",
                  "train/policy_gradient_loss=", "train/value_loss=",
                  "train/entropy_loss="):
        assert field in report
        assert f"{field}unavailable" not in report

    second, repeated = train(**config)
    assert repeated.actions == trace.actions
    assert repeated.episodes == trace.episodes
    assert second.num_timesteps == first.num_timesteps
    for a, b in zip(after, weights(second)):
        torch.testing.assert_close(a, b, rtol=1e-6, atol=1e-7)
    for key in ("train/n_updates", "train/policy_gradient_loss",
                "train/value_loss", "train/entropy_loss"):
        assert second.logger.name_to_value[key] == pytest.approx(
            first.logger.name_to_value[key], rel=1e-6, abs=1e-7
        )

    env = MaskedBattleHexesEnv(step_limit=8)
    obs, _ = env.reset(seed=44)
    for _ in range(8):
        mask = env.action_masks()
        action, _ = first.predict(obs, action_masks=mask)
        assert mask[int(action)]
        obs, _, terminated, truncated, _ = env.step(action)
        if terminated or truncated:
            obs, _ = env.reset()


@pytest.mark.parametrize("kwargs", [
    {"step_limit": 0}, {"total_timesteps": 0}, {"n_steps": 1},
    {"batch_size": 1}, {"n_steps": 4, "batch_size": 5},
    {"seed": True},
])
def test_invalid_training_config(kwargs):
    with pytest.raises(ValueError):
        train(**kwargs)

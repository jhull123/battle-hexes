"""End-to-end inspection checks with authoritative seeded core transitions."""

from dataclasses import replace
import io
from pathlib import Path
import re
import subprocess
import sys

import pytest

from battle_agent_rl.ppo.environment import PPOTrainingEnvironment
from battle_agent_rl.ppo.rollout_inspection import inspect, main
from battle_hexes_core.defensivefire.defensive_fire import (
    DefensiveFireSettings,
)


def trace(seed, limit, policy):
    output = io.StringIO()
    result = inspect(seed, limit, policy, stream=output)
    return output.getvalue(), result


def test_replay_and_completed_episode_matches_legal_actions_and_board():
    text, result = trace(0, 50, "random")
    assert (text, result) == trace(0, 50, "random")
    assert result.terminated and result.reward == 1
    assert "final: win" in text
    assert "combats:\n  combat" in text
    assert "board: L=learner O=opponent" in text
    decisions = re.findall(r"legal: (.+)\naction: index=(\d+) "
                           r"destination=\((\d+), (\d+)\)", text)
    assert len(decisions) == result.info["step_count"]
    for legal, index, row, col in decisions:
        assert f"{index} -> ({row}, {col})" in legal
        assert int(index) == 5 * int(row) + int(col)
    assert "final state: step=" in text
    assert "legal: none" in text
    assert "\033[" not in text


def test_cutoff_and_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    output = io.StringIO()
    output.isatty = lambda: True
    result = inspect(42, 1, "hold", expect_ending="cutoff", stream=output)
    text = output.getvalue()
    assert result.truncated and result.reward == 0
    assert "outcome=in_progress winner=None reason=None" in text
    assert "final: cutoff" in text
    assert "action: index=10 destination=(2, 0)" in text
    assert "legal: none" in text
    assert "\033[" not in text


def test_terminal_color_preserves_labels(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    output = io.StringIO()
    output.isatty = lambda: True
    inspect(42, 1, "hold", stream=output)
    colored = output.getvalue()
    plain, _ = trace(42, 1, "hold")
    assert "\033[" in colored
    assert re.sub(r"\033\[[\d;]+m", "", colored) == plain


def test_fire_retreat_shows_action_and_post_resolution_position():
    class FireEnvironment(PPOTrainingEnvironment):
        def reset(self, seed=None):
            super().reset(seed)
            opponent = self.game.get_board().get_units_for_player(
                self.game.players[1])[0]
            opponent.set_coords(2, 2)
            self.game.set_defensive_fire_settings(
                DefensiveFireSettings(base_probability=1))
            return self._transition(None, (), ())

    output = io.StringIO()
    result = inspect(7, 1, stream=output,
                     environment_factory=FireEnvironment)
    assert result.info["defensive_fire"]
    assert "trigger=" in output.getvalue()
    assert "action: index=11 destination=(2, 1)" in output.getvalue()
    assert result.observation["occupancy"][11] == 0


def test_inconsistent_mask_and_observation_fail_with_step(capsys):
    class BadMask(PPOTrainingEnvironment):
        def reset(self, seed=None):
            result = super().reset(seed)
            return replace(result, legal_action_mask=(False,) * 25)

    class BadObservation(PPOTrainingEnvironment):
        def step(self, action):
            result = super().step(action)
            observation = dict(result.observation)
            observation["occupancy"] = (0,) * 25
            return replace(result, observation=observation)

    for factory, step in ((BadMask, 0), (BadObservation, 1)):
        with pytest.raises(ValueError, match=f"step {step}: .*mismatch"):
            inspect(42, 1, "hold", stream=io.StringIO(),
                    environment_factory=factory)


def test_environment_failure_reports_attempted_step():
    class BrokenEnvironment(PPOTrainingEnvironment):
        def step(self, action):
            raise RuntimeError("transition failed")

    with pytest.raises(ValueError, match="step 1: transition failed"):
        inspect(42, 1, "hold", stream=io.StringIO(),
                environment_factory=BrokenEnvironment)


def test_ending_mask_and_reward_are_checked():
    class BadEndingMask(PPOTrainingEnvironment):
        def step(self, action):
            result = super().step(action)
            return replace(result, legal_action_mask=(True,) + (False,) * 24)

    class BadReward(PPOTrainingEnvironment):
        def step(self, action):
            result = super().step(action)
            return replace(result, reward=1)

    for factory, invariant in ((BadEndingMask, "ending mask"),
                               (BadReward, "reward mismatch")):
        with pytest.raises(ValueError, match=f"step 1: {invariant}"):
            inspect(42, 1, "hold", stream=io.StringIO(),
                    environment_factory=factory)


def test_command_exit_codes_and_validation(capsys):
    assert main(["--seed", "42", "--step-limit", "1", "--policy", "hold",
                 "--expect-ending", "cutoff"]) == 0
    assert main(["--seed", "42", "--step-limit", "1", "--policy", "hold",
                 "--expect-ending", "completed"]) == 1
    assert "step 1: expected completed ending" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(["--seed", "42", "--step-limit", "0"])


def test_subprocess_command_failure_is_nonzero():
    command = [sys.executable, "-m", "battle_agent_rl.ppo.rollout_inspection",
               "--seed", "42", "--step-limit", "1", "--policy", "hold",
               "--expect-ending", "completed"]
    completed = subprocess.run(command, capture_output=True, text=True)
    assert completed.returncode != 0
    assert "step 1: expected completed ending" in completed.stderr


def test_root_script_defaults_and_forwarded_options():
    script = Path(__file__).resolve().parents[3] / "inspect-ppo-rollout.sh"
    completed = subprocess.run([str(script)], capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr
    assert "episode: seed=0 step_limit=50 policy=random" in completed.stdout
    assert "final: win" in completed.stdout

    cutoff = subprocess.run(
        [str(script), "--seed", "42", "--step-limit", "1", "--policy",
         "hold", "--expect-ending", "cutoff"], capture_output=True, text=True)
    assert cutoff.returncode == 0, cutoff.stderr
    assert "final: cutoff" in cutoff.stdout

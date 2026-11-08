"""Public-path helpers shared by the executable-environment regressions."""

from battle_agent_rl.ppo.decision_audit import audit_decision
from battle_agent_rl.ppo.decision_controller import choose_action


def assert_inputs(env, transition):
    audit_decision(env, transition)
    assert env.task.observation_space().contains(transition.observation)
    assert transition.legal_action_mask.shape == (env.task.spec.actions,)


def hold(env):
    return env.step(choose_action(env.binding, env.pending, "hold", env.rng))


def finish_cycle(env):
    turn = env.game.turn_number
    while env.game.turn_number == turn and not env.done:
        transition = hold(env)
    assert_inputs(env, transition)
    return transition

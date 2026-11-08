"""Dependency-light audits of environment returns against core."""

import numpy as np


def audit_decision(env, transition):
    """Audit live fields, pending reachability and authoritative endings."""
    binding, game = env.binding, env.game
    inputs, mask = transition.observation, transition.legal_action_mask
    spec = binding.spec
    _audit_units(binding, inputs)
    expected_pending, expected_mask = _pending_mask(env)
    assert inputs["pending"].tolist() == expected_pending
    np.testing.assert_array_equal(mask, expected_mask)
    assert inputs["remaining_cycles"].tolist() == [
        max(0, spec.turn_limit + 1 - game.turn_number)]
    assert inputs["scores"].tolist() == [
        game.get_score_tracker().get_score(p)
        for p in (binding.learner, binding.opponent)]
    assert inputs["objective_control"].tolist() == [
        int(any(u.player is binding.scoring_player
                for u in game.board.get_units_at(*coords)))
        for coords in spec.objective_coords]
    _audit_reinforcements(binding, inputs)
    assert transition.terminated == (
        game.get_game_status().state == "completed")
    assert transition.truncated == (env.done and not transition.terminated)
    if env.done:
        assert not env.pending and not mask.any()
    else:
        assert mask.any() and game.current_player is binding.learner
        assert game.current_phase == "movement"


def _audit_units(binding, inputs):
    on_board = set(binding.game.board.get_units())
    awaiting = {u for g in binding.reinforcement_groups if not g.entered
                for u in g.units}
    for index, unit in enumerate(binding.slots):
        alive = unit in on_board and unit.get_coords() is not None
        assert inputs["unit_status"][index] == (
            1 if alive else 0 if unit in awaiting else 2)
        cells = np.flatnonzero(inputs["positions"][index]).tolist()
        assert cells == ([] if not alive else [
            unit.row * binding.spec.board_size[1] + unit.column])
        assert inputs["movement_remaining"][index] == (
            unit.current_turn_movement_points_remaining if alive else 0)
        expected = _fire_flags(unit, binding.learner) if alive else [0] * 4
        assert inputs["fire_flags"][index].tolist() == expected
        np.testing.assert_array_equal(inputs["unit_stats"][index], np.array([
            unit.attack, unit.defense, unit.move, unit.defensive_fire_modifier
        ], dtype=np.float32))


def _pending_mask(env):
    binding, board = env.binding, env.game.board
    spec = binding.spec
    mask = np.zeros(spec.actions, dtype=np.bool_)
    pending = []
    for index, unit in enumerate(binding.learner_slots):
        enabled = (not env.done and unit in board.get_units()
                   and unit.get_coords() is not None
                   and unit.id in env.pending)
        pending.append(int(enabled))
        if enabled:
            start = board.get_hex(*unit.get_coords())
            reachable = board.get_reachable_hexes(
                unit, start, unit.current_turn_movement_points_remaining)
            for tile in reachable:
                mask[index * spec.cells + tile.row * spec.board_size[1]
                     + tile.column] = True
    return pending, mask


def _audit_reinforcements(binding, inputs):
    statuses = {tuple(u.id for u in g.units): g.status for g in
                binding.game.reinforcements_deployer.pending(
                    binding.game.turn_number)}
    for row, group in zip(inputs["reinforcement"],
                          binding.reinforcement_groups):
        status = (2 if group.entered else {"scheduled": 0, "delayed": 1}[
            statuses[tuple(u.id for u in group.units)]])
        assert row.tolist() == [group.arrival_turn, *group.coords, status]


def _fire_flags(unit, learner):
    return [unit.public_defensive_fire_status(learner),
            unit.ended_last_friendly_turn_with_defensive_fire_eligibility,
            unit.forced_to_retreat_since_last_friendly_turn,
            unit.defensive_fire_spent_this_off_turn]

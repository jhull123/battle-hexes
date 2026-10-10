"""Independent checks of an environment transition against core state."""


def verify_transition(env, transition, step):
    def require(condition, invariant):
        if not condition:
            raise ValueError(f"step {step}: {invariant}")

    board = env.game.get_board()
    status = env.game.get_game_status()
    require(transition.info["outcome"] == status, "core outcome mismatch")
    require(transition.info["step_count"] == env.step_count,
            "step count mismatch")
    require(transition.info["turn_number"] == env.game.get_turn_number(),
            "turn number mismatch")
    terminated = status.state == "completed"
    truncated = not terminated and step >= env.step_limit
    require(transition.terminated == terminated, "terminated flag mismatch")
    require(transition.truncated == truncated, "truncated flag mismatch")
    require(terminated or truncated or status.state == "in_progress",
            "unrecognized core status")
    require(env.done == (terminated or truncated), "episode ending mismatch")
    reward = 0
    if terminated and status.winner_player_name is not None:
        reward = 1 if status.winner_player_name == env.learner.name else -1
    require(transition.reward == reward, "reward mismatch")

    cells = env.ROWS * env.COLUMNS
    occupants = [board.get_unit_at(*divmod(index, env.COLUMNS))
                 for index in range(cells)]
    occupancy = tuple(0 if unit is None else
                      1 if env.learner.owns(unit) else -1
                      for unit in occupants)
    readiness = tuple(int(unit.public_defensive_fire_status(env.learner))
                      if unit is not None else 0 for unit in occupants)
    observation = transition.observation
    require(observation["occupancy"] == occupancy, "occupancy mismatch")
    require(observation["defensive_fire_ready"] == readiness,
            "defensive-fire readiness mismatch")
    require(observation["remaining_steps"] == env.step_limit - step,
            "remaining steps mismatch")

    mask = transition.legal_action_mask
    require(len(mask) == cells, "mask length mismatch")
    require(all(isinstance(value, bool) for value in mask),
            "mask contains non-boolean values")
    if terminated or truncated:
        require(not any(mask), "ending mask must be all false")
        return
    units = board.get_units_for_player(env.learner)
    require(len(units) == 1, "active learner must have one unit")
    unit = units[0]
    start = board.get_hex(*unit.get_coords())
    reachable = board.get_reachable_hexes(unit, start)
    for index, allowed in enumerate(mask):
        destination = board.get_hex(*divmod(index, env.COLUMNS))
        require(allowed == (destination in reachable),
                f"mask mismatch at index {index}")
        if allowed:
            require(bool(board.shortest_path(unit, start, destination)),
                    f"missing core path at index {index}")
    require(mask[unit.row * env.COLUMNS + unit.column],
            "hold action missing")

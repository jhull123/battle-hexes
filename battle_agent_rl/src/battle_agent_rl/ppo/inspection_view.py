"""Human-readable, optionally styled view of verified rollout data."""


class InspectionView:
    def __init__(self, stream, color=False):
        self.stream = stream
        self.color = color

    def emphasis(self, text, code="1"):
        return f"\033[{code}m{text}\033[0m" if self.color else text

    def line(self, text):
        print(text, file=self.stream)

    def state(self, label, transition, columns, selected=None):
        self.line(self.emphasis(
            f"{label}: step={transition.info['step_count']} "
            f"turn={transition.info['turn_number']}"))
        self.line("board: L=learner O=opponent .=empty *=selected destination")
        self.line("     " + "  ".join(str(col) for col in range(columns)))
        values = transition.observation["occupancy"]
        for row in range(len(values) // columns):
            markers = []
            for col in range(columns):
                index = row * columns + col
                symbol = {1: "L", -1: "O", 0: "."}[values[index]]
                code = {1: "1;34", -1: "1;31", 0: "0"}[values[index]]
                if index == selected:
                    symbol += "*"
                    code = "1;33"
                markers.append(self.emphasis(symbol, code))
            self.line(f"  {row}: " + "  ".join(markers))
        observation = transition.observation
        self.line(f"observation: occupancy={list(values)}")
        self.line("observation: defensive_fire_ready=" +
                  str(list(observation["defensive_fire_ready"])))
        self.line("observation: remaining_steps=" +
                  str(observation["remaining_steps"]))
        legal = [f"{i} -> {divmod(i, columns)}" for i, allowed in
                 enumerate(transition.legal_action_mask) if allowed]
        self.line("legal: " + (", ".join(legal) if legal else "none"))

    def result(self, transition):
        info = transition.info
        fire = info["defensive_fire"]
        combats = info["combats"]
        self.line(self.emphasis("defensive_fire:", "1;35") +
                  (" none" if not fire else ""))
        for event in fire:
            self.line("  " + self.emphasis("fire", "1;35") +
                      f" firing={event.firing_unit_id} "
                      f"target={event.target_unit_id} "
                      f"trigger={event.trigger_hex} "
                      f"target_before={event.target_hex_before} "
                      f"outcome={event.outcome} "
                      f"retreat={event.retreat_destination}")
        self.line(self.emphasis("combats:", "1;36") +
                  (" none" if not combats else ""))
        for event in combats:
            self.line("  " + self.emphasis("combat", "1;36") +
                      f" turn={event.turn_number} player={event.player_name} "
                      f"attackers={[u.name for u in event.attackers]} "
                      f"defenders={[u.name for u in event.defenders]} "
                      f"result={event.result.code} "
                      f"effect={event.result.summary} "
                      f"eliminated={event.eliminated_units} "
                      f"retreated={event.retreated_units}")
        status = info["outcome"]
        self.line(f"reward={transition.reward} step={info['step_count']} "
                  f"turn={info['turn_number']}")
        self.line(f"ending: terminated={transition.terminated} "
                  f"truncated={transition.truncated} outcome={status.state} "
                  f"winner={status.winner_player_name} reason={status.reason}")

    def summary(self, transition, learner_name):
        status = transition.info["outcome"]
        if transition.truncated:
            ending = "cutoff"
        elif status.winner_player_name is None:
            ending = "draw"
        elif status.winner_player_name == learner_name:
            ending = "win"
        else:
            ending = "loss"
        self.line(self.emphasis(f"final: {ending}", "1;32"))

from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.combat.combat import Combat


class GamePlayer:
    def __init__(self, game: Game) -> None:
        self.game = game

    def play(self, max_turns: int | None = None) -> None:
        """Run CPU turns until only one player has units remaining.

        Parameters
        ----------
        max_turns: int | None, optional
            The maximum number of player turns to execute before ending the
            game. ``None`` (default) means play until the game is over.
        """
        for player in self.game.get_players():
            if player.type is not PlayerType.CPU:
                raise ValueError("All players must be of type CPU")

        turns_played = 0
        while not self.game.is_game_over():
            if max_turns is not None and turns_played >= max_turns:
                break

            current_player = self.game.get_current_player()

            plans = current_player.movement()
            self.game.apply_movement_plans(plans)

            Combat(self.game).resolve_combat()

            turns_played += 1

            if self.game.is_game_over():
                break

            self.game.next_player()

        for player in self.game.get_players():
            player.end_game_cb()

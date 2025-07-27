from battle_hexes_core.game.game import Game
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.combat.combat import Combat


class GamePlayer:
    def __init__(self, game: Game) -> None:
        self.game = game

    def play(self) -> None:
        """Run CPU turns until only one player has units remaining."""
        for player in self.game.get_players():
            if player.type is not PlayerType.CPU:
                raise ValueError("All players must be of type CPU")

        while not self.game.is_game_over():
            current_player = self.game.get_current_player()

            plans = current_player.movement()
            self.game.apply_movement_plans(plans)

            Combat(self.game).resolve_combat()

            if self.game.is_game_over():
                break

            self.game.next_player()

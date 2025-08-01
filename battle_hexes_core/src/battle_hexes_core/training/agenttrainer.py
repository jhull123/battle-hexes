from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.gameplayer import GamePlayer


class AgentTrainer:
    def __init__(
        self,
        gamefactory: GameFactory,
        episodes: int = 100,
        max_turns: int | None = None,
    ):
        self.gamefactory = gamefactory
        self.episodes = episodes
        self.max_turns = max_turns

    def train(self) -> None:
        for episode in range(self.episodes):
            game = self.gamefactory.create_game()
            print()
            print(f"Starting game {episode + 1}/{self.episodes}")
            GamePlayer(game).play(max_turns=self.max_turns)

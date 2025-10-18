from pathlib import Path
from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_api.humanplayer import HumanPlayer
from battle_hexes_core.game.player import Player, PlayerType
from battle_hexes_core.game.randomplayer import RandomPlayer


class PlayerFactory:
    def create_player(self, player_type: str, player_name: str) -> Player:
        match player_type:
            case "human":
                return HumanPlayer()
            case "random":
                return RandomPlayer(
                    name=player_name,
                    type=PlayerType.CPU,
                    factions=(),
                    board=None
                )
            case "q-learning":
                repo_root = Path(__file__).resolve().parents[3]
                player = QLearningPlayer(
                    name=player_name,
                    type=PlayerType.CPU,
                    factions=(),
                    board=None,
                    epsilon=0.0,
                )
                q_table_path = repo_root / "battle_agent_rl" / "q_table.pkl"
                player.load_q_table(q_table_path)
                return player
            case _:
                raise ValueError("Unkown player type: " + player_type)

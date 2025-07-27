import uuid

from battle_agent_rl.qlearningplayer import QLearningPlayer
from battle_hexes_core.game.gamefactory import GameFactory
from battle_hexes_core.game.randomplayer import RandomPlayer
from battle_hexes_core.game.player import PlayerType
from battle_hexes_core.training import AgentTrainer
from battle_hexes_core.unit.faction import Faction
from battle_hexes_core.unit.unit import Unit

random_player_factions = [
    Faction(id=uuid.uuid4())
]

random_player = RandomPlayer(
    name="Random Player",
    factions=random_player_factions
)

random_unit = Unit(
    id=uuid.uuid4(),
    name="Random Unit",
    faction=random_player_factions[0],
    player=random_player,
    type="Infantry",
    attack=2,
    defense=2,
    move=1,
    row=2,
    column=2
)

rl_player_factions = [
    Faction(id=uuid.uuid4())
]

rl_player = QLearningPlayer(
    "Q Lerning Player",
    PlayerType.CPU,
    factions=rl_player_factions,
    board=None  # Board will be set later
)

game_factory = GameFactory(
    board_size=(30, 30),
    players=[random_player],
    units=[random_unit]
)

agent_trainer = AgentTrainer(game_factory, 5)
agent_trainer.train()

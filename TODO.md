# Things To Do for Battle Hexes!

## Front End
1. Game creation screen - user can specify the types of players (human, cpu
agents) and other settings.
1. Support multiple friendly units in the same hex.

## Back End
1. Move game state to database (DynamoDB).
1. ~~Replace prints with logging.~~

## Scenario Editor
Create a new project for creating and editing scenarios.

## RL Agent
1. Training should randomize the positions of the units in the episode.
1. Q-learning agent should go in its own folder instead of the root of the
project.
1. State should include all units!

# General
1. Terrain types! Plus rivers, mountains, etc.
1. Movement cost per terrain type.
1. Defense bonus per terrain type.
1. Hex occupancy limits.
1. There are some single unit assumptions in the code... combat, etc. Update
to support multi-unit everywhere.

# Cloud Deployment

1. ~~Dev environment deploy for front end.~~
1. ~~Dev environment deploy for back end.~~
1. Deploy to dev automatically on successful CI workflow run.

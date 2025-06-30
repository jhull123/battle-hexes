import axios from 'axios';
import { CpuPlayer } from '../../src/player/cpu-player.js';
import { Game } from '../../src/model/game.js';
import { Board } from '../../src/model/board.js';
import { Players } from '../../src/player/player.js';
import { API_URL } from '../../src/model/battle-api.js';

jest.mock('axios');

describe('CpuPlayer', () => {
  let cpuPlayer;
  let game;

  beforeEach(() => {
    axios.post.mockClear();
    axios.post.mockResolvedValue({ data: { plans: [] } });
    cpuPlayer = new CpuPlayer('CPU');
    const board = new Board(1, 1);
    const players = new Players([cpuPlayer]);
    game = new Game('game-1', ['Movement', 'Combat'], players, board);
  });

  test('calls movement endpoint during movement phase', async () => {
    await cpuPlayer.play(game);
    expect(axios.post).toHaveBeenCalledWith(`${API_URL}/games/${game.getId()}/movement`);
  });

  test('does not call endpoint in other phases', async () => {
    game.endPhase(); // move to Combat phase
    await cpuPlayer.play(game);
    expect(axios.post).not.toHaveBeenCalled();
  });
});

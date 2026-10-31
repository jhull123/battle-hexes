import { PpoPlayer } from '../../src/player/ppo-player.js';
import { MovementAnimator } from '../../src/animation/movement-animator.js';
import { applyMovementResponse } from '../../src/model/movement-response-handler.js';

jest.mock('../../src/animation/movement-animator.js', () => ({
  MovementAnimator: jest.fn(),
}));
jest.mock('../../src/model/movement-response-handler.js', () => ({
  applyMovementResponse: jest.fn(),
}));

test('PPO applies and acknowledges each live order before requesting another', async () => {
  const sequence = [];
  MovementAnimator.mockImplementation(() => ({
    animate: async () => { sequence.push('animate'); },
  }));
  applyMovementResponse.mockImplementation(() => { sequence.push('fire'); });
  const first = { plan: { unitId: 'learner-0', path: [{ row: 3, column: 2 }] },
    game: { ppoTurn: { pendingUnitIds: ['learner-1'] } } };
  const second = { plan: { unitId: 'learner-1', path: [{ row: 5, column: 2 }] },
    game: { ppoTurn: { pendingUnitIds: [] } } };
  const service = {
    orderPpo: jest.fn(async () => {
      sequence.push('request');
      return sequence.filter((item) => item === 'request').length === 1 ? first : second;
    }),
    acknowledgeResponseApplication: jest.fn(() => { sequence.push('ack'); }),
  };
  const player = new PpoPlayer('Learner', [], { service });
  let active = player;
  const board = { getHex: () => ({}) };
  const game = {
    ppoTurn: { pendingUnitIds: ['learner-0', 'learner-1'] },
    isGameOver: () => false,
    getCurrentPlayer: () => active,
    getCurrentPhase: () => 'Movement',
    getId: () => 'game-id',
    getUnitById: () => ({}),
    getBoard: () => board,
    applyApiState: (response) => {
      sequence.push('state');
      game.ppoTurn = response.game.ppoTurn;
      if (game.ppoTurn.pendingUnitIds.length === 0) active = null;
    },
  };
  await player.play(game);
  expect(sequence).toEqual([
    'request', 'animate', 'fire', 'state', 'ack',
    'request', 'animate', 'fire', 'state', 'ack',
  ]);
  expect(service.orderPpo).toHaveBeenCalledTimes(2);
});

test('PPO hands off to a CPU opponent after the last order is applied', async () => {
  const sequence = [];
  MovementAnimator.mockImplementation(() => ({
    animate: async () => { sequence.push('animate'); },
  }));
  applyMovementResponse.mockImplementation(() => { sequence.push('fire'); });
  const cpu = {
    isHuman: () => false,
    play: jest.fn(() => { sequence.push('cpu-turn'); }),
  };
  const service = {
    orderPpo: jest.fn(async () => ({
      plan: { unitId: 'learner-0', path: [{ row: 3, column: 2 }] },
    })),
    acknowledgeResponseApplication: jest.fn(() => { sequence.push('ack'); }),
  };
  const player = new PpoPlayer('Learner', [], { service });
  let active = player;
  const game = {
    ppoTurn: { pendingUnitIds: ['learner-0'] },
    isGameOver: () => false,
    getCurrentPlayer: () => active,
    getCurrentPhase: () => 'Movement',
    getId: () => 'game-id',
    getUnitById: () => ({}),
    getBoard: () => ({ getHex: () => ({}) }),
    applyApiState: () => {
      sequence.push('state');
      game.ppoTurn.pendingUnitIds = [];
      active = cpu;
    },
  };
  await player.play(game);
  expect(cpu.play).toHaveBeenCalledWith(game);
  expect(sequence).toEqual(['animate', 'fire', 'state', 'ack', 'cpu-turn']);
});

test('PPO order failure shows the replaced-checkpoint message', async () => {
  const banner = { hidden: true, textContent: '' };
  global.document = { getElementById: () => banner };
  const player = new PpoPlayer('Learner', [], { service: {
    orderPpo: async () => {
      throw Object.assign(new Error('Start a new game.'), {
        code: 'ppoSavedCheckpointUnavailable',
      });
    },
  } });
  const game = {
    ppoTurn: { pendingUnitIds: ['learner-0'] },
    isGameOver: () => false,
    getCurrentPlayer: () => player,
    getCurrentPhase: () => 'Movement',
    getId: () => 'old-game',
  };
  const log = jest.spyOn(console, 'error').mockImplementation(() => {});
  try {
    await player.play(game);
    expect(banner.textContent).toBe('Start a new game.');
    expect(banner.hidden).toBe(false);
  } finally {
    log.mockRestore();
    delete global.document;
  }
});

import { MovementAnimator } from '../../src/animation/movement-animator.js';
import { eventBus } from '../../src/event-bus.js';

jest.mock('../../src/event-bus.js', () => ({
  eventBus: {
    emit: jest.fn(),
  },
}));

describe('MovementAnimator', () => {
  let board;
  let animator;
  let unit;
  let hexA, hexB, hexC;

  beforeEach(() => {
    jest.useFakeTimers();
    eventBus.emit.mockClear();
    board = {
      updateUnitPosition: jest.fn(),
      refreshCombat: jest.fn(),
      getAdjacentHexes: jest.fn(() => new Set()),
    };
    unit = { move: jest.fn() };
    hexA = { id: 'a' };
    hexB = { id: 'b' };
    hexC = { id: 'c' };
    animator = new MovementAnimator(board, 50);
  });

  test('animates movement path and updates board', async () => {
    const promise = animator.animate(unit, [hexA, hexB, hexC], true);

    expect(board.updateUnitPosition).toHaveBeenCalledWith(unit, hexA, hexB);
    expect(eventBus.emit).toHaveBeenCalledWith('redraw');

    await jest.runOnlyPendingTimersAsync();
    await Promise.resolve();

    expect(board.updateUnitPosition).toHaveBeenCalledWith(unit, hexB, hexC);
    expect(eventBus.emit).toHaveBeenLastCalledWith('redraw');

    await jest.runOnlyPendingTimersAsync();
    await promise;

    expect(unit.move).toHaveBeenCalledWith(hexC, new Set());
    expect(board.refreshCombat).toHaveBeenCalled();
    expect(eventBus.emit).toHaveBeenCalledWith('menuUpdate');
  });
});

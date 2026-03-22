import { applyMovementResponse } from '../../src/model/movement-response-handler.js';
import { BoardUpdater } from '../../src/model/board-updater.js';
import { eventBus } from '../../src/event-bus.js';

jest.mock('../../src/model/board-updater.js', () => ({
  BoardUpdater: jest.fn().mockImplementation(() => ({
    updateBoard: jest.fn(),
  })),
}));

jest.mock('../../src/event-bus.js', () => ({
  eventBus: {
    emit: jest.fn(),
  },
}));

describe('applyMovementResponse', () => {
  beforeEach(() => {
    BoardUpdater.mockClear();
    eventBus.emit.mockClear();
  });

  test('updates board units and emits defensive fire events from movement responses', () => {
    const board = { id: 'board-1' };
    const response = {
      game: {
        board: {
          units: [{ id: 'unit-1', row: 1, column: 2, defensive_fire_available: false }],
        },
      },
      defensive_fire_events: [
        { message: 'Defensive fire had no effect.' },
      ],
    };

    applyMovementResponse(board, response);

    const updater = BoardUpdater.mock.results[0].value;
    expect(updater.updateBoard).toHaveBeenCalledWith(board, response.game.board.units);
    expect(eventBus.emit).toHaveBeenCalledWith(
      'defensiveFireResolved',
      response.defensive_fire_events
    );
  });

  test('falls back to sparse board units when game board units are unavailable', () => {
    const board = { id: 'board-1' };
    const response = {
      sparse_board: {
        units: [{ id: 'unit-2', row: 3, column: 4 }],
      },
      defensive_fire_events: [],
    };

    applyMovementResponse(board, response);

    const updater = BoardUpdater.mock.results[0].value;
    expect(updater.updateBoard).toHaveBeenCalledWith(board, response.sparse_board.units);
    expect(eventBus.emit).not.toHaveBeenCalled();
  });
});

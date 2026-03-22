import { MovementResponseHandler } from '../../src/model/movement-response-handler.js';

describe('MovementResponseHandler', () => {
  test('prefers sparse board updates and forwards defensive fire events', () => {
    const updateScores = jest.fn();
    const updateTurnState = jest.fn();
    const board = {};
    const updateBoard = jest.fn();
    const game = {
      updateScores,
      updateTurnState,
      getBoard: () => board,
    };

    const handler = new MovementResponseHandler({ updateBoard });
    const responseData = {
      sparse_board: {
        units: [{ id: 'unit-1', row: 2, column: 3 }],
      },
      game: {
        board: {
          units: [{ id: 'unit-1', row: 0, column: 0 }],
        },
      },
      defensive_fire_events: [{ outcome: 'no_effect', message: 'Defensive fire had no effect.' }],
      scores: { Blue: 2 },
      turnLimit: 5,
      turnNumber: 3,
    };

    handler.apply(game, responseData);

    expect(updateScores).toHaveBeenCalledWith({ Blue: 2 });
    expect(updateTurnState).toHaveBeenCalledWith({ turnLimit: 5, turnNumber: 3 });
    expect(updateBoard).toHaveBeenCalledWith(board, [{ id: 'unit-1', row: 2, column: 3 }], {
      defensiveFireEvents: [{ outcome: 'no_effect', message: 'Defensive fire had no effect.' }],
    });
  });
});

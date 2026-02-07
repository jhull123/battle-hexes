import { Objective } from '../../src/model/objective.js';

describe('Objective', () => {
  test('exposes type and points via getters', () => {
    const objective = new Objective('hold', 3);

    expect(objective.type).toBe('hold');
    expect(objective.points).toBe(3);
  });

  test('formats display name with leading capital', () => {
    const objective = new Objective('hold', 3);

    expect(objective.displayName).toBe('Hold');
  });

  test('returns empty display name when type is missing', () => {
    const objective = new Objective('', 3);

    expect(objective.displayName).toBe('');
  });
});

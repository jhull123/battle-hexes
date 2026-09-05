/** @jest-environment jsdom */
import { CombatResultsTableMenu } from '../../src/combat-results-table-menu.js';

const table = {
  dieRolls: [1, 2, 3, 4, 5, 6],
  rows: [
    {
      odds: [1, 7],
      automaticResult: {
        code: 'ATTACKER_ELIMINATED',
        text: 'Attacker Eliminated',
      },
    },
    {
      odds: [1, 6],
      results: Array.from({ length: 6 }, (_, index) => ({
        code: index === 2 ? 'ATTACKER_RETREAT_2' : 'ATTACKER_ELIMINATED',
        text: index === 2 ? 'Attacker Retreat 2 Hexes' : 'Attacker Eliminated',
      })),
    },
  ],
};

beforeEach(() => {
  document.body.innerHTML = '<table id="combatResultsTable"></table>';
});

test('renders accessible die-roll columns and result text from game state', () => {
  new CombatResultsTableMenu({ getCombatResultsTable: () => table });

  expect(document.querySelector('caption').textContent).toBe('Combat Results Table');
  expect([...document.querySelectorAll('thead th')].map((cell) => cell.textContent))
    .toEqual(['Odds', '1', '2', '3', '4', '5', '6']);
  expect(document.querySelectorAll('tbody tr')[1].children).toHaveLength(7);
  expect(document.querySelectorAll('tbody tr')[1].children[3].textContent)
    .toBe('Attacker Retreat 2 Hexes');
});

test('renders automatic results in one clearly labeled spanning cell', () => {
  new CombatResultsTableMenu({ getCombatResultsTable: () => table });

  const automaticCell = document.querySelector('.crt-automatic-result');
  expect(automaticCell.textContent).toBe('Automatic: Attacker Eliminated');
  expect(automaticCell.colSpan).toBe(6);
});

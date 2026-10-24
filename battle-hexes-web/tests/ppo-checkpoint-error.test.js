/** @jest-environment jsdom */

import { showPpoCheckpointError } from '../src/ppo-checkpoint-error.js';

test('a replaced saved PPO checkpoint is explained in the battle UI', () => {
  document.body.innerHTML = '<p id="ppo-checkpoint-error" role="alert" hidden></p>';
  const error = {
    code: 'ppoSavedCheckpointUnavailable',
    message: 'The PPO checkpoint used by this saved game is no longer available. Start a new game.',
  };

  expect(showPpoCheckpointError(error)).toBe(true);
  const banner = document.getElementById('ppo-checkpoint-error');
  expect(banner.hidden).toBe(false);
  expect(banner.textContent).toContain('Start a new game');
  expect(showPpoCheckpointError({ code: 'savedGameIncompatible' })).toBe(false);
});

/** Show why a saved PPO game cannot be resumed after its model is replaced. */
export const showPpoCheckpointError = (error, documentRef = document) => {
  if (error.code !== 'ppoSavedCheckpointUnavailable') return false;
  const banner = documentRef.getElementById('ppo-checkpoint-error');
  banner.textContent = error.message;
  banner.hidden = false;
  return true;
};

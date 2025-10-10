export const LOADING_MESSAGE = 'Loading scenarios…';
export const DEFAULT_STATUS_MESSAGE = 'Choose a scenario to customize your battle.';
export const UNAVAILABLE_MESSAGE = 'Unable to load scenarios. Please try again later.';
export const EMPTY_MESSAGE = 'No scenarios are available yet.';

const setStatusMessage = (statusElement, message) => {
  if (!statusElement) {
    return;
  }

  statusElement.textContent = message;
};

export const populateScenarioOptions = (selectElement, scenarios) => {
  if (!selectElement) {
    return;
  }

  selectElement.innerHTML = '';

  scenarios.forEach((scenario, index) => {
    const option = document.createElement('option');
    option.value = scenario.id;
    option.textContent = scenario.name || scenario.id;

    if (index === 0) {
      option.selected = true;
    }

    selectElement.append(option);
  });
};

export const loadScenarios = async ({
  selectElement,
  statusElement,
  fetchImpl = fetch,
  apiUrl,
}) => {
  if (!selectElement) {
    return [];
  }

  selectElement.disabled = true;
  setStatusMessage(statusElement, LOADING_MESSAGE);

  try {
    const response = await fetchImpl(`${apiUrl}/scenarios`);

    if (!response.ok) {
      throw new Error(`Unexpected status code ${response.status}`);
    }

    const scenarios = await response.json();

    if (!Array.isArray(scenarios) || scenarios.length === 0) {
      selectElement.innerHTML = '<option>No scenarios available</option>';
      selectElement.disabled = true;
      setStatusMessage(statusElement, EMPTY_MESSAGE);
      return [];
    }

    populateScenarioOptions(selectElement, scenarios);
    selectElement.disabled = false;
    setStatusMessage(statusElement, DEFAULT_STATUS_MESSAGE);
    return scenarios;
  } catch (error) {
    console.error('Failed to load scenarios', error);
    selectElement.innerHTML = '<option>Unable to load scenarios</option>';
    selectElement.disabled = true;
    setStatusMessage(statusElement, UNAVAILABLE_MESSAGE);
    return [];
  }
};

export const initializeScenarioPicker = ({
  documentRef = document,
  fetchImpl = fetch,
  apiUrl = process.env.API_URL,
} = {}) => {
  const selectElement = documentRef?.getElementById?.('scenario-select');

  if (!selectElement) {
    return null;
  }

  const statusElement = documentRef.getElementById('scenario-status');

  loadScenarios({ selectElement, statusElement, fetchImpl, apiUrl });

  return { selectElement, statusElement };
};

export const LOADING_MESSAGE = 'Loading player types…';
export const DEFAULT_STATUS_MESSAGE = 'Choose who commands each side.';
export const UNAVAILABLE_MESSAGE = 'Unable to load player types. Please try again later.';
export const EMPTY_MESSAGE = 'No player types are available yet.';

const setStatusMessage = (statusElement, message) => {
  if (!statusElement) {
    return;
  }

  statusElement.textContent = message;
};

export const populatePlayerTypeOptions = (selectElement, playerTypes, selectedId) => {
  if (!selectElement) {
    return;
  }

  selectElement.innerHTML = '';

  playerTypes.forEach((playerType, index) => {
    const option = document.createElement('option');
    option.value = playerType.id;
    option.textContent = playerType.name || playerType.id;

    if (selectedId && selectedId === playerType.id) {
      option.selected = true;
    }

    if (!selectedId && index === 0) {
      option.selected = true;
    }

    selectElement.append(option);
  });
};

const disableSelects = (selectElements) => {
  selectElements.forEach((select) => {
    if (!select) {
      return;
    }

    select.innerHTML = '<option>Loading player types…</option>';
    select.disabled = true;
  });
};

const setErrorState = (selectElements, message) => {
  selectElements.forEach((select) => {
    if (!select) {
      return;
    }

    select.innerHTML = `<option>${message}</option>`;
    select.disabled = true;
  });
};

export const loadPlayerTypes = async ({
  selectElements = [],
  statusElement,
  fetchImpl = fetch,
  apiUrl,
  defaultSelections = [],
}) => {
  const selects = selectElements.filter(Boolean);

  if (selects.length === 0) {
    return [];
  }

  disableSelects(selects);
  setStatusMessage(statusElement, LOADING_MESSAGE);

  try {
    const response = await fetchImpl(`${apiUrl}/player-types`);

    if (!response.ok) {
      throw new Error(`Unexpected status code ${response.status}`);
    }

    const playerTypes = await response.json();

    if (!Array.isArray(playerTypes) || playerTypes.length === 0) {
      setErrorState(selects, 'No player types available');
      setStatusMessage(statusElement, EMPTY_MESSAGE);
      return [];
    }

    selects.forEach((select, index) => {
      const defaultSelection = defaultSelections[index];
      populatePlayerTypeOptions(select, playerTypes, defaultSelection);
      select.disabled = false;

      if (defaultSelection && select.value !== defaultSelection) {
        select.value = playerTypes[0]?.id ?? '';
      }
    });

    setStatusMessage(statusElement, DEFAULT_STATUS_MESSAGE);
    return playerTypes;
  } catch (error) {
    console.error('Failed to load player types', error);
    setErrorState(selects, 'Unable to load player types');
    setStatusMessage(statusElement, UNAVAILABLE_MESSAGE);
    return [];
  }
};

export const initializePlayerTypePicker = ({
  documentRef = document,
  fetchImpl = fetch,
  apiUrl = process.env.API_URL,
  defaultSelections = ['human', 'q-learning'],
} = {}) => {
  const selectElements = [
    documentRef?.getElementById?.('player1-type'),
    documentRef?.getElementById?.('player2-type'),
  ].filter(Boolean);

  if (selectElements.length === 0) {
    return null;
  }

  const statusElement = documentRef.getElementById('player-type-status');

  loadPlayerTypes({
    selectElements,
    statusElement,
    fetchImpl,
    apiUrl,
    defaultSelections,
  });

  return { selectElements, statusElement };
};

import p5 from 'p5';
import { ScrollingHexLandscape, DEFAULT_SCROLL_SPEED } from './animation/scrolling-hex-landscape.js';
import { initializePlayerTypePicker } from './title-screen-player-types.js';
import { initializeScenarioPicker } from './title-screen-scenarios.js';

export const initializeTitleScreen = ({
  documentRef = document,
  fetchImpl = fetch,
  apiUrl = process.env.API_URL,
  locationRef = window.location,
} = {}) => {
  const scenarioPicker = initializeScenarioPicker({
    documentRef,
    fetchImpl,
    apiUrl,
  });
  const playerPicker = initializePlayerTypePicker({
    documentRef,
    fetchImpl,
    apiUrl,
  });

  const enterBattleButton = documentRef?.getElementById?.('enter-battle-button');
  const playerTypeStatus = documentRef?.getElementById?.('player-type-status');

  if (enterBattleButton) {
    const defaultLabel = enterBattleButton.textContent;

    enterBattleButton.addEventListener('click', async (event) => {
      event.preventDefault();

      const scenarioId = scenarioPicker?.selectElement?.value;
      const selectElements = playerPicker?.selectElements ?? [];
      const playerTypes = selectElements.map((select) => select.value).filter(Boolean);

      if (!scenarioId || playerTypes.length !== selectElements.length) {
        return;
      }

      enterBattleButton.disabled = true;
      enterBattleButton.textContent = 'Preparing battle…';

      try {
        const response = await fetchImpl(`${apiUrl}/games`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scenarioId,
            playerTypes,
          }),
        });

        if (!response.ok) {
          throw new Error(`Unexpected status ${response.status}`);
        }

        const game = await response.json();
        locationRef.assign(`battle.html?gameId=${encodeURIComponent(game.id)}`);
      } catch (error) {
        console.error('Failed to create game', error);
        enterBattleButton.disabled = false;
        enterBattleButton.textContent = defaultLabel;
        if (playerTypeStatus) {
          playerTypeStatus.textContent = 'Failed to start game. Please try again.';
        }
      }
    });
  }

  return { scenarioPicker, playerPicker };
};

const backgroundElement = document.getElementById('title-background');

if (backgroundElement) {
  new p5((p) => {
    let landscape;

    p.setup = () => {
      const canvas = p.createCanvas(window.innerWidth, window.innerHeight);
      canvas.parent(backgroundElement);
      canvas.elt.classList.add('title-screen__canvas');
      canvas.elt.style.pointerEvents = 'none';
      canvas.elt.style.position = 'absolute';
      canvas.elt.style.top = '0';
      canvas.elt.style.left = '0';
      canvas.elt.style.width = '100%';
      canvas.elt.style.height = '100%';
      p.pixelDensity(Math.min(window.devicePixelRatio || 1, 2));

      landscape = new ScrollingHexLandscape(p, { hexRadius: 58, scrollSpeed: DEFAULT_SCROLL_SPEED });
      landscape.resize(p.width, p.height);
      p.frameRate(60);
    };

    p.draw = () => {
      if (!landscape) {
        return;
      }

      p.clear(0, 0, 0, 0);
      landscape.draw(p.deltaTime);
    };

    p.windowResized = () => {
      p.resizeCanvas(window.innerWidth, window.innerHeight);
      landscape.resize(p.width, p.height);
    };
  }, backgroundElement);
}

initializeTitleScreen();

import p5 from 'p5';
import { ScrollingHexLandscape, DEFAULT_SCROLL_SPEED } from './animation/scrolling-hex-landscape.js';
import { initializePlayerTypePicker, populatePlayerTypeOptions } from './title-screen-player-types.js';
import { initializeScenarioPicker } from './title-screen-scenarios.js';
import { battleHexesService } from './service/service-factory.js';

export const initializeTitleScreen = ({
  documentRef = document,
  service = battleHexesService,
  locationRef = window.location,
} = {}) => {
  const scenarioPicker = initializeScenarioPicker({
    documentRef,
    service,
  });
  const playerPicker = initializePlayerTypePicker({
    documentRef,
    service,
  });

  if (scenarioPicker && playerPicker) {
    playerPicker.ready.then((types) => {
      const selectForScenario = () => {
        const experimental = scenarioPicker.selectElement.value === 'ppo_9x9_experimental';
        playerPicker.selectElements.forEach((select, index) => {
          const allowed = experimental
            ? types.filter(({ id }) => index === 0
              ? id === 'ppo-9x9-experimental'
              : id !== 'ppo-9x9-experimental')
            : types.filter(({ id }) => id !== 'ppo-9x9-experimental');
          populatePlayerTypeOptions(select, allowed,
            experimental ? allowed[0]?.id : select.value);
        });
      };
      scenarioPicker.selectElement.addEventListener('change', selectForScenario);
      scenarioPicker.ready.then(selectForScenario);
    });
  }

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
        const game = await service.createGame({
          scenarioId,
          playerTypes,
        });
        locationRef.assign(`battle.html?gameId=${encodeURIComponent(game.id)}`);
      } catch (error) {
        console.error('Failed to create game', error);
        enterBattleButton.disabled = false;
        enterBattleButton.textContent = defaultLabel;
        if (playerTypeStatus) {
          playerTypeStatus.textContent = error.code === 'ppoArtifactUnavailable'
            ? 'The trained PPO checkpoint is unavailable on this server.'
            : 'Failed to start game. Please try again.';
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

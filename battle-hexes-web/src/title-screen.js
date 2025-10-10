import p5 from 'p5';
import { ScrollingHexLandscape, DEFAULT_SCROLL_SPEED } from './animation/scrolling-hex-landscape.js';
import { initializePlayerTypePicker } from './title-screen-player-types.js';
import { initializeScenarioPicker } from './title-screen-scenarios.js';

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

initializeScenarioPicker();
initializePlayerTypePicker();

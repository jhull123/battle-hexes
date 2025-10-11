import { Game } from './game.js';

export const extractGameIdFromLocation = () => {
  const pathMatch = window.location.pathname.match(/battle(?:\.html)?\/([^/?#]+)/);
  if (pathMatch && pathMatch[1]) {
    return pathMatch[1];
  }

  const params = new URLSearchParams(window.location.search);
  return params.get('gameId');
};

export const updateUrlWithGameId = (gameId) => {
  const params = new URLSearchParams(window.location.search);
  params.set('gameId', gameId);
  const query = params.toString();
  let pathname = window.location.pathname;

  if (/battle(?:\.html)?\/[^/]+$/.test(pathname)) {
    pathname = pathname.replace(/(battle(?:\.html)?\/)[^/]+$/, `$1${encodeURIComponent(gameId)}`);
  }

  const canReplace =
    window.location.protocol === 'http:' || window.location.protocol === 'https:';

  if (canReplace && 'replaceState' in history) {
    history.replaceState(null, '', `${pathname}${query ? `?${query}` : ''}`);
  }
};

export const loadGameData = async () => {
  const existingGameId = extractGameIdFromLocation();
  if (existingGameId) {
    const gameData = await Game.fetchGameFromServer(existingGameId);
    updateUrlWithGameId(gameData.id);
    return gameData;
  }

  const defaultGame = await Game.newGameFromServer();
  updateUrlWithGameId(defaultGame.id);
  return defaultGame;
};

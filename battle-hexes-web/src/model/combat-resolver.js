// import { API_URL } from './battle-api';
// import axios from 'axios';

export class CombatResolver {
  #board;

  constructor(board) {
    this.#board = board;
  }

  resolveCombat() {
    console.log(this.#board);
  }
}
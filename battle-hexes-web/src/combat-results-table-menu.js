export class CombatResultsTableMenu {
  #game;
  #table;
  #dialog;
  #openLink;
  #closeButton;

  constructor(game) {
    this.#game = game;
    this.#table = document.getElementById('combatResultsTable');
    this.#dialog = document.getElementById('combatResultsTableDialog');
    this.#openLink = document.getElementById('openCombatResultsTable');
    this.#closeButton = document.getElementById('closeCombatResultsTable');
    this.#openLink.addEventListener('click', (event) => {
      event.preventDefault();
      this.#open();
    });
    this.#closeButton.addEventListener('click', () => this.#close());
    this.#dialog.addEventListener('click', (event) => {
      if (event.target === this.#dialog) {
        this.#close();
      }
    });
    this.#dialog.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        this.#close();
      }
    });
    this.render();
  }

  #open() {
    this.#dialog.style.display = 'flex';
    this.#closeButton.focus();
  }

  #close() {
    this.#dialog.style.display = 'none';
    this.#openLink.focus();
  }

  setGame(game) {
    this.#game = game;
    this.render();
  }

  render() {
    const table = this.#game.getCombatResultsTable();
    this.#table.replaceChildren(
      this.#caption(),
      this.#header(table.dieRolls),
      this.#body(table.rows),
    );
  }

  #caption() {
    const caption = document.createElement('caption');
    caption.textContent = 'Combat Results Table';
    return caption;
  }

  #header(dieRolls) {
    const head = document.createElement('thead');
    const row = document.createElement('tr');
    row.appendChild(this.#headerCell('Odds'));
    for (const dieRoll of dieRolls) {
      row.appendChild(this.#headerCell(String(dieRoll)));
    }
    head.appendChild(row);
    return head;
  }

  #headerCell(text) {
    const header = document.createElement('th');
    header.scope = 'col';
    header.textContent = text;
    return header;
  }

  #body(rows) {
    const body = document.createElement('tbody');
    for (const tableRow of rows) {
      const row = document.createElement('tr');
      const odds = document.createElement('th');
      odds.scope = 'row';
      odds.textContent = `${tableRow.odds[0]}:${tableRow.odds[1]}`;
      row.appendChild(odds);

      if (tableRow.automaticResult) {
        const automatic = document.createElement('td');
        automatic.colSpan = 6;
        automatic.className = 'crt-automatic-result';
        automatic.textContent = `Automatic: ${tableRow.automaticResult.text}`;
        row.appendChild(automatic);
      } else {
        for (const result of tableRow.results) {
          const cell = document.createElement('td');
          cell.textContent = result.text;
          row.appendChild(cell);
        }
      }
      body.appendChild(row);
    }
    return body;
  }
}

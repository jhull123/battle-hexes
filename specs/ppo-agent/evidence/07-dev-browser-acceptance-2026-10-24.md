# Increment 07 — deployed browser acceptance (2026-10-24)

**Result: passed on Dev.** This record closes the backend-connected durable-browser gate in [schedule 2](../playable-player-schedule.md) and the [07 specification](../07-trained-9x9-human-visible-slice.md). It is one integration acceptance run, not a policy-strength claim or a replacement for the later Crossroads gate.

## Revision and environment

- Source: `story/ppo-vs-humans` at `bfc50e5bca04e495abf0d45613de99288a9f146c` ([PR #392](https://github.com/jhull123/battle-hexes/pull/392)). The [API deployment](https://github.com/jhull123/battle-hexes/actions/runs/40098772545) and [web deployment](https://github.com/jhull123/battle-hexes/actions/runs/40098796578) both succeeded at this SHA before the run.
- UI: `https://dev.battlehexes.com/index.html`; API: `https://api-dev.battlehexes.com`.
- Scenario: `ppo_9x9_experimental` version 2, trained PPO/Learner first, Human/Opponent second; 10-turn limit. Game-bound checkpoint digest: `979688bebe368e89ceee0fb4b62924aa7516877ead325b07b9dc521e198994e0`.
- The deployed ECS task template sets `DYNAMODB_ENABLED=true` and imports the dev table name. The live `/ready` endpoint returned HTTP 200; game versions and events remained available from separate browser processes and later GETs. No DynamoDB item was inspected directly.

## Browser playthrough and authoritative evidence

- [Completed game](https://dev.battlehexes.com/battle.html?gameId=ec08a761-b0bf-4c8c-a6f8-101f06a2b5de): created through the title UI. PPO issued one order per unit; the human `/move` command moved Opponent 1 from (5,6) to (5,5), version 3 → 4. A fresh browser process loaded the same game during the human movement phase and rendered the retained position.
- Turn 1 human combat: Opponent 1 attacked Learner 1 at base/final 1:1, die 4, `ATTACKER_RETREAT_2`. The UI displayed **Combat - Attacker Retreat 2 Hexes**; the persisted game log recorded the retreat to (6,7).
- Turn 2 human move into (4,4): Learner 1's defensive fire had probability 0.25, roll 0.6443435123916158, outcome `no_effect`. The UI displayed **Defensive Fire - No Effect**; the event and spent fire were reflected in the API/log. This fire did not itself cause a retreat. The following 1:1 combat rolled 5 and eliminated Opponent 0.
- The game reached core `completed` at turn 10/10, version 46: draw, scores 0–0, no winner, null active player/phase, empty pending combats. The browser displayed the same Game Over result. A fresh reload rendered the board canvas and dialog, with the phase button disabled and no page errors.

Captured browser views: [human mid-turn reload](07-dev-browser-images/mid-turn-reload.png), [defensive fire and retreat in the log](07-dev-browser-images/defensive-fire.png), and [completed-game reload](07-dev-browser-images/completed-reload.png).

## Pending-PPO-order reload/resume

The completed game's reload above was on a human movement turn, so a separate saved-state check exercised the narrower pending-PPO-order requirement:

- [Resume game](https://dev.battlehexes.com/battle.html?gameId=1a055920-c4e6-4be5-81fd-9bb9cc2ac3f1) was created through the dev API with both PPO slots pending at version 1. One `/ppo/order` committed `learner-0` at version 2, leaving only `learner-1` pending with the same checkpoint digest.
- A fresh browser process loaded version 2 by GET, observed `pendingUnitIds=["learner-1"]`, issued **exactly one** `/ppo/order` for `learner-1`, and reached version 3 with an empty pending list and the Human/Opponent movement turn active. There were no browser page errors or duplicate PPO orders.

The [resumed browser view](07-dev-browser-images/pending-ppo-resumed.png) shows the human turn after the remaining order; the version/pending-unit facts above are from the captured API responses.

The accepted game and pending-order checks establish the 07 browser gate on the deployed configuration. The 11 DynamoDB integration tests skipped in the earlier PR review remain a test-suite coverage gap, and a defensive-fire-caused retreat was not observed in this random run. Neither changes the observed fire plus combat-retreat acceptance result.

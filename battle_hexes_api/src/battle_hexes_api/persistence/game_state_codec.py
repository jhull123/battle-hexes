"""Public facade for canonical, safe serialization of authoritative state."""

import json
from typing import Callable

from battle_hexes_core.scenario.scenario_loader import (
    ScenarioData,
    load_scenario_data,
)

from .contracts import StoredGame
from .errors import SavedGameIncompatibleError
from .game_state_document import Document
from .game_state_encoder import GameStateEncoder
from .game_state_hydrator import GameStateHydrator
from .game_state_validator import GameStateValidator
from .identity import canonical_json_bytes


class GameStateCodec:
    """Encode games and hydrate detached games against immutable scenarios."""

    STATE_SCHEMA_VERSION = 1

    def __init__(
        self,
        scenario_loader: Callable[[str], ScenarioData] = load_scenario_data,
    ) -> None:
        self._scenario_loader = scenario_loader
        self._encoder = GameStateEncoder(self.STATE_SCHEMA_VERSION)
        self._validator = GameStateValidator(self.STATE_SCHEMA_VERSION)
        self._hydrator = GameStateHydrator()

    def encode(self, game, *, scenario_version: str) -> bytes:
        """Return a complete canonical version-1 state document."""
        try:
            scenario = self._load_scenario(game.scenario_id)
            if scenario.version != scenario_version:
                self._incompatible("scenario_version")
            document = self._encoder.encode(game, scenario, scenario_version)
            self._validator.validate(document, scenario)
            return canonical_json_bytes(document.model_dump(mode="json"))
        except SavedGameIncompatibleError:
            raise
        except Exception as error:
            raise SavedGameIncompatibleError("invalid_game_graph") from error

    def decode(self, stored_game: StoredGame):
        """Validate and hydrate a detached game without running game rules."""
        try:
            if stored_game.state_schema_version != self.STATE_SCHEMA_VERSION:
                self._incompatible("schema_version")
            document = Document.model_validate(
                json.loads(stored_game.state.decode("utf-8"))
            )
            self._validate_metadata(document, stored_game)
            scenario = self._load_scenario(document.scenario_id)
            if scenario.version != document.scenario_version:
                self._incompatible("scenario_version")
            self._validator.validate(document, scenario)
            return self._hydrator.hydrate(document, scenario)
        except SavedGameIncompatibleError:
            raise
        except Exception as error:
            raise SavedGameIncompatibleError("invalid_state") from error

    def _load_scenario(self, scenario_id: str) -> ScenarioData:
        try:
            scenario = self._scenario_loader(scenario_id)
        except Exception as error:
            raise SavedGameIncompatibleError("scenario_missing") from error
        if not isinstance(scenario, ScenarioData):
            self._incompatible("scenario_invalid")
        return scenario

    @staticmethod
    def _validate_metadata(document: Document, stored_game: StoredGame):
        matches = (
            document.game_id == stored_game.game_id
            and document.scenario_id == stored_game.scenario_id
            and document.scenario_version == stored_game.scenario_version
            and document.state_schema_version
            == stored_game.state_schema_version
        )
        if not matches:
            GameStateCodec._incompatible("metadata")

    @staticmethod
    def _incompatible(category):
        raise SavedGameIncompatibleError(category)

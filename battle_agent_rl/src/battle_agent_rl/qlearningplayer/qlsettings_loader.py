"""Utility helpers for loading Q-learning configuration."""

from __future__ import annotations

import inspect
import json
import logging
from pathlib import Path
from typing import Any, Dict

from .qlearningplayer import QLearningPlayer


class QLearningSettingsLoader:
    """Load ``QLearningPlayer`` keyword arguments from an optional JSON file.

    The loader inspects :class:`QLearningPlayer` to discover its configurable
    keyword arguments and default values. When :meth:`load` is called it reads
    a ``qlsettings.json`` file (or a custom path), merges any provided values
    with those defaults, and logs which settings are used. Missing or
    unrecognized values automatically fall back to the class defaults so the
    caller always receives a complete, valid configuration dictionary.
    """

    _IGNORED_PARAMETERS = {"self", "name", "type", "factions", "board"}

    def __init__(
        self,
        settings_path: Path | str = Path("qlsettings.json"),
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings_path = Path(settings_path)
        self._logger = logger or logging.getLogger(__name__)
        self._defaults = self._collect_defaults()

    def load(self) -> Dict[str, Any]:
        """Return the merged Q-learning settings from disk and defaults."""

        defaults = self.defaults
        if not self._settings_path.exists():
            self._logger.info(
                "No qlsettings.json found at %s; using defaults.",
                self._settings_path,
            )
            self._log_default_settings()
            return defaults

        try:
            with self._settings_path.open(encoding="utf-8") as settings_file:
                raw_settings = json.load(settings_file)
        except json.JSONDecodeError as exc:
            self._logger.warning(
                "Failed to parse qlsettings.json at %s (%s); using defaults.",
                self._settings_path,
                exc,
            )
            self._log_default_settings()
            return defaults

        if not isinstance(raw_settings, dict):
            self._logger.warning(
                "Expected qlsettings.json at %s to contain an object; "
                "using defaults.",
                self._settings_path,
            )
            self._log_default_settings()
            return defaults

        for key, value in raw_settings.items():
            if key in self._defaults:
                defaults[key] = value
            else:
                self._logger.warning(
                    "Ignoring unrecognized Q-learning setting '%s'", key
                )

        missing_keys = sorted(set(self._defaults) - raw_settings.keys())
        if missing_keys:
            self._logger.info(
                "Using default values for missing Q-learning settings: %s",
                ", ".join(missing_keys),
            )

        self._logger.info(
            "Using Q-learning settings from %s: %s",
            self._settings_path,
            defaults,
        )
        return defaults

    @property
    def defaults(self) -> Dict[str, Any]:
        """Return a copy of the default Q-learning keyword arguments."""

        return self._defaults.copy()

    def _collect_defaults(self) -> Dict[str, Any]:
        defaults: Dict[str, Any] = {}
        signature = inspect.signature(QLearningPlayer)
        for name, parameter in signature.parameters.items():
            if name in self._IGNORED_PARAMETERS:
                continue
            if parameter.default is inspect._empty:
                continue
            defaults[name] = parameter.default
        return defaults

    def _log_default_settings(self) -> None:
        self._logger.info("Using Q-learning settings: %s", self._defaults)


__all__ = ["QLearningSettingsLoader"]

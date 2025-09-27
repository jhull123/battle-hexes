import json
import logging

from battle_agent_rl.qlearningplayer import QLearningSettingsLoader


LOGGER_NAME = "battle_agent_rl.qlearningplayer.qlsettings_loader"


def test_missing_settings_file_returns_defaults_and_logs(tmp_path, caplog):
    settings_path = tmp_path / "qlsettings.json"
    loader = QLearningSettingsLoader(settings_path=settings_path)

    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    settings = loader.load()

    assert settings == loader.defaults
    assert "No qlsettings.json found" in caplog.text
    assert "Using Q-learning settings:" in caplog.text


def test_partial_settings_override_defaults(tmp_path, caplog):
    settings_path = tmp_path / "qlsettings.json"
    settings_path.write_text(
        json.dumps({"alpha": 0.5, "epsilon": 0.02, "unknown": 42}),
        encoding="utf-8",
    )
    loader = QLearningSettingsLoader(settings_path=settings_path)

    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    settings = loader.load()
    defaults = loader.defaults

    assert settings["alpha"] == 0.5
    assert settings["epsilon"] == 0.02
    for key, value in defaults.items():
        if key not in {"alpha", "epsilon"}:
            assert settings[key] == value

    assert (
        "Ignoring unrecognized Q-learning setting 'unknown'" in caplog.text
    )
    assert (
        "Using default values for missing Q-learning settings" in caplog.text
    )


def test_invalid_json_uses_defaults(tmp_path, caplog):
    settings_path = tmp_path / "qlsettings.json"
    settings_path.write_text("{invalid", encoding="utf-8")
    loader = QLearningSettingsLoader(settings_path=settings_path)

    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    settings = loader.load()

    assert settings == loader.defaults
    assert "Failed to parse qlsettings.json" in caplog.text


def test_non_mapping_json_uses_defaults(tmp_path, caplog):
    settings_path = tmp_path / "qlsettings.json"
    settings_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    loader = QLearningSettingsLoader(settings_path=settings_path)

    caplog.set_level(logging.INFO, logger=LOGGER_NAME)

    settings = loader.load()

    assert settings == loader.defaults
    assert "Expected qlsettings.json" in caplog.text

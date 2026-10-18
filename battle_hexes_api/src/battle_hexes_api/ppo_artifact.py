"""Administrator-configured frozen model; never sourced from a request."""

import logging
import os
from functools import lru_cache
from pathlib import Path
from threading import Lock


logger = logging.getLogger(__name__)
_model_load_lock = Lock()


def _run_dir():
    run_dir = os.environ.get("BATTLE_HEXES_PPO_RUN_DIR")
    if not run_dir:
        logger.error(
            "PPO artifact unavailable: BATTLE_HEXES_PPO_RUN_DIR is unset")
        raise ValueError("Experimental PPO artifact is not configured")
    manifest_path = Path(run_dir) / "manifest.json"
    if not Path(run_dir).is_dir():
        logger.error(
            "PPO artifact directory does not exist or is not a directory: %s",
            run_dir,
        )
    elif not manifest_path.is_file():
        logger.error(
            "PPO artifact manifest is missing: %s", manifest_path)
    return run_dir


def configured_artifact(digest=None):
    """Validate the current manifest and checkpoint without loading a model."""
    run_dir = _run_dir()
    try:
        from battle_agent_rl.ppo.playable_artifact import validate_artifact
        return validate_artifact(run_dir, digest)
    except ImportError as error:
        logger.exception("PPO serving dependencies could not be imported")
        raise ValueError("PPO runtime dependencies are unavailable") from error
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        logger.exception(
            "PPO artifact validation failed (run_dir=%s, "
            "expected_digest=%s): %s",
            run_dir, digest or "not-bound-yet", error,
        )
        raise


@lru_cache(maxsize=1)
def _load_cached_model(run_dir, digest):
    from battle_agent_rl.ppo.playable_artifact import load_model
    model, manifest = load_model(run_dir, digest)
    logger.info(
        "PPO serving artifact loaded (run_dir=%s, contract=%s, "
        "scenario=%s@%s, checkpoint=%s, digest=%s)",
        run_dir,
        manifest["contract"],
        manifest["scenario_id"],
        manifest["scenario_version"],
        manifest["checkpoint"]["path"],
        manifest["checkpoint"]["sha256"],
    )
    return model


def configured_model(digest=None):
    run_dir = _run_dir()
    manifest = configured_artifact(digest)
    checkpoint_digest = manifest["checkpoint"]["sha256"]

    try:
        # lru_cache alone permits duplicate work on concurrent first calls.
        with _model_load_lock:
            model = _load_cached_model(run_dir, checkpoint_digest)
    except ImportError as error:
        logger.exception("PPO serving dependencies could not be imported")
        raise ValueError("PPO runtime dependencies are unavailable") from error
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        logger.exception(
            "PPO artifact validation/loading failed "
            "(run_dir=%s, expected_digest=%s): %s",
            run_dir,
            checkpoint_digest,
            error,
        )
        raise
    return model, manifest

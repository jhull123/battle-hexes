"""Administrator-configured frozen model; never sourced from a request."""

import logging
import os
from pathlib import Path


logger = logging.getLogger(__name__)


def configured_model(digest=None):
    try:
        from battle_agent_rl.ppo.playable_artifact import load_model
    except ImportError as error:
        logger.exception("PPO serving dependencies could not be imported")
        raise ValueError("PPO runtime dependencies are unavailable") from error

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

    try:
        model, manifest = load_model(run_dir, digest)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        logger.exception(
            "PPO artifact validation/loading failed "
            "(run_dir=%s, expected_digest=%s): %s",
            run_dir,
            digest or "not-bound-yet",
            error,
        )
        raise

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
    return model, manifest

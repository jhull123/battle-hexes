"""Bounded, process-local successful validation of a stable artifact pair."""

from copy import deepcopy
from pathlib import Path
from threading import Lock


def _file_identity(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size,
            stat.st_mtime_ns, stat.st_ctime_ns)


def _pair_identity(run_dir, runtime):
    return (run_dir, runtime,
            _file_identity(run_dir / "manifest.json"),
            _file_identity(run_dir / "checkpoint.zip"))


class ArtifactValidationCache:
    """Retain only the last successful validation; never cache failures.

    Stat both files on every lookup, including ctime to detect same-size writes
    with restored mtime and inode/device to detect atomic replacement. This is
    not protection against a hostile filesystem forging unchanged metadata.
    """

    def __init__(self):
        self._lock = Lock()
        self._identity = None
        self._manifest = None

    def validate(self, run_dir, runtime, validator):
        run_dir = Path(run_dir).resolve()
        # Serialize cold validation as well as publication, avoiding duplicate
        # hashes and patch-version warnings for concurrent requests.
        with self._lock:
            try:
                identity = _pair_identity(run_dir, runtime)
                if identity != self._identity:
                    self._identity = None
                    self._manifest = None
                    manifest = validator(run_dir)
                    if identity != _pair_identity(run_dir, runtime):
                        raise ValueError(
                            "PPO artifact changed during validation")
                    self._manifest = manifest
                    self._identity = identity
                # A caller must not be able to mutate trusted cached metadata.
                return deepcopy(self._manifest)
            except (OSError, ValueError):
                self._identity = None
                self._manifest = None
                raise

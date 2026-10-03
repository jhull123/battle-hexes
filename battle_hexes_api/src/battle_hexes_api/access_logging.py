"""Access-log filtering for routine health-check requests."""

import logging


class HealthCheckAccessLogFilter(logging.Filter):
    """Suppress successful Uvicorn access logs for health endpoints."""

    HEALTH_PATHS = {"/health", "/ready"}

    def filter(self, record):
        if record.name != "uvicorn.access" or len(record.args) != 5:
            return True

        _client, _method, path, _http_version, status = record.args
        try:
            status_code = int(status)
        except (TypeError, ValueError):
            return True

        return not (
            path in self.HEALTH_PATHS and 200 <= status_code < 400
        )


def configure_access_log_filter():
    """Install the health-check filter once on Uvicorn's access logger."""
    access_logger = logging.getLogger("uvicorn.access")
    if not any(
        isinstance(log_filter, HealthCheckAccessLogFilter)
        for log_filter in access_logger.filters
    ):
        access_logger.addFilter(HealthCheckAccessLogFilter())

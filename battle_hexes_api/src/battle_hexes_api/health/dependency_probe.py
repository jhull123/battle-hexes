"""Cached, periodic DynamoDB data-path health signal."""

import logging
from threading import Lock

from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# A missing item is a successful GetItem. These keys are never written by the app.
PROBE_KEY = {
    "pk": {"S": "HEALTH#READINESS"},
    "sk": {"S": "HEALTH#READINESS"},
}
PROBE_INTERVAL_SECONDS = 60
FAILURE_THRESHOLD = 3


class DynamoDBReadinessProbe:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self._lock = Lock()
        self._ready = False
        self._failures = 0

    @property
    def is_ready(self) -> bool:
        with self._lock:
            return self._ready

    def probe_once(self) -> None:
        """Check the read path and update readiness without exposing AWS errors."""
        try:
            self.client.get_item(TableName=self.table_name, Key=PROBE_KEY)
        except (BotoCoreError, ClientError):
            with self._lock:
                self._failures += 1
                if self._failures >= FAILURE_THRESHOLD:
                    self._ready = False
                failures = self._failures
            logger.warning(
                "DynamoDB readiness probe failed table=%s consecutive_failures=%s",
                self.table_name,
                failures,
            )
        else:
            with self._lock:
                recovered = not self._ready
                self._ready = True
                self._failures = 0
            if recovered:
                logger.info("DynamoDB readiness probe recovered table=%s", self.table_name)

"""Application liveness and readiness endpoints."""

from battle_hexes_api.health.readiness import router
from battle_hexes_api.health.startup import lifespan

__all__ = ["lifespan", "router"]

"""Application liveness and readiness endpoints."""

from battle_hexes_api.health.readiness import lifespan, router

__all__ = ["lifespan", "router"]

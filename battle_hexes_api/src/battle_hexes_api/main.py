"""Battle Hexes ASGI entry point."""

from battle_hexes_api.access_logging import configure_access_log_filter
from battle_hexes_api.application import create_app

configure_access_log_filter()
app = create_app()

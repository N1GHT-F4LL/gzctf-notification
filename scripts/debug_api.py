#!/usr/bin/env python3
"""
Debug GZCTF API using the same client/auth flow as the bot (cookie-based auth)
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Make sure both project root and bot package are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

from bot.config import load_config
from bot.gzctf_client import GZCTFClient


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_api_calls() -> None:
    """Run auth and a set of API calls via GZCTFClient."""
    config = load_config()

    logger.info("=== GZCTF API Debug ===")
    logger.info(f"Base URL: {config.gzctf.base_url}")
    logger.info(f"Game ID: {config.game_id}")
    logger.info(f"Username: {config.gzctf.username}")

    if not (config.gzctf.username and config.gzctf.password):
        logger.error("Username and password are required")
        return

    async with GZCTFClient(config.gzctf) as client:
        logger.info("Authenticating...")
        if not await client.authenticate():
            logger.error("Authentication failed")
            return
        logger.info("Authentication successful (cookie-based)")

        # Games list (optional; some client builds may not expose this helper)
        if hasattr(client, 'get_games'):
            try:
                games = await client.get_games()  # type: ignore[attr-defined]
                logger.info(f"/api/games → {len(games)} games")
                if games:
                    logger.info(f"First game: {games[0]}")
            except Exception as e:
                logger.warning(f"/api/games fetch issue: {e}")
        else:
            logger.info("Skipping /api/games (client has no get_games method)")

        if config.game_id is not None:
            game_id = config.game_id

            # Game info
            try:
                info = await client.get_game_info(game_id)
                if info:
                    logger.info(f"/api/game/{game_id} → title={info.get('title', 'Unknown')}")
                else:
                    logger.warning(f"/api/game/{game_id} returned no data")
            except Exception as e:
                logger.error(f"Error fetching game info: {e}")

            # Notices
            try:
                notices = await client.get_game_notices(game_id, count=5)
                logger.info(f"/api/game/{game_id}/notices → {len(notices) if notices else 0} items")
                if notices:
                    logger.info(f"First notice: {notices[0]}")
            except Exception as e:
                logger.error(f"Error fetching notices: {e}")

            # Events (try with different params)
            for params in (
                {"count": 5, "skip": 0, "hide_container": False},
                {"count": 5, "skip": 0, "hide_container": True},
            ):
                try:
                    events = await client.get_game_events(
                        game_id,
                        count=params["count"],
                        skip=params["skip"],
                        hide_container=params["hide_container"],
                    )
                    logger.info(
                        f"/api/game/{game_id}/events (count={params['count']}, hideContainer={params['hide_container']}) → {len(events) if events else 0} items"
                    )
                    if getattr(client, 'events_forbidden', False):
                        logger.warning("Events endpoint is forbidden (403) for current account")
                    if events:
                        logger.info(f"First event: {events[0]}")
                except Exception as e:
                    logger.error(f"Error fetching events: {e}")
        else:
            logger.warning("GAME_ID is not set; skipping game-specific endpoints")


if __name__ == "__main__":
    asyncio.run(debug_api_calls())
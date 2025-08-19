#!/usr/bin/env python3
"""
GZCTF Discord Notification Bot

A Discord bot that monitors GZCTF platform for notifications and events,
then pushes them to a Discord channel in real-time.
"""

import os
import sys
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from dotenv import load_dotenv

from config import load_config
from gzctf_client import GZCTFClient
from discord_bot import GZCTFNotificationBot

# Exit codes
EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_CONFIG = 2
EXIT_AUTH = 3

logger = logging.getLogger(__name__)


def _resolve_log_dir(explicit: Optional[str] = None) -> str:
    """Resolve the directory to store log files."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend([
        os.path.join('/app', 'logs'),
        os.path.join(os.getcwd(), 'logs'),
        os.getcwd(),
    ])
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception:
            continue
    return os.getcwd()


def _configure_logging(debug: bool, explicit_log_dir: Optional[str]) -> None:
    """Configure logging for the bot."""
    level = logging.DEBUG if debug else logging.INFO
    log_dir = _resolve_log_dir(explicit_log_dir)
    log_file_path = os.path.join(log_dir, 'gzctf_bot.log')
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                log_file_path,
                maxBytes=5_000_000,
                backupCount=3,
                encoding='utf-8',
                delay=True
            )
        ]
    )


def _validate_config(cfg) -> Optional[str]:
    """Validate the loaded configuration."""
    if not cfg.discord.token:
        return "Discord token is required. Set DISCORD_TOKEN environment variable."
    if not cfg.game_id:
        return "Game ID is required. Set GAME_ID environment variable."
    if not (cfg.gzctf.username and cfg.gzctf.password):
        return "Username and password are required. Set GZCTF_USERNAME and GZCTF_PASSWORD environment variables."
    return None


def _log_startup_info(cfg) -> None:
    """Log startup information for the bot."""
    logger.info("Starting GZCTF Discord Notification Bot...")
    logger.info(f"GZCTF URL: {cfg.gzctf.base_url}")
    logger.info(f"Game ID: {cfg.game_id}")
    logger.info(f"Poll Interval: {cfg.poll_interval}s")
    logger.info(f"Notices Enabled: {cfg.enable_notices}")
    logger.info(f"Events Enabled: {cfg.enable_events}")
    logger.info(f"Debug Mode: {cfg.debug}")
    logger.info(f"Using username/password authentication for user: {cfg.gzctf.username}")


async def main() -> int:
    """Main function to run the bot. Returns an exit code."""
    try:
        # Load environment and configuration
        load_dotenv()
        cfg = load_config()

        # Configure logging after config is loaded
        _configure_logging(cfg.debug, os.getenv('LOG_DIR', '').strip() or None)

        config_error = _validate_config(cfg)
        if config_error:
            logger.error(config_error)
            return EXIT_CONFIG

        _log_startup_info(cfg)

        async with GZCTFClient(cfg.gzctf) as gzctf_client:
            # Authenticate with GZCTF
            if not await gzctf_client.authenticate():
                logger.error("Failed to authenticate with GZCTF. Check your credentials.")
                return EXIT_AUTH

            logger.info("Successfully authenticated with GZCTF")

            bot = GZCTFNotificationBot(config=cfg, gzctf_client=gzctf_client)
            await bot.start(cfg.discord.token)
        return EXIT_OK

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return EXIT_OK
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
#!/usr/bin/env python3
"""
GZCTF Discord Notification Bot

A Discord bot that monitors GZCTF platform for notifications and events,
then pushes them to a Discord channel in real-time.
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from dotenv import load_dotenv

from config import load_config
from gzctf_client import GZCTFClient
from discord_bot import GZCTFNotificationBot

# Load environment variables
load_dotenv()

# Load configuration first to check debug mode
config = load_config()

# Configure logging
log_level = logging.DEBUG if config.debug else logging.INFO

# Determine log directory (container: /app/logs; local: ./logs; env override: LOG_DIR)
def _resolve_log_dir() -> str:
    candidates = []
    env_log_dir = os.getenv('LOG_DIR', '').strip()
    if env_log_dir:
        candidates.append(env_log_dir)
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

log_dir = _resolve_log_dir()
log_file_path = os.path.join(log_dir, 'gzctf_bot.log')

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(log_file_path, maxBytes=5_000_000, backupCount=3, encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot"""
    try:
        # Validate required configuration
        if not config.discord.token:
            logger.error("Discord token is required. Set DISCORD_TOKEN environment variable.")
            sys.exit(1)
        if not config.game_id:
            logger.error("Game ID is required. Set GAME_ID environment variable.")
            sys.exit(1)
        logger.info("Starting GZCTF Discord Notification Bot...")
        logger.info(f"GZCTF URL: {config.gzctf.base_url}")
        logger.info(f"Game ID: {config.game_id}")
        logger.info(f"Poll Interval: {config.poll_interval}s")
        logger.info(f"Notices Enabled: {config.enable_notices}")
        logger.info(f"Events Enabled: {config.enable_events}")
        logger.info(f"Debug Mode: {config.debug}")
        
        # Validate authentication credentials
        if not (config.gzctf.username and config.gzctf.password):
            logger.error("Username and password are required. Set GZCTF_USERNAME and GZCTF_PASSWORD environment variables.")
            sys.exit(1)
        
        logger.info(f"Using username/password authentication for user: {config.gzctf.username}")
        
        # Create GZCTF client
        async with GZCTFClient(config.gzctf) as gzctf_client:
            # Authenticate with GZCTF
            if not await gzctf_client.authenticate():
                logger.error("Failed to authenticate with GZCTF. Check your credentials.")
                sys.exit(1)
            
            logger.info("Successfully authenticated with GZCTF")
            
            # Create and run Discord bot
            bot = GZCTFNotificationBot(
                config=config,
                gzctf_client=gzctf_client
            )
            
            # Run the bot
            await bot.start(config.discord.token)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
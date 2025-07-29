#!/usr/bin/env python3
"""
GZCTF Discord Notification Bot

A Discord bot that monitors GZCTF platform for notifications and events,
then pushes them to a Discord channel in real-time.
"""

import asyncio
import logging
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
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gzctf_bot.log')
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
            
        if not config.discord.channel_id:
            logger.error("Discord channel ID is required. Set DISCORD_CHANNEL_ID environment variable.")
            sys.exit(1)
            
        if not config.game_id:
            logger.error("Game ID is required. Set GAME_ID environment variable.")
            sys.exit(1)
        
        logger.info("Starting GZCTF Discord Notification Bot...")
        logger.info(f"GZCTF URL: {config.gzctf.base_url}")
        logger.info(f"Game ID: {config.game_id}")
        logger.info(f"Discord Channel: {config.discord.channel_id}")
        logger.info(f"Poll Interval: {config.poll_interval}s")
        logger.info(f"Notices Enabled: {config.enable_notices}")
        logger.info(f"Events Enabled: {config.enable_events}")
        logger.info(f"Debug Mode: {config.debug}")
        
        # Log authentication method
        if config.gzctf.api_token:
            logger.info("Using API token authentication")
        elif config.gzctf.username and config.gzctf.password:
            logger.info("Using username/password authentication")
        else:
            logger.warning("No authentication method configured")
        
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
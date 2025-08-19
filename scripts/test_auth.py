#!/usr/bin/env python3
"""
Test script to debug GZCTF authentication issues
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

from bot.config import load_config
from bot.gzctf_client import GZCTFClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_authentication():
    """Test GZCTF authentication and API calls"""
    config = load_config()
    
    logger.info(f"Testing authentication with GZCTF at {config.gzctf.base_url}")
    logger.info(f"Game ID: {config.game_id}")
    
    if config.gzctf.username and config.gzctf.password:
        logger.info(f"Using username/password authentication for user: {config.gzctf.username}")
    else:
        logger.error("Username and password are required")
        return
    
    async with GZCTFClient(config.gzctf) as client:
        # Test authentication
        logger.info("Testing authentication...")
        auth_result = await client.authenticate()
        logger.info(f"Authentication result: {auth_result}")
        
        if not auth_result:
            logger.error("Authentication failed, stopping test")
            return
        
        # Test games endpoint
        logger.info("Testing games endpoint...")
        games = await client.get_games()
        logger.info(f"Games result: {len(games) if games else 0} games found")
        if games:
            for game in games[:3]:  # Show first 3 games
                logger.info(f"  Game: {game.get('title', 'Unknown')} (ID: {game.get('id', 'Unknown')})")
        
        # Test notices endpoint
        logger.info(f"Testing notices endpoint for game {config.game_id}...")
        game_id = config.game_id or 1  # Default to 1 if None
        notices = await client.get_game_notices(game_id, count=5)
        logger.info(f"Notices result: {len(notices) if notices else 0} notices found")
        if notices:
            for notice in notices[:3]:  # Show first 3 notices
                logger.info(f"  Notice {notice.get('id', 'Unknown')}: {notice.get('type', 'Unknown')} - {notice.get('values', [])}")
        
        # Test events endpoint
        logger.info(f"Testing events endpoint for game {config.game_id}...")
        events = await client.get_game_events(game_id, count=5)
        logger.info(f"Events result: {len(events) if events else 0} events found")
        if events:
            for event in events[:3]:  # Show first 3 events
                logger.info(f"  Event: {event.get('type', 'Unknown')} - User: {event.get('user', 'Unknown')} - Team: {event.get('team', 'Unknown')}")
        
        # Test authentication check
        logger.info("Testing authentication check...")
        is_auth = await client.is_authenticated()
        logger.info(f"Is authenticated: {is_auth}")

if __name__ == "__main__":
    asyncio.run(test_authentication())
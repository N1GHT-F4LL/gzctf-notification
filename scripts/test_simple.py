#!/usr/bin/env python3
"""
Simple test script for username/password authentication
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

from config import load_config
from gzctf_client import GZCTFClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_simple():
    """Simple test for authentication and basic API calls"""
    config = load_config()
    
    logger.info("=== GZCTF Bot Authentication Test ===")
    logger.info(f"GZCTF URL: {config.gzctf.base_url}")
    logger.info(f"Username: {config.gzctf.username}")
    logger.info(f"Game ID: {config.game_id}")
    
    async with GZCTFClient(config.gzctf) as client:
        # Test authentication
        logger.info("Testing authentication...")
        if await client.authenticate():
            logger.info("✅ Authentication successful")
        else:
            logger.error("❌ Authentication failed")
            return
        
        # Test notices
        logger.info("Testing notices...")
        notices = await client.get_game_notices(config.game_id, count=3)
        if notices:
            logger.info(f"✅ Notices working: {len(notices)} notices found")
        else:
            logger.error("❌ Notices failed")
        
        # Test events
        logger.info("Testing events...")
        events = await client.get_game_events(config.game_id, count=3)
        if events:
            logger.info(f"✅ Events working: {len(events)} events found")
        else:
            logger.error("❌ Events failed")
    
    logger.info("=== Test completed ===")

if __name__ == "__main__":
    asyncio.run(test_simple())
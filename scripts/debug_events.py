#!/usr/bin/env python3
"""
Debug events specifically
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def debug_events():
    """Debug events endpoint specifically"""
    config = load_config()
    
    logger.info("=== Events Debug ===")
    logger.info(f"Game ID: {config.game_id}")
    
    async with GZCTFClient(config.gzctf) as client:
        # Authenticate
        if not await client.authenticate():
            logger.error("Authentication failed")
            return
        
        logger.info("Authentication successful")
        
        # Test events with different parameters
        test_cases = [
            {"count": 10, "skip": 0, "hide_container": False},
            {"count": 5, "skip": 0, "hide_container": True},
            {"count": 3, "skip": 0, "hide_container": False},
        ]
        
        for i, params in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {i}: {params} ---")
            
            events = await client.get_game_events(
                config.game_id, 
                count=params["count"],
                skip=params["skip"],
                hide_container=params["hide_container"]
            )
            
            if events is None:
                logger.error(f"Events returned None (likely error)")
            elif len(events) == 0:
                logger.warning(f"Events returned empty list")
            else:
                logger.info(f"Events returned {len(events)} events")
                for j, event in enumerate(events[:3]):  # Show first 3
                    logger.info(f"  Event {j+1}: {event.get('type', 'Unknown')} - Time: {event.get('time', 0)} - User: {event.get('user', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(debug_events())
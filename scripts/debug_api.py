#!/usr/bin/env python3
"""
Debug script to examine API requests in detail
"""

import asyncio
import aiohttp
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def debug_api_calls():
    """Debug API calls to understand the 401 issue"""
    
    base_url = os.getenv("GZCTF_BASE_URL", "https://ctf.hackkap.com/").rstrip('/')
    username = os.getenv("GZCTF_USERNAME")
    password = os.getenv("GZCTF_PASSWORD")
    game_id = int(os.getenv("GAME_ID", "7"))
    
    if not username or not password:
        logger.error("Username and password are required")
        return
    
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Game ID: {game_id}")
    logger.info(f"Username: {username}")
    
    # First, authenticate to get token
    auth_token = None
    
    async with aiohttp.ClientSession() as session:
        # First authenticate
        logger.info("Authenticating...")
        login_data = {
            "userName": username,
            "password": password
        }
        
        async with session.post(f"{base_url}/api/account/login", json=login_data) as response:
            if response.status == 200:
                cookies = response.cookies
                if 'token' in cookies:
                    auth_token = cookies['token'].value
                    logger.info("Authentication successful")
                else:
                    logger.error("No token found in cookies")
                    return
            else:
                logger.error(f"Authentication failed: {response.status}")
                return
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
        
        # Test different endpoints
        endpoints = [
            f"/api/games",
            f"/api/game/{game_id}",
            f"/api/game/{game_id}/notices",
            f"/api/game/{game_id}/events",
            f"/api/game/{game_id}/events?count=5&skip=0&hideContainer=false"
        ]
        
        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            logger.info(f"\n--- Testing endpoint: {endpoint} ---")
            logger.info(f"Full URL: {url}")
            
            try:
                async with session.get(url, headers=headers) as response:
                    logger.info(f"Status: {response.status}")
                    logger.info(f"Headers: {dict(response.headers)}")
                    
                    content_type = response.headers.get('content-type', '')
                    text = await response.text()
                    
                    if 'application/json' in content_type:
                        try:
                            import json
                            data = json.loads(text)
                            if isinstance(data, list):
                                logger.info(f"Response: List with {len(data)} items")
                                if data:
                                    logger.info(f"First item: {data[0]}")
                            else:
                                logger.info(f"Response: {data}")
                        except:
                            logger.info(f"Response (raw): {text[:500]}")
                    else:
                        logger.info(f"Response (non-JSON): {text[:200]}")
                        
            except Exception as e:
                logger.error(f"Error calling {endpoint}: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api_calls())
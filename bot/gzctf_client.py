import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from config import GZCTFConfig

logger = logging.getLogger(__name__)

class GZCTFClient:
    """GZCTF API Client for fetching notifications and events"""
    
    def __init__(self, config: GZCTFConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate with GZCTF API"""
        if self.config.api_token:
            self.auth_token = self.config.api_token
            return True
            
        if not (self.config.username and self.config.password):
            logger.warning("No authentication credentials provided")
            return False
            
        try:
            login_data = {
                "userName": self.config.username,
                "password": self.config.password
            }
            
            # Ensure base_url doesn't end with slash to avoid double slashes
            base_url = self.config.base_url.rstrip('/')
            async with self.session.post(
                f"{base_url}/api/account/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    # Extract token from response headers or cookies
                    cookies = response.cookies
                    if 'token' in cookies:
                        self.auth_token = cookies['token'].value
                    else:
                        # Try to get from response headers
                        auth_header = response.headers.get('Authorization')
                        if auth_header and auth_header.startswith('Bearer '):
                            self.auth_token = auth_header[7:]
                    
                    logger.info("Successfully authenticated with GZCTF")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
    
    async def get_game_notices(self, game_id: int, count: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Get game notices from GZCTF API"""
        try:
            # Ensure base_url doesn't end with slash to avoid double slashes
            base_url = self.config.base_url.rstrip('/')
            url = f"{base_url}/api/game/{game_id}/notices"
            params = {"count": count, "skip": skip}
            
            async with self.session.get(
                url, 
                params=params, 
                headers=self._get_headers()
            ) as response:
                logger.debug(f"Game notices response status: {response.status}")
                logger.debug(f"Game notices response headers: {response.headers}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        return data
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {json_error}")
                        logger.debug(f"Response content: {await response.text()}")
                        return []
                else:
                    logger.error(f"Failed to get game notices: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching game notices: {e}")
            return []
    
    async def get_game_events(self, game_id: int, count: int = 100, skip: int = 0, hide_container: bool = False) -> List[Dict[str, Any]]:
        """Get game events from GZCTF API"""
        try:
            # Ensure base_url doesn't end with slash to avoid double slashes
            base_url = self.config.base_url.rstrip('/')
            url = f"{base_url}/api/game/{game_id}/events"
            params = {
                "count": count, 
                "skip": skip,
                "hideContainer": str(hide_container).lower()  # Convert boolean to string
            }
            
            async with self.session.get(
                url, 
                params=params, 
                headers=self._get_headers()
            ) as response:
                logger.debug(f"Game events response status: {response.status}")
                logger.debug(f"Game events response headers: {response.headers}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        return data
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {json_error}")
                        logger.debug(f"Response content: {await response.text()}")
                        return []
                else:
                    logger.error(f"Failed to get game events: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching game events: {e}")
            return []
    
    async def get_games(self) -> List[Dict[str, Any]]:
        """Get list of available games"""
        try:
            # Ensure base_url doesn't end with slash to avoid double slashes
            base_url = self.config.base_url.rstrip('/')
            url = f"{base_url}/api/games"
            
            async with self.session.get(
                url, 
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"Failed to get games: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return [] 
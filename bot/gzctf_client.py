import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

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
        """Authenticate with GZCTF API using username/password"""
        if not (self.config.username and self.config.password):
            logger.error("Username and password are required for authentication")
            return False
            
        try:
            login_data = {
                "userName": self.config.username,
                "password": self.config.password
            }
            
            # Ensure base_url doesn't end with slash to avoid double slashes
            base_url = self.config.base_url.rstrip('/')
            
            # Đóng session cũ nếu có để tránh rò rỉ tài nguyên
            if self.session is not None:
                try:
                    await self.session.close()
                except Exception as e:
                    logger.warning(f"Error closing existing session: {e}")
            
            # Create a new session for each authentication with a cookie jar
            cookie_jar = aiohttp.CookieJar(unsafe=True)  # Allow unsafe cookies (needed for some domains)
            
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(base_url)
            domain = parsed_url.netloc
            logger.debug(f"Using domain for cookies: {domain}")
            
            self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)
            logger.debug("Created new session for authentication with custom cookie jar")
                
            async with self.session.post(
                f"{base_url}/api/account/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    # Log chi tiết về response
                    logger.debug(f"Authentication response status: {response.status}")
                    logger.debug(f"Authentication response headers: {dict(response.headers)}")
                    
                    # Log thông tin về cookies
                    logger.debug(f"Cookies: {[f'{c.key}={c.value}' for c in response.cookies.values()]}")
                    
                    # Đọc nội dung response
                    response_text = await response.text()
                    logger.debug(f"Response body (first 200 chars): {response_text[:200]}")
                    
                    # Extract token from response headers or cookies
                    cookies = response.cookies
                    token_value = None
                    
                    # Only check for 'GZCTF_Token' cookie (based on logs)
                    if 'GZCTF_Token' in cookies:
                        token_value = cookies['GZCTF_Token'].value
                        logger.debug("Found GZCTF_Token cookie")
                        # Save cookie to session
                        from urllib.parse import urlparse
                        parsed_url = urlparse(base_url)
                        domain = parsed_url.netloc
                        
                        # Create cookie with correct domain
                        from http.cookies import SimpleCookie
                        cookie = SimpleCookie()
                        cookie["GZCTF_Token"] = token_value
                        cookie["GZCTF_Token"]["domain"] = domain
                        cookie["GZCTF_Token"]["path"] = "/"
                        self.session.cookie_jar.update_cookies(cookie)
                        logger.debug(f"Added GZCTF_Token cookie to session for domain: {domain}")
                    elif 'token' in cookies:
                        token_value = cookies['token'].value
                        logger.debug("Found token in cookies")
                    else:
                        # Try to get from response headers
                        auth_header = response.headers.get('Authorization')
                        if auth_header and auth_header.startswith('Bearer '):
                            token_value = auth_header[7:]
                            logger.debug("Found token in Authorization header")
                        else:
                            # Thử tìm token trong response body nếu là JSON
                            try:
                                response_json = json.loads(response_text)
                                if isinstance(response_json, dict) and 'token' in response_json:
                                    token_value = response_json['token']
                                    logger.debug("Found token in response body")
                            except json.JSONDecodeError:
                                logger.debug("Response is not JSON format")
                    
                    if token_value:
                        self.auth_token = token_value
                        logger.info("Successfully authenticated with GZCTF")
                        return True
                    else:
                        logger.error("Authentication succeeded but no token found")
                        return False
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
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
            # Don't add token to header, use cookie instead
            # GZCTF_Token cookie will be sent automatically by the session
            logger.debug("Using GZCTF_Token cookie for authentication")
            
        return headers
    
    async def is_authenticated(self) -> bool:
        """Check if we are currently authenticated"""
        if not self.auth_token:
            return False
            
        try:
            base_url = self.config.base_url.rstrip('/')
            if self.session is None:
                cookie_jar = aiohttp.CookieJar(unsafe=True)
                if self.auth_token:
                    # Add GZCTF_Token cookie to cookie jar
                    from urllib.parse import urlparse
                    parsed_url = urlparse(base_url)
                    domain = parsed_url.netloc
                    
                    from http.cookies import SimpleCookie
                    cookie = SimpleCookie()
                    cookie["GZCTF_Token"] = self.auth_token
                    cookie["GZCTF_Token"]["domain"] = domain
                    cookie["GZCTF_Token"]["path"] = "/"
                    cookie_jar.update_cookies(cookie)
                    logger.debug(f"Added GZCTF_Token cookie to new session for domain: {domain}")
                self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)
                logger.debug("Created new session with auth cookie")
                
            async with self.session.get(
                f"{base_url}/api/games",
                headers=self._get_headers()
            ) as response:
                logger.debug(f"Authentication check status: {response.status}")
                if response.status == 401:
                    logger.debug("Authentication check failed with 401")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return False
    
    async def get_game_notices(self, game_id: int, count: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Get game notices from GZCTF API, sorted by timestamp in descending order"""
        try:
            # Ensure base_url doesn't end with slash to avoid double slashes
            base_url = self.config.base_url.rstrip('/')
            url = f"{base_url}/api/game/{game_id}/notices"
            params = {"count": count, "skip": skip}
            
            if self.session is None:
                self.session = aiohttp.ClientSession()
                
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
                        # Sort data by timestamp in descending order, handle empty timestamps
                        def safe_timestamp_parse(item):
                            timestamp = item.get('timestamp', '')
                            if not timestamp:
                                return datetime.min
                            try:
                                return datetime.fromisoformat(timestamp)
                            except ValueError:
                                logger.warning(f"Invalid timestamp format: {timestamp}")
                                return datetime.min
                        
                        sorted_data = sorted(data, key=safe_timestamp_parse, reverse=True)
                        return sorted_data
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {json_error}")
                        logger.debug(f"Response content: {await response.text()}")
                        return []
                elif response.status == 401:
                    # Try to re-authenticate on 401 error
                    logger.warning("Received 401 error for notices, attempting to re-authenticate...")
                    if await self.authenticate():
                        logger.info("Re-authentication successful, retrying notices request...")
                        # Retry the request with new authentication
                        if self.session is None:
                            self.session = aiohttp.ClientSession()
                            
                        async with self.session.get(url, params=params, headers=self._get_headers()) as retry_response:
                            if retry_response.status == 200:
                                try:
                                    data = await retry_response.json()
                                    # Sort data by timestamp in descending order, handle empty timestamps
                                    def safe_timestamp_parse(item):
                                        timestamp = item.get('timestamp', '')
                                        if not timestamp:
                                            return datetime.min
                                        try:
                                            return datetime.fromisoformat(timestamp)
                                        except ValueError:
                                            logger.warning(f"Invalid timestamp format: {timestamp}")
                                            return datetime.min
                                    
                                    sorted_data = sorted(data, key=safe_timestamp_parse, reverse=True)
                                    return sorted_data
                                except Exception as json_error:
                                    logger.error(f"Failed to parse JSON response after retry: {json_error}")
                                    return []
                            else:
                                logger.error(f"Failed to get game notices after re-auth: {retry_response.status}")
                                logger.debug(f"Response content: {await retry_response.text()}")
                                return []
                    else:
                        logger.error("Re-authentication failed for notices")
                        return []
                else:
                    logger.error(f"Failed to get game notices: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching game notices: {e}")
            return []
    
    async def get_game_events(self, game_id: int, count: int = 100, skip: int = 0, hide_container: bool = False) -> List[Dict[str, Any]]:
        """Get game events from GZCTF API, sorted by timestamp in descending order"""
        try:
            base_url = self.config.base_url.rstrip('/')
            url = f"{base_url}/api/game/{game_id}/events"
            params = {
                "count": count, 
                "skip": skip,
                "hideContainer": str(hide_container).lower()  # Convert boolean to string
            }
            headers = self._get_headers()
            # Log in debug mode
            debug_enabled = False
            if hasattr(self.config, 'debug'):
                debug_enabled = getattr(self.config, 'debug', False)
                
            if debug_enabled:
                logger.debug(f"[DEBUG] Requesting events: {url} params={params} headers={headers}")
                
            if self.session is None:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(
                url, 
                params=params, 
                headers=headers
            ) as response:
                if debug_enabled:
                    logger.debug(f"[DEBUG] Game events response status: {response.status}")
                    logger.debug(f"[DEBUG] Game events response headers: {dict(response.headers)}")
                    text = await response.text()
                    logger.debug(f"[DEBUG] Game events response text: {text[:500]}")
                    # parse again if status is 200
                    if response.status == 200:
                        try:
                            data = json.loads(text)
                            # Sort data by timestamp in descending order, handle empty timestamps
                            def safe_timestamp_parse(item):
                                timestamp = item.get('timestamp', '')
                                if not timestamp:
                                    return datetime.min
                                try:
                                    return datetime.fromisoformat(timestamp)
                                except ValueError:
                                    logger.warning(f"Invalid timestamp format: {timestamp}")
                                    return datetime.min
                            
                            sorted_data = sorted(data, key=safe_timestamp_parse, reverse=True)
                            return sorted_data
                        except Exception as json_error:
                            logger.error(f"Failed to parse JSON response: {json_error}")
                            logger.debug(f"Response content: {text}")
                            return []
                    elif response.status == 401:
                        # Try to re-authenticate on 401 error
                        logger.warning("Received 401 error, attempting to re-authenticate...")
                        if await self.authenticate():
                            logger.info("Re-authentication successful, retrying request...")
                            # Retry the request with new authentication
                            headers = self._get_headers()
                            async with self.session.get(url, params=params, headers=headers) as retry_response:
                                if retry_response.status == 200:
                                    try:
                                        data = await retry_response.json()
                                        # Sort data by timestamp in descending order
                                        def safe_timestamp_parse(item):
                                            timestamp = item.get('timestamp', '')
                                            if not timestamp:
                                                return datetime.min
                                            try:
                                                return datetime.fromisoformat(timestamp)
                                            except ValueError:
                                                logger.warning(f"Invalid timestamp format: {timestamp}")
                                                return datetime.min
                                        
                                        sorted_data = sorted(data, key=safe_timestamp_parse, reverse=True)
                                        return sorted_data
                                    except Exception as json_error:
                                        logger.error(f"Failed to parse JSON response after retry: {json_error}")
                                        return []
                                else:
                                    logger.error(f"Failed to get game events after re-auth: {retry_response.status}")
                                    logger.debug(f"Response content: {await retry_response.text()}")
                                    return []
                        else:
                            logger.error("Re-authentication failed")
                            return []
                    else:
                        logger.error(f"Failed to get game events: {response.status}")
                        logger.debug(f"Response content: {text}")
                        return []
                else:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            # Sort data by timestamp in descending order
                            def safe_timestamp_parse(item):
                                timestamp = item.get('timestamp', '')
                                if not timestamp:
                                    return datetime.min
                                try:
                                    return datetime.fromisoformat(timestamp)
                                except ValueError:
                                    logger.warning(f"Invalid timestamp format: {timestamp}")
                                    return datetime.min
                            
                            sorted_data = sorted(data, key=safe_timestamp_parse, reverse=True)
                            return sorted_data
                        except Exception as json_error:
                            logger.error(f"Failed to parse JSON response: {json_error}")
                            logger.debug(f"Response content: {await response.text()}")
                            return []
                    elif response.status == 401:
                        # Try to re-authenticate on 401 error
                        logger.warning("Received 401 error, attempting to re-authenticate...")
                        if await self.authenticate():
                            logger.info("Re-authentication successful, retrying request...")
                            # Retry the request with new authentication
                            headers = self._get_headers()
                            async with self.session.get(url, params=params, headers=headers) as retry_response:
                                if retry_response.status == 200:
                                    try:
                                        data = await retry_response.json()
                                        # Sort data by timestamp in descending order
                                        def safe_timestamp_parse(item):
                                            timestamp = item.get('timestamp', '')
                                            if not timestamp:
                                                return datetime.min
                                            try:
                                                return datetime.fromisoformat(timestamp)
                                            except ValueError:
                                                logger.warning(f"Invalid timestamp format: {timestamp}")
                                                return datetime.min
                                        
                                        sorted_data = sorted(data, key=safe_timestamp_parse, reverse=True)
                                        return sorted_data
                                    except Exception as json_error:
                                        logger.error(f"Failed to parse JSON response after retry: {json_error}")
                                        return []
                                else:
                                    logger.error(f"Failed to get game events after re-auth: {retry_response.status}")
                                    logger.debug(f"Response content: {await retry_response.text()}")
                                    return []
                        else:
                            logger.error("Re-authentication failed")
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
            
            if self.session is None:
                self.session = aiohttp.ClientSession()
                
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
    
    async def get_game_info(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific game"""
        try:
            base_url = self.config.base_url.rstrip('/')
            url = f"{base_url}/api/game/{game_id}"
            
            if self.session is None:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(
                url, 
                headers=self._get_headers()
            ) as response:
                logger.debug(f"Game info response status: {response.status}")
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        logger.info(f"Successfully fetched game info for ID {game_id}: {data.get('title', 'Unknown')}")
                        return data
                    except Exception as json_error:
                        logger.error(f"Failed to parse game info JSON response: {json_error}")
                        logger.debug(f"Response content: {await response.text()}")
                        return None
                elif response.status == 401:
                    # Try to re-authenticate on 401 error
                    logger.warning("Received 401 error for game info, attempting to re-authenticate...")
                    if await self.authenticate():
                        logger.info("Re-authentication successful, retrying game info request...")
                        # Retry the request with new authentication
                        if self.session is None:
                            self.session = aiohttp.ClientSession()
                            
                        async with self.session.get(url, headers=self._get_headers()) as retry_response:
                            if retry_response.status == 200:
                                try:
                                    data = await retry_response.json()
                                    logger.info(f"Successfully fetched game info after re-auth for ID {game_id}: {data.get('title', 'Unknown')}")
                                    return data
                                except Exception as json_error:
                                    logger.error(f"Failed to parse game info JSON response after retry: {json_error}")
                                    return None
                            else:
                                logger.error(f"Failed to get game info after re-auth: {retry_response.status}")
                                logger.debug(f"Response content: {await retry_response.text()}")
                                return None
                    else:
                        logger.error("Re-authentication failed for game info")
                        return None
                else:
                    logger.error(f"Failed to get game info: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching game info for ID {game_id}: {e}")
            return None
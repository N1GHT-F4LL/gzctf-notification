import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
from urllib.parse import urlparse
from http.cookies import SimpleCookie

from config import GZCTFConfig

logger = logging.getLogger(__name__)


class GZCTFClient:
    """GZCTF API Client for fetching notifications and events"""

    def __init__(self, config: GZCTFConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self._auth_lock = asyncio.Lock()
        # Set to True if server returns 403 for events (insufficient privileges)
        self.events_forbidden: bool = False

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure there is an open aiohttp ClientSession with a permissive CookieJar."""
        connector_closed = False
        if self.session is not None:
            try:
                connector = getattr(self.session, "connector", None)
                connector_closed = connector is None or getattr(connector, "closed", False)
            except Exception:
                connector_closed = True
        if self.session is None or self.session.closed or connector_closed:
            # Close any lingering session just in case
            if self.session is not None:
                try:
                    await self.session.close()
                except Exception:
                    pass
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            self.session = aiohttp.ClientSession(cookie_jar=cookie_jar)
        return self.session

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def authenticate(self) -> bool:
        """Authenticate with GZCTF API using username/password"""
        if not (self.config.username and self.config.password):
            logger.error("Username and password are required for authentication")
            return False

        try:
            async with self._auth_lock:
                login_data = {
                    "userName": self.config.username,
                    "password": self.config.password,
                }

                # Ensure base_url doesn't end with slash to avoid double slashes
                base_url = self.config.base_url.rstrip("/")

                # Ensure we have a session (do not close an existing one to avoid racing other tasks)
                session = await self._ensure_session()

                async with session.post(
                    f"{base_url}/api/account/login", json=login_data
                ) as response:
                    if response.status == 200:
                        # Detailed response logging
                        logger.debug(f"Authentication response status: {response.status}")
                        logger.debug(f"Authentication response headers: {dict(response.headers)}")

                        # Log cookie information
                        logger.debug(
                            f"Cookies: {[f'{c.key}={c.value}' for c in response.cookies.values()]}"
                        )

                        # Read response body
                        response_text = await response.text()
                        logger.debug(f"Response body (first 200 chars): {response_text[:200]}")

                        # Extract token from response headers or cookies
                        cookies = response.cookies
                        token_value = None

                        # Only check for 'GZCTF_Token' cookie (based on logs)
                        if "GZCTF_Token" in cookies:
                            token_value = cookies["GZCTF_Token"].value
                            logger.debug("Found GZCTF_Token cookie")
                            # Save cookie to session
                            session = await self._ensure_session()
                            self._set_auth_cookie(session, base_url)
                        elif "token" in cookies:
                            token_value = cookies["token"].value
                            logger.debug("Found token in cookies")
                        else:
                            # Try to get from response headers
                            auth_header = response.headers.get("Authorization")
                            if auth_header and auth_header.startswith("Bearer "):
                                token_value = auth_header[7:]
                                logger.debug("Found token in Authorization header")
                            else:
                                # Try to find token in JSON response body
                                try:
                                    response_json = json.loads(response_text)
                                    if isinstance(response_json, dict) and "token" in response_json:
                                        token_value = response_json["token"]
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
            "Accept": "application/json",
        }

        if self.auth_token:
            # Don't add token to header, use cookie instead
            # GZCTF_Token cookie will be sent automatically by the session
            logger.debug("Using GZCTF_Token cookie for authentication")

        return headers

    def _safe_timestamp_parse(self, item: Dict[str, Any]) -> datetime:
        """Safely parse timestamp from item, return datetime.min if invalid"""
        timestamp = item.get("timestamp", "")
        if not timestamp:
            return datetime.min
        try:
            return datetime.fromisoformat(timestamp)
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return datetime.min

    def _sort_by_timestamp(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort data by timestamp in descending order"""
        return sorted(data, key=self._safe_timestamp_parse, reverse=True)

    def _set_auth_cookie(self, session: aiohttp.ClientSession, base_url: str) -> None:
        """Set authentication cookie on session"""
        if not self.auth_token:
            return
            
        domain = urlparse(base_url).netloc
        cookie = SimpleCookie()
        cookie["GZCTF_Token"] = self.auth_token
        cookie["GZCTF_Token"]["domain"] = domain
        cookie["GZCTF_Token"]["path"] = "/"
        session.cookie_jar.update_cookies(cookie)
        logger.debug(f"Set GZCTF_Token cookie on session for domain: {domain}")

    async def _make_authenticated_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> Optional[aiohttp.ClientResponse]:
        """Make an authenticated request with automatic retry on 401"""
        session = await self._ensure_session()
        base_url = self.config.base_url.rstrip("/")
        self._set_auth_cookie(session, base_url)
        
        # First attempt
        response = await getattr(session, method.lower())(url, headers=self._get_headers(), **kwargs)
        
        if response.status == 401:
            logger.warning("Received 401 error, attempting to re-authenticate...")
            await response.close()  # Close the first response
            
            if await self.authenticate():
                logger.info("Re-authentication successful, retrying request...")
                session = await self._ensure_session()
                self._set_auth_cookie(session, base_url)
                response = await getattr(session, method.lower())(url, headers=self._get_headers(), **kwargs)
                return response
            else:
                logger.error("Re-authentication failed")
                return None
        
        return response

    async def is_authenticated(self) -> bool:
        """Check if we are currently authenticated"""
        if not self.auth_token:
            return False

        base_url = self.config.base_url.rstrip("/")

        async def _check_once() -> bool:
            # Ensure a valid session and cookie are present and perform check under the lock
            async with self._auth_lock:
                session = await self._ensure_session()
                self._set_auth_cookie(session, base_url)

                async with session.get(
                    f"{base_url}/api/game", headers=self._get_headers()
                ) as response:
                    logger.debug(f"Authentication check status: {response.status}")
                    if response.status == 401:
                        logger.debug("Authentication check failed with 401")
                        return False
                    return True

        try:
            return await _check_once()
        except Exception as e:
            # Retry once on transient session/SSL close errors
            msg = str(e)
            if "Session is closed" in msg or "APPLICATION_DATA_AFTER_CLOSE_NOTIFY" in msg:
                try:
                    async with self._auth_lock:
                        # Recreate session and retry
                        if self.session is not None:
                            try:
                                await self.session.close()
                            except Exception:
                                pass
                            self.session = None
                    return await _check_once()
                except Exception as e2:
                    logger.error(f"Error checking authentication (after retry): {e2}")
                    return False
            logger.error(f"Error checking authentication: {e}")
            return False

    async def get_game_notices(
        self, game_id: int, count: int = 100, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get game notices from GZCTF API, sorted by timestamp in descending order"""
        try:
            base_url = self.config.base_url.rstrip("/")
            url = f"{base_url}/api/game/{game_id}/notices"
            params = {"count": count, "skip": skip}

            response = await self._make_authenticated_request("GET", url, params=params)
            if response is None:
                return []

            async with response:
                logger.debug(f"Game notices response status: {response.status}")
                logger.debug(f"Game notices response headers: {response.headers}")

                if response.status == 200:
                    try:
                        data = await response.json()
                        return self._sort_by_timestamp(data)
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

    async def get_game_events(
        self,
        game_id: int,
        count: int = 100,
        skip: int = 0,
        hide_container: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get game events from GZCTF API, sorted by timestamp in descending order"""
        try:
            base_url = self.config.base_url.rstrip("/")
            url = f"{base_url}/api/game/{game_id}/events"
            params = {
                "count": count,
                "skip": skip,
                "hideContainer": str(hide_container).lower(),
            }

            # Debug logging if enabled
            debug_enabled = getattr(self.config, "debug", False)
            if debug_enabled:
                logger.debug(f"[DEBUG] Requesting events: {url} params={params}")

            response = await self._make_authenticated_request("GET", url, params=params)
            if response is None:
                return []

            async with response:
                if debug_enabled:
                    logger.debug(f"[DEBUG] Game events response status: {response.status}")
                    logger.debug(f"[DEBUG] Game events response headers: {dict(response.headers)}")
                    text = await response.text()
                    logger.debug(f"[DEBUG] Game events response text: {text[:500]}")

                if response.status == 200:
                    try:
                        data = await response.json()
                        return self._sort_by_timestamp(data)
                    except Exception as json_error:
                        logger.error(f"Failed to parse JSON response: {json_error}")
                        logger.debug(f"Response content: {await response.text()}")
                        return []
                elif response.status == 403:
                    # Insufficient privileges for events; don't keep retrying
                    self.events_forbidden = True
                    logger.error("Events endpoint returned 403 Forbidden - disabling further event polling")
                    return []
                else:
                    logger.error(f"Failed to get game events: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching game events: {e}")
            return []

    async def get_game(self) -> List[Dict[str, Any]]:
        """Get list of available games"""
        try:
            base_url = self.config.base_url.rstrip("/")
            url = f"{base_url}/api/game"

            response = await self._make_authenticated_request("GET", url)
            if response is None:
                return []

            async with response:
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
            base_url = self.config.base_url.rstrip("/")
            url = f"{base_url}/api/game/{game_id}"

            response = await self._make_authenticated_request("GET", url)
            if response is None:
                return None

            async with response:
                logger.debug(f"Game info response status: {response.status}")

                if response.status == 200:
                    try:
                        data = await response.json()
                        logger.info(
                            f"Successfully fetched game info for ID {game_id}: {data.get('title', 'Unknown')}"
                        )
                        return data
                    except Exception as json_error:
                        logger.error(f"Failed to parse game info JSON response: {json_error}")
                        logger.debug(f"Response content: {await response.text()}")
                        return None
                else:
                    logger.error(f"Failed to get game info: {response.status}")
                    logger.debug(f"Response content: {await response.text()}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching game info for ID {game_id}: {e}")
            return None
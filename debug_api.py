#!/usr/bin/env python3
"""
Debug script to test GZCTF API endpoints
"""

import asyncio
import aiohttp
import json
from dotenv import load_dotenv
from config import load_config

# Load environment variables
load_dotenv()

async def debug_api():
    """Debug GZCTF API endpoints"""
    config = load_config()
    
    print("🔍 GZCTF API Debug Tool")
    print("=" * 50)
    
    # Test basic connectivity
    print(f"Testing connection to: {config.gzctf.base_url}")
    
    async with aiohttp.ClientSession() as session:
        # Test basic connectivity
        try:
            async with session.get(config.gzctf.base_url) as response:
                print(f"✅ Base URL accessible: {response.status}")
                print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        except Exception as e:
            print(f"❌ Base URL not accessible: {e}")
            return
        
        # Test authentication
        print(f"\n🔐 Testing authentication...")
        
        if config.gzctf.api_token:
            print("Using API token authentication")
            headers = {"Authorization": f"Bearer {config.gzctf.api_token}"}
        elif config.gzctf.username and config.gzctf.password:
            print("Using username/password authentication")
            login_data = {
                "userName": config.gzctf.username,
                "password": config.gzctf.password
            }
            
            try:
                base_url = config.gzctf.base_url.rstrip('/')
                async with session.post(
                    f"{base_url}/api/account/login",
                    json=login_data
                ) as response:
                    print(f"Login response: {response.status}")
                    print(f"Login headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        # Try to get token from cookies or headers
                        cookies = response.cookies
                        auth_header = response.headers.get('Authorization')
                        
                        if 'token' in cookies:
                            token = cookies['token'].value
                            print(f"✅ Got token from cookies: {token[:10]}...")
                            headers = {"Authorization": f"Bearer {token}"}
                        elif auth_header and auth_header.startswith('Bearer '):
                            token = auth_header[7:]
                            print(f"✅ Got token from headers: {token[:10]}...")
                            headers = {"Authorization": f"Bearer {token}"}
                        else:
                            print("⚠️  No token found in response")
                            headers = {}
                    else:
                        print(f"❌ Login failed: {response.status}")
                        response_text = await response.text()
                        print(f"Response: {response_text}")
                        headers = {}
            except Exception as e:
                print(f"❌ Login error: {e}")
                headers = {}
        else:
            print("❌ No authentication method configured")
            headers = {}
        
        # Test API endpoints
        base_url = config.gzctf.base_url.rstrip('/')
        
        endpoints = [
            "/api/games",
            f"/api/game/{config.game_id}/notices",
            f"/api/game/{config.game_id}/events"
        ]
        
        for endpoint in endpoints:
            print(f"\n🔗 Testing endpoint: {endpoint}")
            try:
                url = f"{base_url}{endpoint}"
                params = {}
                
                # Add specific parameters for events endpoint
                if "events" in endpoint:
                    params = {"count": 5, "skip": 0, "hideContainer": "false"}
                elif "notices" in endpoint:
                    params = {"count": 5, "skip": 0}
                
                async with session.get(url, params=params, headers=headers) as response:
                    print(f"   Status: {response.status}")
                    print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print(f"   URL: {response.url}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            print(f"   ✅ JSON response: {len(data) if isinstance(data, list) else 'object'}")
                            if isinstance(data, list) and len(data) > 0:
                                print(f"   Sample data: {json.dumps(data[0], indent=2)[:200]}...")
                        except Exception as json_error:
                            text = await response.text()
                            print(f"   ❌ JSON parse error: {json_error}")
                            print(f"   Response text: {text[:500]}...")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error response: {text[:500]}...")
                        
            except Exception as e:
                print(f"   ❌ Request error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api()) 
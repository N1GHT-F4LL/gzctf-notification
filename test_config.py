#!/usr/bin/env python3
"""
Test script to verify GZCTF Discord Notification Bot configuration
"""

import asyncio
import logging
import sys
from dotenv import load_dotenv

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

async def test_gzctf_connection():
    """Test GZCTF API connection and authentication"""
    try:
        config = load_config()
        
        print("🔧 Testing GZCTF Configuration...")
        print(f"   Base URL: {config.gzctf.base_url}")
        print(f"   API Token: {'✅ Set' if config.gzctf.api_token else '❌ Not set'}")
        print(f"   Username: {'✅ Set' if config.gzctf.username else '❌ Not set'}")
        print(f"   Password: {'✅ Set' if config.gzctf.password else '❌ Not set'}")
        
        if not any([config.gzctf.api_token, config.gzctf.username]):
            print("❌ Error: No authentication method configured")
            return False
        
        print("\n🔐 Testing GZCTF Authentication...")
        async with GZCTFClient(config.gzctf) as client:
            if await client.authenticate():
                print("✅ Authentication successful!")
                
                print("\n🎮 Testing Games API...")
                games = await client.get_games()
                if games:
                    print(f"✅ Found {len(games)} games:")
                    for game in games[:5]:  # Show first 5 games
                        game_id = game.get('id', 'Unknown')
                        title = game.get('title', 'Unknown Title')
                        status = game.get('status', 'Unknown')
                        print(f"   - Game {game_id}: {title} ({status})")
                else:
                    print("⚠️  No games found or API error")
                
                if config.game_id:
                    print(f"\n📊 Testing Game {config.game_id} Notices...")
                    notices = await client.get_game_notices(config.game_id, count=5)
                    print(f"✅ Found {len(notices)} recent notices")
                    
                    print(f"\n📊 Testing Game {config.game_id} Events...")
                    events = await client.get_game_events(config.game_id, count=5)
                    print(f"✅ Found {len(events)} recent events")
                else:
                    print("⚠️  No game ID configured for testing")
                
                return True
            else:
                print("❌ Authentication failed")
                return False
                
    except Exception as e:
        print(f"❌ Error testing GZCTF connection: {e}")
        return False

async def test_discord_config():
    """Test Discord configuration"""
    try:
        config = load_config()
        
        print("\n🤖 Testing Discord Configuration...")
        print(f"   Token: {'✅ Set' if config.discord.token else '❌ Not set'}")
        print(f"   Channel ID: {'✅ Set' if config.discord.channel_id else '❌ Not set'}")
        print(f"   Guild ID: {'✅ Set' if config.discord.guild_id else '❌ Not set'}")
        
        if not config.discord.token:
            print("❌ Error: Discord token not configured")
            return False
            
        if not config.discord.channel_id:
            print("❌ Error: Discord channel ID not configured")
            return False
        
        print("✅ Discord configuration looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Discord config: {e}")
        return False

async def test_bot_config():
    """Test bot configuration"""
    try:
        config = load_config()
        
        print("\n⚙️  Testing Bot Configuration...")
        print(f"   Game ID: {'✅ Set' if config.game_id else '❌ Not set'}")
        print(f"   Poll Interval: {config.poll_interval}s")
        print(f"   Enable Notices: {config.enable_notices}")
        print(f"   Enable Events: {config.enable_events}")
        
        if not config.game_id:
            print("❌ Error: Game ID not configured")
            return False
        
        print("✅ Bot configuration looks good!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing bot config: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 GZCTF Discord Notification Bot - Configuration Test")
    print("=" * 60)
    
    # Test configurations
    gzctf_ok = await test_gzctf_connection()
    discord_ok = await test_discord_config()
    bot_ok = await test_bot_config()
    
    print("\n" + "=" * 60)
    print("📋 Test Results:")
    print(f"   GZCTF Connection: {'✅ PASS' if gzctf_ok else '❌ FAIL'}")
    print(f"   Discord Config: {'✅ PASS' if discord_ok else '❌ FAIL'}")
    print(f"   Bot Config: {'✅ PASS' if bot_ok else '❌ FAIL'}")
    
    if all([gzctf_ok, discord_ok, bot_ok]):
        print("\n🎉 All tests passed! Your configuration is ready.")
        print("   You can now run: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        print("   Review the errors above and update your .env file.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
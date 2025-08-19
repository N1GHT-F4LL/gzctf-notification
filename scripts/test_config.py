#!/usr/bin/env python3
"""
Test configuration loading
"""

import sys
import os
from dotenv import load_dotenv

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

from bot.config import load_config

# Load environment variables
load_dotenv()

def test_config():
    """Test configuration loading"""
    config = load_config()
    
    print("=== Configuration Test ===")
    print(f"GZCTF Base URL: {config.gzctf.base_url}")
    print(f"Game ID: {config.game_id}")
    print(f"Poll Interval: {config.poll_interval}")
    print(f"Enable Notices: {config.enable_notices}")
    print(f"Enable Events: {config.enable_events}")
    print(f"Debug Mode: {config.debug}")
    
    print("\n=== Environment Variables ===")
    print(f"ENABLE_NOTICES: {os.getenv('ENABLE_NOTICES')}")
    print(f"ENABLE_EVENTS: {os.getenv('ENABLE_EVENTS')}")
    print(f"DEBUG: {os.getenv('DEBUG')}")

if __name__ == "__main__":
    test_config()
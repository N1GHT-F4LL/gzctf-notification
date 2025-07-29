#!/usr/bin/env python3
"""
Clear bot state file to reset configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clear_state():
    """Clear bot state file"""
    game_id = os.getenv("GAME_ID", "7")
    state_file = f"bot_state_game_{game_id}.json"
    
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"Removed state file: {state_file}")
    else:
        print(f"State file not found: {state_file}")
    
    print("State cleared. Bot will start fresh on next run.")

if __name__ == "__main__":
    clear_state()
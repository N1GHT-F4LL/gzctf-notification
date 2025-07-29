#!/usr/bin/env python3
"""
Test event formatting
"""

import sys
import os
from datetime import datetime

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bot'))

from notification_formatter import NotificationFormatter

def test_formatting():
    """Test event formatting with sample data"""
    formatter = NotificationFormatter()
    
    # Sample events from your data
    sample_events = [
        {
            "time": 1753793984876,
            "user": "dr4kali",
            "team": "JG DiFF",
            "type": "ContainerStart",
            "values": ["97", "Access The Portal"]
        },
        {
            "time": 1753792623447,
            "user": "MR.Enzo",
            "team": "CØDE BREAKERS",
            "type": "FlagSubmit",
            "values": ["WrongAnswer", "K4P{trap_and_lfsr_and_brute_and_crypto_zen_master}", "SIGNAL ECHO", "95"]
        },
        {
            "time": 1753787813253,
            "user": "Alpha999",
            "team": "TEAM ALPHA",
            "type": "FlagSubmit",
            "values": ["Accepted", "K4P{Ph4n70m_4liv3_N3xt_0p_4t_M1dn1ght_9e7c55c0b14f}", "Access The Portal", "97"]
        },
        {
            "time": 1753787815407,
            "user": "Alpha999",
            "team": "TEAM ALPHA",
            "type": "ContainerDestroy",
            "values": ["97", "Access The Portal"]
        }
    ]
    
    print("=== Event Formatting Test ===\n")
    
    for i, event in enumerate(sample_events, 1):
        print(f"--- Event {i}: {event['type']} ---")
        embed = formatter.format_event(event)
        
        if embed:
            print(f"Title: {embed.title}")
            print(f"Description: {embed.description}")
            print(f"Color: #{embed.color.value:06x}")
            print(f"Timestamp: {embed.timestamp}")
            
            if embed.fields:
                print("Fields:")
                for field in embed.fields:
                    print(f"  {field.name}: {field.value}")
            
            if embed.footer:
                print(f"Footer: {embed.footer.text}")
        else:
            print("❌ Failed to format event")
        
        print()

if __name__ == "__main__":
    test_formatting()
#!/usr/bin/env python3
"""
Generate Discord bot invite link with proper permissions
"""

import os
from dotenv import load_dotenv

load_dotenv()

def generate_invite_link():
    """Generate Discord bot invite link"""
    
    # Get bot client ID from Discord Developer Portal
    # This is the Application ID, not the bot token
    client_id = input("Enter your Discord Application ID (Client ID): ").strip()
    
    if not client_id:
        print("Client ID is required")
        return
    
    # Required permissions for the bot
    permissions = [
        "Send Messages",           # 2048
        "Embed Links",            # 16384  
        "Read Message History",   # 65536
        "View Channel",           # 1024
        "Manage Channels",        # 16 (for auto-creating channels)
        "Use External Emojis",    # 262144
        "Manage Roles",           # 268435456 (for setting channel permissions)
    ]
    
    # Calculate permission integer
    # Send Messages (2048) + Embed Links (16384) + Read Message History (65536) + 
    # View Channel (1024) + Manage Channels (16) + Use External Emojis (262144) + Manage Roles (268435456) = 268782608
    permission_int = 268782608
    
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={permission_int}&scope=bot%20applications.commands"
    
    print("\n" + "="*60)
    print("DISCORD BOT INVITE LINK")
    print("="*60)
    print(f"Client ID: {client_id}")
    print(f"Permissions: {', '.join(permissions)}")
    print(f"Permission Integer: {permission_int}")
    print("\nInvite Link:")
    print(invite_url)
    print("\n" + "="*60)
    print("Instructions:")
    print("1. Copy the invite link above")
    print("2. Paste it in your browser")
    print("3. Select your Discord server")
    print("4. Make sure all permissions are checked")
    print("5. Click 'Authorize'")
    print("6. After inviting, use !check_permissions to verify")
    print("7. Use !setup_event_channel to create private event channel")
    print("="*60)

if __name__ == "__main__":
    generate_invite_link()
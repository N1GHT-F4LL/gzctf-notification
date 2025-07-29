#!/usr/bin/env python3
"""
Check Discord bot permissions
"""

import asyncio
import discord
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def check_permissions():
    """Check Discord bot permissions"""
    
    token = os.getenv("DISCORD_TOKEN")
    guild_id = int(os.getenv("DISCORD_GUILD_ID")) if os.getenv("DISCORD_GUILD_ID") else None
    
    if not token:
        logger.error("No Discord token found")
        return
    
    if not guild_id:
        logger.error("No Discord guild ID found")
        return
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        logger.info(f"Bot logged in as {client.user}")
        
        guild = client.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild with ID {guild_id} not found")
            await client.close()
            return
        
        logger.info(f"Guild: {guild.name} (ID: {guild.id})")
        
        # Check bot member
        bot_member = guild.get_member(client.user.id)
        if not bot_member:
            logger.error("Bot is not a member of the guild")
            await client.close()
            return
        
        logger.info(f"Bot member: {bot_member.display_name}")
        logger.info(f"Bot roles: {[role.name for role in bot_member.roles]}")
        
        # Check permissions
        permissions = bot_member.guild_permissions
        logger.info("Bot permissions:")
        logger.info(f"  Send Messages: {permissions.send_messages}")
        logger.info(f"  Embed Links: {permissions.embed_links}")
        logger.info(f"  Read Message History: {permissions.read_message_history}")
        logger.info(f"  View Channels: {permissions.view_channel}")
        logger.info(f"  Manage Channels: {permissions.manage_channels}")
        
        # Check specific channels
        notification_channel_name = os.getenv("NOTIFICATION_CHANNEL_NAME", "notification")
        event_channel_name = os.getenv("EVENT_CHANNEL_NAME", "event")
        
        notification_channel = discord.utils.get(guild.text_channels, name=notification_channel_name)
        event_channel = discord.utils.get(guild.text_channels, name=event_channel_name)
        
        if notification_channel:
            logger.info(f"Notification channel found: #{notification_channel.name} (ID: {notification_channel.id})")
            perms = notification_channel.permissions_for(bot_member)
            logger.info(f"  Can send messages: {perms.send_messages}")
            logger.info(f"  Can embed links: {perms.embed_links}")
        else:
            logger.warning(f"Notification channel '{notification_channel_name}' not found")
        
        if event_channel:
            logger.info(f"Event channel found: #{event_channel.name} (ID: {event_channel.id})")
            perms = event_channel.permissions_for(bot_member)
            logger.info(f"  Can send messages: {perms.send_messages}")
            logger.info(f"  Can embed links: {perms.embed_links}")
        else:
            logger.warning(f"Event channel '{event_channel_name}' not found")
        
        await client.close()
    
    try:
        await client.start(token)
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_permissions())
#!/usr/bin/env python3
"""
Test private channel creation and permissions
"""

import discord
import asyncio
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

async def test_private_channel():
    """Test private channel permissions"""
    
    token = os.getenv("DISCORD_TOKEN")
    guild_id = int(os.getenv("DISCORD_GUILD_ID")) if os.getenv("DISCORD_GUILD_ID") else None
    
    if not token or not guild_id:
        logger.error("Discord token and guild ID are required")
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
        
        logger.info(f"Guild: {guild.name}")
        
        # Check for existing event channel
        event_channel_name = os.getenv("EVENT_CHANNEL_NAME", "event")
        event_channel = discord.utils.get(guild.text_channels, name=event_channel_name)
        
        if event_channel:
            logger.info(f"Found existing event channel: #{event_channel.name}")
            
            # Check permissions
            logger.info("Channel permissions:")
            for target, overwrite in event_channel.overwrites.items():
                if isinstance(target, discord.Role):
                    logger.info(f"  Role {target.name}: view_channel={overwrite.view_channel}")
                elif isinstance(target, discord.Member):
                    logger.info(f"  User {target.display_name}: view_channel={overwrite.view_channel}")
            
            # Check if @everyone can see the channel
            everyone_overwrite = event_channel.overwrites.get(guild.default_role)
            if everyone_overwrite and everyone_overwrite.view_channel is False:
                logger.info("✅ Channel is properly private (@everyone cannot view)")
            else:
                logger.warning("⚠️ Channel may not be private (@everyone can view)")
            
            # Check bot permissions
            bot_member = guild.get_member(client.user.id)
            bot_permissions = event_channel.permissions_for(bot_member)
            
            logger.info("Bot permissions in event channel:")
            logger.info(f"  View Channel: {bot_permissions.view_channel}")
            logger.info(f"  Send Messages: {bot_permissions.send_messages}")
            logger.info(f"  Embed Links: {bot_permissions.embed_links}")
            
        else:
            logger.info(f"Event channel '{event_channel_name}' not found")
        
        await client.close()
    
    try:
        await client.start(token)
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_private_channel())
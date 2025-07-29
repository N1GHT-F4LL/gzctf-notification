import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

from config import DiscordConfig, BotConfig
from gzctf_client import GZCTFClient
from notification_formatter import NotificationFormatter

logger = logging.getLogger(__name__)

class GZCTFNotificationBot(commands.Bot):
    """Discord bot for GZCTF notifications"""
    
    def __init__(self, config: BotConfig, gzctf_client: GZCTFClient):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix="!", intents=intents)
        
        # Add slash command support
        # Use the built-in command tree from discord.py
        
        self.config = config
        self.discord_config = config.discord
        self.gzctf_client = gzctf_client
        self.game_id = config.game_id
        self.poll_interval = config.poll_interval
        self.enable_notices = config.enable_notices
        self.enable_events = config.enable_events
        
        # State file for persistent storage
        self.state_file = f"bot_state_game_{self.game_id}.json"
        
        # Load previous state or initialize
        self.last_notice_id = None
        self.last_event_time = None
        self.load_state()
        
        # Notification formatter with config
        self.formatter = NotificationFormatter(config)
        
        # Start polling task
        self.poll_notifications.start()
        
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        logger.info("Bot setup complete")
        

        
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot logged in as {self.user}")
        logger.info(f"Monitoring game ID: {self.game_id}")
        logger.info(f"Channel ID: {self.discord_config.channel_id}")
        logger.info(f"Notices enabled: {self.enable_notices}")
        logger.info(f"Events enabled: {self.enable_events}")
        
        # Set bot status
        status_text = f"GZCTF Game {self.game_id}"
        if not self.enable_events:
            status_text += " (Notices Only)"
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=status_text
            )
        )
    
    @tasks.loop(seconds=30)
    async def poll_notifications(self):
        """Poll for new notifications from GZCTF"""
        try:
            # Get new notices if enabled
            if self.enable_notices:
                notices = await self.gzctf_client.get_game_notices(self.game_id, count=10)
                if notices:
                    await self.process_notices(notices)
            
            # Get new events if enabled
            if self.enable_events:
                events = await self.gzctf_client.get_game_events(self.game_id, count=10)
                if events:
                    await self.process_events(events)
                
        except Exception as e:
            logger.error(f"Error polling notifications: {e}")
    
    @poll_notifications.before_loop
    async def before_poll_notifications(self):
        """Wait until bot is ready before starting polling"""
        await self.wait_until_ready()
    
    async def process_notices(self, notices: List[Dict[str, Any]]):
        """Process and send new notices to Discord"""
        if not notices:
            return
            
        # Sort by ID to ensure we process in order
        notices.sort(key=lambda x: x.get('id', 0))
        
        for notice in notices:
            notice_id = notice.get('id')
            
            # Skip if we've already seen this notice
            if self.last_notice_id and notice_id <= self.last_notice_id:
                continue
                
            # Update last seen ID
            if not self.last_notice_id or notice_id > self.last_notice_id:
                self.last_notice_id = notice_id
                # Save state after updating
                self.save_state()
            
            # Format and send notice
            embed = self.formatter.format_notice(notice)
            if embed:
                await self.send_notification(embed)
    
    async def process_events(self, events: List[Dict[str, Any]]):
        """Process and send new events to Discord"""
        if not events:
            return
            
        # Sort by time to ensure we process in order
        events.sort(key=lambda x: x.get('time', 0))
        
        for event in events:
            event_time = event.get('time', 0)
            
            # Skip if we've already seen this event
            if self.last_event_time and event_time <= self.last_event_time:
                continue
                
            # Update last seen time
            if not self.last_event_time or event_time > self.last_event_time:
                self.last_event_time = event_time
                # Save state after updating
                self.save_state()
            
            # Format and send event
            embed = self.formatter.format_event(event)
            if embed:
                await self.send_notification(embed)
    
    async def send_notification(self, embed: discord.Embed):
        """Send notification embed to Discord channel"""
        try:
            channel = self.get_channel(self.discord_config.channel_id)
            if channel:
                await channel.send(embed=embed)
                logger.info(f"Sent notification: {embed.title}")
            else:
                logger.error(f"Could not find channel {self.discord_config.channel_id}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def load_state(self):
        """Load bot state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_notice_id = state.get('last_notice_id')
                    self.last_event_time = state.get('last_event_time')
                    logger.info(f"Loaded state: last_notice_id={self.last_notice_id}, last_event_time={self.last_event_time}")
            else:
                logger.info("No previous state found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.last_notice_id = None
            self.last_event_time = None
            
    def save_state(self):
        """Save bot state to file"""
        try:
            state = {
                'last_notice_id': self.last_notice_id,
                'last_event_time': self.last_event_time,
                'game_id': self.game_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}") 
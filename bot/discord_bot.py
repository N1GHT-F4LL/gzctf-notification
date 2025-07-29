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
        self.events_failure_count = 0
        self.events_disabled_due_to_auth = False
        self.load_state()
        
        # Notification formatter with config
        self.formatter = NotificationFormatter(config)
        
        # Start polling task
        self.poll_notifications.change_interval(seconds=self.poll_interval)
        self.poll_notifications.start()
        
    @commands.command(name='reset_events')
    async def reset_events(self, ctx):
        """Reset events failure count and re-enable events"""
        if ctx.author.guild_permissions.administrator:
            self.events_failure_count = 0
            self.events_disabled_due_to_auth = False
            self.save_state()
            await ctx.send("✅ Events failure count reset. Events re-enabled.")
            logger.info("Events manually reset by administrator")
        else:
            await ctx.send("❌ Only administrators can use this command.")
    
    @commands.command(name='bot_status')
    async def bot_status(self, ctx):
        """Show bot status"""
        status_lines = [
            f"🎮 **Game ID:** {self.game_id}",
            f"📢 **Notices:** {'✅ Enabled' if self.enable_notices else '❌ Disabled'}",
            f"📅 **Events:** {'✅ Enabled' if self.enable_events and not self.events_disabled_due_to_auth else '❌ Disabled'}",
            f"🔄 **Poll Interval:** {self.poll_interval}s",
            f"📊 **Last Notice ID:** {self.last_notice_id or 'None'}",
            f"⏰ **Last Event Time:** {self.last_event_time or 'None'}",
        ]
        
        if self.events_disabled_due_to_auth:
            status_lines.append(f"⚠️ **Events disabled due to auth issues** (failures: {self.events_failure_count})")
        
        embed = discord.Embed(
            title="🤖 Bot Status",
            description="\n".join(status_lines),
            color=0x00ff00 if not self.events_disabled_due_to_auth else 0xffaa00
        )
        
        await ctx.send(embed=embed)
        
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        logger.info("Bot setup complete")
        

        
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot logged in as {self.user}")
        logger.info(f"Monitoring game ID: {self.game_id}")
        logger.info(f"Notices enabled: {self.enable_notices}")
        logger.info(f"Events enabled: {self.enable_events}")
        logger.info(f"Events disabled due to auth: {self.events_disabled_due_to_auth}")

        guild = self.get_guild(self.discord_config.guild_id) if self.discord_config.guild_id else None
        if not guild:
            logger.error("Guild not found or GUILD_ID not set.")
            return

        # Lấy tên kênh từ biến môi trường hoặc mặc định
        notification_channel_name = os.getenv("NOTIFICATION_CHANNEL_NAME", "notification")
        event_channel_name = os.getenv("EVENT_CHANNEL_NAME", "event")

        # Tạo hoặc lấy kênh notification
        notification_channel = discord.utils.get(guild.text_channels, name=notification_channel_name)
        if not notification_channel:
            notification_channel = await guild.create_text_channel(notification_channel_name)
            logger.info(f"Created notification channel: {notification_channel.name}")
        self.notification_channel_id = notification_channel.id

        # Tạo hoặc lấy kênh event
        event_channel = discord.utils.get(guild.text_channels, name=event_channel_name)
        if not event_channel:
            event_channel = await guild.create_text_channel(event_channel_name)
            logger.info(f"Created event channel: {event_channel.name}")
        self.event_channel_id = event_channel.id

        # Set bot status
        status_text = f"GZCTF Game {self.game_id}"
        if not self.enable_events or self.events_disabled_due_to_auth:
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
            # Check if we're still authenticated
            if not await self.gzctf_client.is_authenticated():
                logger.warning("Authentication lost, attempting to re-authenticate...")
                if not await self.gzctf_client.authenticate():
                    logger.error("Failed to re-authenticate, skipping this poll cycle")
                    return
                logger.info("Successfully re-authenticated")
            
            # Get new notices if enabled
            if self.enable_notices:
                notices = await self.gzctf_client.get_game_notices(self.game_id, count=10)
                if notices:
                    await self.process_notices(notices)
            
            # Get new events if enabled and not disabled due to auth issues
            if self.enable_events and not self.events_disabled_due_to_auth:
                logger.debug(f"Fetching events for game {self.game_id}...")
                events = await self.gzctf_client.get_game_events(self.game_id, count=10)
                logger.debug(f"Events result: {len(events) if events else 'None/Error'}")
                
                if events:
                    logger.debug(f"Processing {len(events)} events...")
                    await self.process_events(events)
                    # Reset failure count on success
                    self.events_failure_count = 0
                elif events is not None and len(events) == 0:
                    # Empty list is fine, reset failure count
                    logger.debug("No new events found")
                    self.events_failure_count = 0
                else:
                    # If events is None, it means there was an error (likely 401)
                    self.events_failure_count += 1
                    logger.warning(f"Events endpoint failed (attempt {self.events_failure_count}/5)")
                    
                    if self.events_failure_count >= 5:
                        logger.warning("Events endpoint has failed 5 times, disabling events due to authentication issues")
                        self.events_disabled_due_to_auth = True
                        self.save_state()
            elif self.enable_events and self.events_disabled_due_to_auth:
                logger.debug("Events disabled due to authentication issues, skipping events polling")
            else:
                logger.debug("Events disabled in configuration")
                
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
            notice_type = notice.get('type', 'Normal')
            values = notice.get('values', [])
            time = notice.get('time', 0)
            
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
                await self.send_notification(embed, 'notice', notice_type, values, notice_id, time)
    
    async def process_events(self, events: List[Dict[str, Any]]):
        """Process and send new events to Discord"""
        if not events:
            logger.debug("No events to process")
            return
            
        logger.debug(f"Processing {len(events)} events, last_event_time: {self.last_event_time}")
        
        # Sort by time to ensure we process in order
        events.sort(key=lambda x: x.get('time', 0))
        
        new_events_count = 0
        for event in events:
            event_time = event.get('time', 0)
            event_type = event.get('type', 'Normal')
            values = event.get('values', [])
            user = event.get('user', 'Unknown')
            team = event.get('team', 'Unknown')
            
            logger.debug(f"Event: {event_type} at {event_time}, last_seen: {self.last_event_time}")
            
            # Skip if we've already seen this event
            if self.last_event_time and event_time <= self.last_event_time:
                logger.debug(f"Skipping old event: {event_time} <= {self.last_event_time}")
                continue
                
            new_events_count += 1
            logger.debug(f"Processing new event: {event_type} by {user}")
            
            # Update last seen time
            if not self.last_event_time or event_time > self.last_event_time:
                self.last_event_time = event_time
                # Save state after updating
                self.save_state()
            
            # Format and send event
            embed = self.formatter.format_event(event)
            if embed:
                await self.send_notification(embed, 'event', event_type, values, None, event_time, user, team)
        
        logger.debug(f"Processed {new_events_count} new events out of {len(events)} total")
    
    async def send_notification(self, embed: discord.Embed, notification_type: str = 'unknown', 
                              content_type: str = 'Normal', values: List[str] = None, 
                              notification_id: int = None, timestamp: int = None,
                              user: str = None, team: str = None):
        """Send notification embed to correct Discord channel with detailed logging"""
        try:
            if notification_type == 'notice':
                channel = self.get_channel(self.notification_channel_id)
            elif notification_type == 'event':
                channel = self.get_channel(self.event_channel_id)
            else:
                logger.error(f"Unknown notification type '{notification_type}', cannot send message.")
                return
            if channel:
                await channel.send(embed=embed)
                
                # Create detailed log message
                log_parts = []
                log_parts.append(f"Sent {notification_type}: {embed.title}")
                
                # Add content type
                log_parts.append(f"Type: {content_type}")
                
                # Add values if available
                if values:
                    log_parts.append(f"Values: {values}")
                
                # Add user/team for events
                if notification_type == 'event':
                    if user and user != 'Unknown':
                        log_parts.append(f"User: {user}")
                    if team and team != 'Unknown':
                        log_parts.append(f"Team: {team}")
                
                # Add ID if available
                if notification_id:
                    log_parts.append(f"ID: {notification_id}")
                
                # Add timestamp if available
                if timestamp:
                    try:
                        dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
                        log_parts.append(f"Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        pass
                
                # Log the detailed message
                logger.info(" | ".join(log_parts))
                
            else:
                logger.error(f"Could not find target channel for type '{notification_type}'")
                
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
                    self.events_failure_count = state.get('events_failure_count', 0)
                    self.events_disabled_due_to_auth = state.get('events_disabled_due_to_auth', False)
                    logger.info(f"Loaded state: last_notice_id={self.last_notice_id}, last_event_time={self.last_event_time}, events_disabled={self.events_disabled_due_to_auth}")
            else:
                logger.info("No previous state found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.last_notice_id = None
            self.last_event_time = None
            self.events_failure_count = 0
            self.events_disabled_due_to_auth = False
            
    def save_state(self):
        """Save bot state to file"""
        try:
            state = {
                'last_notice_id': self.last_notice_id,
                'last_event_time': self.last_event_time,
                'events_failure_count': self.events_failure_count,
                'events_disabled_due_to_auth': self.events_disabled_due_to_auth,
                'game_id': self.game_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}") 
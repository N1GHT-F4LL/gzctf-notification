import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

from config import DiscordConfig
from gzctf_client import GZCTFClient
from notification_formatter import NotificationFormatter

logger = logging.getLogger(__name__)

class GZCTFNotificationBot(commands.Bot):
    """Discord bot for GZCTF notifications"""
    
    def __init__(self, discord_config: DiscordConfig, gzctf_client: GZCTFClient, 
                 game_id: int, poll_interval: int = 30, enable_notices: bool = True, 
                 enable_events: bool = True):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix=None, intents=intents)
        
        # Add slash command support
        # Use the built-in command tree from discord.py
        
        self.discord_config = discord_config
        self.gzctf_client = gzctf_client
        self.game_id = game_id
        self.poll_interval = poll_interval
        self.enable_notices = enable_notices
        self.enable_events = enable_events
        
        # State file for persistent storage
        self.state_file = f"bot_state_game_{game_id}.json"
        
        # Load previous state or initialize
        self.last_notice_id = None
        self.last_event_time = None
        self.load_state()
        
        # Notification formatter
        self.formatter = NotificationFormatter()
        
        # Start polling task
        self.poll_notifications.start()
        
    async def setup_hook(self):
        """Setup hook called when bot starts"""
        # Setup slash commands using built-in tree
        await self.setup_slash_commands()
        logger.info("Bot setup complete")
        
    async def setup_slash_commands(self):
        """Setup slash commands"""
        # Status command
        @self.tree.command(name="status", description="Show bot status and monitoring information")
        async def status_slash(interaction: discord.Interaction):
            # Check if user has permission to use bot commands
            if not interaction.channel.permissions_for(interaction.user).send_messages:
                await interaction.response.send_message("❌ You don't have permission to use bot commands in this channel.", ephemeral=True)
                return
                
            await interaction.response.defer()
            
            embed = discord.Embed(
                title="🤖 GZCTF Bot Status",
                description="Current bot status and monitoring information",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Status", value="✅ Online", inline=True)
            embed.add_field(name="Game ID", value=str(self.game_id), inline=True)
            embed.add_field(name="Channel", value=f"<#{self.discord_config.channel_id}>", inline=True)
            embed.add_field(name="Poll Interval", value=f"{self.poll_interval}s", inline=True)
            embed.add_field(name="Notices Enabled", value="✅ Yes" if self.enable_notices else "❌ No", inline=True)
            embed.add_field(name="Events Enabled", value="✅ Yes" if self.enable_events else "❌ No", inline=True)
            embed.add_field(name="Last Notice ID", value=str(self.last_notice_id or "None"), inline=True)
            embed.add_field(name="Last Event Time", value=str(self.last_event_time or "None"), inline=True)
            
            await interaction.followup.send(embed=embed)
        
        # Refresh command
        @self.tree.command(name="refresh", description="Manually refresh notifications")
        async def refresh_slash(interaction: discord.Interaction):
            # Check if user has permission to use bot commands
            if not interaction.channel.permissions_for(interaction.user).send_messages:
                await interaction.response.send_message("❌ You don't have permission to use bot commands in this channel.", ephemeral=True)
                return
                
            await interaction.response.defer()
            
            try:
                # Get latest notices and events
                notices = await self.gzctf_client.get_game_notices(self.game_id, count=5)
                events = await self.gzctf_client.get_game_events(self.game_id, count=5)
                
                await self.process_notices(notices)
                await self.process_events(events)
                
                await interaction.followup.send("✅ Notifications refreshed!")
                
            except Exception as e:
                logger.error(f"Error refreshing notifications: {e}")
                await interaction.followup.send(f"❌ Error refreshing notifications: {e}")
        
        # Games command
        @self.tree.command(name="games", description="List available games on the GZCTF platform")
        async def games_slash(interaction: discord.Interaction):
            # Check if user has permission to use bot commands
            if not interaction.channel.permissions_for(interaction.user).send_messages:
                await interaction.response.send_message("❌ You don't have permission to use bot commands in this channel.", ephemeral=True)
                return
                
            await interaction.response.defer()
            
            try:
                games = await self.gzctf_client.get_games()
                
                if not games:
                    await interaction.followup.send("No games found.")
                    return
                
                embed = discord.Embed(
                    title="🎮 Available Games",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                
                for game in games[:10]:  # Limit to 10 games
                    game_id = game.get('id', 'Unknown')
                    title = game.get('title', 'Unknown Title')
                    status = game.get('status', 'Unknown')
                    
                    embed.add_field(
                        name=f"Game {game_id}: {title}",
                        value=f"Status: {status}",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error fetching games: {e}")
                await interaction.followup.send(f"❌ Error fetching games: {e}")
        
        # Reset command
        @self.tree.command(name="reset", description="Reset bot state (start monitoring from beginning)")
        async def reset_slash(interaction: discord.Interaction):
            # Check if user has permission to use bot commands
            if not interaction.channel.permissions_for(interaction.user).send_messages:
                await interaction.response.send_message("❌ You don't have permission to use bot commands in this channel.", ephemeral=True)
                return
                
            await interaction.response.defer()
            
            try:
                # Reset state
                self.last_notice_id = None
                self.last_event_time = None
                
                # Remove state file
                if os.path.exists(self.state_file):
                    os.remove(self.state_file)
                    logger.info(f"Removed state file: {self.state_file}")
                
                await interaction.followup.send("✅ Bot state reset! Will start monitoring from the beginning.")
                logger.info("Bot state reset by user command")
                
            except Exception as e:
                logger.error(f"Error resetting state: {e}")
                await interaction.followup.send(f"❌ Error resetting state: {e}")
        
        # Permissions command
        @self.tree.command(name="permissions", description="Check your permissions for bot commands")
        async def permissions_slash(interaction: discord.Interaction):
            await interaction.response.defer()
            
            user = interaction.user
            channel = interaction.channel
            permissions = channel.permissions_for(user)
            
            embed = discord.Embed(
                title="🔐 Permission Check",
                description=f"Checking permissions for {user.mention}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # Check various permissions
            send_messages = "✅ Yes" if permissions.send_messages else "❌ No"
            use_slash_commands = "✅ Yes" if permissions.use_slash_commands else "❌ No"
            embed_links = "✅ Yes" if permissions.embed_links else "❌ No"
            attach_files = "✅ Yes" if permissions.attach_files else "❌ No"
            
            embed.add_field(name="Send Messages", value=send_messages, inline=True)
            embed.add_field(name="Use Slash Commands", value=use_slash_commands, inline=True)
            embed.add_field(name="Embed Links", value=embed_links, inline=True)
            embed.add_field(name="Attach Files", value=attach_files, inline=True)
            
            # Overall status
            can_use_bot = permissions.send_messages and permissions.use_slash_commands
            status = "✅ You can use bot commands!" if can_use_bot else "❌ You cannot use bot commands"
            embed.add_field(name="Status", value=status, inline=False)
            
            await interaction.followup.send(embed=embed)
        
        # Sync commands to Discord
        try:
            await self.tree.sync()
            logger.info("Slash commands synced successfully")
        except Exception as e:
            logger.error(f"Error syncing slash commands: {e}")
        
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
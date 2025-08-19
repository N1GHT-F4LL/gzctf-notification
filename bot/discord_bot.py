import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, cast
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
        
        # State file for persistent storage - use volume mount
        # Using root directory since we now mount the entire /app folder
        state_dir = os.getenv("STATE_DIR", "/app")
        os.makedirs(state_dir, exist_ok=True)
        self.state_file = os.path.join(state_dir, f"bot_state_game_{self.game_id}.json")
        
    async def close(self):
        """Close the bot and clean up resources"""
        # Ensure GZCTF client session is closed properly
        if hasattr(self, 'gzctf_client') and self.gzctf_client and hasattr(self.gzctf_client, 'session'):
            try:
                if self.gzctf_client.session and not self.gzctf_client.session.closed:
                    await self.gzctf_client.session.close()
                    logger.info("Closed GZCTF client session")
            except Exception as e:
                logger.error(f"Error closing GZCTF client session: {e}")
                
        # Call parent close method
        await super().close()
        
        # Load previous state or initialize
        self.last_notice_id = None
        self.last_event_time = None
        self.events_failure_count = 0
        self.events_disabled_due_to_auth = False
        
        # Initialize channel IDs to prevent AttributeError
        self.notification_channel_id = None
        self.event_channel_id = None
        
        self.load_state()
        
        # Notification formatter with config
        self.formatter = NotificationFormatter(self.config)
        
        # Game info cache
        self.game_title = None
        self.last_game_info_fetch = None
        
        # Start polling task
        self.poll_notifications.change_interval(seconds=self.poll_interval)
        self.poll_notifications.start()
        
        # Start game info update task (every 30 minutes)
        self.update_game_info.start()
        

    

    

        
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

        # Get channel names from environment variables or use defaults
        notification_channel_name = os.getenv("NOTIFICATION_CHANNEL_NAME", "notification")
        event_channel_name = os.getenv("EVENT_CHANNEL_NAME", "event")

        # Create or get notification channel only if notices are enabled
        if self.enable_notices:
            notification_channel = discord.utils.get(guild.text_channels, name=notification_channel_name)
            if not notification_channel:
                try:
                    notification_channel = await guild.create_text_channel(notification_channel_name)
                    logger.info(f"Created notification channel: {notification_channel.name}")
                except discord.Forbidden:
                    logger.error(f"Missing permissions to create notification channel")
            
            if notification_channel:
                self.notification_channel_id = notification_channel.id
                logger.info(f"Using notification channel: {notification_channel.name} (ID: {notification_channel.id})")
            else:
                logger.warning("Notification channel not found and could not be created. Notices will not be sent.")
        else:
            logger.info("Notices are disabled in configuration. Notification channel will not be created.")

        # Create or get event channel only if events are enabled
        if self.enable_events and not self.events_disabled_due_to_auth:
            event_channel = discord.utils.get(guild.text_channels, name=event_channel_name)

            # Build permission overwrites for a private event channel
            allowed_role_ids_env = os.getenv("EVENT_ALLOWED_ROLE_IDS", "").strip()
            allowed_role_names_env = os.getenv("EVENT_ALLOWED_ROLE_NAMES", "").strip()
            allowed_role_ids = set()
            if allowed_role_ids_env:
                for part in allowed_role_ids_env.split(','):
                    part = part.strip()
                    if part.isdigit():
                        try:
                            allowed_role_ids.add(int(part))
                        except:
                            pass
            allowed_roles = []
            # Find roles by ID first
            for role_id in allowed_role_ids:
                role = guild.get_role(role_id)
                if role:
                    allowed_roles.append(role)
            # Find roles by name if provided
            if allowed_role_names_env:
                for name in [n.strip() for n in allowed_role_names_env.split(',') if n.strip()]:
                    role_by_name = discord.utils.get(guild.roles, name=name)
                    if role_by_name and role_by_name not in allowed_roles:
                        allowed_roles.append(role_by_name)

            # Default to Administrator roles if nothing configured
            if not allowed_roles:
                allowed_roles = [r for r in guild.roles if r.permissions.administrator]

            overwrites: dict = {}
            # Hide from everyone by default
            overwrites[guild.default_role] = discord.PermissionOverwrite(view_channel=False)
            # Ensure the bot can access and post in the channel
            bot_member = guild.me
            bot_role = None
            if bot_member and bot_member.roles:
                # Prefer the bot's highest role (not @everyone)
                non_everyone_roles = [r for r in bot_member.roles if r != guild.default_role]
                if non_everyone_roles:
                    bot_role = max(non_everyone_roles, key=lambda r: r.position)
            if bot_member:
                overwrites[bot_member] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    embed_links=True,
                    read_message_history=True
                )
            if bot_role:
                overwrites[bot_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    embed_links=True,
                    read_message_history=True
                )
            # Grant access to allowed roles
            for role in allowed_roles:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    embed_links=True,
                    read_message_history=True
                )

            if not event_channel:
                try:
                    event_channel = await guild.create_text_channel(event_channel_name, overwrites=overwrites)
                    logger.info(f"Created event channel: {event_channel.name}")
                except discord.Forbidden:
                    logger.error("Missing permissions to create event channel - events will be disabled")
                except Exception as e:
                    logger.error(f"Failed to create event channel: {e}")
            else:
                # Ensure existing channel is private with correct permissions
                try:
                    # Apply @everyone deny
                    await event_channel.set_permissions(guild.default_role, view_channel=False)
                    # Apply bot permissions
                    if bot_member:
                        await event_channel.set_permissions(
                            bot_member,
                            view_channel=True,
                            send_messages=True,
                            embed_links=True,
                            read_message_history=True
                        )
                    if bot_role:
                        await event_channel.set_permissions(
                            bot_role,
                            view_channel=True,
                            send_messages=True,
                            embed_links=True,
                            read_message_history=True
                        )
                    # Apply allowed roles
                    for role in allowed_roles:
                        await event_channel.set_permissions(
                            role,
                            view_channel=True,
                            send_messages=True,
                            embed_links=True,
                            read_message_history=True
                        )
                    logger.info("Ensured event channel is private with correct permissions")
                except discord.Forbidden:
                    logger.error("Missing permissions to update event channel overwrites")
                except Exception as e:
                    logger.error(f"Failed to update event channel permissions: {e}")

            if event_channel:
                self.event_channel_id = event_channel.id
                logger.info(f"Using event channel: {event_channel.name} (ID: {event_channel.id})")
                # Final verification: ensure the bot can view the channel
                try:
                    perms = event_channel.permissions_for(bot_member) if bot_member else None
                    if not (perms and perms.view_channel):
                        logger.warning("Bot does not have access to the event channel yet; attempting to grant access again")
                        if bot_member:
                            await event_channel.set_permissions(bot_member, view_channel=True, send_messages=True, embed_links=True, read_message_history=True)
                        if bot_role:
                            await event_channel.set_permissions(bot_role, view_channel=True, send_messages=True, embed_links=True, read_message_history=True)
                except Exception:
                    pass
            else:
                logger.warning("Event channel not found and could not be created. Events will not be sent.")
        else:
            if self.events_disabled_due_to_auth:
                logger.info("Events are disabled due to authentication issues. Event channel will not be created.")
            else:
                logger.info("Events are disabled in configuration. Event channel will not be created.")

        # Initialize auth timing to avoid immediate first-loop re-auth
        self._last_auth_time = datetime.now().timestamp()
        self._poll_count = 0

        # Fetch game info and set bot status
        await self.fetch_and_update_status()
    
    @tasks.loop(seconds=30)
    async def poll_notifications(self):
        """Poll for new notifications from GZCTF"""
        try:
            # Proactively re-authenticate periodically to ensure token is always fresh
            auth_check_interval = 30  # Re-authenticate after every 30 polls (increased from 5)
            auth_time_interval = 3600  # Re-authenticate after 1 hour regardless of poll count
            current_time = datetime.now().timestamp()
            
            # Create static variables if they don't exist
            if not hasattr(self, '_last_auth_time'):
                self._last_auth_time = current_time
                self._poll_count = 0
                
            self._poll_count += 1
            time_since_last_auth = current_time - self._last_auth_time
            
            # Re-authenticate if poll count reached, time interval reached, or token is no longer valid
            token_ok = await self.gzctf_client.is_authenticated()
            need_reauth = (
                self._poll_count >= auth_check_interval or 
                time_since_last_auth >= auth_time_interval or 
                not token_ok
            )
            if need_reauth:
                
                reason = "poll count reached"
                if time_since_last_auth >= auth_time_interval:
                    reason = "time interval reached"
                elif not token_ok:
                    reason = "token validation failed"
                
                logger.info(f"Performing scheduled re-authentication ({reason}, poll count: {self._poll_count})")
                
                if not await self.gzctf_client.authenticate():
                    logger.error("Failed to re-authenticate, skipping this poll cycle")
                    return
                logger.info("Successfully re-authenticated")
                self._last_auth_time = current_time
                self._poll_count = 0
            
            # Get new notices if enabled and game_id is set
            if self.enable_notices and self.game_id is not None:
                notices = await self.gzctf_client.get_game_notices(self.game_id, count=10)
                if notices:
                    await self.process_notices(notices)
            elif self.enable_notices:
                logger.warning("Notices enabled but game_id is not set")
            
            # Get new events if enabled and event channel exists and game_id is set
            events = None
            if self.enable_events and self.event_channel_id and not self.events_disabled_due_to_auth and self.game_id is not None:
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
            elif self.enable_events and not self.events_disabled_due_to_auth and self.game_id is None:
                logger.warning("Events enabled but game_id is not set")
                    
            # Check if we need to disable events due to repeated failures
            if self.events_failure_count >= 5:
                logger.warning("Events endpoint has failed 5 times, disabling events due to authentication issues")
                self.events_disabled_due_to_auth = True
                self.save_state()
            else:
                # Skip events silently - no error logging needed
                pass
                
        except Exception as e:
            logger.error(f"Error polling notifications: {e}")
    
    @poll_notifications.before_loop
    async def before_poll_notifications(self):
        """Wait until bot is ready before starting polling"""
        await self.wait_until_ready()
    
    @tasks.loop(minutes=30)
    async def update_game_info(self):
        """Update game info and bot status every 30 minutes"""
        await self.fetch_and_update_status()
    
    @update_game_info.before_loop
    async def before_update_game_info(self):
        """Wait until bot is ready before starting game info updates"""
        await self.wait_until_ready()
    
    async def fetch_and_update_status(self):
        """Fetch game info and update bot status"""
        try:
            # Check if we're authenticated
            if not await self.gzctf_client.is_authenticated():
                logger.warning("Not authenticated, attempting to authenticate for game info...")
                if not await self.gzctf_client.authenticate():
                    logger.error("Failed to authenticate for game info")
                    return
            
            # Fetch game info if game_id is set
            if self.game_id is not None:
                game_info = await self.gzctf_client.get_game_info(self.game_id)
                if game_info:
                    self.game_title = game_info.get('title', f'Game {self.game_id}')
                    self.last_game_info_fetch = datetime.now()
                    logger.info(f"Updated game title: {self.game_title}")
                    # Save state when we successfully update game title
                    self.save_state()
                else:
                    logger.warning(f"Failed to fetch game info for ID {self.game_id}")
                    if not self.game_title:
                        self.game_title = f"Game {self.game_id}"
            else:
                logger.warning("Game ID not set, cannot fetch game info")
                self.game_title = "No Game ID Set"
            
            # Update bot status
            await self.update_bot_status()
            
        except Exception as e:
            logger.error(f"Error updating game info: {e}")
            if not self.game_title:
                self.game_title = f"Game {self.game_id}"
            await self.update_bot_status()
    
    async def update_bot_status(self):
        """Update bot status with current game title"""
        try:
            status_text = self.game_title or f"Game {self.game_id}"
            
            # Add status indicators
            if not self.enable_events or not self.event_channel_id or self.events_disabled_due_to_auth:
                status_text += " (Notices Only)"
            
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, 
                    name=status_text
                )
            )
            logger.debug(f"Updated bot status: {status_text}")
            
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
    
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
                
            # Update last seen ID if notice_id is not None
            if notice_id is not None and (not self.last_notice_id or notice_id > self.last_notice_id):
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
            
        # Skip if no event channel (this should not happen as we check before calling this method)
        if not self.event_channel_id:
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
                              content_type: str = 'Normal', values: Optional[List[str]] = None, 
                              notification_id: Optional[int] = None, timestamp: Optional[int] = None,
                              user: Optional[str] = None, team: Optional[str] = None):
        """Send notification embed to correct Discord channel with detailed logging"""
        try:
            if notification_type == 'notice':
                if not self.notification_channel_id:
                    logger.error("Notification channel ID not set. Channel may not have been created.")
                    return
                channel_id = self.notification_channel_id
                channel_type_desc = "notification"
            elif notification_type == 'event':
                # Event channel check is now done in process_events before calling this method
                if not self.event_channel_id:
                    logger.error("Event channel ID not set. Channel may not have been created.")
                    return
                channel_id = self.event_channel_id
                channel_type_desc = "event"
            else:
                logger.error(f"Unknown notification type '{notification_type}', cannot send message.")
                return
            
            channel = self.get_channel(channel_id)
            if channel and hasattr(channel, 'send'):
                # Cast to the correct type that has send method
                text_channel = cast(discord.TextChannel, channel)
                await text_channel.send(embed=embed)
                
                # Create detailed log message
                log_parts = []
                log_parts.append(f"Sent {notification_type} to {channel_type_desc} channel: {embed.title}")
                
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
                    self.game_title = state.get('game_title')
                    logger.info(f"Loaded state: last_notice_id={self.last_notice_id}, last_event_time={self.last_event_time}, events_disabled={self.events_disabled_due_to_auth}, game_title={self.game_title}")
            else:
                logger.info("No previous state found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self.last_notice_id = None
            self.last_event_time = None
            self.events_failure_count = 0
            self.events_disabled_due_to_auth = False
            self.game_title = None
            
    def save_state(self):
        """Save bot state to file"""
        try:
            state = {
                'last_notice_id': self.last_notice_id,
                'last_event_time': self.last_event_time,
                'events_failure_count': self.events_failure_count,
                'events_disabled_due_to_auth': self.events_disabled_due_to_auth,
                'game_id': self.game_id,
                'game_title': self.game_title,
                'timestamp': datetime.now().isoformat()
            }
            
            # Ensure directory exists and has proper permissions
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Try to write to a temporary file first, then rename
            temp_file = self.state_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Atomic rename
            os.rename(temp_file, self.state_file)
            logger.debug(f"State saved successfully to {self.state_file}")
            
        except PermissionError as e:
            logger.error(f"Permission denied saving state to {self.state_file}: {e}")
            logger.info("Bot will continue running but state won't be persisted")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            # Clean up temp file if it exists
            temp_file = self.state_file + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass 
import discord
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import random
import os

logger = logging.getLogger(__name__)

class NotificationFormatter:
    """Format GZCTF notifications into Discord embeds"""
    
    def __init__(self, config=None):
        # Color mapping for different notification types
        self.notice_colors = {
            "FirstBlood": 0xFF0000,    # Red
            "SecondBlood": 0xFF6600,   # Orange
            "ThirdBlood": 0xFFCC00,    # Yellow
            "NewHint": 0x00CCFF,       # Light Blue
            "NewChallenge": 0x00FF00,  # Green
            "Normal": 0x808080         # Gray
        }
        # Emoji mapping for different types
        self.notice_emojis = {
            "FirstBlood": "🥇",
            "SecondBlood": "🥈", 
            "ThirdBlood": "🥉",
            "NewHint": "💡",
            "NewChallenge": "🎯",
            "Normal": "📢"
        }
        self.event_emojis = {
            "FlagSubmit": "🚩",
            "ContainerStart": "▶️",
            "ContainerDestroy": "⏹️",
            "CheatDetected": "⚠️",
            "Normal": "📝"
        }
        self.event_colors = {
            "FlagSubmit": 0x00FF00,      # Green for flag submissions
            "ContainerStart": 0x00AAFF,  # Blue for container start
            "ContainerDestroy": 0xFF8800, # Orange for container destroy
            "CheatDetected": 0xFF0000,   # Red for cheat detection
            "Normal": 0x808080           # Gray for normal events
        }
    
    def format_notice(self, notice: Dict[str, Any]) -> Optional[discord.Embed]:
        """Format a game notice into a Discord embed"""
        try:
            notice_type = notice.get('type', 'Normal')
            values = notice.get('values', [])
            notice_id = notice.get('id', 'Unknown')
            time = notice.get('time', 0)
            # Log formatting attempt
            logger.debug(f"Formatting notice - Type: {notice_type}, ID: {notice_id}, Values: {values}")
            # Get color for this notice type
            color = self.notice_colors.get(notice_type, 0x808080)
            # Create embed
            embed = discord.Embed(
                title=self._format_notice_title(notice_type),
                description=self._format_notice_content(notice_type, values),
                color=color,
                timestamp=self._timestamp_to_datetime(time)
            )
            # Add footer
            embed.set_footer(text=f"Notice ID: {notice_id}")
            # Log successful formatting
            logger.debug(f"Successfully formatted notice - Type: {notice_type}, Title: {embed.title}")
            return embed
        except Exception as e:
            logger.error(f"Error formatting notice: {e}")
            return None
    
    def format_event(self, event: Dict[str, Any]) -> Optional[discord.Embed]:
        """Format a game event into a Discord embed"""
        try:
            event_type = event.get('type', 'Normal')
            values = event.get('values', [])
            time = event.get('time', 0)
            user = event.get('user', 'Unknown')
            team = event.get('team', 'Unknown')
            
            # Log formatting attempt
            logger.debug(f"Formatting event - Type: {event_type}, User: {user}, Team: {team}, Values: {values}")
            
            # Get color for this event type (with special handling for flag submissions)
            color = self._get_event_color(event_type, values)
            
            # Create embed
            embed = discord.Embed(
                title=self._format_event_title(event_type, values),
                description=self._format_event_content(event_type, values, event),
                color=color,
                timestamp=self._timestamp_to_datetime(time)
            )
            
            # Add user and team info if available
            if user and user != 'Unknown':
                embed.add_field(name="👤 User", value=f"`{user}`", inline=True)
            if team and team != 'Unknown':
                embed.add_field(name="👥 Team", value=f"**{team}**", inline=True)
            
            # Add challenge info for certain event types
            if event_type in ["FlagSubmit", "ContainerStart", "ContainerDestroy"] and len(values) >= 2:
                challenge = values[2] if event_type == "FlagSubmit" else values[1]
                embed.add_field(name="🎯 Challenge", value=f"**{challenge}**", inline=True)
            
            # Log successful formatting
            logger.debug(f"Successfully formatted event - Type: {event_type}, Title: {embed.title}")
            return embed
        except Exception as e:
            logger.error(f"Error formatting event: {e}")
            return None
    
    def _format_notice_title(self, notice_type: str) -> str:
        """Format notice type into a readable title - Compact format, dùng emoji động nếu có"""
        emoji = self.notice_emojis.get(notice_type, "")
        titles = {
            "FirstBlood": "First Blood",
            "SecondBlood": "Second Blood", 
            "ThirdBlood": "Third Blood",
            "NewHint": "New Hint",
            "NewChallenge": "New Challenge",
            "Normal": "Notice"
        }
        return f"{emoji} {titles.get(notice_type, 'Notice')}".strip()
    
    def _format_event_title(self, event_type: str, values: list = None) -> str:
        """Format event type into a readable title with dynamic content"""
        if event_type == "FlagSubmit" and values and len(values) >= 3:
            result = values[0]
            challenge = values[2]
            if result == "Accepted":
                return f"🎉 {challenge} - Flag Accepted!"
            elif result == "WrongAnswer":
                return f"❌ {challenge} - Wrong Flag"
            else:
                return f"🚩 {challenge} - Flag {result}"
        
        titles = {
            "FlagSubmit": "🚩 Flag Submission",
            "ContainerStart": "🚀 Container Started",
            "ContainerDestroy": "🛑 Container Stopped",
            "CheatDetected": "🚨 Cheat Alert",
            "Normal": "📝 Event"
        }
        return titles.get(event_type, "📝 Event")
    
    def _get_event_color(self, event_type: str, values: list = None) -> int:
        """Get color for event based on type and values"""
        if event_type == "FlagSubmit" and values and len(values) >= 1:
            result = values[0]
            if result == "Accepted":
                return 0x00FF00  # Green for accepted flags
            elif result == "WrongAnswer":
                return 0xFF4444  # Red for wrong flags
            else:
                return 0xFFAA00  # Orange for other results
        
        return self.event_colors.get(event_type, 0x808080)
    
    def _format_notice_content(self, notice_type: str, values: list) -> str:
        """Format notice content based on type and values - Compact 2-line format"""
        if not values:
            return "No additional information available."
        
        if notice_type in ["FirstBlood", "SecondBlood", "ThirdBlood"]:
            if len(values) >= 2:
                challenge = values[0]
                team = values[1]
                blood_type = "FIRST BLOOD" if notice_type == "FirstBlood" else "SECOND BLOOD" if notice_type == "SecondBlood" else "THIRD BLOOD"
                return f"**{team}** has achieved **{blood_type}** on **{challenge}**!"
            else:
                return " ".join(values)
        
        elif notice_type == "NewHint":
            if len(values) >= 2:
                challenge = values[0]
                hint = values[1]
                return f"New hint available for **{challenge}**!\n💡 **Hint**: {hint}"
            else:
                return f"New hint available for **{values[0] if values else 'Unknown Challenge'}**!"
        
        elif notice_type == "NewChallenge":
            if values:
                challenge = values[0]
                return f"**{challenge}** is now available!"
            else:
                return "New challenge is now available!"
        
        else:
            return " ".join(values)
    
    def _format_event_content(self, event_type: str, values: list, event: Dict[str, Any] = None) -> str:
        """Format event content based on type and values - Enhanced formatting"""
        if not values:
            return "No additional information available."
        
        user = event.get('user', 'Unknown') if event else 'Unknown'
        team = event.get('team', 'Unknown') if event else 'Unknown'
        
        if event_type == "FlagSubmit":
            if len(values) >= 3:
                result = values[0]  # Accepted/WrongAnswer
                flag = values[1]    # The flag submitted
                challenge = values[2]  # Challenge name
                challenge_id = values[3] if len(values) > 3 else ""
                
                # Format result with emoji
                if result == "Accepted":
                    result_emoji = "✅"
                    result_text = "**ACCEPTED**"
                    result_color = "�"
                elif result == "WrongAnswer":
                    result_emoji = "❌"
                    result_text = "**WRONG ANSWER**"
                    result_color = "🔴"
                else:
                    result_emoji = "📝"
                    result_text = f"**{result}**"
                    result_color = "🟡"
                
                # Truncate long flags for display
                display_flag = flag if len(flag) <= 50 else f"{flag[:47]}..."
                
                return f"Submitted flag: `{display_flag}`"
            else:
                return f"Flag submission: {' '.join(values)}"
        
        elif event_type == "ContainerStart":
            if len(values) >= 2:
                container_id = values[0]
                challenge = values[1]
                return f"🚀 **{challenge}** container started\n📦 Container ID: `{container_id}`"
            elif values:
                challenge = values[0]
                return f"🚀 **{challenge}** container started"
            else:
                return "🚀 Container started"
        
        elif event_type == "ContainerDestroy":
            if len(values) >= 2:
                container_id = values[0]
                challenge = values[1]
                return f"🛑 **{challenge}** container destroyed\n📦 Container ID: `{container_id}`"
            elif values:
                challenge = values[0]
                return f"🛑 **{challenge}** container destroyed"
            else:
                return "🛑 Container destroyed"
        
        elif event_type == "CheatDetected":
            if values:
                details = ' '.join(values)
                return f"🚨 **Suspicious activity detected!**\n📋 Details: {details}"
            else:
                return "🚨 **Suspicious activity detected!**"
        
        else:
            # Generic event formatting
            return f"📝 **Event Details:**\n{' '.join(values)}"
    
    def _timestamp_to_datetime(self, timestamp: int) -> datetime:
        """Convert Unix timestamp to datetime"""
        try:
            # Handle different timestamp formats
            if isinstance(timestamp, (int, float)):
                # Check if timestamp is in seconds or milliseconds
                if timestamp > 1e10:  # Likely milliseconds
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)
            else:
                return datetime.now()
        except (ValueError, TypeError, OSError):
            # Return current time if timestamp is invalid
            return datetime.now() 
import discord
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationFormatter:
    """Format GZCTF notifications into Discord embeds"""
    
    def __init__(self):
        # Color mapping for different notification types
        self.notice_colors = {
            "FirstBlood": 0xFF0000,    # Red
            "SecondBlood": 0xFF6600,   # Orange
            "ThirdBlood": 0xFFCC00,    # Yellow
            "NewHint": 0x00CCFF,       # Light Blue
            "NewChallenge": 0x00FF00,  # Green
            "Normal": 0x808080         # Gray
        }
        
        self.event_colors = {
            "FlagSubmit": 0x00FF00,    # Green
            "ContainerStart": 0x00CCFF, # Light Blue
            "ContainerDestroy": 0xFF6600, # Orange
            "CheatDetected": 0xFF0000, # Red
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
            "ContainerStart": "🚀",
            "ContainerDestroy": "💥",
            "CheatDetected": "⚠️",
            "Normal": "📝"
        }
    
    def format_notice(self, notice: Dict[str, Any]) -> Optional[discord.Embed]:
        """Format a game notice into a Discord embed"""
        try:
            notice_type = notice.get('type', 'Normal')
            values = notice.get('values', [])
            notice_id = notice.get('id', 'Unknown')
            time = notice.get('time', 0)
            
            # Get color and emoji for this notice type
            color = self.notice_colors.get(notice_type, 0x808080)
            emoji = self.notice_emojis.get(notice_type, "📢")
            
            # Create embed
            embed = discord.Embed(
                title=f"{emoji} {self._format_notice_title(notice_type)}",
                description=self._format_notice_content(notice_type, values),
                color=color,
                timestamp=self._timestamp_to_datetime(time)
            )
            
            # Add footer
            embed.set_footer(text=f"Notice ID: {notice_id}")
            
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
            
            # Get color and emoji for this event type
            color = self.event_colors.get(event_type, 0x808080)
            emoji = self.event_emojis.get(event_type, "📝")
            
            # Create embed
            embed = discord.Embed(
                title=f"{emoji} {self._format_event_title(event_type)}",
                description=self._format_event_content(event_type, values),
                color=color,
                timestamp=self._timestamp_to_datetime(time)
            )
            
            # Add user and team info if available
            if user and user != 'Unknown':
                embed.add_field(name="User", value=user, inline=True)
            if team and team != 'Unknown':
                embed.add_field(name="Team", value=team, inline=True)
            
            return embed
            
        except Exception as e:
            logger.error(f"Error formatting event: {e}")
            return None
    
    def _format_notice_title(self, notice_type: str) -> str:
        """Format notice type into a readable title"""
        titles = {
            "FirstBlood": "First Blood! 🩸",
            "SecondBlood": "Second Blood! 🩸",
            "ThirdBlood": "Third Blood! 🩸",
            "NewHint": "New Hint Available",
            "NewChallenge": "New Challenge Released",
            "Normal": "Game Notice"
        }
        return titles.get(notice_type, "Game Notice")
    
    def _format_event_title(self, event_type: str) -> str:
        """Format event type into a readable title"""
        titles = {
            "FlagSubmit": "Flag Submission",
            "ContainerStart": "Container Started",
            "ContainerDestroy": "Container Destroyed",
            "CheatDetected": "Cheat Detected!",
            "Normal": "Game Event"
        }
        return titles.get(event_type, "Game Event")
    
    def _format_notice_content(self, notice_type: str, values: list) -> str:
        """Format notice content based on type and values"""
        if not values:
            return "No additional information available."
        
        if notice_type in ["FirstBlood", "SecondBlood", "ThirdBlood"]:
            if len(values) >= 2:
                challenge = values[0]
                team = values[1]
                return f"**{challenge}** has been solved by **{team}**!"
            else:
                return " ".join(values)
        
        elif notice_type == "NewHint":
            if len(values) >= 2:
                challenge = values[0]
                hint = values[1]
                return f"New hint for **{challenge}**: {hint}"
            else:
                return " ".join(values)
        
        elif notice_type == "NewChallenge":
            if values:
                challenge = values[0]
                return f"New challenge **{challenge}** is now available!"
            else:
                return " ".join(values)
        
        else:
            return " ".join(values)
    
    def _format_event_content(self, event_type: str, values: list) -> str:
        """Format event content based on type and values"""
        if not values:
            return "No additional information available."
        
        if event_type == "FlagSubmit":
            if len(values) >= 2:
                challenge = values[0]
                result = values[1]
                if result == "Accepted":
                    return f"✅ Flag submitted for **{challenge}** - **ACCEPTED!**"
                elif result == "WrongAnswer":
                    return f"❌ Flag submitted for **{challenge}** - **WRONG ANSWER**"
                else:
                    return f"Flag submitted for **{challenge}** - {result}"
            else:
                return " ".join(values)
        
        elif event_type in ["ContainerStart", "ContainerDestroy"]:
            if values:
                challenge = values[0]
                action = "started" if event_type == "ContainerStart" else "destroyed"
                return f"Container for **{challenge}** has been {action}."
            else:
                return " ".join(values)
        
        elif event_type == "CheatDetected":
            if values:
                return f"🚨 **CHEAT DETECTED**: {' '.join(values)}"
            else:
                return "🚨 **CHEAT DETECTED**"
        
        else:
            return " ".join(values)
    
    def _timestamp_to_datetime(self, timestamp: int) -> datetime:
        """Convert Unix timestamp to datetime"""
        try:
            return datetime.fromtimestamp(timestamp)
        except (ValueError, TypeError):
            return datetime.utcnow() 
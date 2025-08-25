import discord
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class NotificationFormatter:
    """Format GZCTF notifications into Discord embeds"""
    
    def __init__(self, config=None):
        # Color mapping for different notification types
        self.notice_colors = {
            "FirstBlood": 0xFF0000,    # Red
            "SecondBlood": 0xFF0000,   # Red
            "ThirdBlood": 0xFF0000,    # Red
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
            values: List[str] = notice.get('values', [])
            notice_id = notice.get('id', 'Unknown')
            time = notice.get('time', 0)
            
            logger.debug(f"Formatting notice - Type: {notice_type}, ID: {notice_id}, Values: {values}")
            
            color = self.notice_colors.get(notice_type, 0x808080)
            
            embed = discord.Embed(
                title=self._format_notice_title(notice_type),
                description=self._format_notice_content(notice_type, values),
                color=color,
                timestamp=self._timestamp_to_datetime(time)
            )
            
            embed.set_footer(text=f"Notice ID: {notice_id}")
            
            logger.debug(f"Successfully formatted notice - Type: {notice_type}, Title: {embed.title}")
            return embed
        except Exception as e:
            logger.error(f"Error formatting notice: {e}")
            return None
    
    def format_event(self, event: Dict[str, Any]) -> Optional[discord.Embed]:
        """Format a game event into a Discord embed - Compact format"""
        try:
            event_type = event.get('type', 'Normal')
            values: List[str] = event.get('values', [])
            time = event.get('time', 0)
            user = event.get('user', 'Unknown')
            team = event.get('team', 'Unknown')
            
            logger.debug(f"Formatting event - Type: {event_type}, User: {user}, Team: {team}, Values: {values}")
            
            color = self._get_event_color(event_type, values)
            
            # Create compact embed with all info in title
            embed = discord.Embed(
                title=self._format_event_title(event_type, values, user, team),
                description=self._format_event_content(event_type, values),
                color=color,
                timestamp=self._timestamp_to_datetime(time)
            )
            
            logger.debug(f"Successfully formatted event - Type: {event_type}, Title: {embed.title}")
            return embed
        except Exception as e:
            logger.error(f"Error formatting event: {e}")
            return None
    
    def _format_notice_title(self, notice_type: str) -> str:
        """Format notice type into a readable title"""
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
    
    def _format_event_title(self, event_type: str, values: Optional[List[str]] = None, user: Optional[str] = None, team: Optional[str] = None) -> str:
        """Format event type into a compact title with all essential info"""
        # Clean user and team info
        user_display = user if user and user != 'Unknown' else ""
        team_display = team if team and team != 'Unknown' else ""
        
        # Create user info string
        if user_display and team_display:
            user_info = f"{user_display} ({team_display})"
        elif user_display:
            user_info = user_display
        elif team_display:
            user_info = f"({team_display})"
        else:
            user_info = ""
        
        if event_type == "FlagSubmit" and values and len(values) >= 3:
            result = values[0]
            challenge = values[2]
            if result == "Accepted":
                return f"🎉 {user_info} solved {challenge}"
            elif result == "WrongAnswer":
                return f"❌ {user_info} - Wrong flag on {challenge}"
            else:
                return f"🚩 {user_info} - {result} on {challenge}"
        
        elif event_type == "ContainerStart" and values and len(values) >= 2:
            challenge = values[1]
            return f"🐳 {user_info} started {challenge}"
        
        elif event_type == "ContainerDestroy" and values and len(values) >= 2:
            challenge = values[1]
            return f"🛑 {user_info} stopped {challenge}"
        
        elif event_type == "CheatDetected":
            # Prefer explicit, descriptive message using values if available
            if values and len(values) >= 3:
                challenge = values[0]
                offender_team = values[1]
                victim_team = values[2]
                # Title focuses on challenge context
                return f"🚨 Cheat detected in {challenge}"
            # Fallback to generic alert with user/team info
            return f"🚨 Cheat Alert - {user_info}"
        
        # Fallback titles
        titles = {
            "FlagSubmit": f"🚩 {user_info} - Flag Submission",
            "ContainerStart": f"🐳 {user_info} - Container Started",
            "ContainerDestroy": f"🛑 {user_info} - Container Stopped",
            "CheatDetected": f"🚨 {user_info} - Cheat Alert",
            "Normal": f"📝 {user_info} - Event"
        }
        return titles.get(event_type, f"📝 {user_info} - Event").strip()
    
    def _get_event_color(self, event_type: str, values: Optional[List[str]] = None) -> int:
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
        """Format notice content based on type and values"""
        if not values:
            return "No additional information available."
        
        if notice_type in ["FirstBlood", "SecondBlood", "ThirdBlood"]:
            if len(values) >= 2:
                challenge = values[0]
                team = values[1]
                blood_type = "FIRST BLOOD" if notice_type == "FirstBlood" else "SECOND BLOOD" if notice_type == "SecondBlood" else "THIRD BLOOD"
                return f"**{team}** achieved **{blood_type}** on **{challenge}**!"
            else:
                return " ".join(values)
        
        elif notice_type == "NewHint":
            if len(values) >= 2:
                challenge = values[0]
                hint = values[1]
                return f"New hint for **{challenge}**!\n💡 {hint}"
            else:
                return f"New hint for **{values[0] if values else 'Unknown Challenge'}**!"
        
        elif notice_type == "NewChallenge":
            if values:
                challenge = values[0]
                return f"**{challenge}** is now available!"
            else:
                return "New challenge is now available!"
        
        else:
            return " ".join(values)
    
    def _format_event_content(self, event_type: str, values: list) -> str:
        """Format event content - minimal and focused on unique info only"""
        if not values:
            return ""
        
        if event_type == "FlagSubmit" and len(values) >= 2:
            flag = values[1]
            # Truncate long flags for display
            display_flag = flag if len(flag) <= 40 else f"{flag[:37]}..."
            return f"Flag: `{display_flag}`"
        
        elif event_type in ["ContainerStart", "ContainerDestroy"] and len(values) >= 1:
            container_id = values[0]
            return f"Container ID: `{container_id}`"
        
        elif event_type == "CheatDetected" and values:
            # Expecting values as [challenge, offender_team, victim_team]
            if len(values) >= 3:
                challenge = values[0]
                offender_team = values[1]
                victim_team = values[2]
                return f"Team {offender_team} used {victim_team}'s flag."
            # Fallback to a compact joined representation if structure is unknown
            details = '-'.join(values)
            return f"Details: {details}"
        
        return ""
    
    def _timestamp_to_datetime(self, timestamp: Optional[float | int]) -> datetime:
        """Convert Unix timestamp to datetime"""
        try:
            if isinstance(timestamp, (int, float)):
                # Check if timestamp is in seconds or milliseconds
                if timestamp > 1e10:  # Likely milliseconds
                    ts = int(timestamp // 1000)
                else:
                    ts = int(timestamp)
                return datetime.fromtimestamp(ts)
            else:
                return datetime.now()
        except (ValueError, TypeError, OSError):
            return datetime.now()
import discord
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import random

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
        
        # Random congratulation messages for different blood types
        self.first_blood_messages = [
            "🎉 **CONGRATULATIONS!** 🎉\n\n**{team}** has achieved the **FIRST BLOOD** on **{challenge}**!\n\n🌟 *Making history with the first solve!* 🌟",
            "🏆 **LEGENDARY!** 🏆\n\n**{team}** has claimed the **FIRST BLOOD** on **{challenge}**!\n\n🔥 *The first to conquer this challenge!* 🔥",
            "⚡ **INCREDIBLE!** ⚡\n\n**{team}** has secured the **FIRST BLOOD** on **{challenge}**!\n\n💎 *Setting the standard for others to follow!* 💎",
            "🚀 **PHENOMENAL!** 🚀\n\n**{team}** has achieved the **FIRST BLOOD** on **{challenge}**!\n\n👑 *The crown belongs to the first!* 👑",
            "💫 **SPECTACULAR!** 💫\n\n**{team}** has earned the **FIRST BLOOD** on **{challenge}**!\n\n⭐ *Leading the pack with brilliance!* ⭐",
            "🎊 **EXTRAORDINARY!** 🎊\n\n**{team}** has conquered the **FIRST BLOOD** on **{challenge}**!\n\n🏅 *The pioneer of this challenge!* 🏅",
            "🌟 **MAGNIFICENT!** 🌟\n\n**{team}** has seized the **FIRST BLOOD** on **{challenge}**!\n\n💫 *A masterclass in problem-solving!* 💫",
            "🔥 **SENSATIONAL!** 🔥\n\n**{team}** has captured the **FIRST BLOOD** on **{challenge}**!\n\n⚔️ *The first warrior to victory!* ⚔️",
            "💎 **REMARKABLE!** 💎\n\n**{team}** has dominated the **FIRST BLOOD** on **{challenge}**!\n\n🎯 *Precision and speed combined!* 🎯",
            "✨ **FABULOUS!** ✨\n\n**{team}** has mastered the **FIRST BLOOD** on **{challenge}**!\n\n🎪 *The showstopper of the competition!* 🎪"
        ]
        
        self.second_blood_messages = [
            "🎊 **AMAZING!** 🎊\n\n**{team}** has secured the **SECOND BLOOD** on **{challenge}**!\n\n⚡ *Quick thinking and great skills!* ⚡",
            "🥈 **OUTSTANDING!** 🥈\n\n**{team}** has claimed the **SECOND BLOOD** on **{challenge}**!\n\n💪 *Proving that speed isn't everything!* 💪",
            "🌟 **FANTASTIC!** 🌟\n\n**{team}** has achieved the **SECOND BLOOD** on **{challenge}**!\n\n🎯 *Precision and determination pay off!* 🎯",
            "🔥 **EXCELLENT!** 🔥\n\n**{team}** has earned the **SECOND BLOOD** on **{challenge}**!\n\n⚔️ *A worthy challenger emerges!* ⚔️",
            "💎 **BRILLIANT!** 💎\n\n**{team}** has secured the **SECOND BLOOD** on **{challenge}**!\n\n🎪 *The show must go on!* 🎪",
            "🎯 **IMPRESSIVE!** 🎯\n\n**{team}** has captured the **SECOND BLOOD** on **{challenge}**!\n\n🚀 *Rocketing to the top!* 🚀",
            "✨ **STUNNING!** ✨\n\n**{team}** has conquered the **SECOND BLOOD** on **{challenge}**!\n\n💫 *A dazzling display of skill!* 💫",
            "🏅 **EXCEPTIONAL!** 🏅\n\n**{team}** has mastered the **SECOND BLOOD** on **{challenge}**!\n\n🎨 *Artistry in problem-solving!* 🎨",
            "⚡ **DYNAMIC!** ⚡\n\n**{team}** has dominated the **SECOND BLOOD** on **{challenge}**!\n\n🔥 *Burning with determination!* 🔥",
            "💎 **SPARKLING!** 💎\n\n**{team}** has seized the **SECOND BLOOD** on **{challenge}**!\n\n🌟 *Shining bright in the competition!* 🌟"
        ]
        
        self.third_blood_messages = [
            "🎯 **EXCELLENT!** 🎯\n\n**{team}** has claimed the **THIRD BLOOD** on **{challenge}**!\n\n💪 *Persistence pays off!* 💪",
            "🥉 **GREAT JOB!** 🥉\n\n**{team}** has achieved the **THIRD BLOOD** on **{challenge}**!\n\n🎨 *Creativity and skill combined!* 🎨",
            "✨ **WONDERFUL!** ✨\n\n**{team}** has earned the **THIRD BLOOD** on **{challenge}**!\n\n🎭 *The third time's the charm!* 🎭",
            "🎪 **SPLENDID!** 🎪\n\n**{team}** has secured the **THIRD BLOOD** on **{challenge}**!\n\n🎲 *Luck favors the prepared!* 🎲",
            "🏅 **SUPERB!** 🏅\n\n**{team}** has claimed the **THIRD BLOOD** on **{challenge}**!\n\n🎪 *The competition is heating up!* 🎪",
            "🌟 **MARVELOUS!** 🌟\n\n**{team}** has captured the **THIRD BLOOD** on **{challenge}**!\n\n💎 *A gem of a performance!* 💎",
            "🔥 **TREMENDOUS!** 🔥\n\n**{team}** has conquered the **THIRD BLOOD** on **{challenge}**!\n\n⚡ *Electrifying problem-solving!* ⚡",
            "🎊 **FANTASTIC!** 🎊\n\n**{team}** has mastered the **THIRD BLOOD** on **{challenge}**!\n\n🚀 *Soaring to new heights!* 🚀",
            "💫 **BRILLIANT!** 💫\n\n**{team}** has dominated the **THIRD BLOOD** on **{challenge}**!\n\n👑 *Royal problem-solving skills!* 👑",
            "🎯 **OUTSTANDING!** 🎯\n\n**{team}** has seized the **THIRD BLOOD** on **{challenge}**!\n\n🏆 *A champion's performance!* 🏆"
        ]
        
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
            "FirstBlood": "🏆 FIRST BLOOD! 🏆",
            "SecondBlood": "🥈 SECOND BLOOD! 🥈",
            "ThirdBlood": "🥉 THIRD BLOOD! 🥉",
            "NewHint": "💡 New Hint Available",
            "NewChallenge": "🎯 New Challenge Released",
            "Normal": "📢 Game Notice"
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
                if notice_type == "FirstBlood":
                    return random.choice(self.first_blood_messages).format(team=team, challenge=challenge)
                elif notice_type == "SecondBlood":
                    return random.choice(self.second_blood_messages).format(team=team, challenge=challenge)
                else:  # ThirdBlood
                    return random.choice(self.third_blood_messages).format(team=team, challenge=challenge)
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
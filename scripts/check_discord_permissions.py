#!/usr/bin/env python3
"""
Discord Bot Permission Checker
Checks if the bot has proper permissions to send messages to the specified channel.
"""

import discord
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DiscordPermissionChecker:
    def __init__(self):
        self.token = os.getenv('DISCORD_TOKEN')
        self.channel_id = int(os.getenv('DISCORD_CHANNEL_ID', 0))
        self.guild_id = os.getenv('DISCORD_GUILD_ID')
        
        if not self.token:
            print("❌ DISCORD_TOKEN not found in environment variables")
            return
            
        if not self.channel_id:
            print("❌ DISCORD_CHANNEL_ID not found in environment variables")
            return
            
        self.bot = discord.Client(intents=discord.Intents.default())
        
    async def check_permissions(self):
        """Check bot permissions in the specified channel"""
        try:
            print("🔍 Checking Discord Bot Permissions...")
            print("=" * 50)
            
            # Connect to Discord
            await self.bot.start(self.token)
            
        except discord.LoginFailure:
            print("❌ Failed to login with Discord token")
            print("   Please check your DISCORD_TOKEN in the .env file")
            return
        except Exception as e:
            print(f"❌ Error connecting to Discord: {e}")
            return
            
    async def on_ready(self):
        """Called when bot is ready"""
        print(f"✅ Bot logged in as: {self.bot.user}")
        print(f"📋 Bot ID: {self.bot.user.id}")
        
        # Check if we can find the channel
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"❌ Cannot find channel with ID: {self.channel_id}")
            print("   Please check your DISCORD_CHANNEL_ID")
            await self.bot.close()
            return
            
        print(f"✅ Found channel: #{channel.name}")
        print(f"📋 Channel ID: {channel.id}")
        print(f"🏠 Guild: {channel.guild.name}")
        
        # Check bot permissions in the channel
        bot_member = channel.guild.get_member(self.bot.user.id)
        if not bot_member:
            print("❌ Bot is not a member of this guild")
            await self.bot.close()
            return
            
        # Get bot permissions
        permissions = channel.permissions_for(bot_member)
        
        print("\n🔐 Bot Permissions in Channel:")
        print("-" * 30)
        
        required_permissions = [
            'send_messages',
            'embed_links', 
            'use_external_emojis',
            'attach_files',
            'read_message_history'
        ]
        
        all_good = True
        for permission in required_permissions:
            has_perm = getattr(permissions, permission, False)
            status = "✅" if has_perm else "❌"
            print(f"{status} {permission.replace('_', ' ').title()}: {has_perm}")
            if not has_perm:
                all_good = False
                
        if all_good:
            print("\n🎉 All required permissions are granted!")
            print("   The bot should be able to send notifications.")
        else:
            print("\n⚠️  Missing required permissions!")
            print("   Please check the channel permissions and bot role.")
            print("\n📝 How to fix:")
            print("   1. Right-click the channel → Edit Channel → Permissions")
            print("   2. Add the bot role if not present")
            print("   3. Enable the missing permissions for the bot role")
            print("   4. Or invite the bot with proper permissions using OAuth2")
            
        # Test sending a message
        try:
            test_embed = discord.Embed(
                title="🔧 Permission Test",
                description="This is a test message to verify bot permissions.",
                color=0x00ff00
            )
            test_embed.add_field(name="Status", value="✅ Permissions working!", inline=False)
            test_embed.add_field(name="Channel", value=f"#{channel.name}", inline=True)
            test_embed.add_field(name="Guild", value=channel.guild.name, inline=True)
            
            await channel.send(embed=test_embed)
            print("\n✅ Successfully sent test message!")
            print("   The bot is ready to send notifications.")
            
        except discord.Forbidden:
            print("\n❌ Failed to send test message!")
            print("   The bot lacks permission to send messages in this channel.")
        except Exception as e:
            print(f"\n❌ Error sending test message: {e}")
            
        await self.bot.close()

async def main():
    """Main function"""
    checker = DiscordPermissionChecker()
    if checker.token and checker.channel_id:
        checker.bot.event(checker.on_ready)
        await checker.check_permissions()
    else:
        print("❌ Missing required environment variables")
        print("   Please check your .env file")

if __name__ == "__main__":
    asyncio.run(main()) 
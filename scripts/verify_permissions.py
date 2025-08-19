#!/usr/bin/env python3
"""
Verify Discord permissions required by the bot.

Checks:
- Bot can log in and is a member of the target guild
- Guild-level permissions: Manage Channels (for auto-create), View Channel, Send Messages, Embed Links, Read Message History
- Notification channel permissions (if exists)
- Event channel permissions (if exists): also checks that @everyone cannot view the channel

Environment variables used:
- DISCORD_TOKEN
- DISCORD_GUILD_ID
- NOTIFICATION_CHANNEL_NAME (default: notification)
- EVENT_CHANNEL_NAME (default: event)
"""

import asyncio
import logging
import os
import sys
from typing import List

import discord
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _bool_to_symbol(value: bool) -> str:
    return '✅' if value else '❌'


async def verify():
    load_dotenv()

    token = os.getenv('DISCORD_TOKEN', '').strip()
    guild_id_str = os.getenv('DISCORD_GUILD_ID', '').strip()
    notification_channel_name = os.getenv('NOTIFICATION_CHANNEL_NAME', 'notification').strip()
    event_channel_name = os.getenv('EVENT_CHANNEL_NAME', 'event').strip()

    if not token:
        logger.error('DISCORD_TOKEN is not set')
        return 2
    if not guild_id_str or not guild_id_str.isdigit():
        logger.error('DISCORD_GUILD_ID is not set or invalid')
        return 2
    guild_id = int(guild_id_str)

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    result_code = 0

    @client.event
    async def on_ready():
        nonlocal result_code
        try:
            logger.info('Logged in as %s', client.user)

            guild = client.get_guild(guild_id)
            if not guild:
                logger.error('Guild with ID %s not found or bot is not a member', guild_id)
                result_code = 2
                await client.close()
                return

            bot_member = guild.get_member(client.user.id if client.user else 0)
            if not bot_member:
                logger.error('Bot is not a member of the guild')
                result_code = 2
                await client.close()
                return

            logger.info('Guild: %s (%s)', guild.name, guild.id)
            logger.info('Bot roles: %s', [r.name for r in bot_member.roles])

            # Required permissions
            required_guild_perms = [
                ('manage_channels', 'Manage Channels'),
                ('view_channel', 'View Channels'),
                ('send_messages', 'Send Messages'),
                ('embed_links', 'Embed Links'),
                ('read_message_history', 'Read Message History'),
            ]

            gp = bot_member.guild_permissions
            logger.info('Guild permissions check:')
            missing_guild_perms: List[str] = []
            for attr, label in required_guild_perms:
                has = getattr(gp, attr, False)
                logger.info('  %s %s', _bool_to_symbol(has), label)
                if not has:
                    missing_guild_perms.append(label)

            if missing_guild_perms:
                result_code = 1
                logger.warning('Missing guild permissions: %s', ', '.join(missing_guild_perms))

            # Channels
            def report_channel_perms(ch: discord.TextChannel, title: str, check_private: bool = False):
                nonlocal result_code
                perms = ch.permissions_for(bot_member)
                logger.info('%s #%s (%s)', title, ch.name, ch.id)
                ok_view = perms.view_channel
                ok_send = perms.send_messages
                ok_embed = perms.embed_links
                ok_read = perms.read_message_history
                logger.info('  %s View Channel', _bool_to_symbol(ok_view))
                logger.info('  %s Send Messages', _bool_to_symbol(ok_send))
                logger.info('  %s Embed Links', _bool_to_symbol(ok_embed))
                logger.info('  %s Read Message History', _bool_to_symbol(ok_read))
                if not (ok_view and ok_send and ok_embed and ok_read):
                    result_code = 1
                    logger.warning('  Missing one or more permissions in channel %s', ch.name)
                if check_private:
                    everyone_ow = ch.overwrites_for(guild.default_role)
                    private_ok = (everyone_ow.view_channel is False)
                    logger.info('  %s Private (everyone cannot view)', _bool_to_symbol(private_ok))
                    if not private_ok:
                        result_code = 1
                        logger.warning('  Channel %s is not private to @everyone', ch.name)

            notification_channel = discord.utils.get(guild.text_channels, name=notification_channel_name)
            if notification_channel:
                report_channel_perms(notification_channel, 'Notification channel')
            else:
                logger.warning("Notification channel '%s' not found", notification_channel_name)
                if not gp.manage_channels:
                    result_code = 1
                    logger.warning('Missing Manage Channels to auto-create notification channel')

            event_channel = discord.utils.get(guild.text_channels, name=event_channel_name)
            if event_channel:
                report_channel_perms(event_channel, 'Event channel', check_private=True)
            else:
                logger.warning("Event channel '%s' not found", event_channel_name)
                if not gp.manage_channels:
                    result_code = 1
                    logger.warning('Missing Manage Channels to auto-create event channel')

        finally:
            await client.close()

    try:
        async with client:
            await client.start(token)
    except Exception as e:
        logger.error('Failed to start client: %s', e)
        return 2

    return result_code


if __name__ == '__main__':
    exit_code = asyncio.run(verify())
    sys.exit(exit_code)



#!/usr/bin/env python3
"""
Clear all slash (application) commands for the current Discord bot application.

This script will:
- Clear guild-specific commands if DISCORD_GUILD_ID is set
- Clear global commands

Requirements:
- DISCORD_TOKEN must be set (e.g., via .env)
- Optionally DISCORD_GUILD_ID to also clear guild commands

Run:
  python scripts/clear_slash_commands.py
"""

import asyncio
import logging
import os
from typing import Optional, Iterable, Set

import discord
from discord.ext import commands
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CleanerBot(commands.Bot):
    def __init__(self, *, token: str, guild_ids: Set[int]):
        intents = discord.Intents.none()
        super().__init__(command_prefix="!", intents=intents)
        self._token = token
        self._guild_ids = guild_ids

    async def _get_application_id(self) -> int:
        # application_id may be None until ready; fetch if needed
        if self.application_id:
            return int(self.application_id)
        app = await self.application_info()
        return app.id

    async def _clear_guild(self, guild_id: int) -> None:
        guild_obj = discord.Object(id=guild_id)
        try:
            before = await self.tree.fetch_commands(guild=guild_obj)
            logger.info(f"Guild {guild_id}: commands before: {len(before)}")
        except Exception as e:
            logger.warning(f"Guild {guild_id}: failed to fetch before-list: {e}")

        try:
            logger.info(f"Guild {guild_id}: clearing via CommandTree.sync(empty)")
            self.tree.clear_commands(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
        except Exception as e:
            logger.warning(f"Guild {guild_id}: CommandTree sync clear failed: {e}")

        # Extra assurance: use HTTP bulk upsert to empty list
        try:
            app_id = await self._get_application_id()
            await self.http.bulk_upsert_guild_commands(app_id, guild_id, [])
            logger.info(f"Guild {guild_id}: HTTP bulk upsert to empty succeeded")
        except Exception as e:
            logger.warning(f"Guild {guild_id}: HTTP bulk clear failed: {e}")

        try:
            after = await self.tree.fetch_commands(guild=guild_obj)
            logger.info(f"Guild {guild_id}: commands after: {len(after)} (propagation may take a few minutes)")
        except Exception as e:
            logger.warning(f"Guild {guild_id}: failed to fetch after-list: {e}")

    async def _clear_global(self) -> None:
        try:
            before = await self.tree.fetch_commands()
            logger.info(f"Global: commands before: {len(before)}")
        except Exception as e:
            logger.warning(f"Global: failed to fetch before-list: {e}")

        try:
            logger.info("Global: clearing via CommandTree.sync(empty)")
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
        except Exception as e:
            logger.warning(f"Global: CommandTree sync clear failed: {e}")

        try:
            app_id = await self._get_application_id()
            await self.http.bulk_upsert_global_commands(app_id, [])
            logger.info("Global: HTTP bulk upsert to empty succeeded")
        except Exception as e:
            logger.warning(f"Global: HTTP bulk clear failed: {e}")

        try:
            after = await self.tree.fetch_commands()
            logger.info(f"Global: commands after: {len(after)} (global propagation can take up to 1 hour)")
        except Exception as e:
            logger.warning(f"Global: failed to fetch after-list: {e}")

    async def setup_hook(self) -> None:
        # If requested, discover all guilds via REST to clear per-guild commands
        if not self._guild_ids:
            logger.info("No explicit guild IDs provided; skipping per-guild clear")
        else:
            for gid in sorted(self._guild_ids):
                await self._clear_guild(gid)

        await self._clear_global()
        await self.close()


async def main() -> int:
    load_dotenv()
    token = os.getenv('DISCORD_TOKEN', '').strip()
    guild_id_env = os.getenv('DISCORD_GUILD_ID', '').strip()
    extra_guild_ids_env = os.getenv('EXTRA_GUILD_IDS', '').strip()
    clear_all_guilds = os.getenv('CLEAR_ALL_GUILDS', 'false').strip().lower() == 'true'

    explicit_guild_ids: Set[int] = set()
    if guild_id_env.isdigit():
        explicit_guild_ids.add(int(guild_id_env))
    if extra_guild_ids_env:
        for part in extra_guild_ids_env.split(','):
            part = part.strip()
            if part.isdigit():
                explicit_guild_ids.add(int(part))

    if not token:
        logger.error("DISCORD_TOKEN is not set")
        return 2

    # If CLEAR_ALL_GUILDS, fetch all guilds via REST and add them to the clear list
    if clear_all_guilds:
        # Temporary client to fetch guilds list
        intents = discord.Intents.none()
        tmp_client = discord.Client(intents=intents)
        try:
            async with tmp_client:
                await tmp_client.start(token)
        except Exception as e:
            logger.warning(f"Could not pre-fetch guilds list (will clear globals only): {e}")
        else:
            try:
                fetched: Set[int] = set()
                async for g in tmp_client.fetch_guilds(limit=None):
                    fetched.add(g.id)
                explicit_guild_ids |= fetched
                logger.info(f"CLEAR_ALL_GUILDS: will clear {len(fetched)} guild(s)")
            except Exception as e:
                logger.warning(f"Failed to enumerate guilds: {e}")
        finally:
            try:
                await tmp_client.close()
            except Exception:
                pass

    bot = CleanerBot(token=token, guild_ids=explicit_guild_ids)
    try:
        await bot.start(token)
        return 0
    except Exception as e:
        logger.error(f"Failed to start cleaner bot: {e}")
        return 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))



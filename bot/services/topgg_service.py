"""
top.gg vote integration.

This used to rely on a topgg.WebhookManager listening on a locally
exposed HTTP port, which meant the bot had to be reachable from the
public internet (reverse proxy / port forward / tunnel) for top.gg to
be able to POST vote events to it.

Instead, this module uses topgg.DBLClient to poll the top.gg API on a
timer and credit votes itself - no inbound webhook, no open port, no
public URL required. The bot fully "handles itself".
"""

import logging
from datetime import datetime, timedelta, timezone

import topgg
from discord.ext import tasks

from bot.config import TOPGG_TOKEN
from bot.database.models.user_model import UserProfile
from bot.database.session import SessionLocal
from bot.services.update_user import add_vote

logger = logging.getLogger(__name__)

# How often to ask top.gg whether anyone has voted.
VOTE_CHECK_INTERVAL_MINUTES = 5

# How long a top.gg vote stays "active" (top.gg's own vote cooldown).
VOTE_COOLDOWN_HOURS = 12


def _known_user_ids():
    """
    Returns {discord_id: last_voted_datetime_or_None} for every user
    profile we've ever created. These are the only users worth polling
    top.gg about - anyone else has never interacted with the bot.
    """
    db = SessionLocal()
    try:
        rows = db.query(UserProfile.discord_id, UserProfile.last_voted).all()
    finally:
        db.close()

    latest = {}
    for discord_id, last_voted in rows:
        current = latest.get(discord_id)
        if current is None or (last_voted is not None and (current is None or last_voted > current)):
            latest[discord_id] = last_voted
    return latest


class TopggService:
    """
    Owns the connection to top.gg and the background task that checks
    for new votes. Created once in MyClient.setup_hook.
    """

    def __init__(self, bot):
        self.bot = bot
        self.client = topgg.DBLClient(bot, TOPGG_TOKEN)
        # Keep a handle on the bot so other cogs/services can reach the
        # top.gg client directly if needed (e.g. bot.topgg_client.get_bot_info()).
        self.bot.topgg_client = self.client

    def start(self):
        if not TOPGG_TOKEN:
            print("TOPGG_TOKEN is not set - skipping top.gg vote polling.")
            return
        if not self.check_votes.is_running():
            self.check_votes.start()

    def stop(self):
        if self.check_votes.is_running():
            self.check_votes.cancel()

    @tasks.loop(minutes=VOTE_CHECK_INTERVAL_MINUTES)
    async def check_votes(self):
        now = datetime.now(timezone.utc)

        for discord_id, last_voted in _known_user_ids().items():
            if last_voted is not None:
                if last_voted.tzinfo is None:
                    last_voted = last_voted.replace(tzinfo=timezone.utc)
                # Already credited for the current 12h vote window.
                if now - last_voted < timedelta(hours=VOTE_COOLDOWN_HOURS):
                    continue

            try:
                has_voted = await self.client.get_user_vote(int(discord_id))
            except Exception as exc:
                print(f"top.gg vote check failed for user {discord_id}: {exc}")
                continue

            if has_voted:
                await add_vote(discord_id)
                print(f"Vote credited for user {discord_id} (via top.gg poll)")

    @check_votes.before_loop
    async def _before_check_votes(self):
        await self.bot.wait_until_ready()


async def setup_topgg(bot):
    """
    Call once from setup_hook. Starts the self-contained vote polling
    loop and returns the TopggService instance (also stashed on the bot
    as bot.topgg_service).
    """
    service = TopggService(bot)
    service.start()
    return service

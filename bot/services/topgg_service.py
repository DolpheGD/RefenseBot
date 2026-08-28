"""
top.gg vote integration.

This used to rely on a topgg.WebhookManager listening on a locally
exposed HTTP port, which meant the bot had to be reachable from the
public internet (reverse proxy / port forward / tunnel) for top.gg to
be able to POST vote events to it.

Instead, this module uses topgg.DBLClient to poll the top.gg API on a
timer and credit votes itself - no inbound webhook, no open port, no
public URL required. The bot fully "handles itself".

Polling strategy (two steps, to stay well under top.gg's rate limits):
  1. One bulk call, get_bot_votes(), which returns everyone who shows up
     in top.gg's recent-votes log for this bot. This costs a single
     request no matter how many members the bot has.
  2. Only for the (usually tiny) overlap between that list and users we
     actually track who are out of their 12h credit cooldown, we make a
     precise per-user get_user_vote() call - this is the endpoint that
     actually answers "did they vote in the last 12 hours", and it's
     cheap because step 1 already filtered out everyone else.

Checking every known user individually (no step 1) is what used to blow
through top.gg's ~60-requests/minute bot rate limit and log a wall of
404 "User not found" errors for ordinary members who've never touched
top.gg at all.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import topgg
from discord.ext import tasks
from topgg import errors as topgg_errors

from bot.config import TOPGG_TOKEN
from bot.database.models.user_model import UserProfile
from bot.database.session import SessionLocal
from bot.services.update_user import add_vote

logger = logging.getLogger(__name__)

# How often to ask top.gg whether anyone has voted.
VOTE_CHECK_INTERVAL_MINUTES = 5

# How long a top.gg vote stays "active" (top.gg's own vote cooldown).
VOTE_COOLDOWN_HOURS = 12

# Small delay between individual get_user_vote calls, just to avoid
# bursting the per-bot rate limit even further.
PER_USER_CHECK_DELAY_SECONDS = 1.0


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


def _still_in_cooldown(last_voted, now):
    if last_voted is None:
        return False
    if last_voted.tzinfo is None:
        last_voted = last_voted.replace(tzinfo=timezone.utc)
    return now - last_voted < timedelta(hours=VOTE_COOLDOWN_HOURS)


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
        # Step 1: one cheap bulk call to find out who's voted recently at all.
        try:
            recent_voters = await self.client.get_bot_votes()
        except topgg_errors.HTTPException as exc:
            print(f"top.gg get_bot_votes failed, will retry next cycle: {exc}")
            return
        except Exception as exc:
            print(f"top.gg get_bot_votes failed, will retry next cycle: {exc}")
            return

        recent_voter_ids = {str(voter["id"]) for voter in recent_voters}
        if not recent_voter_ids:
            return

        known_users = _known_user_ids()
        now = datetime.now(timezone.utc)

        # Only bother with users we actually track, who showed up in the
        # recent-votes list, and who aren't already credited for this
        # 12h window.
        candidates = [
            discord_id
            for discord_id in recent_voter_ids
            if discord_id in known_users
            and not _still_in_cooldown(known_users[discord_id], now)
        ]

        for discord_id in candidates:
            try:
                has_voted = await self.client.get_user_vote(int(discord_id))
            except topgg_errors.NotFound:
                # No top.gg vote record for this user (shouldn't normally
                # happen since they were just in the recent-votes list).
                continue
            except Exception as exc:
                print(f"top.gg vote check failed for user {discord_id}: {exc}")
                continue

            if has_voted:
                await add_vote(discord_id)
                print(f"Vote credited for user {discord_id} (via top.gg poll)")

            await asyncio.sleep(PER_USER_CHECK_DELAY_SECONDS)

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

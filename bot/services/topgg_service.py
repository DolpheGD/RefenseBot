"""
top.gg vote integration.

History of this module, for context:
  1. Originally used topgg.WebhookManager, which needed a public HTTP
     port for top.gg to POST vote events to.
  2. Replaced with topggpy's DBLClient, polling the old v0 REST API
     (https://top.gg/api/bots/{id}/...). That looked like it worked (no
     exceptions most of the time) but silently returned nothing useful:
     top.gg has since moved to a new v1 API (https://top.gg/api/v1) with
     a different auth scheme, and topggpy (last released in 2021) was
     never updated for it. Votes were never actually being detected.
  3. This version talks to the v1 API directly over aiohttp - no
     third-party top.gg library, no webhook, no open port.

IMPORTANT: v1 requires a v1-style API token and sends it as
"Authorization: Bearer <token>". A token generated a while ago (back
when this bot only had a webhook secret) may be a legacy v0-only token,
which v1 will reject. Generate/confirm a fresh token from your project's
"Integrations & API" settings on top.gg and put it in TOPGG_TOKEN.

API reference: https://docs.top.gg/api/v1/votes
  GET /projects/@me/votes  - cursor-paginated vote history, newest first,
                              filtered by a required startDate on the
                              first page.
      -> {"cursor": "...", "data": [{"platform_id": "<discord id>",
                                      "created_at": "...", ...}, ...]}
"""

import logging
from datetime import datetime, timedelta, timezone

import aiohttp
from discord.ext import tasks

from bot.config import TOPGG_TOKEN
from bot.database.models.user_model import UserProfile
from bot.database.session import SessionLocal
from bot.services.update_user import add_vote

logger = logging.getLogger(__name__)

# How often to ask top.gg for recent votes.
VOTE_CHECK_INTERVAL_MINUTES = 5

# How far back to look every poll. This is just a downtime-safety margin
# (e.g. the bot being offline for a while) - actual "is this vote new"
# dedup is done per-user against last_voted in the database, not this
# window, so it's safe to make this generous.
LOOKBACK_HOURS = 48

# Hard cap on pagination per poll, just so a bug/huge vote history can't
# turn this into an infinite loop.
MAX_PAGES_PER_POLL = 20

TOPGG_API_BASE = "https://top.gg/api/v1"


def _known_user_ids():
    """
    Returns {discord_id: last_voted_datetime_or_None} for every user
    profile we've ever created. Only these users are worth crediting -
    anyone else has never interacted with the bot.
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


def _parse_iso8601(value):
    if not value:
        return None
    # Python's fromisoformat doesn't accept a trailing "Z" before 3.11.
    value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class TopggV1Client:
    """Minimal client for the parts of top.gg's v1 API this bot needs."""

    def __init__(self, token: str):
        self._token = token
        self._session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def get_recent_votes(self, start_date: datetime, max_pages: int = MAX_PAGES_PER_POLL):
        """
        Returns every vote entry from /projects/@me/votes with
        created_at >= start_date, following pagination.
        """
        session = await self._get_session()
        headers = {"Authorization": f"Bearer {self._token}"}
        start_iso = start_date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        votes = []
        cursor = None

        for _ in range(max_pages):
            params = {"startDate": start_iso}
            if cursor:
                params["cursor"] = cursor

            async with session.get(
                f"{TOPGG_API_BASE}/projects/@me/votes",
                headers=headers,
                params=params,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(
                        f"top.gg API returned {resp.status} for /projects/@me/votes: {text}"
                    )
                payload = await resp.json()

            page = payload.get("data") or []
            votes.extend(page)

            cursor = payload.get("cursor")
            if not cursor or not page:
                break

        return votes


class TopggService:
    """
    Owns the connection to top.gg and the background task that checks
    for new votes. Created once in MyClient.setup_hook.
    """

    def __init__(self, bot):
        self.bot = bot
        self.client = TopggV1Client(TOPGG_TOKEN)

    def start(self):
        if not TOPGG_TOKEN:
            print("TOPGG_TOKEN is not set - skipping top.gg vote polling.")
            return
        if not self.check_votes.is_running():
            self.check_votes.start()

    async def stop(self):
        if self.check_votes.is_running():
            self.check_votes.cancel()
        await self.client.close()

    @tasks.loop(minutes=VOTE_CHECK_INTERVAL_MINUTES)
    async def check_votes(self):
        start_date = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

        try:
            votes = await self.client.get_recent_votes(start_date)
        except Exception as exc:
            print(f"top.gg vote poll failed, will retry next cycle: {exc}")
            return

        if not votes:
            return

        # Collapse to the most recent vote timestamp per Discord user id.
        latest_vote_at = {}
        for entry in votes:
            discord_id = entry.get("platform_id")
            voted_at = _parse_iso8601(entry.get("created_at"))
            if not discord_id or voted_at is None:
                continue
            discord_id = str(discord_id)
            if discord_id not in latest_vote_at or voted_at > latest_vote_at[discord_id]:
                latest_vote_at[discord_id] = voted_at

        known_users = _known_user_ids()

        for discord_id, voted_at in latest_vote_at.items():
            if discord_id not in known_users:
                # top.gg voter we've never seen chat/interact in a server we track.
                continue

            last_voted = known_users[discord_id]
            if last_voted is not None:
                if last_voted.tzinfo is None:
                    last_voted = last_voted.replace(tzinfo=timezone.utc)
                if voted_at <= last_voted:
                    # Already credited for this vote (or a newer one).
                    continue

            await add_vote(discord_id)
            print(f"Vote credited for user {discord_id} (voted at {voted_at.isoformat()})")

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

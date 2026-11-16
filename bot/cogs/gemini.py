import asyncio
import logging
from typing import Any

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from bot.config import GEMINI_API_KEY

logger = logging.getLogger("refensebot.gemini")

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)
MAX_PROMPT_LENGTH = 4_000
MAX_DISCORD_MESSAGE_LENGTH = 1_900


class GeminiAPIError(Exception):
    def __init__(self, message: str, user_message: str):
        super().__init__(message)
        self.user_message = user_message


def _extract_response_text(data: Any) -> str:
    if not isinstance(data, dict):
        raise GeminiAPIError(
            "Gemini returned a non-object response.",
            "Gemini returned an invalid response. Please try again later.",
        )

    prompt_feedback = data.get("promptFeedback")
    if isinstance(prompt_feedback, dict) and prompt_feedback.get("blockReason"):
        reason = prompt_feedback["blockReason"]
        raise GeminiAPIError(
            f"Gemini blocked the prompt: {reason}.",
            "Gemini blocked this prompt. Please revise it and try again.",
        )

    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GeminiAPIError(
            "Gemini returned no candidates.",
            "Gemini did not return a response. Please try again with a different prompt.",
        )

    candidate = candidates[0]
    if not isinstance(candidate, dict):
        raise GeminiAPIError(
            "Gemini returned a malformed candidate.",
            "Gemini returned an invalid response. Please try again later.",
        )

    finish_reason = candidate.get("finishReason")
    if finish_reason is not None and not isinstance(finish_reason, str):
        raise GeminiAPIError(
            "Gemini returned a malformed finish reason.",
            "Gemini returned an invalid response. Please try again later.",
        )
    if finish_reason in {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII"}:
        raise GeminiAPIError(
            f"Gemini blocked the response: {finish_reason}.",
            "Gemini could not provide a response to that prompt. Please try rephrasing it.",
        )

    content = candidate.get("content")
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        raise GeminiAPIError(
            "Gemini response candidate did not contain text parts.",
            "Gemini did not return a text response. Please try again with a different prompt.",
        )

    response = "\n".join(
        part["text"]
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    ).strip()

    if not response:
        raise GeminiAPIError(
            "Gemini returned an empty text candidate.",
            "Gemini returned an empty response. Please try a different prompt.",
        )
    if finish_reason == "MAX_TOKENS":
        response += "\n\n[Response may be incomplete: Gemini reached its output limit.]"
    return response


async def _generate_response(prompt: str) -> str:
    timeout = aiohttp.ClientTimeout(total=45)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            GEMINI_API_URL,
            headers={"x-goog-api-key": GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 1_024},
            },
        ) as response:
            if response.status >= 400:
                logger.error("Gemini API returned HTTP %s.", response.status)
                if response.status == 429:
                    message = "Gemini's free-tier rate limit was reached. Please try again later."
                elif response.status in (401, 403):
                    message = "Gemini rejected the API key. Check GEMINI_API_KEY in the bot configuration."
                elif response.status == 400:
                    message = "Gemini rejected the request. Please revise your prompt and try again."
                elif response.status == 404:
                    message = "The configured Gemini model is unavailable. Contact the bot administrator."
                else:
                    message = "Gemini could not process the request. Please try again later."
                raise GeminiAPIError(
                    f"Gemini API returned HTTP {response.status}.",
                    message,
                )

            try:
                data = await response.json()
            except (aiohttp.ContentTypeError, ValueError) as exc:
                logger.error(
                    "Gemini API returned invalid JSON (%s).",
                    type(exc).__name__,
                )
                raise GeminiAPIError(
                    "Gemini API returned invalid JSON.",
                    "Gemini returned an invalid response. Please try again later.",
                ) from exc

    return _extract_response_text(data)


def _split_response(text: str) -> list[str]:
    return [
        text[start : start + MAX_DISCORD_MESSAGE_LENGTH]
        for start in range(0, len(text), MAX_DISCORD_MESSAGE_LENGTH)
    ]


async def _send_private_error(
    interaction: discord.Interaction,
    message: str,
) -> None:
    try:
        await interaction.followup.send(message, ephemeral=True)
    except discord.HTTPException as exc:
        logger.warning("Could not deliver Gemini error message to Discord: %s", exc)


class Gemini(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="gemini",
        description="Prompt Gemini Flash",
    )
    @app_commands.describe(prompt="Your prompt for Gemini (up to 4000 characters)")
    async def gemini(self, interaction: discord.Interaction, prompt: str):
        prompt = prompt.strip()
        if not prompt:
            await interaction.response.send_message(
                "Please provide a prompt.",
                ephemeral=True,
            )
            return
        if len(prompt) > MAX_PROMPT_LENGTH:
            await interaction.response.send_message(
                f"Prompts must be {MAX_PROMPT_LENGTH:,} characters or fewer.",
                ephemeral=True,
            )
            return
        if not GEMINI_API_KEY:
            await interaction.response.send_message(
                "Gemini is not configured. Set GEMINI_API_KEY in the bot environment.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            result = await _generate_response(prompt)
        except GeminiAPIError as exc:
            await _send_private_error(interaction, exc.user_message)
            return
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            logger.warning("Gemini request failed: %s", exc)
            await _send_private_error(
                interaction,
                "Could not connect to Gemini. Please try again later.",
            )
            return

        try:
            for part in _split_response(result):
                await interaction.followup.send(
                    part,
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
        except discord.HTTPException as exc:
            logger.warning("Could not deliver Gemini's response to Discord: %s", exc)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gemini(bot))

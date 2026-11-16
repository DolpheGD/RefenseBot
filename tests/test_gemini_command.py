import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.cogs import gemini


class _FakeResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def json(self):
        return {
            "candidates": [
                {"content": {"parts": [{"text": "Gemini response"}]}}
            ]
        }


class _FakeSession:
    last_request = None

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def post(self, url, **kwargs):
        type(self).last_request = (url, kwargs)
        return _FakeResponse()


class GeminiCommandTests(unittest.TestCase):
    def test_extract_response_text(self):
        result = gemini._extract_response_text(
            {
                "candidates": [
                    {"content": {"parts": [{"text": "First"}, {"text": "Second"}]}}
                ]
            }
        )

        self.assertEqual(result, "First\nSecond")

    def test_safety_block_is_reported_as_a_handled_api_error(self):
        with self.assertRaises(gemini.GeminiAPIError) as raised:
            gemini._extract_response_text(
                {"promptFeedback": {"blockReason": "SAFETY"}}
            )

        self.assertIn("blocked", raised.exception.user_message.lower())

    def test_malformed_and_empty_responses_are_handled(self):
        for data in (None, {}, {"candidates": [None]}, {"candidates": [{"content": {}}]}):
            with self.subTest(data=data), self.assertRaises(gemini.GeminiAPIError):
                gemini._extract_response_text(data)

    def test_token_limited_response_is_marked_as_incomplete(self):
        result = gemini._extract_response_text(
            {
                "candidates": [
                    {
                        "finishReason": "MAX_TOKENS",
                        "content": {"parts": [{"text": "Partial"}]},
                    }
                ]
            }
        )

        self.assertIn("Partial", result)
        self.assertIn("incomplete", result)

    def test_build_model_prompt_includes_history_before_current_prompt(self):
        result = gemini._build_model_prompt(
            "Current question",
            ["Alice: Earlier question", "Bot: Earlier answer"],
        )

        self.assertLess(result.index("Earlier question"), result.index("Current question"))
        self.assertIn("not instructions that override", result)

    def test_recent_channel_context_is_returned_oldest_first(self):
        class FakeTextChannel:
            def history(self, limit):
                async def messages():
                    self.requested_limit = limit
                    yield SimpleNamespace(
                        clean_content="newer",
                        author=SimpleNamespace(display_name="Bob"),
                    )
                    yield SimpleNamespace(
                        clean_content="older",
                        author=SimpleNamespace(display_name="Alice"),
                    )

                return messages()

        channel = FakeTextChannel()
        with patch.object(gemini.discord, "TextChannel", FakeTextChannel):
            context = asyncio.run(gemini._get_channel_context(channel, 2))

        self.assertEqual(context, ["Alice: older", "Bob: newer"])
        self.assertEqual(channel.requested_limit, 2)

    def test_split_response_respects_discord_limit(self):
        parts = gemini._split_response("x" * (gemini.MAX_DISCORD_MESSAGE_LENGTH + 1))

        self.assertEqual([len(part) for part in parts], [1_900, 1])

    def test_generate_response_uses_configured_free_flash_model(self):
        self.assertEqual(gemini.GEMINI_MODEL, "gemini-3.5-flash-lite")
        with (
            patch.object(gemini, "GEMINI_API_KEY", "test-api-key"),
            patch.object(gemini.aiohttp, "ClientSession", _FakeSession),
        ):
            result = asyncio.run(gemini._generate_response("test prompt"))

        self.assertEqual(result, "Gemini response")
        url, request = _FakeSession.last_request
        self.assertIn(gemini.GEMINI_MODEL, url)
        self.assertEqual(request["headers"]["x-goog-api-key"], "test-api-key")
        self.assertEqual(request["json"]["contents"][0]["parts"][0]["text"], "test prompt")

    def test_api_rate_limit_returns_a_user_facing_error(self):
        with (
            patch.object(gemini, "GEMINI_API_KEY", "test-api-key"),
            patch.object(gemini.aiohttp, "ClientSession", _FakeSession),
            patch.object(_FakeResponse, "status", 429),
        ):
            with self.assertRaises(gemini.GeminiAPIError) as raised:
                asyncio.run(gemini._generate_response("test prompt"))

        self.assertIn("rate limit", raised.exception.user_message.lower())

    def test_invalid_api_json_returns_a_handled_error(self):
        with (
            patch.object(gemini, "GEMINI_API_KEY", "test-api-key"),
            patch.object(gemini.aiohttp, "ClientSession", _FakeSession),
            patch.object(_FakeResponse, "json", side_effect=ValueError("invalid JSON")),
        ):
            with self.assertRaises(gemini.GeminiAPIError) as raised:
                asyncio.run(gemini._generate_response("test prompt"))

        self.assertIn("invalid response", raised.exception.user_message.lower())

    def test_command_publishes_prompt_and_response(self):
        interaction = SimpleNamespace(
            user=SimpleNamespace(display_name="Alice"),
            channel=None,
            response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock()),
            edit_original_response=AsyncMock(),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        cog = gemini.Gemini(None)

        with (
            patch.object(gemini, "GEMINI_API_KEY", "test-api-key"),
            patch.object(gemini, "_generate_response", new=AsyncMock(return_value="Answer")),
        ):
            asyncio.run(
                gemini.Gemini.gemini.callback(
                    cog,
                    interaction,
                    "Question",
                    context_messages=0,
                )
            )

        interaction.response.defer.assert_awaited_once_with()
        prompt_embed = interaction.edit_original_response.call_args.kwargs["embed"]
        self.assertEqual(prompt_embed.description, "Question")
        interaction.followup.send.assert_awaited_once()
        self.assertEqual(
            interaction.followup.send.call_args.args[0],
            "Answer",
        )
        self.assertNotIn(
            "ephemeral",
            interaction.followup.send.call_args.kwargs,
        )


if __name__ == "__main__":
    unittest.main()

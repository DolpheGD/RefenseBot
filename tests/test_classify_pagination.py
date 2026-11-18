import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bot.utils import embedder


class ClassifyPaginationTests(unittest.IsolatedAsyncioTestCase):
    async def test_requested_messages_are_split_into_ten_message_pages(self):
        messages = [
            SimpleNamespace(content=f"Message {number}", danger_score=0.1)
            for number in range(1, 12)
        ]
        user = SimpleNamespace(
            id=123,
            guild=SimpleNamespace(),
            display_name="Test User",
            avatar=None,
        )

        with (
            patch.object(
                embedder,
                "get_top_ten_and_avg",
                new=AsyncMock(return_value=(messages, 0.5)),
            ),
            patch.object(embedder, "get_total_messages", new=AsyncMock(return_value=11)),
            patch.object(embedder, "get_vote_count", new=AsyncMock(return_value=(0, 0))),
            patch.object(embedder, "get_is_banned", new=AsyncMock(return_value=False)),
        ):
            first_embed, view = await embedder.classify_user_with_output(
                user,
                message_limit=11,
            )

        self.assertIsNotNone(view)
        self.assertEqual(len(first_embed.fields), 10)
        self.assertEqual(first_embed.fields[0].name, "1. Message 1")
        self.assertEqual(first_embed.footer.text, "Page 1/2")
        self.assertEqual(len(view.embeds[1].fields), 1)
        self.assertEqual(view.embeds[1].fields[0].name, "11. Message 11")
        self.assertEqual(view.embeds[1].footer.text, "Page 2/2")

    async def test_single_page_does_not_add_pagination_controls(self):
        messages = [SimpleNamespace(content="Message 1", danger_score=0.1)]
        user = SimpleNamespace(
            id=123,
            guild=SimpleNamespace(),
            display_name="Test User",
            avatar=None,
        )

        with (
            patch.object(
                embedder,
                "get_top_ten_and_avg",
                new=AsyncMock(return_value=(messages, 0.5)),
            ),
            patch.object(embedder, "get_total_messages", new=AsyncMock(return_value=1)),
            patch.object(embedder, "get_vote_count", new=AsyncMock(return_value=(0, 0))),
            patch.object(embedder, "get_is_banned", new=AsyncMock(return_value=False)),
        ):
            embed, view = await embedder.classify_user_with_output(
                user,
                message_limit=1,
            )

        self.assertEqual(len(embed.fields), 1)
        self.assertIsNone(view)


if __name__ == "__main__":
    unittest.main()

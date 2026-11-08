import discord
import logging

from bot.ml.classifier import classify_danger_level
from bot.ml.image_classifier import classify_image

logger = logging.getLogger("refensebot.classifier")


async def classify_message_and_image(content: str, message_id: str = "", attachments: list[discord.Attachment] | None = None):
    """
    Classify the message text and any image attachments, keeping the most dangerous signal.
    Returns scores, content and is_image.
    """
    if attachments is None:
        attachments = []

    message_text = str(content or "")
    scores = await classify_danger_level(message_text)
    is_image = False

    for attachment in attachments:
        if attachment is None:
            continue
        if attachment.content_type and not attachment.content_type.startswith("image/"):
            continue

        try:
            result = await classify_image(attachment)
        except Exception:
            logger.exception("Image classification failed for message %s", message_id)
            continue

        if result.get("Danger", 0.0) > scores.get("Danger", 0.0):
            scores["Danger"] = result["Danger"]
            scores["Sexual"] = result["Sexual"]
            scores["Hate"] = result["Hate"]
            scores["Concern"] = result["Concern"]
            scores["Scam"] = result["Scam"]
            is_image = True

    if is_image:
        message_text = f"[Image Attachment: {message_id}]"

    return scores, message_text, is_image
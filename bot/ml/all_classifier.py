import discord

from bot.ml.classifier import classify_danger_level
from bot.ml.image_classifier import classify_image


async def classify_message_and_image(content: str, message_id: str = "", attachments: list[discord.Attachment] = []):
    """
    classifies image and message, determines which one is priority to store
    returns scores, content and is_image
    """
    # classify message
    # the bigger danger score is from the image. We only keep track of the max of either the text or the image, not both. This is to avoid double counting.
    scores = await classify_danger_level(content)

    is_image = False
    for attachment in attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            result = await classify_image(attachment)
            if result["Danger"] > scores["Danger"]: #update new scores if the image is more dangerous than the text
                scores["Danger"] = result["Danger"]
                scores["Sexual"] = result["Sexual"]
                scores["Hate"] = result["Hate"]
                scores["Concern"] = result["Concern"]
                scores["Scam"] = result["Scam"]
                is_image = True
    
    if is_image: 
        content = f"[Image Attachment: {message_id}]"

    return scores, content, is_image
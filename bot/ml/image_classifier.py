import asyncio
import io
import logging

import numpy as np
from PIL import Image

from bot.config import HF_TOKEN
from bot.ml.classifier import classify_danger_level

logger = logging.getLogger("refensebot.image_classifier")

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 4_000_000

_IMAGE_CLASSIFIER = None
_OCR_READER = None
_IMAGE_CLASSIFICATION_LOCK = asyncio.Lock()


def _empty_scores():
    return {"Hate": 0.0, "Sexual": 0.0, "Concern": 0.0, "Danger": 0.0, "Scam": 0.0}


def _get_image_classifier():
    global _IMAGE_CLASSIFIER
    if _IMAGE_CLASSIFIER is None:
        try:
            from transformers import pipeline

            _IMAGE_CLASSIFIER = pipeline(
                "image-classification",
                model="Falconsai/nsfw_image_detection",
                token=HF_TOKEN,
            )
        except Exception:
            logger.exception("Could not load the NSFW image classifier")
            _IMAGE_CLASSIFIER = False
    return _IMAGE_CLASSIFIER if _IMAGE_CLASSIFIER is not False else None


def _get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None:
        try:
            import easyocr

            _OCR_READER = easyocr.Reader(["en"], gpu=False)
        except Exception:
            logger.exception("Could not load the EasyOCR reader")
            _OCR_READER = False
    return _OCR_READER if _OCR_READER is not False else None


async def classify_image_NSFW(image):
    """Classify an image as NSFW when the model is available."""
    model = await asyncio.to_thread(_get_image_classifier)
    if model is None:
        return {"nsfw": 0.0}

    try:
        results = await asyncio.to_thread(model, image)
    except Exception:
        logger.exception("NSFW image classification failed")
        return {"nsfw": 0.0}

    normalized = {"nsfw": 0.0}
    for result in results or []:
        label = str(result.get("label", "")).lower()
        score = float(result.get("score", 0.0))
        if label == "nsfw":
            normalized["nsfw"] = score
    return normalized


async def classify_OCR(image):
    """Perform OCR on an image, returning danger scores for the extracted text."""
    reader = await asyncio.to_thread(_get_ocr_reader)
    if reader is None:
        return _empty_scores()

    try:
        image_np = np.array(image)
        results = await asyncio.to_thread(
            reader.readtext,
            image_np,
            canvas_size=1600,
            batch_size=1,
        )
    except Exception:
        logger.exception("OCR failed while reading an image")
        return _empty_scores()

    text = ""
    for result in results or []:
        try:
            _, word, confidence = result
        except ValueError:
            continue

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            continue

        if confidence > 0.4 and word:
            text += str(word) + " "

    return await classify_danger_level(text)


async def classify_image(attachment):
    """Classify a Discord image attachment using NSFW detection and OCR."""
    if attachment is None:
        return _empty_scores()

    if attachment.content_type and not attachment.content_type.startswith("image/"):
        return _empty_scores()

    async with _IMAGE_CLASSIFICATION_LOCK:
        if getattr(attachment, "size", 0) > MAX_IMAGE_BYTES:
            logger.warning(
                "Skipping image attachment of %s bytes (limit: %s)",
                attachment.size,
                MAX_IMAGE_BYTES,
            )
            return _empty_scores()

        try:
            image_bytes = await attachment.read()
            if len(image_bytes) > MAX_IMAGE_BYTES:
                logger.warning(
                    "Skipping image attachment of %s bytes (limit: %s)",
                    len(image_bytes),
                    MAX_IMAGE_BYTES,
                )
                return _empty_scores()
            image = await asyncio.to_thread(_open_bounded_image, image_bytes)
        except Exception:
            logger.exception("Could not decode image attachment")
            return _empty_scores()

        if image is None:
            return _empty_scores()

        try:
            nsfw_result = await classify_image_NSFW(image)
            ocr_result = await classify_OCR(image)
        except Exception:
            logger.exception("Image classification failed")
            return _empty_scores()

    default = _empty_scores()
    final_result = {
        "Hate": float(ocr_result.get("Hate", default["Hate"])),
        "Sexual": min(float(ocr_result.get("Sexual", default["Sexual"])) + float(nsfw_result.get("nsfw", 0.0)), 1.0),
        "Concern": float(ocr_result.get("Concern", default["Concern"])),
        "Danger": float(ocr_result.get("Danger", default["Danger"])) + float(nsfw_result.get("nsfw", 0.0)) * 1.5 + float(ocr_result.get("Scam", default["Scam"])) * 0.5,
        "Scam": float(ocr_result.get("Scam", default["Scam"])),
    }

    return final_result


def _open_bounded_image(image_bytes):
    with Image.open(io.BytesIO(image_bytes)) as source:
        width, height = source.size
        if width * height > MAX_IMAGE_PIXELS:
            logger.warning(
                "Skipping image with %s pixels (limit: %s)",
                width * height,
                MAX_IMAGE_PIXELS,
            )
            return None

        source.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        return source.convert("RGB")
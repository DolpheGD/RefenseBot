import io
import numpy as np
from transformers import pipeline
import easyocr
from PIL import Image
from bot.config import HF_TOKEN
from bot.ml.classifier import classify_danger_level

image_classifier = pipeline(
    "image-classification",
    model="Falconsai/nsfw_image_detection",
    token=HF_TOKEN
)

reader = easyocr.Reader(['en'])


async def classify_image_NSFW(image):
    """
    Classifies an image using the NSFW image detection model from FalconsAI.
    Returns a dictionary with the classification results and their corresponding probabilities.
    """
    results = image_classifier(image)
    return {result['label']: result['score'] for result in results}


async def classify_OCR(image):
    """
    Performs Optical Character Recognition (OCR) on the given image using easyocr.
    Returns the extracted text from the image.
    """
    image_np = np.array(image)
    results = reader.readtext(image_np)

    text = ""

    for _, word, confidence in results:
        if confidence > 0.4:  # filter noise
            text += word + " "

    scores = await classify_danger_level(text)
    return scores



async def classify_image(attachment):
    """
    Classifies an image from a Discord attachment using both NSFW detection and OCR.
    Returns a dictionary containing the results from both classification methods.
    """
    image_bytes = await attachment.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    nsfw_result = await classify_image_NSFW(image)
    ocr_result = await classify_OCR(image)

    final_result = {
        'Hate': ocr_result['Hate'],
        'Sexual': min(ocr_result['Sexual'] + nsfw_result.get('nsfw', 0), 1.0),
        'Concern': ocr_result['Concern'],
        'Danger': ocr_result['Danger'] + nsfw_result.get('nsfw', 0) * 1.5,
        'Scam': ocr_result['Scam'] * 1.5,
    }

    return final_result
# classifies text using a pre-trained model from Hugging Face. The model is loaded using the transformers library and the classify_message function takes
# a string input and returns a dictionary of classification results with their corresponding probabilities.

import math

from bot.config import HF_TOKEN
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from bot.helpers.scam_identifier import identify_scam
from bot.helpers.slur_identifier import identify_slurs
import torch

CLASS_TERMS = {
    "S" : "Sexual",
    "H" : "Hate",
    "V" : "Violence",
    "HR" : "Harassment",
    "SH" : "Self-Harm",
    "S3" : "Sexual-Minors",
    "H2" : "Targeted-Violence",
    "V2" : "Graphic-Violence",
    "OK" : "Safe"
}

#load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "KoalaAI/Text-Moderation",
    token=HF_TOKEN
)

model = AutoModelForSequenceClassification.from_pretrained(
    "KoalaAI/Text-Moderation",
    token=HF_TOKEN
)

toxic_model = pipeline(
    "text-classification",
    model="unitary/toxic-bert",
    token=HF_TOKEN
)


def classify_general(text):
    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad(): # no training, just inference
        outputs = model(**inputs)

    probabilities = outputs.logits.softmax(dim=-1).squeeze()

    id2label = model.config.id2label

    results = {id2label[idx]: prob.item() for idx, prob in enumerate(probabilities)}

    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))


def classify_toxicity(message):
    results = toxic_model(message)
    return results[0]['score']


async def classify_danger_level(message, image=False):
    """
    danger levels
    """
    if (not message or message.strip() == "") and not image:
        return {"Hate": 0.0, "Sexual": 0.0, "Concern": 0.0, "Danger": 0.0, "Scam": 0.0}
    
    results = classify_general(message)
    toxicity_score = classify_toxicity(message)
    slurs = identify_slurs(message)
    scam_score = identify_scam(message)

    sexual = min(
        results["S"] * 0.8 + (results["S3"] * 1.5),
        1.0
    )

    hate = min(
        results["H"] * 0.25 +
        results["HR"] * 0.20 +
        results["V"] * 0.20 +
        results["H2"] * 0.35 +
        results["V2"] * 0.30 +
        toxicity_score * 0.3 +
        slurs["count"] * 0.5,
        1.0
    )

    concern = min(
        results["SH"] * 1.5 + (toxicity_score * 0.1),
        1.0
    )

    scam = min(scam_score, 1.0)

    danger = sexual * 0.45 + hate * 0.55 + concern * 0.25 + scam * 0.25
    for label, prob in results.items():
        if label not in ["OK", "H"]:
            if prob > 0.6: #if specifically high in any category besides hate, add danger bonus
                danger += prob / 1.5
            elif prob > 0.4:
                danger += prob / 2.0
            elif prob > 0.2:
                danger += prob / 3.0

    if results["S3"] > 0.25:
        danger += results["S3"] / 1.5
    
    if results["H2"] > 0.25:
        danger += results["H2"] / 1.5

    if results["V2"] > 0.25:
        danger += results["V2"] / 1.5

    if slurs["count"] > 0:
        danger += math.log(slurs["count"] + 1) * 2 + 0.2

    return {"Hate": hate, "Sexual": sexual, "Concern": concern, "Danger": danger, "Scam": scam}



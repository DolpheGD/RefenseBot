# classifies text using a pre-trained model from Hugging Face. The model is loaded using the transformers library and the classify_message function takes
# a string input and returns a dictionary of classification results with their corresponding probabilities.

from bot.config import HF_TOKEN
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
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


def classify_danger_level(message):
    """
    danger levels
    """
    results = classify_general(message)
    toxicity_score = classify_toxicity(message)

    sexual = min(
        results["S"] + (results["S3"] * 2.0),
        1.0
    )

    hate = min(
        results["H"] * 0.25 +
        results["HR"] * 0.20 +
        results["V"] * 0.20 +
        results["H2"] * 0.35 +
        results["V2"] * 0.30 +
        toxicity_score * 0.20,
        1.0
    )

    concern = min(
        results["SH"] + (toxicity_score * 0.05),
        1.0
    )

    danger = sexual * 0.60 + hate * 0.90 + concern * 0.5
    for label, prob in results.items():
        if label not in ["OK"]:
            if prob > 0.25: #if specifically high in any category, add danger
                danger += prob / 2

    if results["S3"] > 0.25:
        danger += 0.40


    return {"Hate": hate, "Sexual": sexual, "Concern": concern, "Danger": danger}
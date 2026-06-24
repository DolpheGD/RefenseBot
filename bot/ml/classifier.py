# classifies text using a pre-trained model from Hugging Face. The model is loaded using the transformers library and the classify_message function takes
# a string input and returns a dictionary of classification results with their corresponding probabilities.
from bot.config import HF_TOKEN
from transformers import AutoModelForSequenceClassification, AutoTokenizer
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


def classify_message(text):
    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad(): # no training, just inference
        outputs = model(**inputs)

    probabilities = outputs.logits.softmax(dim=-1).squeeze()

    id2label = model.config.id2label

    results = {id2label[idx]: prob.item() for idx, prob in enumerate(probabilities)}

    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))


def classify_with_output(message):
    results = classify_message(message)
    output = ""
    for label, prob in results.items():
        output += f"{CLASS_TERMS[label]}: {prob:.2%}\n"
    return output
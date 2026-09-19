# Classifies text using either local Hugging Face transformers models (heavy) or the
# remote Hugging Face Inference API (lightweight, network calls). Local models are
# loaded lazily on first use to avoid high RAM at import time. Prefer remote inference
# on memory-constrained hosts (set USE_LOCAL_ML=False in environment).

import math
import os
import asyncio
import requests
from typing import Dict, Any

from bot.config import HF_TOKEN, USE_LOCAL_ML
from bot.helpers.scam_identifier import identify_scam
from bot.helpers.slur_identifier import identify_slurs

# Label mapping expected from the moderation model
CLASS_TERMS = {
    "S": "Sexual",
    "H": "Hate",
    "V": "Violence",
    "HR": "Harassment",
    "SH": "Self-Harm",
    "S3": "Sexual-Minors",
    "H2": "Targeted-Violence",
    "V2": "Graphic-Violence",
    "OK": "Safe",
}

# Globals for lazy-loaded local models
_tokenizer = None
_model = None
_toxic_pipeline = None
_torch = None

HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}


def _load_local_models() -> None:
    """Load transformers / torch models into global variables. This is blocking and
    should only be called on hosts that have enough RAM and CPU.
    """
    global _tokenizer, _model, _toxic_pipeline, _torch
    if _tokenizer is not None and _model is not None and _toxic_pipeline is not None:
        return

    # Import heavy libraries only when needed
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
    import torch as _torch_local

    _tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation", use_auth_token=HF_TOKEN)
    _model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation", use_auth_token=HF_TOKEN)
    _toxic_pipeline = pipeline("text-classification", model="unitary/toxic-bert", use_auth_token=HF_TOKEN)
    _torch = _torch_local


def _classify_general_local(text: str) -> Dict[str, float]:
    """Run local model inference (blocking). Returns a dict mapping labels like 'S','H',... to scores."""
    global _tokenizer, _model, _torch
    if _tokenizer is None or _model is None:
        _load_local_models()

    inputs = _tokenizer(text, return_tensors="pt")
    with _torch.no_grad():
        outputs = _model(**inputs)

    probabilities = outputs.logits.softmax(dim=-1).squeeze()
    id2label = _model.config.id2label
    results = {id2label[idx]: float(probabilities[idx].item()) for idx in range(len(probabilities))}

    # Ensure all expected keys exist with default 0.0
    for k in CLASS_TERMS.keys():
        results.setdefault(k, 0.0)

    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))


def _classify_toxicity_local(message: str) -> float:
    global _toxic_pipeline
    if _toxic_pipeline is None:
        _load_local_models()

    out = _toxic_pipeline(message)
    if isinstance(out, list) and len(out) > 0:
        # pipeline usually returns list of dicts
        return float(out[0].get("score", 0.0))
    return 0.0


def _classify_general_remote(text: str) -> Dict[str, float]:
    """Use Hugging Face Inference API for the moderation model. Best-effort mapping of labels."""
    if not HF_TOKEN:
        # No token available; return safe defaults
        return {k: 0.0 for k in CLASS_TERMS}

    url = "https://api-inference.huggingface.co/models/KoalaAI/Text-Moderation"
    try:
        resp = requests.post(url, headers=HF_HEADERS, json={"inputs": text}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = {}

        # Response might be a list of {label,score} items
        if isinstance(data, list):
            for item in data:
                label = item.get("label")
                score = float(item.get("score", 0.0))
                if label:
                    results[label] = score
        elif isinstance(data, dict):
            # Some models return {label: score} or nested structure
            # Attempt to flatten
            if "labels" in data and "scores" in data:
                for label, score in zip(data["labels"], data["scores"]):
                    results[label] = float(score)
            else:
                # Unknown format - fallback
                pass

        # Ensure all expected keys exist
        for k in CLASS_TERMS.keys():
            results.setdefault(k, 0.0)

        return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))
    except Exception:
        # On any failure, return safe defaults to avoid crashing the bot
        return {k: 0.0 for k in CLASS_TERMS}


def _classify_toxicity_remote(message: str) -> float:
    if not HF_TOKEN:
        return 0.0
    url = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    try:
        resp = requests.post(url, headers=HF_HEADERS, json={"inputs": message}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            # Try to find a 'toxic' label
            for item in data:
                label = item.get("label", "").lower()
                score = float(item.get("score", 0.0))
                if "toxic" in label or "tox" in label:
                    return score
            # no explicit toxic label; return top score
            return float(data[0].get("score", 0.0))
        return 0.0
    except Exception:
        return 0.0


async def classify_danger_level(message: str, image: bool = False) -> Dict[str, float]:
    """Compute danger-related scores for a message.

    This function intentionally avoids importing heavy ML libraries at import time.
    On memory-constrained hosts set USE_LOCAL_ML=False and ensure HF_TOKEN is set so
    remote inference is used instead.
    """
    if (not message or message.strip() == "") and not image:
        return {"Hate": 0.0, "Sexual": 0.0, "Concern": 0.0, "Danger": 0.0, "Scam": 0.0}

    # Choose remote or local classification; run blocking work in thread to not block the event loop
    if USE_LOCAL_ML:
        results = await asyncio.to_thread(_classify_general_local, message)
        toxicity_score = await asyncio.to_thread(_classify_toxicity_local, message)
    else:
        results = await asyncio.to_thread(_classify_general_remote, message)
        toxicity_score = await asyncio.to_thread(_classify_toxicity_remote, message)

    slurs = identify_slurs(message)
    scam_score = identify_scam(message)

    # Be defensive about missing keys
    def get_score(k: str) -> float:
        return float(results.get(k, 0.0))

    sexual = min(get_score("S") * 0.8 + (get_score("S3") * 1.5), 1.0)

    hate = min(
        get_score("H") * 0.25
        + get_score("HR") * 0.20
        + get_score("V") * 0.20
        + get_score("H2") * 0.35
        + get_score("V2") * 0.30
        + toxicity_score * 0.3
        + slurs.get("count", 0) * 0.5,
        1.0,
    )

    concern = min(get_score("SH") * 1.5 + (toxicity_score * 0.1), 1.0)
    scam = min(scam_score, 1.0)

    danger = sexual * 0.45 + hate * 0.55 + concern * 0.25 + scam * 0.25

    for label, prob in results.items():
        if label not in ["OK", "H"]:
            if prob > 0.6:
                danger += prob / 1.5
            elif prob > 0.4:
                danger += prob / 2.0
            elif prob > 0.2:
                danger += prob / 3.0

    if get_score("S3") > 0.25:
        danger += get_score("S3") / 1.5
    if get_score("H2") > 0.25:
        danger += get_score("H2") / 1.5
    if get_score("V2") > 0.25:
        danger += get_score("V2") / 1.5
    if slurs.get("count", 0) > 0:
        danger += math.log(slurs.get("count", 0) + 1) * 2 + 0.2

    return {"Hate": hate, "Sexual": sexual, "Concern": concern, "Danger": danger, "Scam": scam}

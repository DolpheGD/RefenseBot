# Classifies text using a local moderation model and a network backup model.
# The local model is used when available, and the remote Hugging Face endpoint is
# used as a fallback. If the remote API hits its usage limit, new messages are
# blocked until the failure is resolved unless a local model is available.

import asyncio
import math
from typing import Any, Dict

import requests

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
_torch = None
_REMOTE_USAGE_BLOCKED = False
_REMOTE_USAGE_BLOCK_REASON = ""
_LOCAL_MODEL_ERROR = ""

HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}


def _local_model_available() -> bool:
    return _tokenizer is not None and _model is not None and _torch is not None


def _ensure_local_model_loaded() -> bool:
    """Attempt to load the local model when the host is configured to prefer it."""
    global _LOCAL_MODEL_ERROR
    if not USE_LOCAL_ML:
        return False

    if _local_model_available():
        _LOCAL_MODEL_ERROR = ""
        return True

    try:
        _load_local_models()
        _LOCAL_MODEL_ERROR = ""
        return _local_model_available()
    except Exception as exc:  # pragma: no cover - runtime-only diagnostics
        _LOCAL_MODEL_ERROR = f"{type(exc).__name__}: {exc}"
        return False


def get_remote_model_status() -> Dict[str, Any]:
    """Return the current remote moderation state for monitoring and admin checks."""
    if USE_LOCAL_ML:
        _ensure_local_model_loaded()

    return {
        "token_configured": bool(HF_TOKEN),
        "local_available": _local_model_available(),
        "local_error": _LOCAL_MODEL_ERROR,
        "remote_blocked": _REMOTE_USAGE_BLOCKED,
        "remote_reason": _REMOTE_USAGE_BLOCK_REASON or "normal",
        "mode": "local-first" if USE_LOCAL_ML else "remote-first",
    }


def _block_remote_usage(reason: str) -> None:
    global _REMOTE_USAGE_BLOCKED, _REMOTE_USAGE_BLOCK_REASON
    _REMOTE_USAGE_BLOCKED = True
    _REMOTE_USAGE_BLOCK_REASON = reason


def _clear_remote_usage_block() -> None:
    global _REMOTE_USAGE_BLOCKED, _REMOTE_USAGE_BLOCK_REASON
    _REMOTE_USAGE_BLOCKED = False
    _REMOTE_USAGE_BLOCK_REASON = ""


def _load_local_models() -> None:
    """Load the moderation model only when needed.

    Keeping this to a single model keeps RAM usage substantially lower on
    8 GB devices while preserving the core moderation signals.
    """
    global _tokenizer, _model, _torch
    if _tokenizer is not None and _model is not None:
        return

    # Import heavy libraries only when needed
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch as _torch_local

    pretrained_kwargs = {"token": HF_TOKEN} if HF_TOKEN else {}
    _tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation", **pretrained_kwargs)
    _model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation", **pretrained_kwargs)
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

    for k in CLASS_TERMS.keys():
        results.setdefault(k, 0.0)

    return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))


def _classify_general_remote(text: str) -> Dict[str, float]:
    """Use the remote Hugging Face moderation model when available."""
    if not HF_TOKEN:
        _block_remote_usage("HF_TOKEN missing")
        return {k: 0.0 for k in CLASS_TERMS}

    if _REMOTE_USAGE_BLOCKED:
        return {k: 0.0 for k in CLASS_TERMS}

    url = "https://api-inference.huggingface.co/models/KoalaAI/Text-Moderation"
    try:
        resp = requests.post(url, headers=HF_HEADERS, json={"inputs": text}, timeout=30)
        if resp.status_code in {401, 403, 429, 500, 502, 503, 504}:
            _block_remote_usage(f"HTTP {resp.status_code}")
            return {k: 0.0 for k in CLASS_TERMS}

        resp.raise_for_status()
        data = resp.json()
        results = {}

        if isinstance(data, list):
            for item in data:
                label = item.get("label")
                score = float(item.get("score", 0.0))
                if label:
                    results[label] = score
        elif isinstance(data, dict):
            if "labels" in data and "scores" in data:
                for label, score in zip(data["labels"], data["scores"]):
                    results[label] = float(score)

        for k in CLASS_TERMS.keys():
            results.setdefault(k, 0.0)

        _clear_remote_usage_block()
        return dict(sorted(results.items(), key=lambda item: item[1], reverse=True))
    except Exception as exc:
        message = str(exc).lower()
        if "429" in message or "rate limit" in message or "quota" in message or "too many requests" in message:
            _block_remote_usage("HF usage limit hit")
        elif "403" in message or "401" in message:
            _block_remote_usage("HF auth rejected")
        else:
            _block_remote_usage(f"remote inference failure: {type(exc).__name__}")
        return {k: 0.0 for k in CLASS_TERMS}


async def classify_danger_level(message: str, image: bool = False) -> Dict[str, float]:
    """Compute danger-related scores for a message.

    Local moderation is preferred when it is already loaded. Remote moderation is a
    network fallback. If the remote API is blocked by a usage limit and no local
    model is available, message analysis is skipped to avoid sending unsupported
    requests to the network model.
    """
    if (not message or message.strip() == "") and not image:
        return {"Hate": 0.0, "Sexual": 0.0, "Concern": 0.0, "Danger": 0.0, "Scam": 0.0}

    local_ready = _local_model_available()
    remote_blocked = _REMOTE_USAGE_BLOCKED

    if USE_LOCAL_ML:
        if not local_ready:
            local_ready = _ensure_local_model_loaded()
        if local_ready:
            results = await asyncio.to_thread(_classify_general_local, message)
        elif HF_TOKEN and not remote_blocked:
            results = await asyncio.to_thread(_classify_general_remote, message)
        else:
            return {"Hate": 0.0, "Sexual": 0.0, "Concern": 0.0, "Danger": 0.0, "Scam": 0.0}
    elif local_ready and (remote_blocked or not HF_TOKEN):
        results = await asyncio.to_thread(_classify_general_local, message)
    elif HF_TOKEN and not remote_blocked:
        results = await asyncio.to_thread(_classify_general_remote, message)
    elif local_ready:
        results = await asyncio.to_thread(_classify_general_local, message)
    else:
        return {"Hate": 0.0, "Sexual": 0.0, "Concern": 0.0, "Danger": 0.0, "Scam": 0.0}

    slurs = identify_slurs(message)
    scam_score = identify_scam(message)

    def get_score(k: str) -> float:
        return float(results.get(k, 0.0))

    sexual = min(get_score("S") * 0.8 + (get_score("S3") * 1.5), 1.0)

    hate = min(
        get_score("H") * 0.25
        + get_score("HR") * 0.20
        + get_score("V") * 0.20
        + get_score("H2") * 0.35
        + get_score("V2") * 0.30
        + slurs.get("count", 0) * 0.5,
        1.0,
    )

    concern = min(get_score("SH") * 1.5, 1.0)
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

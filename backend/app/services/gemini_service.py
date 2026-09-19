import re

import httpx
from google import genai

from app.config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Models confirmed decommissioned/broken — always skip these
DEPRECATED_MODELS = {
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
}

# Confirmed live Gemini models from API key (ordered best-to-fallback)
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.5-flash",       # Best: fast, generous free quota
    "gemini-2.5-flash-lite",  # Lighter variant, still generous
    "gemini-3.5-flash",       # Newer preview available on this key
    "gemini-3.1-flash-lite",  # Additional fallback
    "gemini-flash-latest",    # Latest alias — always resolves
]

# Confirmed live Groq models from API key (ordered most-capable-to-smallest)
GROQ_MODEL_FALLBACKS = [
    "openai/gpt-oss-20b",    # Smaller, lower TPM usage — safer fallback
    "openai/gpt-oss-120b",   # Largest but hits 8k TPM limit fast
    "qwen/qwen3.8-27b",      # Good secondary
    "groq/compound-mini",    # Lightest fallback
]

_gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def clean_text(text: str) -> str:
    # Strips markdown bold, heading, and code fence characters from plain text
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"`+", "", text)
    return text.strip()


def _unique_models(primary: str, fallbacks: list[str]) -> list[str]:
    # Deduplicates model list and removes deprecated entries
    seen: set[str] = set()
    ordered: list[str] = []
    for model in [primary, *fallbacks]:
        model = model.strip()
        if model and model not in seen and model not in DEPRECATED_MODELS:
            seen.add(model)
            ordered.append(model)
    return ordered


def _should_retry_on_next_model(error: Exception) -> bool:
    # Returns True for transient errors where trying a different model makes sense
    msg = str(error).lower()
    return any(
        token in msg
        for token in (
            "404", "429", "500", "502", "503", "504",
            "rate_limit", "tokens per minute", "high demand",
            "unavailable", "temporarily", "not_found",
            "decommissioned", "no longer available", "does not exist",
            "not found", "model_decommissioned",
        )
    )


def _generate_with_gemini(prompt: str) -> str:
    # Tries each Gemini model in order, waiting briefly on 503 before next
    if not _gemini_client:
        raise ValueError("GEMINI_API_KEY is not configured.")

    import time
    last_error: Exception | None = None
    for model in _unique_models(GEMINI_MODEL, GEMINI_MODEL_FALLBACKS):
        try:
            response = _gemini_client.models.generate_content(
                model=model,
                contents=prompt,
            )
            text = response.text
            if not text or not text.strip():
                raise ValueError(f"Gemini ({model}) returned an empty response.")
            if model != GEMINI_MODEL:
                print(f"Gemini succeeded with fallback model: {model}")
            return text.strip()
        except Exception as e:
            last_error = e
            print(f"Gemini model failed ({model}): {e}")
            # Brief pause on server-side overload before trying next model
            if "503" in str(e) or "unavailable" in str(e).lower() or "high demand" in str(e).lower():
                time.sleep(1.5)
            continue  # Always try next model

    raise last_error or ValueError("No Gemini models available.")


def _generate_with_groq(prompt: str, expect_json: bool = False) -> str:
    # Tries each Groq model in order, pausing on 429 rate-limit before next
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    import time
    messages = []
    if expect_json:
        # System prompt enforces clean JSON-only responses from Groq
        messages.append({
            "role": "system",
            "content": (
                "You must respond with valid JSON only. "
                "Do not wrap the response in markdown code fences or add any extra text."
            ),
        })
    messages.append({"role": "user", "content": prompt})

    last_error: Exception | None = None
    for model in _unique_models(GROQ_MODEL, GROQ_MODEL_FALLBACKS):
        try:
            response = httpx.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                },
                timeout=120.0,
            )
            if response.status_code >= 400:
                detail = response.text.strip() or response.reason_phrase
                if response.status_code == 429:
                    # Rate limited — pause briefly then try next model
                    print(f"Groq rate limited ({model}), trying next model...")
                    time.sleep(2.0)
                raise ValueError(f"HTTP {response.status_code}: {detail}")

            data = response.json()
            text = data["choices"][0]["message"]["content"]
            if not text or not text.strip():
                raise ValueError(f"Groq ({model}) returned an empty response.")
            if model != GROQ_MODEL:
                print(f"Groq succeeded with fallback model: {model}")
            return text.strip()
        except Exception as e:
            last_error = e
            print(f"Groq model failed ({model}): {e}")
            continue  # Always try next model

    raise last_error or ValueError("No Groq models available.")


def _provider_order() -> list[str]:
    # Returns the AI provider attempt order based on AI_PROVIDER config
    if AI_PROVIDER == "groq":
        return ["groq", "gemini"]
    if AI_PROVIDER == "gemini":
        return ["gemini", "groq"]
    return ["gemini", "groq"]


def generate_content(prompt: str, expect_json: bool = False) -> str:
    """Generate content using configured AI providers with automatic fallback."""
    from fastapi import HTTPException, status

    errors: list[str] = []
    providers = {
        "gemini": (GEMINI_API_KEY, _generate_with_gemini),
        "groq": (GROQ_API_KEY, lambda p: _generate_with_groq(p, expect_json=expect_json)),
    }

    # Try each provider in configured order, collecting errors for full fallback
    for name in _provider_order():
        api_key, generate_fn = providers[name]
        if not api_key:
            continue
        try:
            result = generate_fn(prompt)
            if errors:
                print(f"Fell back to {name} after earlier provider failure.")
            return result
        except Exception as e:
            print(f"{name.capitalize()} Error:", e)
            errors.append(f"{name.capitalize()}: {e}")

    if not errors:
        errors.append("No AI provider configured. Set GEMINI_API_KEY and/or GROQ_API_KEY in .env.")

    # Both providers exhausted — return error response
    combined = " | ".join(errors)
    if expect_json:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {combined}",
        )
    return f"AI generation temporarily unavailable.\nError: {combined}"

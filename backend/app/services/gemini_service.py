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

# Older model IDs that Google/Groq have retired for new accounts
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]
GROQ_MODEL_FALLBACKS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
]

_gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def clean_text(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"`+", "", text)
    return text.strip()


def _unique_models(primary: str, fallbacks: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for model in [primary, *fallbacks]:
        model = model.strip()
        if model and model not in seen:
            seen.add(model)
            ordered.append(model)
    return ordered


def _is_model_unavailable_error(error: Exception) -> bool:
    msg = str(error).lower()
    return any(
        token in msg
        for token in ("404", "not_found", "no longer available", "does not exist", "not found")
    )


def _generate_with_gemini(prompt: str) -> str:
    if not _gemini_client:
        raise ValueError("GEMINI_API_KEY is not configured.")

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
            if _is_model_unavailable_error(e):
                print(f"Gemini model unavailable ({model}): {e}")
                continue
            raise

    raise last_error or ValueError("No Gemini models available.")


def _generate_with_groq(prompt: str, expect_json: bool = False) -> str:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    messages = []
    if expect_json:
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
            if _is_model_unavailable_error(e):
                print(f"Groq model unavailable ({model}): {e}")
                continue
            raise

    raise last_error or ValueError("No Groq models available.")


def _provider_order() -> list[str]:
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

    combined = " | ".join(errors)
    if expect_json:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {combined}",
        )
    return f"AI generation temporarily unavailable.\nError: {combined}"

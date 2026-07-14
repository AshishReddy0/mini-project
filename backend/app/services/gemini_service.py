import re
from google import genai
from app.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def clean_text(text: str) -> str:
    # Deprecated/Only used if plain text is explicitly desired somewhere
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"`+", "", text)
    return text.strip()

def generate_content(prompt: str) -> str:
    """Generate content from Gemini. Returns the raw response text preserving markdown elements."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        # Preserve markdown syntax (headers, bold, lists, backticks) for chat rendering and JSON parsing
        return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)
        return f"""
Demo Mode:
AI generation temporarily unavailable.
Error: {str(e)}
"""
import re
from google import genai
from app.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def clean_text(text: str) -> str:
    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#+", "", text)
    text = re.sub(r"`+", "", text)
    return text.strip()

def generate_content(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return clean_text(response.text)
    except Exception as e:
        print("Gemini Error:", e)
        return f"""
Demo Mode:
AI generation temporarily unavailable.
Error: {str(e)}
"""
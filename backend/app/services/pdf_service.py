from pypdf import PdfReader

def extract_pdf_text(file_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception:
        pass

    # Fallback to pdfplumber if available and pypdf extracted nothing
    if not text.strip():
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    p_text = page.extract_text()
                    if p_text:
                        text += p_text + "\n"
        except Exception:
            pass

    # Second fallback: read raw string characters if plain text embedded
    if not text.strip():
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read()
                import re
                clean = re.sub(r'[^\x20-\x7E\n\r\t]', '', raw)
                if len(clean.strip()) > 50:
                    text = clean
        except Exception:
            pass

    return text
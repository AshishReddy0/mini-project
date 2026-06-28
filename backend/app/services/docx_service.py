from docx import Document

def extract_docx_text(file_path: str) -> str:
    text = ""
    doc = Document(file_path)

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text
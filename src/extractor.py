"""
Step 1 — PDF Rule Extraction
Reads a PDF and returns its raw text.
A downstream LLM call (Step 2) then structures the text into Markdown.
"""

import io
import PyPDF2


def extraire_texte_pdf(source) -> str:
    """Extract raw text from a PDF file path or a file-like object.

    Args:
        source: str path to a PDF file, or a file-like object (e.g. from Streamlit uploader).

    Returns:
        The concatenated text of all pages.
    """
    texte = ""

    if isinstance(source, (str, bytes)):
        # Called from CLI with a file path
        with open(source, "rb") as fichier:
            lecteur = PyPDF2.PdfReader(fichier)
            for page in lecteur.pages:
                page_text = page.extract_text()
                if page_text:
                    texte += page_text + "\n"
    else:
        # Called from Streamlit with an uploaded file object
        contenu = source.read()
        lecteur = PyPDF2.PdfReader(io.BytesIO(contenu))
        for page in lecteur.pages:
            page_text = page.extract_text()
            if page_text:
                texte += page_text + "\n"

    return texte.strip()

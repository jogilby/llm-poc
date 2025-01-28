# pdf_processing.py
import PyPDF2

def pdf_to_text_chunks(pdf_path, chunk_size=500, overlap=50):
    """
    Convert a PDF file into a list of text chunks.
    Each chunk has ~chunk_size characters (with overlap).
    """
    text_chunks = []
    reader = PyPDF2.PdfReader(open(pdf_path, 'rb'))

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            start = 0
            while start < len(page_text):
                end = min(start + chunk_size, len(page_text))
                chunk = page_text[start:end]
                text_chunks.append(chunk.strip())
                start += chunk_size - overlap  # move forward but keep some overlap
    return text_chunks
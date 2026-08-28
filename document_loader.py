import os
import sys
import logging
import argparse
from bs4 import BeautifulSoup
import pypdf

# Configure stdout/stderr to use UTF-8 to prevent encoding issues on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class Document:
    """
    Represents a loaded document with its content, length, and source citation path.
    """
    def __init__(self, source: str, content: str):
        self.source = source
        self.content = content
        self.length = len(content)

    def __repr__(self) -> str:
        return f"Document(source='{self.source}', length={self.length})"


def load_txt(file_path: str) -> str:
    """Loads plain text file with UTF-8 encoding."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def load_md(file_path: str) -> str:
    """Loads Markdown file. Since MD is human-readable text, it is loaded as plain text."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def load_html(file_path: str) -> str:
    """Loads HTML file, extracts body text, and strips HTML tags cleanly."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
        # Remove scripting and style components
        for element in soup(["script", "style", "header", "footer", "nav"]):
            element.decompose()
            
        # Get raw text
        text = soup.get_text()
        
        # Clean up whitespace formatting
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = "\n".join(chunk for chunk in chunks if chunk)
        return cleaned_text


def load_pdf(file_path: str) -> str:
    """Loads PDF file page by page using pypdf and extracts plain text."""
    reader = pypdf.PdfReader(file_path)
    
    # Trigger a read of the first page to raise errors early if corrupted
    if len(reader.pages) == 0:
        raise ValueError("PDF file has 0 pages.")
        
    text_parts = []
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
            
    extracted = "\n".join(text_parts).strip()
    if not extracted:
        logger.warning(f"No extractable text found in PDF: {file_path}")
    return extracted


# Map supported file extensions to their corresponding loaders
LOADERS = {
    ".txt": load_txt,
    ".md": load_md,
    ".html": load_html,
    ".htm": load_html,
    ".pdf": load_pdf,
}


def load_document(file_path: str) -> Document:
    """
    Loads a single document based on its extension.
    Raises exceptions for unsupported formats, missing files, or corruption.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
        
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext not in LOADERS:
        raise ValueError(f"Unsupported file format: {ext}")
        
    loader_func = LOADERS[ext]
    content = loader_func(file_path)
    return Document(source=file_path, content=content)


def load_directory(directory_path: str) -> list:
    """
    Recursively scans directory_path for documents.
    Gracefully skips corrupt, missing, or unsupported files and logs warning/error messages.
    Returns a list of successfully loaded Document objects.
    """
    loaded_documents = []
    
    if not os.path.isdir(directory_path):
        logger.error(f"Provided path is not a directory: {directory_path}")
        return loaded_documents

    # Walk directory
    for root, _, files in os.walk(directory_path):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Skip hidden files or system files
            if file.startswith("."):
                continue
                
            if ext not in LOADERS:
                logger.warning(f"Skipping unsupported file format: {file_path}")
                continue
                
            try:
                doc = load_document(file_path)
                loaded_documents.append(doc)
            except Exception as e:
                logger.error(f"Skipping corrupt or unreadable file {file_path} - Reason: {e}")
                
    return loaded_documents


def main():
    parser = argparse.ArgumentParser(description="Corpus Document Loader for RAG.")
    parser.add_argument("directory", help="Path to directory containing corpus documents.")
    args = parser.parse_args()
    
    print(f"\n=== Intake Scanning: {args.directory} ===\n")
    
    loaded_docs = load_directory(args.directory)
    
    print(f"\n=== Intake Confirmation Summary ===")
    print(f"Successfully loaded: {len(loaded_docs)} documents\n")
    
    for i, doc in enumerate(loaded_docs, 1):
        print(f"[{i}] SOURCE: {doc.source}")
        print(f"    LENGTH: {doc.length} characters")
        snippet = doc.content[:150].replace('\n', ' ')
        suffix = "..." if len(doc.content) > 150 else ""
        print(f"    SAMPLE: \"{snippet}{suffix}\"")
        print("-" * 50)


if __name__ == "__main__":
    main()

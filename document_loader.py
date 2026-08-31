import os
import sys
import logging
import argparse
import json
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


class DocumentChunk:
    """
    Represents a chunk of a document with consistent metadata fields.
    """
    def __init__(self, text: str, metadata: dict):
        self.text = text
        self.metadata = {
            "source": metadata.get("source"),
            "section": metadata.get("section", "N/A"),
            "page": metadata.get("page"),
            "position": metadata.get("position", 0)
        }

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "metadata": self.metadata
        }

    def __repr__(self) -> str:
        return (f"DocumentChunk(source='{self.metadata['source']}', "
                f"section='{self.metadata['section']}', "
                f"page={self.metadata['page']}, "
                f"position={self.metadata['position']}, "
                f"length={len(self.text)})")


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


# --- Chunker Implementation Details ---

def split_text_by_length(text: str, max_chars: int = 500, overlap: int = 100) -> list:
    """
    Splits text into chunks of max_chars length with overlap.
    Returns list of tuples (chunk_text, start_char_offset).
    """
    chunks = []
    if not text:
        return chunks
    start = 0
    text_len = len(text)
    
    # If the text is shorter than max_chars, return it as a single chunk
    if text_len <= max_chars:
        return [(text.strip(), 0)]
        
    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            last_space = text.rfind(" ", start, end)
            if last_space > start + int(max_chars * 0.75):
                end = last_space
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append((chunk_text, start))
        
        if end >= text_len:
            break
            
        start = max(start + 1, end - overlap)
    return chunks


def chunk_txt(file_path: str) -> list:
    """
    Chunks a plain text file.
    Splits by double newlines (paragraphs) and creates chunks.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    chunks = []
    paragraphs = content.split("\n\n")
    current_offset = 0
    
    for p in paragraphs:
        p_offset = content.find(p, current_offset)
        if p_offset == -1:
            p_offset = current_offset
        
        p_clean = p.strip()
        if p_clean:
            if len(p_clean) > 500:
                sub_chunks = split_text_by_length(p_clean, max_chars=500, overlap=100)
                for sub_text, sub_off in sub_chunks:
                    chunks.append(DocumentChunk(
                        text=sub_text,
                        metadata={
                            "source": file_path,
                            "section": "N/A",
                            "page": None,
                            "position": p_offset + sub_off
                        }
                    ))
            else:
                chunks.append(DocumentChunk(
                    text=p_clean,
                    metadata={
                        "source": file_path,
                        "section": "N/A",
                        "page": None,
                        "position": p_offset
                    }
                ))
        current_offset = p_offset + len(p)
    return chunks


def chunk_md(file_path: str) -> list:
    """
    Chunks a markdown file by headers (#, ##, ###, etc.).
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    chunks = []
    newline_char = "\r\n" if "\r\n" in content else "\n"
    lines = content.split(newline_char)
    current_section = "N/A"
    section_text_blocks = []
    section_start_offset = 0
    current_offset = 0

    for line in lines:
        line_len = len(line) + len(newline_char)
        if line.strip().startswith("#"):
            if section_text_blocks:
                section_body = newline_char.join(section_text_blocks).strip()
                if section_body:
                    pos = content.find(section_body, section_start_offset)
                    if pos == -1:
                        pos = section_start_offset
                    if len(section_body) > 500:
                        sub_chunks = split_text_by_length(section_body, max_chars=500, overlap=100)
                        for sub_text, sub_off in sub_chunks:
                            chunks.append(DocumentChunk(
                                text=sub_text,
                                metadata={
                                    "source": file_path,
                                    "section": current_section,
                                    "page": None,
                                    "position": pos + sub_off
                                }
                            ))
                    else:
                        chunks.append(DocumentChunk(
                            text=section_body,
                            metadata={
                                "source": file_path,
                                "section": current_section,
                                "page": None,
                                "position": pos
                            }
                        ))
            current_section = line.strip()
            section_text_blocks = []
            section_start_offset = current_offset
        else:
            section_text_blocks.append(line)
        current_offset += line_len

    if section_text_blocks:
        section_body = newline_char.join(section_text_blocks).strip()
        if section_body:
            pos = content.find(section_body, section_start_offset)
            if pos == -1:
                pos = section_start_offset
            if len(section_body) > 500:
                sub_chunks = split_text_by_length(section_body, max_chars=500, overlap=100)
                for sub_text, sub_off in sub_chunks:
                    chunks.append(DocumentChunk(
                        text=sub_text,
                        metadata={
                            "source": file_path,
                            "section": current_section,
                            "page": None,
                            "position": pos + sub_off
                        }
                    ))
            else:
                chunks.append(DocumentChunk(
                    text=section_body,
                    metadata={
                        "source": file_path,
                        "section": current_section,
                        "page": None,
                        "position": pos
                    }
                ))
    
    if not chunks and content.strip():
        chunks.append(DocumentChunk(
            text=content.strip(),
            metadata={
                "source": file_path,
                "section": "N/A",
                "page": None,
                "position": 0
            }
        ))

    return chunks


def chunk_html(file_path: str) -> list:
    """
    Chunks an HTML file by block elements and headers.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        raw_html = f.read()

    soup = BeautifulSoup(raw_html, "html.parser")
    for element in soup(["script", "style"]):
        element.decompose()

    chunks = []
    body = soup.body if soup.body else soup
    
    def get_text_blocks(element):
        blocks = []
        for child in element.children:
            if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                blocks.append(("header", child.get_text().strip(), child.name))
            elif child.name in ["p", "li", "div"]:
                nested = child.find_all(["p", "li", "div"])
                if not nested:
                    text = child.get_text().strip()
                    if text:
                        blocks.append(("text", text, None))
                else:
                    blocks.extend(get_text_blocks(child))
            elif child.name is None:
                text = child.strip()
                if text:
                    blocks.append(("text", text, None))
            else:
                if hasattr(child, "children"):
                    blocks.extend(get_text_blocks(child))
        return blocks

    blocks = get_text_blocks(body)
    
    last_section = "N/A"
    for block_type, text, tag in blocks:
        if block_type == "header":
            last_section = f"{tag.upper()}: {text}"
        elif block_type == "text" and text:
            pos = raw_html.find(text)
            if pos == -1:
                pos = raw_html.find(text[:20])
                if pos == -1:
                    pos = 0
            
            if len(text) > 500:
                sub_chunks = split_text_by_length(text, max_chars=500, overlap=100)
                for sub_text, sub_off in sub_chunks:
                    chunks.append(DocumentChunk(
                        text=sub_text,
                        metadata={
                            "source": file_path,
                            "section": last_section,
                            "page": None,
                            "position": pos + sub_off
                        }
                    ))
            else:
                chunks.append(DocumentChunk(
                    text=text,
                    metadata={
                        "source": file_path,
                        "section": last_section,
                        "page": None,
                        "position": pos
                    }
                ))
    return chunks


def chunk_pdf(file_path: str) -> list:
    """
    Chunks a PDF page-by-page.
    """
    reader = pypdf.PdfReader(file_path)
    if len(reader.pages) == 0:
        raise ValueError("PDF file has 0 pages.")

    chunks = []
    for page_num, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        if not page_text:
            continue
        
        lines = page_text.split("\n")
        sub_chunks = split_text_by_length(page_text, max_chars=500, overlap=100)
        
        for sub_text, sub_off in sub_chunks:
            best_section = "N/A"
            running_off = 0
            for line in lines:
                line_clean = line.strip()
                line_len = len(line) + 1
                if running_off > sub_off:
                    break
                if line_clean and len(line_clean) < 60 and line_clean[0].isupper() and not line_clean.endswith(('.', ',', ';', ':')):
                    best_section = line_clean
                running_off += line_len
            
            chunks.append(DocumentChunk(
                text=sub_text,
                metadata={
                    "source": file_path,
                    "section": best_section,
                    "page": page_num,
                    "position": sub_off
                }
            ))
    return chunks


CHUNKER_FUNCS = {
    ".txt": chunk_txt,
    ".md": chunk_md,
    ".html": chunk_html,
    ".htm": chunk_html,
    ".pdf": chunk_pdf,
}


def chunk_document(file_path: str) -> list:
    """
    Chunks a single document based on its extension.
    Returns a list of DocumentChunk objects.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
        
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext not in CHUNKER_FUNCS:
        raise ValueError(f"Unsupported file format for chunking: {ext}")
        
    chunker_func = CHUNKER_FUNCS[ext]
    return chunker_func(file_path)


def chunk_directory(directory_path: str) -> list:
    """
    Recursively scans directory_path, chunks all supported documents,
    and returns a list of DocumentChunk objects.
    """
    all_chunks = []
    
    if not os.path.isdir(directory_path):
        logger.error(f"Provided path is not a directory: {directory_path}")
        return all_chunks

    for root, _, files in os.walk(directory_path):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            if file.startswith("."):
                continue
                
            if ext not in CHUNKER_FUNCS:
                logger.warning(f"Skipping unsupported file format: {file_path}")
                continue
                
            try:
                rel_path = os.path.relpath(file_path).replace("\\", "/")
                chunks = chunk_document(file_path)
                for chunk in chunks:
                    chunk.metadata["source"] = rel_path
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Skipping chunking for corrupt or unreadable file {file_path} - Reason: {e}")
                
    return all_chunks


def save_chunks_to_json(chunks: list, output_path: str):
    """
    Saves a list of DocumentChunk objects to a JSON file.
    """
    data = [chunk.to_dict() for chunk in chunks]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Corpus Document Loader and Chunker for RAG.")
    parser.add_argument("directory", help="Path to directory containing corpus documents.")
    parser.add_argument("--chunk", action="store_true", help="Chunk the documents and print chunk metadata.")
    parser.add_argument("--output", default="data/sample_chunks.json", help="Path to save the JSON chunk export.")
    args = parser.parse_args()
    
    if args.chunk:
        print(f"\n=== Intake Chunking: {args.directory} ===\n")
        chunks = chunk_directory(args.directory)
        print(f"\n=== Chunking Confirmation Summary ===")
        print(f"Successfully generated: {len(chunks)} chunks\n")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"[{i}] SOURCE: {chunk.metadata['source']}")
            print(f"    SECTION: {chunk.metadata['section']}")
            print(f"    PAGE: {chunk.metadata['page']}")
            print(f"    POSITION: {chunk.metadata['position']}")
            print(f"    LENGTH: {len(chunk.text)} characters")
            snippet = chunk.text[:150].replace('\n', ' ')
            suffix = "..." if len(chunk.text) > 150 else ""
            print(f"    TEXT: \"{snippet}{suffix}\"")
            print("-" * 50)
            
        if args.output:
            save_chunks_to_json(chunks, args.output)
            print(f"Saved chunks to: {args.output}")
    else:
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

"""
Corporate Contract Ingestion & Processing Pipeline.

Handles PDF/DOCX/TXT file parsing, text cleaning, metadata extraction,
and token-aware semantic chunking with overlap.
"""

import os
import re
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import tiktoken

from app.config import AppConfig, setup_logger

logger = setup_logger("contract_processor")

def estimate_tokens(text: str, model_name: str = "gpt-4") -> int:
    """Estimates the token count of a string using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback estimation: ~4 chars per token
        return max(1, len(text) // 4)


class ContractProcessor:
    """
    Parses, cleans, tags metadata, and chunks corporate contract documents.
    """

    def __init__(self, target_chunk_tokens: int = 350, chunk_overlap_tokens: int = 50):
        self.target_chunk_tokens = target_chunk_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

    def extract_raw_text(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Parses PDF, DOCX, or TXT document and extracts full raw text and basic metadata."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Contract file not found: {file_path}")

        ext = file_path.suffix.lower()
        metadata = {
            "filename": file_path.name,
            "extension": ext,
            "file_size": file_path.stat().st_size,
            "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        raw_text = ""
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                metadata["page_count"] = len(reader.pages)
                page_texts = []
                for i, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    page_texts.append(f"--- [Page {i+1}] ---\n{txt}")
                raw_text = "\n\n".join(page_texts)
            except Exception as e:
                logger.error(f"Error reading PDF {file_path.name}: {e}")
                raise ValueError(f"Failed to parse PDF contract: {e}")

        elif ext in (".docx", ".doc"):
            try:
                import docx
                doc = docx.Document(str(file_path))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                raw_text = "\n\n".join(paragraphs)
            except Exception as e:
                logger.error(f"Error reading DOCX {file_path.name}: {e}")
                raise ValueError(f"Failed to parse DOCX contract: {e}")

        elif ext in (".txt", ".md"):
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()

        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: PDF, DOCX, TXT, MD.")

        return raw_text, metadata

    def clean_contract_text(self, text: str) -> str:
        """Cleans raw text by removing repetitive page headers/footers, excess whitespace, and noise."""
        # 1. Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 2. Strip confidential/page footer stamps like "Page 1 of 12"
        text = re.sub(r'page\s+\d+\s+of\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'confidential\s*-\s*for\s*internal\s*use\s*only', '', text, flags=re.IGNORECASE)

        # 3. Collapse multiple spaces & newlines (preserve paragraph breaks)
        lines = [line.strip() for line in text.split("\n")]
        cleaned_lines = []
        blank_count = 0
        for line in lines:
            if not line:
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append("")
            else:
                blank_count = 0
                cleaned_lines.append(line)

        cleaned_text = "\n".join(cleaned_lines).strip()
        return cleaned_text

    def extract_contract_metadata(self, filename: str, cleaned_text: str) -> Dict[str, Any]:
        """Extracts high-level contract metadata such as Title, Parties, and Document ID."""
        contract_id = f"contract-{uuid.uuid5(uuid.NAMESPACE_DNS, filename).hex[:12]}"
        
        # Extract title from first non-empty lines
        lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]
        title = lines[0] if lines else filename
        if len(title) > 100:
            title = filename

        # Simple classification heuristics
        contract_type = "Corporate Agreement"
        lower = cleaned_text[:2000].lower()
        if "non-disclosure" in lower or "nda" in lower:
            contract_type = "Non-Disclosure Agreement (NDA)"
        elif "service agreement" in lower or "master services" in lower or "msa" in lower:
            contract_type = "Master Services Agreement (MSA)"
        elif "employment contract" in lower or "employment agreement" in lower:
            contract_type = "Employment Agreement"
        elif "license agreement" in lower or "software license" in lower:
            contract_type = "Software License Agreement"
        elif "lease agreement" in lower:
            contract_type = "Lease Agreement"

        return {
            "contract_id": contract_id,
            "contract_title": title,
            "contract_type": contract_type,
            "total_character_count": len(cleaned_text),
            "estimated_tokens": estimate_tokens(cleaned_text)
        }

    def chunk_contract(self, cleaned_text: str, base_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits cleaned contract text into token-aware semantic chunks with section heading context and overlap.
        """
        paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [cleaned_text]

        chunks = []
        current_chunk_paragraphs = []
        current_tokens = 0
        chunk_counter = 1
        current_section = "Preamble / General Provisions"

        section_regex = re.compile(r'^(section|article|clause|\d+\.|\d+\.\d+)\s+.*', re.IGNORECASE)

        for p in paragraphs:
            # Check if paragraph is a Section Header
            if len(p) < 120 and section_regex.match(p):
                current_section = p.strip()

            p_tokens = estimate_tokens(p)

            # If adding this paragraph exceeds target tokens and we already have content, finalize current chunk
            if current_tokens + p_tokens > self.target_chunk_tokens and current_chunk_paragraphs:
                chunk_text = "\n\n".join(current_chunk_paragraphs)
                chunk_id = f"{base_metadata['contract_id']}-chunk-{chunk_counter}"
                
                chunk_meta = {
                    **base_metadata,
                    "chunk_id": chunk_id,
                    "chunk_index": chunk_counter,
                    "section_title": current_section,
                    "token_count": current_tokens
                }
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "metadata": chunk_meta
                })
                chunk_counter += 1

                # Overlap management: retain last paragraph for overlap
                overlap_paragraphs = []
                overlap_tokens = 0
                for prev_p in reversed(current_chunk_paragraphs):
                    prev_tok = estimate_tokens(prev_p)
                    if overlap_tokens + prev_tok <= self.chunk_overlap_tokens:
                        overlap_paragraphs.insert(0, prev_p)
                        overlap_tokens += prev_tok
                    else:
                        break

                current_chunk_paragraphs = overlap_paragraphs
                current_tokens = overlap_tokens

            current_chunk_paragraphs.append(p)
            current_tokens += p_tokens

        # Add remaining text as final chunk
        if current_chunk_paragraphs:
            chunk_text = "\n\n".join(current_chunk_paragraphs)
            chunk_id = f"{base_metadata['contract_id']}-chunk-{chunk_counter}"
            chunk_meta = {
                **base_metadata,
                "chunk_id": chunk_id,
                "chunk_index": chunk_counter,
                "section_title": current_section,
                "token_count": current_tokens
            }
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "metadata": chunk_meta
            })

        logger.info(f"Processed '{base_metadata['contract_title']}': generated {len(chunks)} chunks.")
        return chunks

    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Full pipeline: parsing -> cleaning -> metadata extraction -> token-aware chunking."""
        raw_text, file_meta = self.extract_raw_text(file_path)
        cleaned_text = self.clean_contract_text(raw_text)
        contract_meta = self.extract_contract_metadata(file_meta["filename"], cleaned_text)
        merged_meta = {**file_meta, **contract_meta}
        return self.chunk_contract(cleaned_text, merged_meta)

contract_processor = ContractProcessor()

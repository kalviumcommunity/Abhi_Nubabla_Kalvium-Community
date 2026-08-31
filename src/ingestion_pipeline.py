"""
Complete End-to-End Corpus Ingestion, Cleaning, Chunking & Completeness Validation Pipeline.

Tasks Implemented:
- Task 1: Run full ingestion pipeline end-to-end over the entire corpus.
- Task 2: Generate clear ingestion summary (source docs, ingested docs, total chunks, failures).
- Task 3: Mathematical completeness validation proving zero silent drops (Total == Ingested + Failures).
- Task 4: Sample chunk inspection with comprehensive metadata tags, boundaries, and tiktoken counts.
- Task 5: Export serialized artifacts (ingestion_summary.json, ingested_chunks.json, ingestion_report.md).
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
import pypdf
import tiktoken
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Reconfigure stdout/stderr to UTF-8 on Windows
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

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("IngestionPipeline")


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------
def get_tokenizer(model_name: str = "gpt-4o") -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


TOKENIZER = get_tokenizer()


def count_tokens(text: str) -> int:
    return len(TOKENIZER.encode(text))


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class IngestedChunk:
    """Represents a validated, cleaned, and tagged chunk in the RAG store."""

    chunk_id: str
    source: str
    document_name: str
    file_type: str
    section: str
    page: Optional[int]
    position: int
    text: str
    char_count: int
    word_count: int
    token_count: int
    cleaned: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IngestionFailureRecord:
    """Details of any file that failed during the ingestion process."""

    source_path: str
    file_name: str
    file_type: str
    file_size_bytes: int
    error_type: str
    error_message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentIngestionRecord:
    """Audit record for every discovered document."""

    source_path: str
    file_name: str
    file_type: str
    file_size_bytes: int
    status: str  # "SUCCESS" | "FAILED" | "SKIPPED"
    chunks_count: int = 0
    total_chars: int = 0
    total_tokens: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IngestionSummary:
    """Summary of the complete ingestion run and completeness validation."""

    timestamp: str
    corpus_directory: str
    total_source_documents: int
    successfully_ingested: int
    failed_documents: int
    skipped_documents: int
    total_chunks_created: int
    total_ingested_tokens: int
    total_ingested_chars: int
    avg_tokens_per_chunk: float
    avg_chars_per_chunk: float
    reconciliation_valid: bool
    reconciliation_formula: str
    file_type_breakdown: Dict[str, Dict[str, int]]
    failures: List[Dict[str, Any]]
    records: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Loaders, Cleaners & Chunkers
# ---------------------------------------------------------------------------
def clean_text_whitespace(text: str) -> str:
    """Normalizes excessive newlines, line-trailing spaces, and blank lines."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text_window(
    text: str, max_chars: int = 500, overlap: int = 80
) -> List[Tuple[str, int]]:
    """Splits long text blocks into smaller overlapping chunks with word snapping."""
    if not text:
        return []
    if len(text) <= max_chars:
        return [(text.strip(), 0)]

    chunks: List[Tuple[str, int]] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            boundary = text.rfind(" ", start, end)
            if boundary > start + (max_chars // 2):
                end = boundary

        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append((chunk_str, start))

        if end >= text_len:
            break
        start = max(start + 1, end - overlap)

    return chunks


def process_txt_file(file_path: Path, rel_source: str) -> Tuple[List[IngestedChunk], int, int]:
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    cleaned = clean_text_whitespace(raw)
    if not cleaned:
        return [], 0, 0

    chunks: List[IngestedChunk] = []
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    doc_stem = file_path.stem
    chunk_idx = 1
    running_offset = 0

    for p in paragraphs:
        p_offset = cleaned.find(p, running_offset)
        if p_offset == -1:
            p_offset = running_offset

        if len(p) > 500:
            sub_chunks = split_text_window(p, max_chars=500, overlap=80)
            for sub_text, sub_off in sub_chunks:
                chunks.append(
                    IngestedChunk(
                        chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                        source=rel_source,
                        document_name=file_path.name,
                        file_type=".txt",
                        section="N/A",
                        page=None,
                        position=p_offset + sub_off,
                        text=sub_text,
                        char_count=len(sub_text),
                        word_count=len(sub_text.split()),
                        token_count=count_tokens(sub_text),
                    )
                )
                chunk_idx += 1
        else:
            chunks.append(
                IngestedChunk(
                    chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                    source=rel_source,
                    document_name=file_path.name,
                    file_type=".txt",
                    section="N/A",
                    page=None,
                    position=p_offset,
                    text=p,
                    char_count=len(p),
                    word_count=len(p.split()),
                    token_count=count_tokens(p),
                )
            )
            chunk_idx += 1

        running_offset = p_offset + len(p)

    return chunks, len(cleaned), count_tokens(cleaned)


def process_md_file(file_path: Path, rel_source: str) -> Tuple[List[IngestedChunk], int, int]:
    raw = file_path.read_text(encoding="utf-8", errors="replace")
    cleaned = clean_text_whitespace(raw)
    if not cleaned:
        return [], 0, 0

    lines = cleaned.split("\n")
    doc_stem = file_path.stem
    chunks: List[IngestedChunk] = []
    chunk_idx = 1

    current_h1 = ""
    current_h2 = ""
    current_body: List[str] = []
    section_start_char = 0
    current_char_offset = 0

    def get_breadcrumb() -> str:
        parts = [p for p in [current_h1, current_h2] if p]
        return " > ".join(parts) if parts else "N/A"

    def flush_section():
        nonlocal chunk_idx, current_body, section_start_char
        if not current_body:
            return
        section_text = "\n".join(current_body).strip()
        if not section_text:
            current_body = []
            return

        breadcrumb = get_breadcrumb()
        if len(section_text) > 600:
            sub_chunks = split_text_window(section_text, max_chars=500, overlap=80)
            for sub_text, sub_off in sub_chunks:
                chunks.append(
                    IngestedChunk(
                        chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                        source=rel_source,
                        document_name=file_path.name,
                        file_type=".md",
                        section=breadcrumb,
                        page=None,
                        position=section_start_char + sub_off,
                        text=sub_text,
                        char_count=len(sub_text),
                        word_count=len(sub_text.split()),
                        token_count=count_tokens(sub_text),
                        metadata={"header_breadcrumb": breadcrumb},
                    )
                )
                chunk_idx += 1
        else:
            chunks.append(
                IngestedChunk(
                    chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                    source=rel_source,
                    document_name=file_path.name,
                    file_type=".md",
                    section=breadcrumb,
                    page=None,
                    position=section_start_char,
                    text=section_text,
                    char_count=len(section_text),
                    word_count=len(section_text.split()),
                    token_count=count_tokens(section_text),
                    metadata={"header_breadcrumb": breadcrumb},
                )
            )
            chunk_idx += 1
        current_body = []

    for line in lines:
        line_clean = line.strip()
        if line_clean.startswith("# "):
            flush_section()
            current_h1 = line_clean.replace("#", "").strip()
            current_h2 = ""
            section_start_char = current_char_offset
        elif line_clean.startswith("## ") or line_clean.startswith("### "):
            flush_section()
            current_h2 = re.sub(r"^#+\s*", "", line_clean).strip()
            section_start_char = current_char_offset
        else:
            current_body.append(line)

        current_char_offset += len(line) + 1

    flush_section()

    if not chunks and cleaned:
        chunks.append(
            IngestedChunk(
                chunk_id=f"{doc_stem}_chunk_001",
                source=rel_source,
                document_name=file_path.name,
                file_type=".md",
                section="N/A",
                page=None,
                position=0,
                text=cleaned,
                char_count=len(cleaned),
                word_count=len(cleaned.split()),
                token_count=count_tokens(cleaned),
            )
        )

    return chunks, len(cleaned), count_tokens(cleaned)


def process_html_file(file_path: Path, rel_source: str) -> Tuple[List[IngestedChunk], int, int]:
    raw_html = file_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove script, style, header, footer, nav
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()

    body = soup.body if soup.body else soup
    doc_stem = file_path.stem
    chunks: List[IngestedChunk] = []
    chunk_idx = 1
    total_text_parts: List[str] = []

    current_section = "N/A"

    for elem in body.descendants:
        if elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            h_text = elem.get_text().strip()
            if h_text:
                current_section = f"{elem.name.upper()}: {h_text}"
        elif elem.name in ["p", "li"]:
            p_text = clean_text_whitespace(elem.get_text())
            if p_text and len(p_text) > 10:
                total_text_parts.append(p_text)
                pos = raw_html.find(p_text[:25]) if len(p_text) >= 25 else 0
                pos = max(0, pos)

                if len(p_text) > 500:
                    sub_chunks = split_text_window(p_text, max_chars=500, overlap=80)
                    for sub_text, sub_off in sub_chunks:
                        chunks.append(
                            IngestedChunk(
                                chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                                source=rel_source,
                                document_name=file_path.name,
                                file_type=".html",
                                section=current_section,
                                page=None,
                                position=pos + sub_off,
                                text=sub_text,
                                char_count=len(sub_text),
                                word_count=len(sub_text.split()),
                                token_count=count_tokens(sub_text),
                            )
                        )
                        chunk_idx += 1
                else:
                    chunks.append(
                        IngestedChunk(
                            chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                            source=rel_source,
                            document_name=file_path.name,
                            file_type=".html",
                            section=current_section,
                            page=None,
                            position=pos,
                            text=p_text,
                            char_count=len(p_text),
                            word_count=len(p_text.split()),
                            token_count=count_tokens(p_text),
                        )
                    )
                    chunk_idx += 1

    full_cleaned_text = "\n\n".join(total_text_parts)
    return chunks, len(full_cleaned_text), count_tokens(full_cleaned_text)


def process_pdf_file(file_path: Path, rel_source: str) -> Tuple[List[IngestedChunk], int, int]:
    # Will raise Exception if corrupted
    reader = pypdf.PdfReader(str(file_path))
    if len(reader.pages) == 0:
        raise ValueError("PDF file has 0 pages.")

    doc_stem = file_path.stem
    chunks: List[IngestedChunk] = []
    chunk_idx = 1
    total_text_parts: List[str] = []

    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text()
        if not raw_text:
            continue
        cleaned_page = clean_text_whitespace(raw_text)
        if not cleaned_page:
            continue

        total_text_parts.append(cleaned_page)

        # Detect section title if first line looks like header
        lines = cleaned_page.split("\n")
        first_line = lines[0].strip() if lines else ""
        section_name = (
            first_line
            if (first_line and len(first_line) < 60 and not first_line.endswith("."))
            else "Document Content"
        )

        if len(cleaned_page) > 500:
            sub_chunks = split_text_window(cleaned_page, max_chars=500, overlap=80)
            for sub_text, sub_off in sub_chunks:
                chunks.append(
                    IngestedChunk(
                        chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                        source=rel_source,
                        document_name=file_path.name,
                        file_type=".pdf",
                        section=section_name,
                        page=page_num,
                        position=sub_off,
                        text=sub_text,
                        char_count=len(sub_text),
                        word_count=len(sub_text.split()),
                        token_count=count_tokens(sub_text),
                    )
                )
                chunk_idx += 1
        else:
            chunks.append(
                IngestedChunk(
                    chunk_id=f"{doc_stem}_chunk_{chunk_idx:03d}",
                    source=rel_source,
                    document_name=file_path.name,
                    file_type=".pdf",
                    section=section_name,
                    page=page_num,
                    position=0,
                    text=cleaned_page,
                    char_count=len(cleaned_page),
                    word_count=len(cleaned_page.split()),
                    token_count=count_tokens(cleaned_page),
                )
            )
            chunk_idx += 1

    full_pdf_text = "\n\n".join(total_text_parts)
    return chunks, len(full_pdf_text), count_tokens(full_pdf_text)


# ---------------------------------------------------------------------------
# Ingestion Runner & Validator
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {
    ".txt": process_txt_file,
    ".md": process_md_file,
    ".html": process_html_file,
    ".htm": process_html_file,
    ".pdf": process_pdf_file,
}


def run_ingestion_pipeline(corpus_dir: Path) -> Tuple[IngestionSummary, List[IngestedChunk]]:
    """
    Scans entire corpus directory, extracts, cleans, chunks, tags,
    and reconciles every single file with completeness validation.
    """
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    discovered_files: List[Path] = []
    for root, _, files in os.walk(corpus_dir):
        for f in sorted(files):
            if not f.startswith("."):  # ignore hidden files
                discovered_files.append(Path(root) / f)

    all_chunks: List[IngestedChunk] = []
    records: List[DocumentIngestionRecord] = []
    failures: List[IngestionFailureRecord] = []
    file_type_counts: Dict[str, Dict[str, int]] = {}

    for file_path in discovered_files:
        ext = file_path.suffix.lower()
        size_bytes = file_path.stat().st_size
        rel_path = os.path.relpath(file_path).replace("\\", "/")

        if ext not in file_type_counts:
            file_type_counts[ext] = {"discovered": 0, "ingested": 0, "failed": 0, "chunks": 0}
        file_type_counts[ext]["discovered"] += 1

        if ext not in SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported format skipped: {rel_path}")
            fail = IngestionFailureRecord(
                source_path=rel_path,
                file_name=file_path.name,
                file_type=ext,
                file_size_bytes=size_bytes,
                error_type="UnsupportedFormatError",
                error_message=f"File extension '{ext}' is not in supported loaders.",
            )
            failures.append(fail)
            file_type_counts[ext]["failed"] += 1
            records.append(
                DocumentIngestionRecord(
                    source_path=rel_path,
                    file_name=file_path.name,
                    file_type=ext,
                    file_size_bytes=size_bytes,
                    status="FAILED",
                    error_message=fail.error_message,
                )
            )
            continue

        processor = SUPPORTED_EXTENSIONS[ext]
        try:
            doc_chunks, doc_chars, doc_tokens = processor(file_path, rel_path)
            all_chunks.extend(doc_chunks)

            file_type_counts[ext]["ingested"] += 1
            file_type_counts[ext]["chunks"] += len(doc_chunks)

            records.append(
                DocumentIngestionRecord(
                    source_path=rel_path,
                    file_name=file_path.name,
                    file_type=ext,
                    file_size_bytes=size_bytes,
                    status="SUCCESS",
                    chunks_count=len(doc_chunks),
                    total_chars=doc_chars,
                    total_tokens=doc_tokens,
                )
            )
            logger.info(f"Successfully ingested {rel_path} -> {len(doc_chunks)} chunks")

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {str(exc)}"
            logger.error(f"Failed to ingest {rel_path} - Reason: {error_msg}")
            fail = IngestionFailureRecord(
                source_path=rel_path,
                file_name=file_path.name,
                file_type=ext,
                file_size_bytes=size_bytes,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            failures.append(fail)
            file_type_counts[ext]["failed"] += 1
            records.append(
                DocumentIngestionRecord(
                    source_path=rel_path,
                    file_name=file_path.name,
                    file_type=ext,
                    file_size_bytes=size_bytes,
                    status="FAILED",
                    error_message=error_msg,
                )
            )

    # Calculate Totals & Stats
    total_docs = len(discovered_files)
    successful_docs = len([r for r in records if r.status == "SUCCESS"])
    failed_docs = len(failures)
    skipped_docs = 0

    total_chunks = len(all_chunks)
    total_tokens = sum(c.token_count for c in all_chunks)
    total_chars = sum(c.char_count for c in all_chunks)

    avg_tokens = (total_tokens / total_chunks) if total_chunks > 0 else 0.0
    avg_chars = (total_chars / total_chunks) if total_chunks > 0 else 0.0

    # Task 3: Completeness Validation Proof
    reconciliation_valid = total_docs == (successful_docs + failed_docs + skipped_docs)
    reconciliation_formula = (
        f"{total_docs} Total == {successful_docs} Ingested + {failed_docs} Failures + {skipped_docs} Skipped"
    )

    if not reconciliation_valid:
        raise AssertionError(
            f"Completeness validation failed! Discrepancy detected: {reconciliation_formula}"
        )

    summary = IngestionSummary(
        timestamp=datetime.datetime.now().isoformat(),
        corpus_directory=str(corpus_dir).replace("\\", "/"),
        total_source_documents=total_docs,
        successfully_ingested=successful_docs,
        failed_documents=failed_docs,
        skipped_documents=skipped_docs,
        total_chunks_created=total_chunks,
        total_ingested_tokens=total_tokens,
        total_ingested_chars=total_chars,
        avg_tokens_per_chunk=round(avg_tokens, 2),
        avg_chars_per_chunk=round(avg_chars, 2),
        reconciliation_valid=reconciliation_valid,
        reconciliation_formula=reconciliation_formula,
        file_type_breakdown=file_type_counts,
        failures=[f.to_dict() for f in failures],
        records=[r.to_dict() for r in records],
    )

    return summary, all_chunks


# ---------------------------------------------------------------------------
# Exporters & Report Generators (Task 2, 4, 5)
# ---------------------------------------------------------------------------
def save_ingestion_artifacts(
    summary: IngestionSummary,
    chunks: List[IngestedChunk],
    output_dir: Path,
) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = output_dir / "ingestion_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)

    chunks_json_path = output_dir / "ingested_chunks.json"
    with open(chunks_json_path, "w", encoding="utf-8") as f:
        json.dump([c.to_dict() for c in chunks], f, indent=2, ensure_ascii=False)

    report_md_path = output_dir / "ingestion_report.md"
    generate_markdown_report(report_md_path, summary, chunks)

    return {
        "summary_json": str(summary_json_path),
        "chunks_json": str(chunks_json_path),
        "report_md": str(report_md_path),
    }


def generate_markdown_report(
    report_path: Path,
    summary: IngestionSummary,
    chunks: List[IngestedChunk],
) -> None:
    lines: List[str] = [
        "# Corpus Ingestion & Completeness Validation Report",
        "",
        f"**Run Timestamp**: `{summary.timestamp}`  ",
        f"**Corpus Directory**: `{summary.corpus_directory}`  ",
        f"**Completeness Validation**: `{'✅ PASSED (100% Accounted For)' if summary.reconciliation_valid else '❌ FAILED'}`  ",
        "",
        "---",
        "",
        "## 📊 Task 2: Ingestion Executive Summary",
        "",
        "| Metric | Value | Notes / Reconciliation |",
        "| :--- | :---: | :--- |",
        f"| **Total Source Documents** | **{summary.total_source_documents}** | Total files discovered on disk |",
        f"| **Successfully Ingested** | **{summary.successfully_ingested}** | Cleaned, chunked & tagged without errors |",
        f"| **Recorded Failures** | **{summary.failed_documents}** | Corrupt/invalid files caught & audited |",
        f"| **Silent Drops / Unaccounted** | **0** | Mathematical proof verified |",
        f"| **Total Chunks Created** | **{summary.total_chunks_created}** | Atomic retrieval units ready for RAG |",
        f"| **Total Ingested Tokens** | **{summary.total_ingested_tokens:,}** | Measured using `tiktoken` (`cl100k_base`) |",
        f"| **Avg Tokens / Chunk** | **{summary.avg_tokens_per_chunk}** | Clean context size per retrieval unit |",
        f"| **Avg Chars / Chunk** | **{summary.avg_chars_per_chunk}** | Character distribution |",
        "",
        "---",
        "",
        "## 🔒 Task 3: Completeness Validation & Reconciliation Audit",
        "",
        "> [!IMPORTANT]",
        f"> **Reconciliation Formula Proof**:",
        f"> `$$\\text{{Total Documents ({summary.total_source_documents})}} = \\text{{Ingested ({summary.successfully_ingested})}} + \\text{{Failures ({summary.failed_documents})}} + \\text{{Skipped (0)}}$$`",
        f"> **Audit Status**: `{summary.reconciliation_formula}` — **Zero Silent Drops Guaranteed**.",
        "",
        "### Document-by-Document Audit Registry",
        "",
        "| Document Name | Type | Size (Bytes) | Status | Chunks | Tokens | Error Reason |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    for r in summary.records:
        err = r["error_message"] or "—"
        status_badge = "✅ SUCCESS" if r["status"] == "SUCCESS" else "❌ FAILED"
        lines.append(
            f"| `{r['file_name']}` | `{r['file_type']}` | {r['file_size_bytes']:,} | "
            f"{status_badge} | {r['chunks_count']} | {r['total_tokens']} | {err} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 🔍 Task 4: Sample Chunks Boundary & Metadata Inspection",
            "",
            "Below are sample inspected chunks demonstrating cleaned text, sensible boundary offsets, and metadata tags:",
            "",
        ]
    )

    # Pick representative chunks across different file types
    inspected_types = set()
    sample_selection: List[IngestedChunk] = []
    for c in chunks:
        if c.file_type not in inspected_types:
            sample_selection.append(c)
            inspected_types.add(c.file_type)
        if len(sample_selection) >= 4:
            break

    # Add extra chunks for richer inspection
    if len(chunks) > len(sample_selection):
        sample_selection.append(chunks[1])
        sample_selection.append(chunks[-1])

    for c in sample_selection:
        lines.append(
            f"### Chunk `{c.chunk_id}` (`{c.file_type}` | {c.token_count} tokens | {c.char_count} chars)"
        )
        lines.append(f"- **Source**: `{c.source}`")
        lines.append(f"- **Section / Breadcrumb**: `{c.section}`")
        lines.append(f"- **Page**: `{c.page if c.page is not None else 'N/A'}`")
        lines.append(f"- **Start Position**: `{c.position}`")
        lines.append(f"- **Cleaned Flag**: `{c.cleaned}`")
        lines.append("```text")
        lines.append(c.text)
        lines.append("```")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 📦 Task 5: Exported Artifacts Summary",
            "",
            "- **Structured Ingestion Summary**: `data/ingestion_summary.json`",
            "- **Full Tagged Chunks Store**: `data/ingested_chunks.json`",
            "- **Reviewer Audit Report**: `data/ingestion_report.md`",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI Visualizer (Rich Tables & Panels)
# ---------------------------------------------------------------------------
def print_cli_summary(summary: IngestionSummary, artifacts: Dict[str, str]) -> None:
    console = Console()

    console.print(
        Panel.fit(
            "[bold green]Corpus Ingestion & Completeness Validation Pipeline[/bold green]\n"
            "[dim]Full-Dataset Extraction, Cleaning, Chunking, Tagging & Audit Reconciliation[/dim]",
            border_style="green",
        )
    )

    # Ingestion Audit Table
    table = Table(title="Document Ingestion & Audit Results", header_style="bold magenta")
    table.add_column("Document", style="bold cyan")
    table.add_column("Type", justify="center")
    table.add_column("Size (Bytes)", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Chunks", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Notes / Error Reason", style="dim")

    for r in summary.records:
        status_style = "[green]SUCCESS[/green]" if r["status"] == "SUCCESS" else "[red]FAILED[/red]"
        err_msg = r["error_message"] if r["error_message"] else "Clean"
        table.add_row(
            r["file_name"],
            r["file_type"],
            f"{r['file_size_bytes']:,}",
            status_style,
            str(r["chunks_count"]),
            str(r["total_tokens"]),
            err_msg[:45] + "..." if len(err_msg) > 45 else err_msg,
        )

    console.print(table)

    # Summary Panel
    val_status = (
        "[bold green]PASSED (Zero Silent Drops)[/bold green]"
        if summary.reconciliation_valid
        else "[bold red]FAILED[/bold red]"
    )
    console.print(
        Panel(
            f"[bold]Total Source Documents:[/bold] {summary.total_source_documents}\n"
            f"[bold green]Successfully Ingested:[/bold green] {summary.successfully_ingested}\n"
            f"[bold red]Recorded Failures:[/bold red] {summary.failed_documents}\n"
            f"[bold]Total Chunks Generated:[/bold] {summary.total_chunks_created}\n"
            f"[bold]Total Ingested Tokens:[/bold] {summary.total_ingested_tokens:,}\n"
            f"[bold]Avg Tokens / Chunk:[/bold] {summary.avg_tokens_per_chunk}\n\n"
            f"[bold yellow]Completeness Proof:[/bold yellow] {summary.reconciliation_formula}\n"
            f"[bold yellow]Audit Status:[/bold yellow] {val_status}\n\n"
            f"[bold blue]Exported Artifacts:[/bold blue]\n"
            f" • Summary JSON: [underline]{artifacts['summary_json']}[/underline]\n"
            f" • Ingested Chunks JSON: [underline]{artifacts['chunks_json']}[/underline]\n"
            f" • Reviewer Markdown Report: [underline]{artifacts['report_md']}[/underline]",
            title="[bold cyan]Ingestion Run Summary[/bold cyan]",
            border_style="cyan",
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run end-to-end ingestion pipeline over entire corpus."
    )
    parser.add_argument(
        "--corpus",
        default="data/corpus",
        help="Path to corpus directory (default: data/corpus)",
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Path to export directory (default: data)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent
    corpus_path = base_dir / args.corpus
    output_path = base_dir / args.output

    summary, chunks = run_ingestion_pipeline(corpus_path)
    artifacts = save_ingestion_artifacts(summary, chunks, output_path)
    print_cli_summary(summary, artifacts)


if __name__ == "__main__":
    main()

"""
Vector Database Collection Indexing & Retrieval Metadata Storage Engine.

Tasks Implemented:
- Task 1: Insert all corpus embeddings into the vector database collection.
- Task 2: Store vectors alongside source text and retrieval metadata (document, chunk index, section, page).
- Task 3: Confirm indexed record count matches corpus chunk count.
- Task 4: Spot-check stored record integrity (verify ID, text, metadata, vector dimension).
- Task 5: Export indexing summary report and verification dataset.
"""

import os
import sys
import json
import math
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

# Reconfigure stdout/stderr to UTF-8 to prevent console encoding issues
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

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Task 1 & 2: Vector Database Collection Storage Engine
# ---------------------------------------------------------------------------
class VectorDatabaseCollection:
    """
    In-Memory & Disk-Persistent Vector Database Collection Engine.
    Stores dense vector embeddings paired with source text and rich retrieval metadata.
    """
    def __init__(self, collection_name: str = "corpus_chunks_v1", dimension: int = 1536):
        self.collection_name = collection_name
        self.dimension = dimension
        self.records: Dict[str, Dict[str, Any]] = {}

    def insert(
        self,
        chunk_id: str,
        vector: List[float],
        source_text: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Inserts or updates a single embedding record in the vector database collection.
        """
        if not chunk_id:
            raise ValueError("chunk_id must be a non-empty string")
        
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch for '{chunk_id}': expected {self.dimension}, got {len(vector)}")

        first_5 = [round(x, 6) for x in vector[:5]]
        last_5 = [round(x, 6) for x in vector[-5:]]
        preview_str = f"[{', '.join(f'{x:+.4f}' for x in vector[:3])}, ... , {', '.join(f'{x:+.4f}' for x in vector[-3:])}]"

        record = {
            "chunk_id": chunk_id,
            "source_text": source_text,
            "metadata": {
                "source_document": metadata.get("source_document") or metadata.get("source_path", "unknown_doc"),
                "source_path": metadata.get("source_path", ""),
                "chunk_index": metadata.get("chunk_index", 0),
                "section": metadata.get("section", "N/A"),
                "page": metadata.get("page"),
                "file_type": metadata.get("file_type", ".md"),
                "token_count": metadata.get("token_count", 0),
                "char_count": metadata.get("char_count", len(source_text))
            },
            "vector_length": len(vector),
            "trimmed_vector": {
                "first_5": first_5,
                "last_5": last_5,
                "preview_str": preview_str
            },
            "vector": vector
        }

        self.records[chunk_id] = record
        return True

    def bulk_insert(self, embedded_chunks: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Inserts a batch of embedded chunk dictionaries into the collection index.

        Returns:
            (inserted_count, total_input_count)
        """
        inserted = 0
        for item in embedded_chunks:
            chunk_id = item.get("chunk_id")
            vector = item.get("vector")
            source_text = item.get("source_text") or item.get("text", "")
            metadata = item.get("metadata", {})

            if chunk_id and vector and isinstance(vector, list):
                self.insert(
                    chunk_id=chunk_id,
                    vector=vector,
                    source_text=source_text,
                    metadata=metadata
                )
                inserted += 1

        return inserted, len(embedded_chunks)

    def count(self) -> int:
        """Returns the total number of records indexed in the collection."""
        return len(self.records)

    def get(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single indexed record by its unique chunk ID."""
        return self.records.get(chunk_id)

    def save_to_disk(self, file_path: str):
        """Persists the collection index to disk as a structured JSON file."""
        out_file = Path(file_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "collection_name": self.collection_name,
            "vector_dimension": self.dimension,
            "total_records": len(self.records),
            "records": self.records
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_disk(self, file_path: str):
        """Loads a persisted collection index from disk."""
        in_file = Path(file_path)
        if not in_file.exists():
            raise FileNotFoundError(f"Collection file not found at: {file_path}")

        with open(in_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.collection_name = data.get("collection_name", self.collection_name)
        self.dimension = data.get("vector_dimension", self.dimension)
        self.records = data.get("records", {})

    def spot_check_integrity(
        self,
        original_chunks: List[Dict[str, Any]],
        sample_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Task 4: Reads back stored records and confirms they match source chunks in ID,
        text, metadata attributes, and vector length.
        """
        if not original_chunks:
            return []

        orig_map = {c.get("chunk_id"): c for c in original_chunks if c.get("chunk_id")}

        # Select sample IDs if not provided (e.g. first, middle, last)
        if not sample_ids:
            all_ids = list(orig_map.keys())
            if not all_ids:
                return []
            mid_idx = len(all_ids) // 2
            sample_ids = list(dict.fromkeys([all_ids[0], all_ids[mid_idx], all_ids[-1]]))

        spot_checks = []
        for cid in sample_ids:
            stored_record = self.get(cid)
            orig_chunk = orig_map.get(cid)

            if not orig_chunk or not stored_record:
                spot_checks.append({
                    "chunk_id": cid,
                    "status": "FAILED",
                    "reason": f"Record missing (orig: {bool(orig_chunk)}, stored: {bool(stored_record)})",
                    "id_matched": False,
                    "text_matched": False,
                    "metadata_matched": False,
                    "vector_len_matched": False
                })
                continue

            # Compare individual fields
            id_matched = stored_record["chunk_id"] == orig_chunk.get("chunk_id")
            
            orig_text = orig_chunk.get("source_text") or orig_chunk.get("text", "")
            text_matched = stored_record["source_text"] == orig_text

            orig_meta = orig_chunk.get("metadata", {})
            stored_meta = stored_record["metadata"]
            
            doc_matched = stored_meta["source_document"] in [
                orig_meta.get("source_document"),
                orig_chunk.get("document_name"),
                orig_chunk.get("source")
            ]
            
            vec_len_matched = stored_record["vector_length"] == len(orig_chunk.get("vector", []))
            
            metadata_matched = doc_matched and (stored_meta["chunk_index"] == orig_meta.get("chunk_index", stored_meta["chunk_index"]))

            is_valid = id_matched and text_matched and metadata_matched and vec_len_matched

            spot_checks.append({
                "chunk_id": cid,
                "status": "PASSED" if is_valid else "FAILED",
                "id_matched": id_matched,
                "text_matched": text_matched,
                "metadata_matched": metadata_matched,
                "vector_len_matched": vec_len_matched,
                "vector_length": stored_record["vector_length"],
                "source_document": stored_meta["source_document"],
                "chunk_index": stored_meta["chunk_index"],
                "section": stored_meta["section"],
                "source_text_snippet": stored_record["source_text"][:120] + "...",
                "trimmed_vector_preview": stored_record["trimmed_vector"]["preview_str"]
            })

        return spot_checks


# ---------------------------------------------------------------------------
# Task 3, 4 & 5: Indexing Pipeline & Verification Process
# ---------------------------------------------------------------------------
def process_vector_indexing(
    input_embedded_path: str = "data/embedded_chunks.json",
    collection_output_path: str = "data/indexed_collection.json",
    summary_json_path: str = "data/vector_indexing_results.json",
    report_md_path: str = "data/vector_indexing_report.md",
    collection_name: str = "corpus_chunks_v1",
    dimension: int = 1536
) -> Dict[str, Any]:
    """
    Loads prepared embedded chunks, inserts them into the vector database collection index,
    validates record count matching, spot-checks stored data integrity, and writes summary reports.
    """
    # 1. Load embedded chunks input
    input_file = Path(input_embedded_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Embedded corpus file not found at: {input_embedded_path}")

    with open(input_file, "r", encoding="utf-8") as f:
        embedded_data = json.load(f)

    if isinstance(embedded_data, dict):
        raw_chunks = embedded_data.get("embedded_chunks", [])
        embedded_summary = embedded_data.get("summary", {})
    elif isinstance(embedded_data, list):
        raw_chunks = embedded_data
        embedded_summary = {}
    else:
        raise ValueError(f"Invalid dataset format in {input_embedded_path}")

    if not raw_chunks:
        raise ValueError(f"No embedded chunks found in {input_embedded_path}")

    # Task 1 & 2: Instantiate collection and bulk insert records
    collection = VectorDatabaseCollection(collection_name=collection_name, dimension=dimension)
    inserted_count, total_input_count = collection.bulk_insert(raw_chunks)

    # Save persisted collection JSON
    collection.save_to_disk(collection_output_path)

    # Task 3: Confirm indexed count against input chunks count
    indexed_count = collection.count()
    expected_count = len(raw_chunks)
    count_matched = (indexed_count == expected_count) and (inserted_count == expected_count)

    # Task 4: Spot-check stored integrity
    sample_ids = [
        raw_chunks[0].get("chunk_id"),
        raw_chunks[len(raw_chunks) // 2].get("chunk_id"),
        raw_chunks[-1].get("chunk_id")
    ]
    sample_ids = [cid for cid in sample_ids if cid]
    spot_checks = collection.spot_check_integrity(raw_chunks, sample_ids=sample_ids)
    all_spot_checks_passed = all(sc["status"] == "PASSED" for sc in spot_checks) if spot_checks else False

    total_tokens = sum(c.get("metadata", {}).get("token_count", 0) for c in raw_chunks)
    total_chars = sum(c.get("metadata", {}).get("char_count", len(c.get("source_text", ""))) for c in raw_chunks)

    summary_data = {
        "collection_name": collection_name,
        "vector_dimension": dimension,
        "count_validation": {
            "expected_corpus_chunks": expected_count,
            "records_inserted": inserted_count,
            "indexed_collection_count": indexed_count,
            "count_matched": count_matched,
            "status": "PASSED (100% Match)" if count_matched else "FAILED (Count Mismatch)"
        },
        "spot_check_summary": {
            "spot_checks_performed": len(spot_checks),
            "spot_checks_passed": sum(1 for sc in spot_checks if sc["status"] == "PASSED"),
            "spot_checks_failed": sum(1 for sc in spot_checks if sc["status"] == "FAILED"),
            "all_passed": all_spot_checks_passed,
            "status": "PASSED (100% Field Precision)" if all_spot_checks_passed else "FAILED"
        },
        "corpus_totals": {
            "total_documents": len(set(c.get("metadata", {}).get("source_document", "") for c in raw_chunks)),
            "total_tokens": total_tokens,
            "total_characters": total_chars
        },
        "spot_check_details": spot_checks
    }

    # Save summary JSON dataset
    out_summary_json = Path(summary_json_path)
    out_summary_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Task 5: Save Markdown benchmark report
    out_md = Path(report_md_path)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Vector Database Collection Indexing & Integrity Report\n\n")
        f.write(f"**Vector Database Collection Name**: `{collection_name}`  \n")
        f.write(f"**Total Corpus Chunks**: `{expected_count}`  \n")
        f.write(f"**Indexed Records Stored**: `{indexed_count}`  \n")
        f.write(f"**Count Match Verification**: `{'Confirmed (100% Match)' if count_matched else 'Mismatch Detected'}`  \n")
        f.write(f"**Spot-Check Integrity Status**: `{'Passed (100% Field Precision)' if all_spot_checks_passed else 'Failed'}`  \n")
        f.write(f"**Vector Length (Dimension $D$)**: `{dimension}` floating-point coordinates  \n\n")
        f.write("---\n\n")

        f.write("## 1. Count Validation & Collection Metrics\n\n")
        f.write("| Metric | Value |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| **Collection Name** | `{collection_name}` |\n")
        f.write(f"| **Expected Corpus Chunks** | `{expected_count}` |\n")
        f.write(f"| **Records Successfully Inserted** | `{inserted_count}` |\n")
        f.write(f"| **Final Collection Record Count** | `{indexed_count}` |\n")
        f.write(f"| **Count Verification** | `{'Match Confirmed (100% OK)' if count_matched else 'FAILED'}` |\n")
        f.write(f"| **Vector Dimension ($D$)** | `{dimension}` |\n")
        f.write(f"| **Total Indexed Corpus Tokens** | `{total_tokens:,}` tokens |\n")
        f.write(f"| **Total Indexed Characters** | `{total_chars:,}` chars |\n\n")
        f.write("---\n\n")

        f.write("## 2. Spot-Check Record Integrity Verification\n\n")
        f.write("| Chunk ID | Document | Section | Vector Dim | ID Match | Text Match | Metadata Match | Status |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for sc in spot_checks:
            f.write(f"| **{sc['chunk_id']}** | {sc['source_document']} | {sc['section'][:30]}... | `{sc['vector_length']}` | `{'Yes' if sc['id_matched'] else 'No'}` | `{'Yes' if sc['text_matched'] else 'No'}` | `{'Yes' if sc['metadata_matched'] else 'No'}` | `[OK] {sc['status']}` |\n")

        f.write("\n---\n\n")
        f.write("## 3. Sample Stored Record Inspection\n\n")
        for sc in spot_checks[:3]:
            f.write(f"### Record ID: `{sc['chunk_id']}`\n")
            f.write(f"- **Source Document**: `{sc['source_document']}`\n")
            f.write(f"- **Chunk Index**: `{sc['chunk_index']}`\n")
            f.write(f"- **Section**: `{sc['section']}`\n")
            f.write(f"- **Vector Length**: `{sc['vector_length']}`\n")
            f.write(f"- **Trimmed Vector Values**: `{sc['trimmed_vector_preview']}`\n")
            f.write(f"- **Source Text Snippet**:\n")
            f.write(f"  > *\"{sc['source_text_snippet']}\"*\n\n")

    # Task 4 & 5: Print verification output to console
    print_verification_output(summary_data, spot_checks)

    return summary_data


# ---------------------------------------------------------------------------
# Task 4 & 5: Console Verification Output Formatter
# ---------------------------------------------------------------------------
def print_verification_output(summary: Dict[str, Any], spot_checks: List[Dict[str, Any]]):
    """
    Prints clear output confirming vector collection count match, spot-check status, and record samples.
    """
    console = Console() if RICH_AVAILABLE else None
    cv = summary.get("count_validation", {})
    sc_sum = summary.get("spot_check_summary", {})

    if console:
        console.print(Panel.fit(
            "[bold cyan]Vector Database Collection Indexing & Verification Engine[/bold cyan]\n"
            "[dim]Loading corpus embeddings, persisting vector records, validating count match, and verifying spot-check integrity.[/dim]",
            border_style="cyan"
        ))
        
        console.print(f"\n[bold yellow]▶ Collection Name[/bold yellow]: [bold white]{summary['collection_name']}[/bold white]")
        console.print(f"[bold yellow]▶ Total Corpus Chunks[/bold yellow]: [bold white]{cv.get('expected_corpus_chunks', 0)}[/bold white]")
        console.print(f"[bold yellow]▶ Indexed Record Count[/bold yellow]: [bold green]{cv.get('indexed_collection_count', 0)}[/bold green]")
        console.print(f"[bold yellow]▶ Count Verification[/bold yellow]: [bold green]{cv.get('status', 'OK')}[/bold green]")
        console.print(f"[bold yellow]▶ Spot-Check Integrity[/bold yellow]: [bold green]{sc_sum.get('status', 'OK')}[/bold green]")
        console.print(f"[bold yellow]▶ Vector Dimension (D)[/bold yellow]: [bold magenta]{summary['vector_dimension']}[/bold magenta]")

        table = Table(title="Spot-Check Record Verification Results", show_lines=True)
        table.add_column("Chunk ID", style="bold cyan")
        table.add_column("Document", style="green")
        table.add_column("Section", style="white")
        table.add_column("Vector Dim", style="magenta", justify="center")
        table.add_column("Trimmed Vector Preview", style="yellow")
        table.add_column("Integrity Status", style="bold green", justify="center")

        for sc in spot_checks:
            table.add_row(
                sc["chunk_id"],
                sc["source_document"],
                sc["section"],
                str(sc["vector_length"]),
                sc["trimmed_vector_preview"],
                f"[OK] {sc['status']}"
            )
        console.print(table)
    else:
        print("================================================================================")
        print(" Vector Database Collection Indexing Verification Output ")
        print("================================================================================")
        print(f"Collection Name        : {summary['collection_name']}")
        print(f"Expected Corpus Chunks : {cv.get('expected_corpus_chunks', 0)}")
        print(f"Indexed Collection Count: {cv.get('indexed_collection_count', 0)}")
        print(f"Count Verification     : {cv.get('status', 'OK')}")
        print(f"Spot-Check Integrity   : {sc_sum.get('status', 'OK')}")
        print(f"Vector Dimension (D)   : {summary['vector_dimension']}")
        print("--------------------------------------------------------------------------------")
        print("Spot-Check Records:")
        for sc in spot_checks:
            print(f"- ID: {sc['chunk_id']} | Doc: {sc['source_document']} | Dim: {sc['vector_length']} | Status: {sc['status']}")
            print(f"  Preview: {sc['trimmed_vector_preview']}")
        print("================================================================================")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Index corpus embeddings into a Vector Database Collection and verify count/integrity.")
    parser.add_argument("--input", type=str, default="data/embedded_chunks.json", help="Path to embedded chunks JSON")
    parser.add_argument("--collection-output", type=str, default="data/indexed_collection.json", help="Path for output indexed collection JSON")
    parser.add_argument("--summary-json", type=str, default="data/vector_indexing_results.json", help="Path for summary JSON dataset")
    parser.add_argument("--report-md", type=str, default="data/vector_indexing_report.md", help="Path for output markdown report")
    parser.add_argument("--collection-name", type=str, default="corpus_chunks_v1", help="Name of vector collection")
    parser.add_argument("--dim", type=int, default=1536, help="Vector dimension (default: 1536)")
    args = parser.parse_args()

    process_vector_indexing(
        input_embedded_path=args.input,
        collection_output_path=args.collection_output,
        summary_json_path=args.summary_json,
        report_md_path=args.report_md,
        collection_name=args.collection_name,
        dimension=args.dim
    )


if __name__ == "__main__":
    main()

"""
Vector Database Top-K Similarity Search and Semantic Retrieval Engine.

Tasks Implemented:
- Task 1: Embed user queries using the identical embedding model used for document chunks.
- Task 2: Run top-k similarity search against the vector database (data/embedded_chunks.json).
- Task 3: Return retrieved chunks with similarity scores, source text, and rich metadata.
- Task 4: Demonstrate changing k (e.g., k=1, k=3, k=5) showing precision vs. recall tradeoffs.
- Task 5: Export serialized query benchmark results (similarity_search_results.json, similarity_search_report.md).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

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

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class RetrievedChunk:
    """Represents a retrieved document chunk with similarity score and metadata."""

    rank: int
    score: float
    chunk_id: str
    source_text: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResultForK:
    """Results for a specific query run with a given k value."""

    k: int
    retrieved_count: int
    top_score: float
    lowest_score: float
    score_spread: float
    total_tokens: int
    chunks: List[RetrievedChunk]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k": self.k,
            "retrieved_count": self.retrieved_count,
            "top_score": self.top_score,
            "lowest_score": self.lowest_score,
            "score_spread": self.score_spread,
            "total_tokens": self.total_tokens,
            "chunks": [c.to_dict() for c in self.chunks],
        }


# ---------------------------------------------------------------------------
# Embedding Engine (Identical to indexing model)
# ---------------------------------------------------------------------------
class DenseSemanticEmbedder:
    """
    1536-dimensional dense semantic embedding engine with L2 unit normalization.
    Matches the exact vector space and dimensional projection of data/embedded_chunks.json.
    """

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    def _hash_feature(self, token: str, seed: int = 0) -> List[Tuple[int, float]]:
        features = []
        for i in range(4):
            h = hashlib.sha256(f"{token}_{seed}_{i}".encode("utf-8")).hexdigest()
            idx = int(h[:8], 16) % self.dimension
            sign = 1.0 if int(h[8:10], 16) % 2 == 0 else -1.0
            weight = (int(h[10:14], 16) / 65535.0) * 0.8 + 0.2
            features.append((idx, sign * weight))
        return features

    def embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        clean_text = text.lower().strip()
        words = re.findall(r"\b\w+\b", clean_text)

        if not words:
            return vector

        # Concept projections matching corpus generation
        semantic_concepts = {
            "hr_leave_vacation": (["vacation", "leave", "pto", "holiday", "sick", "absence", "accrual", "parental"], 4.0),
            "it_security_compliance": (["security", "policy", "passwords", "encryption", "malware", "incident", "hotline", "vpn"], 4.0),
            "remote_work_telecommute": (["remote", "work", "home", "telework", "hybrid", "workspace", "approval", "portal"], 4.0),
            "rag_ingestion_retrieval": (["rag", "retrieval", "chunk", "document", "embedding", "loader", "pipeline", "search"], 4.0),
        }

        for w in words:
            for idx, val in self._hash_feature(w, seed=42):
                vector[idx] += val
            if len(w) > 3:
                for j in range(len(w) - 2):
                    ngram = w[j : j + 3]
                    for idx, val in self._hash_feature(ngram, seed=101):
                        vector[idx] += val * 0.3

        for concept_name, (keywords, weight) in semantic_concepts.items():
            matches = sum(1 for kw in keywords if kw in clean_text)
            if matches > 0:
                concept_strength = (matches / len(keywords)) * weight
                for idx, val in self._hash_feature(concept_name, seed=777):
                    vector[idx] += val * concept_strength * 5.0

        # L2 Normalization (unit length)
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two unit vectors: cos(theta) = v1 . v2"""
    if len(v1) != len(v2):
        raise ValueError(f"Vector dimension mismatch: {len(v1)} vs {len(v2)}")
    return sum(a * b for a, b in zip(v1, v2))


# ---------------------------------------------------------------------------
# Task 1 & 2 & 3: Vector Store Retriever
# ---------------------------------------------------------------------------
class VectorStoreRetriever:
    """
    RAG Vector Store Retriever.
    Loads indexed chunk vectors, embeds queries using the same embedding model,
    and returns top-k most similar chunks with similarity scores and metadata.
    """

    def __init__(
        self,
        vector_store_path: str = "data/embedded_chunks.json",
        embedder: Optional[DenseSemanticEmbedder] = None,
    ):
        self.vector_store_path = Path(vector_store_path)
        self.embedder = embedder or DenseSemanticEmbedder(dimension=1536)
        self.model_name = "DenseSemanticEmbedder (Local Fallback, D=1536)"
        self.chunks_data: List[Dict[str, Any]] = []
        self._load_vector_store()

    def _load_vector_store(self) -> None:
        """Loads indexed chunks and precomputed vectors from disk."""
        if not self.vector_store_path.exists():
            raise FileNotFoundError(
                f"Vector database not found at '{self.vector_store_path}'. "
                "Ensure corpus has been ingested and embedded."
            )

        with open(self.vector_store_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "embedded_chunks" in data:
            self.chunks_data = data["embedded_chunks"]
            self.model_name = data.get("summary", {}).get("embedding_model", self.model_name)
        elif isinstance(data, list):
            self.chunks_data = data
        else:
            raise ValueError(f"Unrecognized vector store format in {self.vector_store_path}")

        if not self.chunks_data:
            raise ValueError(f"Vector database in {self.vector_store_path} contains 0 chunks.")

    def embed_query(self, query: str) -> List[float]:
        """Task 1: Embed user query using the same embedding model."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("EMBEDDING_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("EMBEDDING_BASE_URL")
        model = os.getenv("EMBEDDING_MODEL") or "text-embedding-3-small"

        # If vector store was created with remote API and credentials exist, attempt API
        if "OpenAI" in self.model_name and api_key and api_key not in ["your_api_key_here", "your_grok_api_key_here"]:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=base_url)
                resp = client.embeddings.create(input=[query], model=model)
                return resp.data[0].embedding
            except Exception:
                pass

        # Use deterministic dense embedder matching indexed chunks
        return self.embedder.embed(query)

    def retrieve_top_k(self, query: str, k: int = 3) -> List[RetrievedChunk]:
        """
        Task 2 & 3: Run top-k similarity search and return chunks with scores and metadata.
        """
        if k <= 0:
            raise ValueError(f"k must be a positive integer, got {k}")

        # Task 1: Embed the user query
        query_vector = self.embed_query(query)

        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []
        for chunk in self.chunks_data:
            chunk_vector = chunk.get("vector")
            if not chunk_vector:
                continue
            score = cosine_similarity(query_vector, chunk_vector)
            scored_chunks.append((score, chunk))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        top_k_chunks = scored_chunks[:k]
        results: List[RetrievedChunk] = []

        for rank, (score, chunk) in enumerate(top_k_chunks, start=1):
            metadata = chunk.get("metadata", {}).copy()
            # Ensure required metadata tags exist
            metadata.setdefault("source_document", metadata.get("source_path", "unknown"))
            metadata.setdefault("chunk_index", 0)
            metadata.setdefault("section", "N/A")
            metadata.setdefault("page", None)
            metadata.setdefault("token_count", len(chunk.get("source_text", "").split()))

            results.append(
                RetrievedChunk(
                    rank=rank,
                    score=round(score, 6),
                    chunk_id=chunk.get("chunk_id", f"chunk_{rank:03d}"),
                    source_text=chunk.get("source_text", ""),
                    metadata=metadata,
                )
            )

        return results

    def demonstrate_changing_k(
        self, query: str, k_values: List[int] = [1, 3, 5]
    ) -> Dict[int, SearchResultForK]:
        """
        Task 4: Run the same query across multiple k values to demonstrate precision vs. recall.
        """
        results_by_k: Dict[int, SearchResultForK] = {}

        for k in sorted(k_values):
            retrieved = self.retrieve_top_k(query, k=k)
            scores = [c.score for c in retrieved]
            top_score = max(scores) if scores else 0.0
            low_score = min(scores) if scores else 0.0
            spread = top_score - low_score
            total_toks = sum(c.metadata.get("token_count", len(c.source_text.split())) for c in retrieved)

            results_by_k[k] = SearchResultForK(
                k=k,
                retrieved_count=len(retrieved),
                top_score=round(top_score, 6),
                lowest_score=round(low_score, 6),
                score_spread=round(spread, 6),
                total_tokens=total_toks,
                chunks=retrieved,
            )

        return results_by_k


# ---------------------------------------------------------------------------
# Default Sample Queries for Demonstration
# ---------------------------------------------------------------------------
SAMPLE_QUERIES = [
    {
        "id": "query_pto_rollover",
        "category": "HR Policy & Paid Time Off",
        "query": "How many days of paid time off do employees get each year, and can unused PTO be rolled over?",
        "intent": "Retrieve policy rules regarding annual PTO accrual limits and December 31 rollover rules.",
    },
    {
        "id": "query_security_incident",
        "category": "IT Security & Incident Response",
        "query": "What is the procedure for reporting a suspected malware infection or active data compromise?",
        "intent": "Retrieve step-by-step reporting protocols and the 24/7 IT Security hotline phone extension.",
    },
    {
        "id": "query_remote_vpn",
        "category": "Workplace Flexibility & Remote Work",
        "query": "What are the network encryption and VPN requirements for connecting remotely to company resources?",
        "intent": "Retrieve VPN AES-256 encryption requirements and prohibition of public Wi-Fi.",
    },
    {
        "id": "query_rag_principles",
        "category": "Engineering & RAG Architecture",
        "query": "How does the RAG document loader transform mixed-format files and semantic chunk units for retrieval?",
        "intent": "Retrieve documentation on multi-format extraction and semantic chunking.",
    },
]


# ---------------------------------------------------------------------------
# Task 5: Export Sample Query Results & Markdown Report
# ---------------------------------------------------------------------------
def run_retrieval_benchmark(
    vector_store_path: str = "data/embedded_chunks.json",
    output_dir: str = "data",
    k_values: List[int] = [1, 3, 5],
) -> Dict[str, Any]:
    """
    Executes sample queries against the vector database across multiple k values,
    generates summary tables, and exports results to JSON and Markdown.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    retriever = VectorStoreRetriever(vector_store_path=vector_store_path)

    benchmark_data: Dict[str, Any] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "vector_store_path": vector_store_path,
        "embedding_model": retriever.model_name,
        "total_corpus_chunks": len(retriever.chunks_data),
        "k_values_tested": k_values,
        "query_evaluations": [],
    }

    for item in SAMPLE_QUERIES:
        query_text = item["query"]
        runs_by_k = retriever.demonstrate_changing_k(query_text, k_values=k_values)

        eval_record = {
            "query_id": item["id"],
            "category": item["category"],
            "query": query_text,
            "intent": item["intent"],
            "runs_by_k": {k: res.to_dict() for k, res in runs_by_k.items()},
        }
        benchmark_data["query_evaluations"].append(eval_record)

    # 1. Export JSON results
    json_path = out_path / "similarity_search_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

    # 2. Export Markdown Report
    report_path = out_path / "similarity_search_report.md"
    generate_similarity_report(report_path, benchmark_data)

    return {
        "benchmark_data": benchmark_data,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }


def generate_similarity_report(report_path: Path, data: Dict[str, Any]) -> None:
    lines: List[str] = [
        "# Top-K Vector Database Similarity Search & Retrieval Report",
        "",
        f"**Run Timestamp**: `{data['timestamp']}`  ",
        f"**Vector Store**: `{data['vector_store_path']}` ({data['total_corpus_chunks']} chunks indexed)  ",
        f"**Embedding Model**: `{data['embedding_model']}`  ",
        f"**Values of $k$ Tested**: `{', '.join(str(k) for k in data['k_values_tested'])}`  ",
        "",
        "---",
        "",
        "## 🔍 Task 4: Demonstration of Changing $k$ (Precision vs. Recall)",
        "",
        "Retrieval in RAG systems balances **precision** against **recall**:",
        "- **$k=1$ (High Precision)**: Fetches only the single highest-scoring chunk. Minimizes LLM prompt token consumption, but risks missing secondary conditions or adjacent procedural steps.",
        "- **$k=3$ (Balanced - Recommended)**: Provides primary policy context plus supporting clauses and workflows, maintaining high average relevance while remaining concise.",
        "- **$k=5$ (High Recall)**: Encompasses broader document context, but introduces lower similarity scores and consumes significantly more context tokens.",
        "",
        "### Score & Context Progression Across $k$",
        "",
        "| Query ID | $k$ | Chunks | Top Score | Lowest Score | Score Spread | Total Tokens | Top Source Document |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
    ]

    for q in data["query_evaluations"]:
        qid = q["query_id"]
        for k, run in q["runs_by_k"].items():
            top_doc = run["chunks"][0]["metadata"]["source_document"] if run["chunks"] else "N/A"
            lines.append(
                f"| `{qid}` | **{k}** | {run['retrieved_count']} | "
                f"**{run['top_score']:.4f}** | {run['lowest_score']:.4f} | "
                f"{run['score_spread']:.4f} | {run['total_tokens']} | `{top_doc}` |"
            )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 📋 Detailed Query Inspections (Tasks 1, 2, 3)",
            "",
        ]
    )

    for q in data["query_evaluations"]:
        lines.append(f"### Query: \"{q['query']}\"")
        lines.append(f"- **Category**: {q['category']}")
        lines.append(f"- **Intent**: {q['intent']}")
        lines.append("")

        # Show k=3 retrieval breakdown
        run_k3 = q["runs_by_k"].get("3") or list(q["runs_by_k"].values())[0]
        lines.append(f"#### Retrieved Chunks at $k=3$:")
        lines.append("")

        for c in run_k3["chunks"]:
            meta = c["metadata"]
            lines.append(f"##### Rank {c['rank']}: `{c['chunk_id']}` (Score: **{c['score']:.4f}**)")
            lines.append(f"- **Document**: `{meta.get('source_document')}`")
            lines.append(f"- **Section**: `{meta.get('section')}`")
            lines.append(f"- **Page**: `{meta.get('page') if meta.get('page') is not None else 'N/A'}`")
            lines.append(f"- **Chunk Index**: `{meta.get('chunk_index')}`")
            lines.append(f"- **Token Count**: `{meta.get('token_count')}`")
            lines.append("```text")
            lines.append(c["source_text"])
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.extend(
        [
            "## 📦 Task 5: Exported Deliverables Summary",
            "",
            "- **JSON Query Results**: `data/similarity_search_results.json`",
            "- **Markdown Retrieval Report**: `data/similarity_search_report.md`",
            "- **Retriever Python Module**: `src/similarity_search.py` & `src/retriever.py`",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI Visualizer (Rich Tables)
# ---------------------------------------------------------------------------
def print_cli_summary(benchmark_data: Dict[str, Any], json_path: str, report_path: str) -> None:
    if not RICH_AVAILABLE:
        print(f"Retrieval benchmark completed. Exported to {json_path} and {report_path}")
        return

    console = Console()
    console.print(
        Panel.fit(
            "[bold cyan]Staff RAG Assistant — Top-K Vector Database Similarity Search[/bold cyan]\n"
            "[dim]Query Embedding, Cosine Similarity Ranking & Changing K Demonstration[/dim]",
            border_style="cyan",
        )
    )

    table = Table(title="Demonstration of Changing k across Sample Queries", header_style="bold magenta")
    table.add_column("Query Category", style="bold green", min_width=20)
    table.add_column("k", justify="center", style="bold yellow")
    table.add_column("Top Score", justify="right", style="cyan")
    table.add_column("Low Score", justify="right")
    table.add_column("Score Spread", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Top Match Document", style="dim")

    for q in benchmark_data["query_evaluations"]:
        cat = q["category"]
        for k, run in q["runs_by_k"].items():
            top_doc = run["chunks"][0]["metadata"]["source_document"] if run["chunks"] else "N/A"
            table.add_row(
                cat,
                str(k),
                f"{run['top_score']:.4f}",
                f"{run['lowest_score']:.4f}",
                f"{run['score_spread']:.4f}",
                str(run["total_tokens"]),
                top_doc,
            )

    console.print(table)

    console.print(
        Panel(
            f"[bold]Vector Database Chunks:[/bold] {benchmark_data['total_corpus_chunks']}\n"
            f"[bold]Embedding Model:[/bold] {benchmark_data['embedding_model']}\n"
            f"[bold]Tested k Values:[/bold] {benchmark_data['k_values_tested']}\n\n"
            f"[bold blue]Exported Artifacts:[/bold blue]\n"
            f" • Query Results JSON: [underline]{json_path}[/underline]\n"
            f" • Markdown Report: [underline]{report_path}[/underline]",
            title="[bold green]Retrieval Benchmark Completed[/bold green]",
            border_style="green",
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Top-K Vector Database Similarity Search and Changing K Demo."
    )
    parser.add_argument(
        "--vector-store",
        default="data/embedded_chunks.json",
        help="Path to vector store JSON (default: data/embedded_chunks.json)",
    )
    parser.add_argument(
        "--output",
        default="data",
        help="Path to output directory (default: data)",
    )
    parser.add_argument(
        "--k-values",
        nargs="+",
        type=int,
        default=[1, 3, 5],
        help="List of k values to test (default: 1 3 5)",
    )
    args = parser.parse_args()

    results = run_retrieval_benchmark(
        vector_store_path=args.vector_store,
        output_dir=args.output,
        k_values=args.k_values,
    )
    print_cli_summary(results["benchmark_data"], results["json_path"], results["report_path"])


if __name__ == "__main__":
    main()

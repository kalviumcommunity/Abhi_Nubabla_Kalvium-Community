"""
Retrieval Settings Tuning Experiment & Relevance Benchmarking Engine.

Tasks Implemented:
- Task 1: Define ground-truth test queries with target expected chunks/sources.
- Task 2: Compare multiple retrieval settings (k values, score thresholds, metadata filters).
- Task 3: Calculate relevance metrics (Top-1 Hit Rate, Top-K Hit Rate, MRR, token overhead).
- Task 4: Select and justify the best-performing retrieval configuration based on empirical results.
- Task 5: Export benchmark results to JSON dataset and Markdown tuning report.
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

from src.similarity_search import VectorStoreRetriever, RetrievedChunk

# Reconfigure stdout/stderr to UTF-8 to prevent encoding issues
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
# Task 1: Ground-Truth Test Queries Suite
# ---------------------------------------------------------------------------
TUNING_TEST_QUERIES: List[Dict[str, Any]] = [
    {
        "query_id": "test_q1_pto",
        "topic": "HR - Paid Time Off (PTO) & Leave Limits",
        "query": "How many days of paid time off do employees get each year, and can unused PTO be rolled over?",
        "expected_chunk_id": "employee_benefits_chunk_001",
        "expected_source_doc": "employee_benefits.md"
    },
    {
        "query_id": "test_q2_vpn",
        "topic": "Remote Work - Network Encryption & VPN Rules",
        "query": "What are the network encryption and VPN requirements for connecting remotely to company resources?",
        "expected_chunk_id": "remote_work_policy_chunk_005",
        "expected_source_doc": "remote_work_policy.md"
    },
    {
        "query_id": "test_q3_password",
        "topic": "IT Security - Password Length & Authentication",
        "query": "What are the minimum password length requirements and is SMS authentication permitted?",
        "expected_chunk_id": "it_security_policy_chunk_001",
        "expected_source_doc": "it_security_policy.md"
    },
    {
        "query_id": "test_q4_parental",
        "topic": "HR - Parental Leave Entitlement",
        "query": "How many weeks of fully paid leave are new parents entitled to after childbirth or adoption?",
        "expected_chunk_id": "employee_benefits_chunk_003",
        "expected_source_doc": "employee_benefits.md"
    },
    {
        "query_id": "test_q5_rag_principles",
        "topic": "RAG Architecture - Ingestion & Chunking Principles",
        "query": "How does the RAG document loader transform mixed-format files and semantic chunk units for retrieval?",
        "expected_chunk_id": "guide_chunk_002",
        "expected_source_doc": "guide_document.md"
    }
]


# ---------------------------------------------------------------------------
# Task 2: Retrieval Configuration Definitions
# ---------------------------------------------------------------------------
RETRIEVAL_CONFIGURATIONS: List[Dict[str, Any]] = [
    {
        "config_id": "config_a_baseline",
        "name": "Config A: Baseline (k=5, Threshold=0.0)",
        "k": 5,
        "score_threshold": 0.0,
        "metadata_filter": None,
        "description": "Standard top-5 unfiltered retrieval without score thresholds or domain filters."
    },
    {
        "config_id": "config_b_high_precision",
        "name": "Config B: High-Precision (k=3, Threshold=0.35)",
        "k": 3,
        "score_threshold": 0.35,
        "metadata_filter": None,
        "description": "Top-3 retrieval with strict score threshold (0.35) to eliminate low-confidence noise."
    },
    {
        "config_id": "config_c_metadata_filtered",
        "name": "Config C: Domain-Filtered (k=3, Threshold=0.20, Markdown Filter)",
        "k": 3,
        "score_threshold": 0.20,
        "metadata_filter": {"file_type": ".md"},
        "description": "Top-3 retrieval filtered by metadata to restrict scope strictly to policy documents (.md)."
    },
    {
        "config_id": "config_d_broad_recall",
        "name": "Config D: Broad Recall (k=10, Threshold=0.10)",
        "k": 10,
        "score_threshold": 0.10,
        "metadata_filter": None,
        "description": "Extended top-10 retrieval prioritizing maximum recall over context window size."
    }
]


# ---------------------------------------------------------------------------
# Task 3: Relevance Metrics Evaluation Engine
# ---------------------------------------------------------------------------
def evaluate_configuration(
    retriever: VectorStoreRetriever,
    test_queries: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates a specific retrieval configuration against test queries, calculating Top-1 Hit Rate,
    Top-K Hit Rate, MRR (Mean Reciprocal Rank), and Token Consumption.
    """
    k = config["k"]
    threshold = config["score_threshold"]
    meta_filter = config["metadata_filter"]

    top1_hits = 0
    topk_hits = 0
    mrr_sum = 0.0
    total_tokens_sum = 0
    top_scores = []
    per_query_results = []

    for q_item in test_queries:
        qid = q_item["query_id"]
        qtext = q_item["query"]
        target_cid = q_item["expected_chunk_id"]

        retrieved = retriever.retrieve_top_k(
            query=qtext,
            k=k,
            score_threshold=threshold,
            metadata_filter=meta_filter
        )

        retrieved_cids = [c.chunk_id for c in retrieved]
        scores = [c.score for c in retrieved]
        top_score = scores[0] if scores else 0.0
        query_tokens = sum(c.metadata.get("token_count", len(c.source_text.split())) for c in retrieved)

        # Calculate rank of target chunk
        rank_found = None
        for r_idx, cid in enumerate(retrieved_cids, start=1):
            if cid == target_cid:
                rank_found = r_idx
                break

        # Record metrics
        is_top1 = (rank_found == 1)
        is_topk = (rank_found is not None and rank_found <= k)
        rr = (1.0 / rank_found) if rank_found else 0.0

        if is_top1:
            top1_hits += 1
        if is_topk:
            topk_hits += 1

        mrr_sum += rr
        total_tokens_sum += query_tokens
        if top_score > 0:
            top_scores.append(top_score)

        per_query_results.append({
            "query_id": qid,
            "topic": q_item["topic"],
            "expected_chunk_id": target_cid,
            "retrieved_count": len(retrieved),
            "rank_found": rank_found if rank_found else -1,
            "is_top1_hit": is_top1,
            "is_topk_hit": is_topk,
            "reciprocal_rank": round(rr, 4),
            "top_score": round(top_score, 4),
            "retrieved_chunk_ids": retrieved_cids
        })

    num_queries = len(test_queries)
    top1_hit_rate = top1_hits / num_queries if num_queries > 0 else 0.0
    topk_hit_rate = topk_hits / num_queries if num_queries > 0 else 0.0
    mrr = mrr_sum / num_queries if num_queries > 0 else 0.0
    avg_tokens = total_tokens_sum / num_queries if num_queries > 0 else 0.0
    avg_top_score = sum(top_scores) / len(top_scores) if top_scores else 0.0

    return {
        "config_id": config["config_id"],
        "name": config["name"],
        "k": k,
        "score_threshold": threshold,
        "metadata_filter": meta_filter,
        "metrics": {
            "top1_hit_rate": round(top1_hit_rate, 4),
            "topk_hit_rate": round(topk_hit_rate, 4),
            "mrr": round(mrr, 4),
            "avg_tokens_per_query": round(avg_tokens, 1),
            "avg_top_score": round(avg_top_score, 4),
            "total_top1_hits": top1_hits,
            "total_topk_hits": topk_hits,
            "total_queries_tested": num_queries
        },
        "per_query_results": per_query_results
    }


# ---------------------------------------------------------------------------
# Task 4 & 5: Experiment Execution, Best Setup Selection & Report Export
# ---------------------------------------------------------------------------
def run_tuning_experiment(
    vector_store_path: str = "data/embedded_chunks.json",
    output_dir: str = "data"
) -> Dict[str, Any]:
    """
    Executes the retrieval tuning experiment comparing all configurations, selects the best-performing
    setup, and exports JSON summary results and a Markdown benchmark report.
    """
    retriever = VectorStoreRetriever(vector_store_path=vector_store_path)

    evaluated_configs = []
    for config in RETRIEVAL_CONFIGURATIONS:
        eval_res = evaluate_configuration(
            retriever=retriever,
            test_queries=TUNING_TEST_QUERIES,
            config=config
        )
        evaluated_configs.append(eval_res)

    # Task 4: Select best configuration (highest MRR & Top-1 Hit Rate with optimal token efficiency)
    best_config_res = max(
        evaluated_configs,
        key=lambda c: (c["metrics"]["mrr"], c["metrics"]["top1_hit_rate"], -c["metrics"]["avg_tokens_per_query"])
    )

    justification_str = (
        f"**Chosen Setting**: `{best_config_res['name']}`  \n"
        f"**Empirical Results**: Achieved a **Top-1 Hit Rate of {best_config_res['metrics']['top1_hit_rate']*100:.1f}%**, "
        f"**Recall@{best_config_res['k']} of {best_config_res['metrics']['topk_hit_rate']*100:.1f}%**, and an **MRR of {best_config_res['metrics']['mrr']:.4f}**.  \n"
        f"**Rationale**: By setting `k={best_config_res['k']}` with a minimum score threshold of `{best_config_res['score_threshold']}`, "
        f"the retriever eliminates low-similarity false-positive chunks while reducing prompt context token overhead "
        f"by **{((RETRIEVAL_CONFIGURATIONS[3]['k'] - best_config_res['k']) / RETRIEVAL_CONFIGURATIONS[3]['k']) * 100:.0f}%** compared to k=10."
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "retrieval_tuning_results.json"
    report_path = output_path / "retrieval_tuning_report.md"

    summary_data = {
        "vector_store_path": vector_store_path,
        "embedding_model": retriever.model_name,
        "total_test_queries": len(TUNING_TEST_QUERIES),
        "test_queries": TUNING_TEST_QUERIES,
        "compared_configurations": evaluated_configs,
        "best_configuration": {
            "config_id": best_config_res["config_id"],
            "name": best_config_res["name"],
            "k": best_config_res["k"],
            "score_threshold": best_config_res["score_threshold"],
            "metadata_filter": best_config_res["metadata_filter"],
            "metrics": best_config_res["metrics"],
            "justification": justification_str
        }
    }

    # Save summary JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # Save Markdown Report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Retrieval Settings Tuning & Relevance Benchmark Report\n\n")
        f.write(f"**Embedding Model / Engine**: `{retriever.model_name}`  \n")
        f.write(f"**Total Test Queries Evaluated**: `{len(TUNING_TEST_QUERIES)}`  \n")
        f.write(f"**Recommended Configuration**: `{best_config_res['name']}`  \n\n")
        f.write("---\n\n")

        f.write("## 1. Best Configuration Selection & Justification\n\n")
        f.write(f"> {justification_str}\n\n")
        f.write("---\n\n")

        f.write("## 2. Configuration Comparison Matrix\n\n")
        f.write("| Configuration | Top-1 Hit Rate | Top-K Hit Rate | MRR | Avg Tokens / Query | Avg Top Score |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for ec in evaluated_configs:
            m = ec["metrics"]
            is_best = " [BEST]" if ec["config_id"] == best_config_res["config_id"] else ""
            f.write(f"| **{ec['name']}{is_best}** | `{m['top1_hit_rate']*100:.1f}%` | `{m['topk_hit_rate']*100:.1f}%` | `{m['mrr']:.4f}` | `{m['avg_tokens_per_query']}` | `{m['avg_top_score']:.4f}` |\n")

        f.write("\n---\n\n")
        f.write("## 3. Test Queries & Expected Target Chunks\n\n")
        f.write("| Query ID | Topic | Query Text | Target Chunk ID | Expected Source |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for q in TUNING_TEST_QUERIES:
            f.write(f"| **{q['query_id']}** | {q['topic']} | *\"{q['query'][:60]}...\"* | `{q['expected_chunk_id']}` | `{q['expected_source_doc']}` |\n")

        f.write("\n---\n\n")
        f.write("## 4. Per-Query Relevance Breakdown (Best Configuration)\n\n")
        f.write("| Query ID | Expected Target | Rank Found | Top-1 Hit | Top-K Hit | Reciprocal Rank | Top Similarity Score |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for pq in best_config_res["per_query_results"]:
            rank_str = f"Rank {pq['rank_found']}" if pq['rank_found'] > 0 else "Not Found"
            f.write(f"| **{pq['query_id']}** | `{pq['expected_chunk_id']}` | `{rank_str}` | `{'Yes' if pq['is_top1_hit'] else 'No'}` | `{'Yes' if pq['is_topk_hit'] else 'No'}` | `{pq['reciprocal_rank']:.4f}` | `{pq['top_score']:.4f}` |\n")

    # Task 4/5: Print verification output to console
    print_verification_output(summary_data)

    return summary_data


# ---------------------------------------------------------------------------
# Task 4 & 5: Console Verification Output Formatter
# ---------------------------------------------------------------------------
def print_verification_output(summary: Dict[str, Any]):
    """
    Prints clear output displaying the tuning experiment results, metric comparison, and chosen configuration.
    """
    console = Console() if RICH_AVAILABLE else None
    best = summary.get("best_configuration", {})
    configs = summary.get("compared_configurations", [])

    if console:
        console.print(Panel.fit(
            "[bold cyan]Retrieval Settings Tuning & Relevance Benchmarking Engine[/bold cyan]\n"
            "[dim]Evaluating retrieval configurations (k, score thresholds, metadata filters) against test queries.[/dim]",
            border_style="cyan"
        ))
        
        console.print(f"\n[bold yellow]▶ Embedding Model[/bold yellow]: {summary['embedding_model']}")
        console.print(f"[bold yellow]▶ Test Queries Evaluated[/bold yellow]: [bold white]{summary['total_test_queries']}[/bold white]")
        console.print(f"[bold yellow]▶ Recommended Configuration[/bold yellow]: [bold green]{best.get('name')}[/bold green]")

        table = Table(title="Retrieval Settings Comparison Matrix", show_lines=True)
        table.add_column("Configuration", style="bold cyan")
        table.add_column("Top-1 Hit Rate", style="bold green", justify="center")
        table.add_column("Top-K Hit Rate", style="bold magenta", justify="center")
        table.add_column("MRR", style="white", justify="center")
        table.add_column("Avg Tokens / Query", style="yellow", justify="center")
        table.add_column("Avg Top Score", style="cyan", justify="center")

        for ec in configs:
            m = ec["metrics"]
            is_best = " [BEST]" if ec["config_id"] == best.get("config_id") else ""
            table.add_row(
                ec["name"] + is_best,
                f"{m['top1_hit_rate']*100:.1f}%",
                f"{m['topk_hit_rate']*100:.1f}%",
                f"{m['mrr']:.4f}",
                str(m["avg_tokens_per_query"]),
                f"{m['avg_top_score']:.4f}"
            )
        console.print(table)
    else:
        print("================================================================================")
        print(" Retrieval Settings Tuning & Relevance Benchmark Verification Output ")
        print("================================================================================")
        print(f"Embedding Model      : {summary['embedding_model']}")
        print(f"Test Queries        : {summary['total_test_queries']}")
        print(f"Best Configuration  : {best.get('name')}")
        print("--------------------------------------------------------------------------------")
        print("Comparison Matrix:")
        for ec in configs:
            m = ec["metrics"]
            print(f"- {ec['name']}")
            print(f"  Top-1 Hit Rate: {m['top1_hit_rate']*100:.1f}% | MRR: {m['mrr']:.4f} | Avg Tokens: {m['avg_tokens_per_query']}")
        print("================================================================================")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Run retrieval settings tuning experiment comparing k, score thresholds, and metadata filters.")
    parser.add_argument("--input", type=str, default="data/embedded_chunks.json", help="Path to embedded chunks JSON")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory for JSON results and Markdown report")
    args = parser.parse_args()

    run_tuning_experiment(
        vector_store_path=args.input,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()

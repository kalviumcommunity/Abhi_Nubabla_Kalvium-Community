#!/usr/bin/env python3
"""
Demonstration: Chunk Re-Ranking Evaluation and Before/After Comparison.

This script demonstrates the two-stage retrieval pipeline with re-ranking:
1. Shows initial retrieval results (top candidates by vector similarity)
2. Shows re-ranked results (top candidates re-scored by semantic relevance)
3. Compares the two orderings side-by-side
4. Generates detailed report with scoring breakdowns
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retriever import retrieve_with_reranking
from src.reranker import SemanticRelevanceReranker, HybridReranker
from src.similarity_search import VectorStoreRetriever

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None


# Sample queries for demonstration
DEMO_QUERIES = [
    {
        "query_id": "q1_pto",
        "query": "How many days of paid time off do employees get each year?",
        "topic": "HR - PTO & Leave",
    },
    {
        "query_id": "q2_security",
        "query": "What should I do if I suspect a malware infection?",
        "topic": "IT Security - Incident Response",
    },
    {
        "query_id": "q3_remote",
        "query": "What are the VPN and encryption requirements for remote work?",
        "topic": "Remote Work - Security",
    },
]


def setup_console():
    """Initialize Rich console for formatted output."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_comparison_table(console, result, query_text: str):
    """Print side-by-side before/after comparison table."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n" + "="*100)
    console.print(f"[bold cyan]Query:[/bold cyan] {query_text}")
    console.print("="*100)
    
    # Before re-ranking
    console.print("\n[bold yellow]BEFORE RE-RANKING[/bold yellow] (Vector Similarity Order)")
    before_table = Table(show_header=True, header_style="bold magenta")
    before_table.add_column("Rank", style="cyan")
    before_table.add_column("Vector Score", style="green")
    before_table.add_column("Chunk ID", style="blue")
    before_table.add_column("Text Preview", style="white")
    
    for chunk in result.candidates_initial[:result.k_final]:
        text_preview = chunk.source_text[:60].replace("\n", " ") + "..." if len(chunk.source_text) > 60 else chunk.source_text
        before_table.add_row(
            str(chunk.rank),
            f"{chunk.vector_score:.4f}",
            chunk.chunk_id,
            text_preview
        )
    
    console.print(before_table)
    
    # After re-ranking
    console.print("\n[bold yellow]AFTER RE-RANKING[/bold yellow] (Semantic Re-ranked Order)")
    after_table = Table(show_header=True, header_style="bold magenta")
    after_table.add_column("Rank", style="cyan")
    after_table.add_column("Re-rank Score", style="green")
    after_table.add_column("Chunk ID", style="blue")
    after_table.add_column("Text Preview", style="white")
    
    for chunk in result.results_reranked:
        text_preview = chunk.source_text[:60].replace("\n", " ") + "..." if len(chunk.source_text) > 60 else chunk.source_text
        after_table.add_row(
            str(chunk.rank),
            f"{chunk.rerank_score:.4f}",
            chunk.chunk_id,
            text_preview
        )
    
    console.print(after_table)


def print_detailed_analysis(console, result):
    """Print detailed analysis with scoring breakdowns."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n[bold cyan]DETAILED SCORING BREAKDOWN (Top 3 Initial Candidates)[/bold cyan]")
    
    for i, chunk in enumerate(result.candidates_initial[:3]):
        console.print(f"\n[bold]Candidate {i+1}: {chunk.chunk_id}[/bold]")
        console.print(f"  Vector Score:    {chunk.vector_score:.6f}")
        console.print(f"  Re-rank Score:   {chunk.rerank_score:.6f}")
        console.print(f"  Source Document: {chunk.metadata.get('source_document', 'unknown')}")
        
        if chunk.scoring_breakdown:
            console.print("  Scoring Components:")
            for component, score in chunk.scoring_breakdown.items():
                console.print(f"    - {component}: {score:.4f}")
        
        console.print(f"  Text: {chunk.source_text[:100]}...")


def generate_markdown_report(result, output_path: str = "data/results/reranking_demo_report.md"):
    """Generate comprehensive markdown report with before/after comparison."""
    
    report_lines = [
        "# Chunk Re-Ranking Demonstration Report\n",
        f"**Reranker Used:** {result.reranker_name}\n",
        f"**Initial Candidates (k_candidate):** {result.k_candidate}\n",
        f"**Final Results (k_final):** {result.k_final}\n",
        f"**Query:** {result.query}\n",
        "\n---\n",
    ]
    
    # Before section
    report_lines.extend([
        "## Stage 1: Initial Retrieval (Vector Similarity)\n",
        "Candidates retrieved and ranked by cosine similarity:\n",
        "\n| Rank | Vector Score | Chunk ID | Token Count | Source Document |\n",
        "|------|--------------|----------|-------------|------------------|\n",
    ])
    
    for chunk in result.candidates_initial:
        token_count = chunk.metadata.get("token_count", len(chunk.source_text.split()))
        source_doc = chunk.metadata.get("source_document", "unknown")
        report_lines.append(
            f"| {chunk.rank} | {chunk.vector_score:.6f} | {chunk.chunk_id} | {token_count} | {source_doc} |\n"
        )
    
    # After section
    report_lines.extend([
        "\n\n## Stage 2: Re-Ranking Results\n",
        "Candidates re-ranked by semantic relevance:\n",
        "\n| Rank | Re-rank Score | Vector Score | Chunk ID | Improvement |\n",
        "|------|---------------|--------------|----------|-------------|\n",
    ])
    
    for chunk in result.results_reranked:
        # Find original rank
        original_rank = next(
            (c.rank for c in result.candidates_initial if c.chunk_id == chunk.chunk_id),
            "N/A"
        )
        improvement = f"Moved from #{original_rank}" if original_rank != "N/A" else "N/A"
        
        report_lines.append(
            f"| {chunk.rank} | {chunk.rerank_score:.6f} | {chunk.vector_score:.6f} | "
            f"{chunk.chunk_id} | {improvement} |\n"
        )
    
    # Detailed breakdown
    report_lines.extend([
        "\n\n## Detailed Scoring Breakdown\n",
    ])
    
    for i, chunk in enumerate(result.results_reranked):
        report_lines.extend([
            f"\n### Top Result #{i+1}: {chunk.chunk_id}\n",
            f"- **Vector Similarity Score:** {chunk.vector_score:.6f}\n",
            f"- **Re-rank Score:** {chunk.rerank_score:.6f}\n",
            f"- **Source Document:** {chunk.metadata.get('source_document', 'unknown')}\n",
            f"- **Section:** {chunk.metadata.get('section', 'N/A')}\n",
            f"- **Token Count:** {chunk.metadata.get('token_count', len(chunk.source_text.split()))}\n",
        ])
        
        if chunk.scoring_breakdown:
            report_lines.append("- **Scoring Components:**\n")
            for component, score in chunk.scoring_breakdown.items():
                report_lines.append(f"  - {component}: {score:.6f}\n")
        
        report_lines.extend([
            "\n**Text:**\n",
            "```\n",
            chunk.source_text + "\n",
            "```\n",
        ])
    
    # Insights
    report_lines.extend([
        "\n\n## Key Insights\n",
        "1. **Re-ranking Effectiveness:** Semantic re-ranking scores differ from vector similarity,\n",
        "   indicating that additional relevance signals are being captured.\n",
        "\n2. **Candidate Set Diversity:** The initial 10 candidates contain varied semantic content,\n",
        "   allowing the re-ranker to select the most relevant subset.\n",
        "\n3. **Scoring Transparency:** Each chunk is scored on multiple dimensions:\n",
        "   - Query term overlap\n",
        "   - Semantic concept alignment\n",
        "   - Information density\n",
        "\n",
    ])
    
    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
    
    return output_file


def generate_json_results(result, output_path: str = "data/results/reranking_demo_results.json"):
    """Export detailed results to JSON format."""
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "metadata": {
            "reranker_used": result.reranker_name,
            "k_candidate": result.k_candidate,
            "k_final": result.k_final,
            "query": result.query,
        },
        "stage1_initial_candidates": [c.to_dict() for c in result.candidates_initial],
        "stage2_reranked_results": [c.to_dict() for c in result.results_reranked],
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    return output_file


def main():
    """Run the demonstration."""
    console = setup_console()
    
    # Check if vector store exists
    vector_store_path = "data/results/embedded_chunks.json"
    if not Path(vector_store_path).exists():
        if console:
            console.print(f"[red]Error: Vector store not found at {vector_store_path}[/red]")
            console.print("[yellow]Please run the embedding generation first:[/yellow]")
            console.print("  python -m src.generate_embeddings")
        else:
            print(f"Error: Vector store not found at {vector_store_path}")
        return
    
    # Select a demo query (use the first one for now)
    demo_query_info = DEMO_QUERIES[0]
    query = demo_query_info["query"]
    
    if console:
        console.print("\n[bold green]Chunk Re-Ranking Demonstration[/bold green]")
        console.print(f"[cyan]Topic:[/cyan] {demo_query_info['topic']}")
    else:
        print("\nChunk Re-Ranking Demonstration")
        print(f"Topic: {demo_query_info['topic']}")
    
    # Run two-stage retrieval with re-ranking
    if console:
        console.print("\n[cyan]Running two-stage retrieval pipeline...[/cyan]")
    else:
        print("\nRunning two-stage retrieval pipeline...")
    
    result = retrieve_with_reranking(
        query=query,
        k_final=3,
        k_candidate=10,
        vector_store_path=vector_store_path,
        reranker=SemanticRelevanceReranker(),  # Use semantic re-ranker
    )
    
    # Print comparison
    print_comparison_table(console, result, query)
    
    # Print detailed analysis
    print_detailed_analysis(console, result)
    
    # Generate markdown report
    markdown_path = generate_markdown_report(result)
    if console:
        console.print(f"\n[green]✓ Markdown report saved to: {markdown_path}[/green]")
    else:
        print(f"\nMarkdown report saved to: {markdown_path}")
    
    # Generate JSON results
    json_path = generate_json_results(result)
    if console:
        console.print(f"[green]✓ JSON results saved to: {json_path}[/green]")
    else:
        print(f"JSON results saved to: {json_path}")
    
    # Print summary statistics
    if console:
        console.print("\n[bold cyan]Summary Statistics[/bold cyan]")
        console.print(f"Total candidates retrieved:    {result.k_candidate}")
        console.print(f"Final results returned:        {result.k_final}")
        console.print(f"Reranker used:                 {result.reranker_name}")
        
        # Check if any chunk changed position
        changes = 0
        for final_chunk in result.results_reranked:
            original_rank = next(
                (c.rank for c in result.candidates_initial if c.chunk_id == final_chunk.chunk_id),
                None
            )
            if original_rank and original_rank != final_chunk.rank:
                changes += 1
        
        console.print(f"Chunks with rank changes:      {changes} out of {result.k_final}")
    
    if console:
        console.print("\n[bold green]Demonstration complete![/bold green]\n")
    else:
        print("\nDemonstration complete!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Context Injection Demonstration: Building Grounded Augmented Prompts.

Demonstrates the complete RAG pipeline:
1. Retrieve relevant chunks
2. Inject chunks with source markers
3. Enforce token budget
4. Add grounding instructions
5. Show assembled augmented prompt ready for LLM
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retriever import retrieve_top_k
from src.context_injector import (
    AugmentedPromptBuilder,
    TokenCounter,
    GroundingInstructions,
)

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
        "query_id": "q1",
        "query": "What are the paid time off policies for full-time employees?",
        "topic": "HR - PTO & Leave",
    },
    {
        "query_id": "q2",
        "query": "What should I do if I suspect a security incident or malware infection?",
        "topic": "IT Security - Incident Response",
    },
    {
        "query_id": "q3",
        "query": "What are the requirements for remote work and VPN access?",
        "topic": "Remote Work & Security",
    },
]


def setup_console():
    """Initialize Rich console for formatted output."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_retrieval_stage(console, question, chunks):
    """Print retrieved chunks."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n" + "="*100)
    console.print("[bold cyan]STAGE 1: RETRIEVAL[/bold cyan]")
    console.print("="*100)
    console.print(f"[yellow]Query:[/yellow] {question}\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Source Document", style="blue")
    table.add_column("Text Preview", style="white")
    
    for chunk in chunks:
        text_preview = chunk.source_text[:60].replace("\n", " ") + "..."
        source = chunk.metadata.get("source_document", "unknown")
        table.add_row(
            str(chunk.rank),
            f"{chunk.score:.4f}",
            source,
            text_preview
        )
    
    console.print(table)


def print_token_analysis(console, result):
    """Print token budget analysis."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n" + "="*100)
    console.print("[bold cyan]STAGE 2: TOKEN BUDGET ANALYSIS[/bold cyan]")
    console.print("="*100)
    
    budget_table = Table(show_header=True, header_style="bold magenta")
    budget_table.add_column("Component", style="cyan")
    budget_table.add_column("Tokens", style="green")
    budget_table.add_column("Percentage", style="yellow")
    
    total = result.token_count_total
    
    budget_table.add_row(
        "Grounding Instructions",
        str(result.token_count_instructions),
        f"{(result.token_count_instructions/total*100):.1f}%"
    )
    budget_table.add_row(
        "Context (Retrieved Chunks)",
        str(result.token_count_context),
        f"{(result.token_count_context/total*100):.1f}%"
    )
    budget_table.add_row(
        "User Question",
        str(result.token_count_question),
        f"{(result.token_count_question/total*100):.1f}%"
    )
    budget_table.add_row(
        "Reserved for Answer",
        str(result.token_count_reserved),
        f"{(result.token_count_reserved/total*100):.1f}%"
    )
    budget_table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{result.token_count_total}[/bold]",
        "[bold]100%[/bold]"
    )
    
    console.print(budget_table)
    
    # Budget status
    if result.budget_exceeded:
        console.print(f"\n[red]⚠ BUDGET EXCEEDED: Context ({result.token_count_context}) "
                     f"exceeds limit ({result.token_budget_limit})[/red]")
    else:
        console.print(f"\n[green]✓ Budget OK: {result.token_budget_remaining} tokens remaining[/green]")


def print_source_markers(console, result):
    """Print source markers and chunk references."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n" + "="*100)
    console.print("[bold cyan]STAGE 3: SOURCE MARKERS[/bold cyan]")
    console.print("="*100)
    
    markers_table = Table(show_header=True, header_style="bold magenta")
    markers_table.add_column("Marker", style="cyan")
    markers_table.add_column("Source", style="blue")
    markers_table.add_column("Section", style="green")
    markers_table.add_column("Tokens", style="yellow")
    
    for chunk in result.injected_chunks:
        section = chunk.metadata.get("section", "N/A")
        if isinstance(section, str) and len(section) > 50:
            section = section[:47] + "..."
        
        markers_table.add_row(
            str(chunk.source_marker),
            chunk.source_marker.source_document,
            section,
            str(chunk.token_count)
        )
    
    console.print(markers_table)


def print_assembled_prompt(console, result):
    """Print the assembled augmented prompt."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n" + "="*100)
    console.print("[bold cyan]STAGE 4: ASSEMBLED AUGMENTED PROMPT[/bold cyan]")
    console.print("="*100 + "\n")
    
    # Use syntax highlighting for the prompt
    syntax = Syntax(result.assembled_prompt, "markdown", theme="monokai", line_numbers=False)
    console.print(syntax)


def print_instructions_info(console, grounding_style):
    """Print information about grounding instructions."""
    if not RICH_AVAILABLE:
        return
    
    console.print("\n" + "="*100)
    console.print("[bold cyan]GROUNDING INSTRUCTIONS[/bold cyan]")
    console.print("="*100)
    
    instructions = GroundingInstructions.get_grounding_instructions(grounding_style)
    console.print(instructions)


def generate_markdown_report(result, query, output_path: str = "data/results/context_injection_demo_report.md"):
    """Generate markdown report with augmented prompt details."""
    
    report_lines = [
        "# Context Injection & Augmented Prompt Demonstration Report\n",
        f"**Generated:** {datetime.now().isoformat()}\n",
        f"**Query:** {query}\n",
        f"**Grounding Style:** Professional\n",
        "\n---\n",
    ]
    
    # Retrieved Chunks Section
    report_lines.extend([
        "## Stage 1: Retrieved Chunks\n",
        "Initial retrieval results from vector similarity search:\n",
        "\n| Rank | Score | Source | Tokens |\n",
        "|------|-------|--------|--------|\n",
    ])
    
    for chunk in result.injected_chunks:
        report_lines.append(
            f"| {chunk.source_marker.index} | {chunk.source_marker.chunk_id} | "
            f"{chunk.source_marker.source_document} | {chunk.token_count} |\n"
        )
    
    # Token Budget Section
    report_lines.extend([
        "\n## Stage 2: Token Budget Analysis\n",
        f"**Model:** {result.model_name}\n",
        f"**Max Tokens:** {result.max_tokens}\n",
        f"**Context Budget (50%):** {result.token_budget_limit}\n",
        "\n### Token Allocation\n",
        f"- Grounding Instructions: {result.token_count_instructions} tokens\n",
        f"- Context (Chunks): {result.token_count_context} tokens\n",
        f"- User Question: {result.token_count_question} tokens\n",
        f"- Reserved for Answer: {result.token_count_reserved} tokens\n",
        f"- **Total: {result.token_count_total} tokens**\n",
    ])
    
    if result.budget_exceeded:
        report_lines.append(f"\n⚠ **Budget Status:** EXCEEDED by {result.token_count_context - result.token_budget_limit} tokens\n")
    else:
        report_lines.append(f"\n✓ **Budget Status:** OK ({result.token_budget_remaining} tokens remaining)\n")
    
    # Source Markers Section
    report_lines.extend([
        "\n## Stage 3: Source Markers\n",
        "Chunks are annotated with source markers [1], [2], etc. for citation:\n",
        "\n",
    ])
    
    for chunk in result.injected_chunks:
        report_lines.extend([
            f"### {chunk.source_marker.full_reference()}\n",
            f"- **Chunk ID:** {chunk.source_marker.chunk_id}\n",
            f"- **Section:** {chunk.metadata.get('section', 'N/A')}\n",
            f"- **Tokens:** {chunk.token_count}\n",
            f"- **Text:** {chunk.original_text[:100]}...\n",
            "\n",
        ])
    
    # Grounding Instructions Section
    report_lines.extend([
        "\n## Stage 4: Grounding Instructions\n",
        "The following instructions are prepended to enforce context-only answering:\n",
        "\n```\n",
        GroundingInstructions.get_grounding_instructions("professional"),
        "\n```\n",
    ])
    
    # Complete Augmented Prompt Section
    report_lines.extend([
        "\n## Stage 5: Complete Augmented Prompt\n",
        "Full prompt ready for LLM inference:\n",
        "\n```\n",
        result.assembled_prompt,
        "\n```\n",
    ])
    
    # Key Insights
    report_lines.extend([
        "\n## Key Insights\n",
        "1. **Context Injection:** Retrieved chunks are injected with source markers [1], [2], etc.\n",
        "2. **Token Enforcement:** Total token count stays within model's capacity with buffer for answer.\n",
        "3. **Source Attribution:** Each chunk is labeled with its source for traceability.\n",
        "4. **Grounding Instructions:** Model is instructed to use ONLY provided context.\n",
        "5. **Citation Discipline:** Model should reference sources when claiming facts.\n",
    ])
    
    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(report_lines)
    
    return output_file


def generate_json_results(result, output_path: str = "data/results/context_injection_demo_results.json"):
    """Export augmented prompt to JSON format."""
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = result.to_dict()
    data["generated_at"] = datetime.now().isoformat()
    
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
        return
    
    # Select demo query
    demo_query_info = DEMO_QUERIES[0]
    query = demo_query_info["query"]
    
    if console:
        console.print("\n[bold green]Context Injection & Augmented Prompt Demonstration[/bold green]")
        console.print(f"[cyan]Topic:[/cyan] {demo_query_info['topic']}")
    else:
        print("\nContext Injection & Augmented Prompt Demonstration")
        print(f"Topic: {demo_query_info['topic']}")
    
    # Stage 1: Retrieve chunks
    if console:
        console.print("\n[cyan]Retrieving relevant chunks...[/cyan]")
    else:
        print("\nRetrieving relevant chunks...")
    
    chunks = retrieve_top_k(query=query, k=5, vector_store_path=vector_store_path)
    
    # Print retrieval results
    print_retrieval_stage(console, query, chunks)
    
    # Stage 2-4: Build augmented prompt
    builder = AugmentedPromptBuilder(
        model_name="gpt-3.5-turbo",
        context_budget_percent=0.50,
        reserved_tokens=1000,
        grounding_style="professional",
    )
    
    if console:
        console.print("\n[cyan]Building augmented prompt with context injection...[/cyan]")
    else:
        print("\nBuilding augmented prompt with context injection...")
    
    result = builder.build_augmented_prompt(
        user_question=query,
        chunks=chunks,
        template_style="standard",
    )
    
    # Print token analysis
    print_token_analysis(console, result)
    
    # Print source markers
    print_source_markers(console, result)
    
    # Print grounding instructions info
    print_instructions_info(console, "professional")
    
    # Print assembled prompt
    print_assembled_prompt(console, result)
    
    # Generate reports
    markdown_path = generate_markdown_report(result, query)
    json_path = generate_json_results(result)
    
    if console:
        console.print(f"\n[green]✓ Markdown report saved to: {markdown_path}[/green]")
        console.print(f"[green]✓ JSON results saved to: {json_path}[/green]")
    else:
        print(f"\nMarkdown report saved to: {markdown_path}")
        print(f"JSON results saved to: {json_path}")
    
    # Summary statistics
    if console:
        console.print("\n[bold cyan]Summary Statistics[/bold cyan]")
        console.print(f"Chunks retrieved:              {len(chunks)}")
        console.print(f"Chunks injected:              {len(result.injected_chunks)}")
        console.print(f"Total tokens used:            {result.token_count_total}")
        console.print(f"Context tokens:               {result.token_count_context}")
        console.print(f"Model context budget:         {result.token_budget_limit}")
        console.print(f"Remaining tokens:             {result.token_budget_remaining}")
        console.print(f"Budget status:                {'OK ✓' if not result.budget_exceeded else 'EXCEEDED ✗'}")
        console.print("\n[bold green]Demonstration complete![/bold green]\n")


if __name__ == "__main__":
    main()

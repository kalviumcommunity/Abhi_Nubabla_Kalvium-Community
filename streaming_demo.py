#!/usr/bin/env python3
"""
RAG Streaming & Citations Demo Script

This script demonstrates the streaming response and citation features
of the RAG Pipeline API by making requests to the /query/stream endpoint
and displaying the results in real-time.

Usage:
    python streaming_demo.py
    
Prerequisites:
    1. Ensure API is running: python -m src.api
    2. Ensure OPENAI_API_KEY is set in .env
    3. Ensure vector store exists at data/embedded_chunks.json
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import AsyncGenerator

try:
    import httpx
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.progress import Progress
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: Rich library not found. Install with: pip install rich httpx")

# Configuration
API_BASE_URL = "http://localhost:8000"
DEMO_QUERIES = [
    "What are the password requirements for company systems?",
    "What is the remote work policy?",
    "How do I report a security incident?"
]


async def stream_query(query: str, api_url: str = API_BASE_URL) -> dict:
    """
    Stream a query to the RAG API and collect results.
    
    Returns:
        Dictionary with:
        - answer: The complete answer text
        - citations: List of citation metadata
        - status: Final status
        - metadata: Request metadata
    """
    result = {
        "answer": "",
        "citations": {},
        "status": "pending",
        "metadata": {},
        "events": []
    }
    
    if not RICH_AVAILABLE:
        print(f"\n📤 Sending query: {query}")
        return result
    
    console = Console()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            console.print(f"\n🚀 [bold cyan]Streaming query:[/bold cyan] {query}", style="bold")
            
            async with client.stream(
                "POST",
                f"{api_url}/query/stream",
                json={
                    "question": query,
                    "k": 3,
                    "score_threshold": 0.0,
                    "metadata_filter": None
                }
            ) as response:
                if response.status_code != 200:
                    console.print(f"[red]Error: HTTP {response.status_code}[/red]")
                    result["status"] = "error"
                    return result
                
                # Process SSE stream
                buffer = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            result["events"].append(data)
                            
                            event_type = data.get("type")
                            
                            if event_type == "metadata":
                                result["metadata"] = data
                                console.print(f"[dim]Request ID: {data.get('request_id')}[/dim]")
                            
                            elif event_type == "status":
                                console.print(f"⏳ {data.get('message')}")
                            
                            elif event_type == "answer_chunk":
                                chunk = data.get("chunk", "")
                                result["answer"] += chunk
                                # Print without newline for progressive display
                                console.print(chunk, end="", highlight=False)
                            
                            elif event_type == "citation":
                                tag = data.get("tag")
                                metadata = data.get("metadata", {})
                                result["citations"][tag] = metadata
                                console.print()  # Newline after answer
                                console.print(f"📌 {tag} Added to sources")
                            
                            elif event_type == "complete":
                                result["status"] = "success"
                                console.print(f"\n✅ [green]Response complete[/green]")
                            
                            elif event_type == "error":
                                result["status"] = "error"
                                console.print(f"\n❌ [red]Error: {data.get('message')}[/red]")
                        
                        except json.JSONDecodeError as e:
                            console.print(f"[yellow]Warning: Could not parse event[/yellow]")
    
    except httpx.ConnectError:
        console.print(f"[red]❌ Connection error: Cannot reach {api_url}[/red]")
        console.print("[yellow]💡 Make sure the API is running: python -m src.api[/yellow]")
        result["status"] = "error"
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error: {str(e)}[/red]")
        else:
            print(f"Error: {str(e)}")
        result["status"] = "error"
    
    return result


def display_results(results: list):
    """Display comprehensive results of the streaming demo."""
    if not RICH_AVAILABLE:
        print("\n=== Demo Results ===")
        for i, result in enumerate(results, 1):
            print(f"\nQuery {i}:")
            print(f"Status: {result['status']}")
            print(f"Answer length: {len(result['answer'])} characters")
            print(f"Citations count: {len(result['citations'])}")
        return
    
    console = Console()
    
    console.print("\n" + "="*80)
    console.print("[bold cyan]📊 STREAMING DEMO RESULTS[/bold cyan]", justify="center")
    console.print("="*80)
    
    for idx, result in enumerate(results, 1):
        query = result.get("metadata", {}).get("query", f"Query {idx}")
        status = result.get("status", "unknown")
        
        status_icon = "✅" if status == "success" else "❌"
        status_color = "green" if status == "success" else "red"
        
        console.print(f"\n[bold]{idx}. {query}[/bold]")
        console.print(f"{status_icon} Status: [bold {status_color}]{status}[/bold {status_color}]")
        
        answer = result.get("answer", "")
        if answer:
            console.print(f"\n[bold cyan]Answer:[/bold cyan]")
            console.print(f"{answer[:300]}{'...' if len(answer) > 300 else ''}")
        
        citations = result.get("citations", {})
        if citations:
            console.print(f"\n[bold yellow]📚 Sources ({len(citations)}):[/bold yellow]")
            
            for tag, metadata in citations.items():
                table = Table(show_header=False, box=None, padding=(0, 1))
                
                doc_name = metadata.get("source_document", "Unknown")
                section = metadata.get("section", "N/A")
                score = metadata.get("similarity_score", 0)
                
                table.add_row(f"[bold]{tag}[/bold]", f"{doc_name}")
                table.add_row("", f"📄 Section: {section}")
                table.add_row("", f"🎯 Relevance: {score*100:.2f}%")
                
                if metadata.get("page"):
                    table.add_row("", f"📖 Page: {metadata.get('page')}")
                
                console.print(table)
        
        # Show event types received
        events = result.get("events", [])
        event_types = {}
        for event in events:
            etype = event.get("type", "unknown")
            event_types[etype] = event_types.get(etype, 0) + 1
        
        if event_types:
            console.print(f"\n[dim]Events streamed: {', '.join(f'{t}({c})' for t, c in event_types.items())}[/dim]")


async def run_demo():
    """Run the streaming demonstration."""
    if not RICH_AVAILABLE:
        print("RAG Streaming Demo")
        print("=" * 50)
        print("Note: Install 'rich' for better formatting")
        print("Running simplified demo...\n")
        
        for query in DEMO_QUERIES[:1]:  # Run just one query for basic demo
            await stream_query(query)
        return
    
    console = Console()
    
    # Header
    console.print("\n" + "="*80)
    console.print("[bold cyan]🤖 RAG PIPELINE - STREAMING & CITATIONS DEMO[/bold cyan]", justify="center")
    console.print("="*80)
    
    console.print("""
[bold]This demonstration shows:[/bold]

1. ✅ Progressive answer streaming (word-by-word)
2. ✅ Citation metadata streamed after answer
3. ✅ Real-time source tracking with relevance scores
4. ✅ Status updates during retrieval and generation
5. ✅ Error handling for network/backend issues

[dim]Making requests to: http://localhost:8000/query/stream[/dim]
""")
    
    results = []
    
    for query in DEMO_QUERIES:
        result = await stream_query(query)
        results.append(result)
        
        # Small delay between queries
        await asyncio.sleep(0.5)
    
    # Display results
    display_results(results)
    
    # Summary
    console.print("\n" + "="*80)
    successful = sum(1 for r in results if r.get("status") == "success")
    console.print(f"\n[bold cyan]Summary:[/bold cyan]")
    console.print(f"  • Queries processed: {len(results)}")
    console.print(f"  • Successful: {successful}")
    console.print(f"  • Failed: {len(results) - successful}")
    console.print("\n[dim]💡 Tip: Open chat_ui.html in your browser for interactive UI[/dim]")
    console.print("="*80 + "\n")


def main():
    """Main entry point."""
    if sys.platform == "win32":
        # Handle Windows asyncio event loop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n\n✋ Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error running demo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

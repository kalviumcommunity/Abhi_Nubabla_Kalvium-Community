"""
Context Injection Module for RAG Augmented Prompt Assembly.

Assembles retrieved chunks into grounded augmented prompts with:
- Token budget enforcement
- Source marker injection
- Grounding instructions
- Context-only answering constraints

This module enables the LLM to answer with evidence while staying within
token limits and enforcing citation discipline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Token Counting
# ---------------------------------------------------------------------------
class TokenCounter:
    """
    Estimates token counts using simple heuristics.
    Approximates OpenAI GPT tokenization (rough but fast).
    """
    
    # Average tokens per word (empirical: ~1.3 for English)
    AVG_TOKENS_PER_WORD = 1.3
    
    # Average tokens per character (empirical: ~0.25 for English)
    AVG_TOKENS_PER_CHAR = 0.25
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Estimate token count for text.
        Uses average of word-based and character-based estimates.
        """
        if not text:
            return 0
        
        # Word-based estimate
        words = len(text.split())
        word_tokens = int(words * cls.AVG_TOKENS_PER_WORD)
        
        # Character-based estimate (as backup)
        char_tokens = int(len(text) * cls.AVG_TOKENS_PER_CHAR)
        
        # Use word-based if we have words, otherwise character-based
        if words > 0:
            return max(word_tokens, 1)
        return max(char_tokens, 1)
    
    @classmethod
    def count_tokens_in_list(cls, items: List[str]) -> int:
        """Count total tokens across multiple text items."""
        return sum(cls.estimate_tokens(item) for item in items)


# ---------------------------------------------------------------------------
# Source Markers
# ---------------------------------------------------------------------------
@dataclass
class SourceMarker:
    """Represents a source marker for a chunk."""
    
    index: int  # Numeric ID like [1], [2], [3]
    chunk_id: str
    source_document: str
    section: Optional[str] = None
    
    def __str__(self) -> str:
        """Format as [1], [2], etc."""
        return f"[{self.index}]"
    
    def full_reference(self) -> str:
        """Format as [1] (document.pdf - Section Name)"""
        if self.section:
            return f"[{self.index}] ({self.source_document} - {self.section})"
        return f"[{self.index}] ({self.source_document})"


# ---------------------------------------------------------------------------
# Injected Chunk with Source Markers
# ---------------------------------------------------------------------------
@dataclass
class InjectedChunk:
    """A chunk injected into the context with source marker."""
    
    source_marker: SourceMarker
    original_text: str
    injected_text: str  # Text with source marker prefixed
    token_count: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "marker": str(self.source_marker),
            "full_reference": self.source_marker.full_reference(),
            "chunk_id": self.source_marker.chunk_id,
            "source_document": self.source_marker.source_document,
            "token_count": self.token_count,
            "original_text": self.original_text,
            "injected_text": self.injected_text,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Grounding Instructions
# ---------------------------------------------------------------------------
class GroundingInstructions:
    """
    Standard grounding instructions for enforcing context-only answering.
    """
    
    BASIC_GROUNDING = """You are a helpful assistant that answers questions using ONLY the provided context.

**Instructions:**
1. Answer ONLY using information from the provided context.
2. Reference sources using the marker format [1], [2], etc.
3. If the context does not contain sufficient information to answer the question, say: "I don't have enough information in the provided context to answer this question."
4. Do not use external knowledge or make assumptions beyond what is explicitly stated.
5. Be concise and direct.
"""
    
    STRICT_GROUNDING = """You are a strict context-grounded assistant. Your ONLY knowledge source is the provided context.

**Instructions:**
1. ONLY cite and use information from the numbered sources [1], [2], [3], etc.
2. Every claim must be traceable to a specific source.
3. If asked about something not in the context, respond: "This information is not available in the provided context."
4. Do not infer, speculate, or use external knowledge.
5. Quote directly when possible; paraphrase when necessary but always cite the source.
6. Acknowledge limitations and gaps in the provided information.
"""
    
    PROFESSIONAL_GROUNDING = """You are a professional assistant answering based on company policies and documentation.

**Context Guidelines:**
1. Provide accurate, sourced answers from the official documentation provided below.
2. Use source citations [1], [2], etc., to indicate where information comes from.
3. When information is incomplete or ambiguous in the documentation, acknowledge this limitation.
4. Follow the hierarchy: documented policy > supporting context > admit insufficient information.
5. Format answers clearly with proper citations and section references.
6. For policy questions, prioritize accuracy over brevity.
"""
    
    @staticmethod
    def get_grounding_instructions(style: str = "basic") -> str:
        """
        Get grounding instructions by style.
        
        Args:
            style: "basic", "strict", or "professional"
        
        Returns:
            Grounding instruction text
        """
        if style == "strict":
            return GroundingInstructions.STRICT_GROUNDING
        elif style == "professional":
            return GroundingInstructions.PROFESSIONAL_GROUNDING
        else:
            return GroundingInstructions.BASIC_GROUNDING


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------
class PromptTemplate:
    """
    Templates for assembling augmented prompts with injected context.
    """
    
    STANDARD_TEMPLATE = """{grounding_instructions}

---

**Context:**
{injected_context}

---

**Question:** {user_question}

**Answer:**"""
    
    SECTION_TEMPLATE = """{grounding_instructions}

---

**Documents Provided:**
{source_references}

---

**Context:**
{injected_context}

---

**Question:** {user_question}

**Answer:**"""
    
    DETAILED_TEMPLATE = """{grounding_instructions}

---

**Context Information:**
- Total sources: {source_count}
- Date: {timestamp}
- Relevant policy sections provided below

**Source References:**
{source_references}

**Context:**
{injected_context}

---

**Question:** {user_question}

**Answer:**"""
    
    @staticmethod
    def format_standard(
        user_question: str,
        injected_context: str,
        grounding_instructions: str,
    ) -> str:
        """Format a standard augmented prompt."""
        return PromptTemplate.STANDARD_TEMPLATE.format(
            grounding_instructions=grounding_instructions,
            injected_context=injected_context,
            user_question=user_question,
        )
    
    @staticmethod
    def format_with_sources(
        user_question: str,
        injected_context: str,
        grounding_instructions: str,
        source_references: str,
    ) -> str:
        """Format a prompt with explicit source references."""
        return PromptTemplate.SECTION_TEMPLATE.format(
            grounding_instructions=grounding_instructions,
            source_references=source_references,
            injected_context=injected_context,
            user_question=user_question,
        )


# ---------------------------------------------------------------------------
# Context Assembly
# ---------------------------------------------------------------------------
@dataclass
class AugmentedPrompt:
    """Result of augmented prompt assembly."""
    
    user_question: str
    injected_chunks: List[InjectedChunk]
    assembled_prompt: str
    
    # Token budgets
    token_count_total: int
    token_count_instructions: int
    token_count_context: int
    token_count_question: int
    token_count_reserved: int
    
    # Budget status
    token_budget_limit: int
    token_budget_remaining: int
    budget_exceeded: bool
    
    # Metadata
    model_name: str
    max_tokens: int
    grounding_style: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return {
            "user_question": self.user_question,
            "model": self.model_name,
            "grounding_style": self.grounding_style,
            "injected_chunks": [c.to_dict() for c in self.injected_chunks],
            "assembled_prompt": self.assembled_prompt,
            "token_counts": {
                "total": self.token_count_total,
                "instructions": self.token_count_instructions,
                "context": self.token_count_context,
                "question": self.token_count_question,
                "reserved": self.token_count_reserved,
            },
            "token_budget": {
                "limit": self.token_budget_limit,
                "remaining": self.token_budget_remaining,
                "exceeded": self.budget_exceeded,
            },
            "max_tokens": self.max_tokens,
        }


class AugmentedPromptBuilder:
    """
    Builds augmented prompts with context injection and token budget management.
    """
    
    # Model token budgets (approximate)
    MODEL_TOKEN_LIMITS = {
        "gpt-3.5-turbo": 4096,
        "gpt-4": 8192,
        "gpt-4-turbo": 128000,
        "claude-2": 100000,
        "llama-2-7b": 4096,
    }
    
    # Reserved tokens for answer generation
    RESERVED_TOKENS_DEFAULT = 1000
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        context_budget_percent: float = 0.50,
        reserved_tokens: int = RESERVED_TOKENS_DEFAULT,
        grounding_style: str = "professional",
    ):
        """
        Initialize the augmented prompt builder.
        
        Args:
            model_name: Name of the target model (e.g., "gpt-3.5-turbo")
            context_budget_percent: Percentage of total tokens for context (default: 50%)
            reserved_tokens: Tokens reserved for model answer (default: 1000)
            grounding_style: Style of grounding instructions ("basic", "strict", "professional")
        """
        self.model_name = model_name
        self.context_budget_percent = context_budget_percent
        self.reserved_tokens = reserved_tokens
        self.grounding_style = grounding_style
        
        # Get max tokens for model
        self.max_tokens = self.MODEL_TOKEN_LIMITS.get(model_name, 4096)
        
        # Calculate context budget
        self.context_budget = int(self.max_tokens * context_budget_percent)
    
    def inject_chunks(
        self,
        chunks: List[Any],  # List of RetrievedChunk or dict
        preserve_order: bool = True,
    ) -> List[InjectedChunk]:
        """
        Inject chunks with source markers.
        
        Args:
            chunks: List of chunks to inject
            preserve_order: Whether to preserve original order or sort by relevance
        
        Returns:
            List of InjectedChunk with source markers
        """
        injected_chunks = []
        
        for idx, chunk in enumerate(chunks, start=1):
            # Handle both RetrievedChunk objects and dicts
            if hasattr(chunk, "source_text"):
                source_text = chunk.source_text
                metadata = chunk.metadata
                chunk_id = chunk.chunk_id
            else:
                source_text = chunk.get("source_text", "")
                metadata = chunk.get("metadata", {})
                chunk_id = chunk.get("chunk_id", f"chunk_{idx}")
            
            # Create source marker
            source_doc = metadata.get("source_document", "unknown")
            section = metadata.get("section")
            marker = SourceMarker(
                index=idx,
                chunk_id=chunk_id,
                source_document=source_doc,
                section=section,
            )
            
            # Format injected text with marker
            injected_text = f"{marker.full_reference()}\n{source_text}"
            
            # Count tokens
            token_count = TokenCounter.estimate_tokens(source_text)
            
            # Create InjectedChunk
            injected = InjectedChunk(
                source_marker=marker,
                original_text=source_text,
                injected_text=injected_text,
                token_count=token_count,
                metadata=metadata,
            )
            
            injected_chunks.append(injected)
        
        return injected_chunks
    
    def enforce_token_budget(
        self,
        chunks: List[InjectedChunk],
        budget: Optional[int] = None,
    ) -> List[InjectedChunk]:
        """
        Enforce token budget by dropping chunks that exceed limit.
        
        Args:
            chunks: List of injected chunks
            budget: Optional custom budget. Uses self.context_budget if None.
        
        Returns:
            Subset of chunks that fit within budget
        """
        budget = budget or self.context_budget
        
        selected = []
        total_tokens = 0
        
        for chunk in chunks:
            if total_tokens + chunk.token_count <= budget:
                selected.append(chunk)
                total_tokens += chunk.token_count
            else:
                # Budget exceeded, stop adding
                break
        
        return selected
    
    def build_augmented_prompt(
        self,
        user_question: str,
        chunks: List[Any],
        template_style: str = "standard",
    ) -> AugmentedPrompt:
        """
        Build a complete augmented prompt with context injection and token enforcement.
        
        Args:
            user_question: The user's question
            chunks: List of retrieved chunks to inject
            template_style: "standard" or "with_sources"
        
        Returns:
            AugmentedPrompt with assembled prompt and token budget info
        """
        # Step 1: Inject chunks with source markers
        injected_chunks = self.inject_chunks(chunks)
        
        # Step 2: Enforce token budget
        budget_enforced_chunks = self.enforce_token_budget(injected_chunks)
        
        # Step 3: Get grounding instructions
        grounding_instructions = GroundingInstructions.get_grounding_instructions(
            self.grounding_style
        )
        
        # Step 4: Format injected context
        injected_context = "\n\n".join(
            chunk.injected_text for chunk in budget_enforced_chunks
        )
        
        # Step 5: Calculate token counts
        token_instructions = TokenCounter.estimate_tokens(grounding_instructions)
        token_context = sum(c.token_count for c in budget_enforced_chunks)
        token_question = TokenCounter.estimate_tokens(user_question)
        token_reserved = self.reserved_tokens
        
        token_total = (
            token_instructions + 
            token_context + 
            token_question + 
            token_reserved
        )
        
        # Step 6: Check budget
        token_budget_limit = self.context_budget
        token_budget_remaining = max(0, token_budget_limit - token_context)
        budget_exceeded = token_context > token_budget_limit
        
        # Step 7: Assemble prompt
        if template_style == "with_sources":
            source_refs = "\n".join(
                f"- {c.source_marker.full_reference()}"
                for c in budget_enforced_chunks
            )
            assembled_prompt = PromptTemplate.format_with_sources(
                user_question=user_question,
                injected_context=injected_context,
                grounding_instructions=grounding_instructions,
                source_references=source_refs,
            )
        else:
            assembled_prompt = PromptTemplate.format_standard(
                user_question=user_question,
                injected_context=injected_context,
                grounding_instructions=grounding_instructions,
            )
        
        # Step 8: Return result
        return AugmentedPrompt(
            user_question=user_question,
            injected_chunks=budget_enforced_chunks,
            assembled_prompt=assembled_prompt,
            token_count_total=token_total,
            token_count_instructions=token_instructions,
            token_count_context=token_context,
            token_count_question=token_question,
            token_count_reserved=token_reserved,
            token_budget_limit=token_budget_limit,
            token_budget_remaining=token_budget_remaining,
            budget_exceeded=budget_exceeded,
            model_name=self.model_name,
            max_tokens=self.max_tokens,
            grounding_style=self.grounding_style,
        )

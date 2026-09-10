"""
Unit Tests for Context Injection Module.
Tests token counting, source markers, grounding instructions, and prompt assembly.
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context_injector import (
    TokenCounter,
    SourceMarker,
    InjectedChunk,
    AugmentedPrompt,
    AugmentedPromptBuilder,
    GroundingInstructions,
    PromptTemplate,
)


class TestTokenCounter(unittest.TestCase):
    """Test cases for token counting."""
    
    def test_estimate_tokens_simple(self):
        """Test basic token estimation."""
        text = "This is a sample text."
        tokens = TokenCounter.estimate_tokens(text)
        
        # Should be roughly 4-5 words * 1.3
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, 10)
    
    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        tokens = TokenCounter.estimate_tokens("")
        self.assertEqual(tokens, 0)
    
    def test_estimate_tokens_long(self):
        """Test token estimation for longer text."""
        text = "This is a longer piece of text. " * 10
        tokens = TokenCounter.estimate_tokens(text)
        
        # Should be proportional to length
        self.assertGreater(tokens, 30)
    
    def test_count_tokens_in_list(self):
        """Test counting tokens across multiple items."""
        items = ["Hello world", "Goodbye world", "Test"]
        total = TokenCounter.count_tokens_in_list(items)
        
        # Sum of individual estimates
        expected = sum(TokenCounter.estimate_tokens(item) for item in items)
        self.assertEqual(total, expected)


class TestSourceMarker(unittest.TestCase):
    """Test cases for source markers."""
    
    def test_source_marker_creation(self):
        """Test creating a source marker."""
        marker = SourceMarker(
            index=1,
            chunk_id="chunk_001",
            source_document="policy.md",
            section="Section 1"
        )
        
        self.assertEqual(marker.index, 1)
        self.assertEqual(str(marker), "[1]")
    
    def test_source_marker_full_reference(self):
        """Test full reference string."""
        marker = SourceMarker(
            index=2,
            chunk_id="chunk_002",
            source_document="document.pdf",
            section="Background"
        )
        
        ref = marker.full_reference()
        self.assertIn("[2]", ref)
        self.assertIn("document.pdf", ref)
        self.assertIn("Background", ref)
    
    def test_source_marker_without_section(self):
        """Test marker without section."""
        marker = SourceMarker(
            index=1,
            chunk_id="chunk_001",
            source_document="policy.md",
            section=None
        )
        
        ref = marker.full_reference()
        self.assertIn("[1]", ref)
        self.assertIn("policy.md", ref)


class TestInjectedChunk(unittest.TestCase):
    """Test cases for injected chunks."""
    
    def test_injected_chunk_creation(self):
        """Test creating an injected chunk."""
        marker = SourceMarker(1, "c1", "doc.md")
        chunk = InjectedChunk(
            source_marker=marker,
            original_text="Sample text",
            injected_text="[1] (doc.md)\nSample text",
            token_count=5,
            metadata={"source": "doc.md"}
        )
        
        self.assertEqual(chunk.source_marker.index, 1)
        self.assertEqual(chunk.token_count, 5)
    
    def test_injected_chunk_to_dict(self):
        """Test converting injected chunk to dict."""
        marker = SourceMarker(1, "c1", "doc.md", "Intro")
        chunk = InjectedChunk(
            source_marker=marker,
            original_text="Text",
            injected_text="[1] (doc.md - Intro)\nText",
            token_count=5,
            metadata={"key": "value"}
        )
        
        chunk_dict = chunk.to_dict()
        self.assertIsInstance(chunk_dict, dict)
        self.assertEqual(chunk_dict["marker"], "[1]")
        self.assertEqual(chunk_dict["token_count"], 5)


class TestAugmentedPromptBuilder(unittest.TestCase):
    """Test cases for augmented prompt builder."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = AugmentedPromptBuilder(
            model_name="gpt-3.5-turbo",
            context_budget_percent=0.50,
            reserved_tokens=1000,
        )
        
        # Sample chunks (dicts)
        self.chunks = [
            {
                "chunk_id": "c1",
                "source_text": "This is the first chunk about PTO policy.",
                "metadata": {
                    "source_document": "hr_policy.md",
                    "section": "Paid Time Off",
                }
            },
            {
                "chunk_id": "c2",
                "source_text": "Sick leave benefits and requirements are outlined here.",
                "metadata": {
                    "source_document": "hr_policy.md",
                    "section": "Sick Leave",
                }
            },
        ]
    
    def test_builder_initialization(self):
        """Test builder initialization."""
        self.assertEqual(self.builder.model_name, "gpt-3.5-turbo")
        self.assertEqual(self.builder.max_tokens, 4096)
        self.assertEqual(self.builder.context_budget, 2048)
    
    def test_inject_chunks(self):
        """Test injecting chunks with source markers."""
        injected = self.builder.inject_chunks(self.chunks)
        
        self.assertEqual(len(injected), 2)
        self.assertEqual(injected[0].source_marker.index, 1)
        self.assertEqual(injected[1].source_marker.index, 2)
        
        # Check markers are in injected text
        self.assertIn("[1]", injected[0].injected_text)
        self.assertIn("[2]", injected[1].injected_text)
    
    def test_enforce_token_budget(self):
        """Test token budget enforcement."""
        injected = self.builder.inject_chunks(self.chunks)
        budget = 100  # Very small budget
        
        selected = self.builder.enforce_token_budget(injected, budget)
        
        # Calculate total tokens for selected chunks
        total = sum(c.token_count for c in selected)
        self.assertLessEqual(total, budget)
    
    def test_build_augmented_prompt(self):
        """Test building complete augmented prompt."""
        result = self.builder.build_augmented_prompt(
            user_question="What is our PTO policy?",
            chunks=self.chunks,
        )
        
        self.assertIsInstance(result, AugmentedPrompt)
        self.assertEqual(len(result.injected_chunks), 2)
        self.assertIn("What is our PTO policy?", result.assembled_prompt)
        self.assertIn("[1]", result.assembled_prompt)
        self.assertIn("[2]", result.assembled_prompt)
    
    def test_token_counts_accurate(self):
        """Test that token counts are calculated accurately."""
        result = self.builder.build_augmented_prompt(
            user_question="Question?",
            chunks=self.chunks,
        )
        
        # Sum of components should equal total
        calculated_total = (
            result.token_count_instructions +
            result.token_count_context +
            result.token_count_question +
            result.token_count_reserved
        )
        
        self.assertEqual(result.token_count_total, calculated_total)
    
    def test_budget_status_ok(self):
        """Test budget status when within limits."""
        result = self.builder.build_augmented_prompt(
            user_question="Short?",
            chunks=self.chunks,
        )
        
        self.assertFalse(result.budget_exceeded)
        self.assertGreater(result.token_budget_remaining, 0)


class TestGroundingInstructions(unittest.TestCase):
    """Test cases for grounding instructions."""
    
    def test_get_basic_grounding(self):
        """Test retrieving basic grounding instructions."""
        instructions = GroundingInstructions.get_grounding_instructions("basic")
        self.assertIn("ONLY", instructions)
        self.assertIn("context", instructions)
    
    def test_get_strict_grounding(self):
        """Test retrieving strict grounding instructions."""
        instructions = GroundingInstructions.get_grounding_instructions("strict")
        self.assertIn("ONLY", instructions)
        self.assertIn("strict", instructions.lower())
    
    def test_get_professional_grounding(self):
        """Test retrieving professional grounding instructions."""
        instructions = GroundingInstructions.get_grounding_instructions("professional")
        self.assertIn("professional", instructions.lower())
        self.assertIn("policy", instructions.lower())
    
    def test_get_default_grounding(self):
        """Test default grounding instructions."""
        default = GroundingInstructions.get_grounding_instructions()
        basic = GroundingInstructions.get_grounding_instructions("basic")
        self.assertEqual(default, basic)


class TestPromptTemplate(unittest.TestCase):
    """Test cases for prompt templates."""
    
    def test_format_standard(self):
        """Test standard prompt template formatting."""
        prompt = PromptTemplate.format_standard(
            user_question="What is the policy?",
            injected_context="[1] Policy text here.",
            grounding_instructions="Answer using context only.",
        )
        
        self.assertIn("What is the policy?", prompt)
        self.assertIn("[1] Policy text here.", prompt)
        self.assertIn("Answer using context only.", prompt)
    
    def test_format_with_sources(self):
        """Test template with source references."""
        prompt = PromptTemplate.format_with_sources(
            user_question="Question?",
            injected_context="Context",
            grounding_instructions="Instructions",
            source_references="[1] (source.md)\n[2] (other.md)",
        )
        
        self.assertIn("Question?", prompt)
        self.assertIn("Documents Provided:", prompt)
        self.assertIn("[1] (source.md)", prompt)


class TestAugmentedPromptResult(unittest.TestCase):
    """Test cases for augmented prompt results."""
    
    def test_augmented_prompt_to_dict(self):
        """Test converting augmented prompt to dict."""
        builder = AugmentedPromptBuilder()
        chunks = [
            {
                "chunk_id": "c1",
                "source_text": "Text",
                "metadata": {"source_document": "doc.md"}
            }
        ]
        
        result = builder.build_augmented_prompt(
            user_question="Q?",
            chunks=chunks,
        )
        
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertIn("user_question", result_dict)
        self.assertIn("token_counts", result_dict)
        self.assertIn("token_budget", result_dict)
        self.assertIn("assembled_prompt", result_dict)


if __name__ == "__main__":
    unittest.main()

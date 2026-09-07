"""
Unit Tests for End-to-End Grounded RAG Pipeline (src/rag_pipeline.py).
"""

import unittest
from pathlib import Path

from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from src.rag_pipeline import (
    stage_embed_query,
    stage_retrieve_chunks,
    stage_assemble_context,
    stage_generate_answer,
    run_rag_pipeline,
    run_pipeline_demo
)


class TestRAGPipeline(unittest.TestCase):
    def setUp(self):
        self.vector_store_path = "data/embedded_chunks.json"
        self.retriever = VectorStoreRetriever(vector_store_path=self.vector_store_path)

    def test_stage1_embed_query(self):
        """Task 2 & 4: Verify Stage 1 query embedding produces 1536-D unit vector."""
        query = "How many days of paid time off do employees get?"
        vec = stage_embed_query(query, retriever=self.retriever)

        self.assertEqual(len(vec), 1536)
        norm = sum(x * x for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=4)

        # Invalid empty query raises ValueError
        with self.assertRaises(ValueError):
            stage_embed_query("", retriever=self.retriever)

    def test_stage2_retrieve_chunks(self):
        """Task 2 & 4: Verify Stage 2 retrieves top-k ranked chunks with scores."""
        query = "What is the procedure for VPN encryption and remote work?"
        chunks = stage_retrieve_chunks(query, k=3, retriever=self.retriever)

        self.assertEqual(len(chunks), 3)
        self.assertTrue(all(isinstance(c, RetrievedChunk) for c in chunks))
        self.assertEqual([c.rank for c in chunks], [1, 2, 3])
        scores = [c.score for c in chunks]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_stage3_assemble_context(self):
        """Task 2 & 4: Verify Stage 3 constructs grounded context block and sources list."""
        query = "Password length rules"
        chunks = stage_retrieve_chunks(query, k=2, retriever=self.retriever)

        context_block, sources = stage_assemble_context(chunks, max_context_tokens=1500)

        self.assertIn("Source 1:", context_block)
        self.assertIn("Source 2:", context_block)
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["rank"], 1)
        self.assertIn("source_document", sources[0])
        self.assertIn("section", sources[0])

    def test_stage4_generate_answer(self):
        """Task 2 & 4: Verify Stage 4 generates grounded response with returned sources."""
        query = "What are the password length requirements?"
        chunks = stage_retrieve_chunks(query, k=2, retriever=self.retriever)
        context_block, sources = stage_assemble_context(chunks)

        result = stage_generate_answer(query=query, context=context_block, sources=sources)

        self.assertIn("answer", result)
        self.assertIn("returned_sources", result)
        self.assertEqual(len(result["returned_sources"]), 2)
        self.assertTrue(result["answer"])

    def test_task3_end_to_end_rag_pipeline(self):
        """Task 3: Run full end-to-end pipeline and verify answer and returned sources."""
        query = "How many weeks of parental leave do new parents get?"
        result = run_rag_pipeline(query=query, k=3, retriever=self.retriever)

        self.assertEqual(result["query"], query)
        self.assertTrue(result["answer"])
        self.assertEqual(len(result["returned_sources"]), 3)
        self.assertIn("stage_metrics", result)

        metrics = result["stage_metrics"]
        self.assertEqual(metrics["query_embed_dimension"], 1536)
        self.assertEqual(metrics["retrieved_chunk_count"], 3)
        self.assertGreater(metrics["top_similarity_score"], 0.0)

    def test_fallback_unanswered_query(self):
        """Verify fallback instruction when no context sources are available."""
        context_block, sources = stage_assemble_context([])
        result = stage_generate_answer(query="What is the CEO personal phone number?", context=context_block, sources=sources)

        self.assertIn("don't have access to this information", result["answer"])
        self.assertEqual(result["retrieved_chunk_count"], 0)

    def test_task5_pipeline_demo_runner(self):
        """Task 5: Verify pipeline demo runner exports JSON results and Markdown report."""
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            summary = run_pipeline_demo(vector_store_path=self.vector_store_path, output_dir=temp_dir)

            self.assertIn("pipeline_runs", summary)
            self.assertEqual(len(summary["pipeline_runs"]), 4)

            json_file = Path(temp_dir) / "rag_pipeline_results.json"
            report_file = Path(temp_dir) / "rag_pipeline_report.md"

            self.assertTrue(json_file.exists())
            self.assertTrue(report_file.exists())


if __name__ == "__main__":
    unittest.main()

"""
Unit & Integration Tests for Runtime Document Upload, Ingestion, Dynamic Indexing & REST API Server.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.document_uploader import (
    RuntimeDocumentUploader,
    UploadProcessingResult,
    DynamicQueryResponse,
    RAGAPIHandler,
    ThreadedHTTPServer,
    SAMPLE_AI_GUIDELINES_MD,
    run_runtime_searchability_demo,
)
from src.similarity_search import VectorStoreRetriever, DenseSemanticEmbedder


class TestRuntimeDocumentUploader(unittest.TestCase):
    """Unit tests for document upload validation, ingestion, embedding, and indexing."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_rag_upload_"))
        self.uploads_dir = self.temp_dir / "uploads"
        self.vector_store_path = self.temp_dir / "embedded_chunks.json"

        # Create a sample initial vector store
        initial_store = {
            "summary": {
                "embedding_model": "text-embedding-3-small",
                "vector_dimension": 1536,
                "total_chunks_embedded": 1,
            },
            "embedded_chunks": [
                {
                    "chunk_id": "seed_chunk_001",
                    "source_text": "Company travel policy: Domestic travel per diem is capped at $75 per day.",
                    "metadata": {
                        "source_document": "travel_policy.txt",
                        "source_path": "data/corpus/travel_policy.txt",
                        "chunk_index": 0,
                        "section": "Per Diem",
                        "token_count": 15,
                    },
                    "vector": DenseSemanticEmbedder().embed("Company travel policy: Domestic travel per diem is capped at $75 per day."),
                }
            ],
        }
        with open(self.vector_store_path, "w", encoding="utf-8") as f:
            json.dump(initial_store, f)

        self.uploader = RuntimeDocumentUploader(
            uploads_dir=self.uploads_dir,
            vector_store_path=self.vector_store_path,
            max_file_size_bytes=1024 * 1024,  # 1 MB limit for tests
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_upload_valid_markdown_document(self):
        """Verify uploading and indexing a structured Markdown document."""
        md_content = (
            "# Section 9.0: On-Call & Incident Escalation\n\n"
            "## 1. PagerDuty Rotation\n"
            "Primary on-call engineers must acknowledge critical alerts within 15 minutes of paging.\n\n"
            "## 2. Secondary Escalation\n"
            "If unacknowledged after 20 minutes, alerts automatically escalate to the Engineering Director."
        )
        res = self.uploader.upload_and_index_document(
            filename="on_call_policy.md",
            content=md_content.encode("utf-8"),
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.document_name, "on_call_policy.md")
        self.assertGreaterEqual(res.chunks_created, 2)
        self.assertGreater(res.tokens_indexed, 20)
        self.assertEqual(len(self.uploader.retriever.chunks_data), 1 + res.chunks_created)

    def test_upload_valid_txt_document(self):
        """Verify uploading and indexing a plain text document."""
        txt_content = (
            "Standard Operating Procedure for Server Maintenance.\n\n"
            "Routine patches must be applied during the Wednesday 02:00 UTC maintenance window."
        )
        res = self.uploader.upload_and_index_document(
            filename="maintenance_sop.txt",
            content=txt_content.encode("utf-8"),
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.document_name, "maintenance_sop.txt")
        self.assertGreaterEqual(res.chunks_created, 1)

    def test_upload_valid_html_document(self):
        """Verify uploading and indexing an HTML document with tag stripping."""
        html_content = (
            "<!DOCTYPE html><html><body>"
            "<h1>Engineering Compensation Guidelines</h1>"
            "<p>Annual equity refresh grants are evaluated during Q4 talent calibration cycles.</p>"
            "</body></html>"
        )
        res = self.uploader.upload_and_index_document(
            filename="equity_guidelines.html",
            content=html_content.encode("utf-8"),
        )
        self.assertEqual(res.status, "SUCCESS")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.document_name, "equity_guidelines.html")
        self.assertGreaterEqual(res.chunks_created, 1)

    def test_runtime_searchability_without_restart(self):
        """
        Task 3: Prove that new document content is immediately searchable
        through the query endpoint without restarting the application.
        """
        query = "What is the PagerDuty alert acknowledgment deadline for primary on-call engineers?"

        # 1. Pre-upload query: should trigger fallback or have low relevance
        pre_resp = self.uploader.query(query_text=query, k=3)
        self.assertTrue(pre_resp.is_fallback or pre_resp.top_score < 0.40)

        # 2. Upload the on-call policy document
        md_content = (
            "# Section 9.0: On-Call & Incident Escalation Policy\n\n"
            "## 1. PagerDuty Alert Response SLA\n"
            "Primary on-call engineers must acknowledge critical PagerDuty alerts within exactly 15 minutes of paging."
        )
        upload_res = self.uploader.upload_and_index_document(
            filename="on_call_sla.md",
            content=md_content.encode("utf-8"),
        )
        self.assertEqual(upload_res.status, "SUCCESS")

        # 3. Post-upload query on SAME session/process: must retrieve on_call_sla.md at rank 1!
        post_resp = self.uploader.query(query_text=query, k=3)
        self.assertFalse(post_resp.is_fallback)
        self.assertGreaterEqual(post_resp.top_score, 0.40)
        self.assertGreater(len(post_resp.retrieved_chunks), 0)
        top_chunk_doc = post_resp.retrieved_chunks[0]["metadata"]["source_document"]
        self.assertEqual(top_chunk_doc, "on_call_sla.md")
        self.assertTrue("15 minutes" in post_resp.answer)

    def test_empty_file_rejection(self):
        """Task 4: Empty files (0 bytes) must return HTTP 400."""
        res = self.uploader.upload_and_index_document(
            filename="empty.md",
            content=b"",
        )
        self.assertEqual(res.status, "ERROR")
        self.assertEqual(res.status_code, 400)
        self.assertIn("empty", res.message.lower())

    def test_unsupported_format_rejection(self):
        """Task 4: Unsupported formats (.exe, .py, .zip) must return HTTP 415."""
        res = self.uploader.upload_and_index_document(
            filename="script.py",
            content=b"import os\nprint('hello')",
        )
        self.assertEqual(res.status, "ERROR")
        self.assertEqual(res.status_code, 415)
        self.assertIn("unsupported", res.message.lower())

    def test_oversized_file_rejection(self):
        """Task 4: Files exceeding max size threshold must return HTTP 413."""
        oversized_content = b"X" * (2 * 1024 * 1024)  # 2 MB > 1 MB test limit
        res = self.uploader.upload_and_index_document(
            filename="huge.txt",
            content=oversized_content,
        )
        self.assertEqual(res.status, "ERROR")
        self.assertEqual(res.status_code, 413)
        self.assertIn("exceeds", res.message.lower())

    def test_corrupted_file_rejection(self):
        """Task 4: Malformed/corrupt PDF streams must return HTTP 422."""
        corrupt_pdf_content = b"%PDF-1.4\nBROKEN_NON_PDF_BINARY_STREAM_DATA"
        res = self.uploader.upload_and_index_document(
            filename="corrupt.pdf",
            content=corrupt_pdf_content,
        )
        self.assertEqual(res.status, "ERROR")
        self.assertEqual(res.status_code, 422)
        self.assertIn("ingestion error", res.message.lower())

    def test_list_documents_catalog(self):
        """Verify catalog of indexed documents and section hierarchies."""
        self.uploader.upload_and_index_document(
            filename="doc_a.txt",
            content=b"Short document content A.",
        )
        catalog = self.uploader.list_documents()
        self.assertGreaterEqual(catalog["total_documents"], 2)
        doc_names = [d["document_name"] for d in catalog["documents"]]
        self.assertIn("doc_a.txt", doc_names)


class TestRAGAPIServerHTTP(unittest.TestCase):
    """Integration tests running live HTTP REST API requests against RAGAPIServer."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="test_http_rag_"))
        cls.uploads_dir = cls.temp_dir / "uploads"
        cls.vector_store_path = cls.temp_dir / "embedded_chunks.json"

        # Create initial vector store
        initial_store = {
            "summary": {
                "embedding_model": "text-embedding-3-small",
                "vector_dimension": 1536,
                "total_chunks_embedded": 1,
            },
            "embedded_chunks": [
                {
                    "chunk_id": "seed_001",
                    "source_text": "Remote work security: Corporate VPN is mandatory on all public Wi-Fi networks.",
                    "metadata": {
                        "source_document": "remote_work.md",
                        "section": "VPN Protocols",
                        "token_count": 14,
                    },
                    "vector": DenseSemanticEmbedder().embed("Remote work security: Corporate VPN is mandatory on all public Wi-Fi networks."),
                }
            ],
        }
        with open(cls.vector_store_path, "w", encoding="utf-8") as f:
            json.dump(initial_store, f)

        cls.uploader = RuntimeDocumentUploader(
            uploads_dir=cls.uploads_dir,
            vector_store_path=cls.vector_store_path,
        )
        RAGAPIHandler.uploader = cls.uploader
        RAGAPIHandler.server_start_time = time.time()

        # Bind to port 0 (OS allocates ephemeral free port)
        cls.server = ThreadedHTTPServer(("127.0.0.1", 0), RAGAPIHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2.0)
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_http_get_health(self):
        """Test GET /api/health endpoint."""
        req = urllib.request.Request(f"{self.base_url}/api/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "healthy")
            self.assertGreaterEqual(data["total_indexed_chunks"], 1)

    def test_http_get_documents(self):
        """Test GET /api/documents endpoint."""
        req = urllib.request.Request(f"{self.base_url}/api/documents")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(data["total_documents"], 1)

    def test_http_post_upload_json(self):
        """Test POST /api/upload with JSON payload."""
        upload_payload = {
            "filename": "cloud_compliance.md",
            "text": "# Section 12.0: Cloud Infrastructure Compliance\nAll AWS S3 buckets must enforce server-side AES-256 encryption at rest.",
        }
        req_data = json.dumps(upload_payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/upload",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "SUCCESS")
            self.assertEqual(data["document_name"], "cloud_compliance.md")

    def test_http_post_query(self):
        """Test POST /api/query endpoint."""
        query_payload = {
            "query": "What are the encryption requirements for AWS S3 buckets?",
            "k": 3,
        }
        req_data = json.dumps(query_payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/query",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("query", data)
            self.assertIn("answer", data)
            self.assertIn("retrieved_chunks", data)

    def test_http_post_upload_unsupported_error(self):
        """Test POST /api/upload rejecting unsupported format with 415."""
        upload_payload = {
            "filename": "malware.exe",
            "content_base64": base64.b64encode(b"binary").decode("utf-8"),
        }
        req_data = json.dumps(upload_payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/upload",
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Expected HTTP 415 error, got 200")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 415)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertEqual(err_data["status"], "ERROR")


class TestRuntimeSearchabilityDemo(unittest.TestCase):
    """Test the complete demo and report generation runner."""

    def test_run_demo_and_export_reports(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="test_demo_rag_"))
        try:
            results = run_runtime_searchability_demo(export_dir=temp_dir)
            self.assertIn("steps", results)
            self.assertEqual(len(results["steps"]), 3)
            self.assertEqual(len(results["negative_tests"]), 4)
            self.assertTrue(all(t["passed"] for t in results["negative_tests"]))

            json_file = temp_dir / "document_upload_results.json"
            md_file = temp_dir / "document_upload_report.md"
            self.assertTrue(json_file.exists())
            self.assertTrue(md_file.exists())
            self.assertGreater(json_file.stat().st_size, 100)
            self.assertGreater(md_file.stat().st_size, 100)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

"""
Systematic RAG System Evaluation & Answer Quality Scoring Engine.

Tasks Implemented:
- Task 1: Benchmark test set of queries with expected answers, key facts, and expected sources.
- Task 2: Score answers for correctness (ground-truth key fact coverage) and grounding (context faithfulness).
- Task 3: Check citation accuracy (citation precision, recall, hallucinated tag detection, claim-to-source alignment).
- Task 4: Summarize overall quality scores and notable failure cases with diagnostic root-cause categorization.
- Task 5: Export serialized evaluation dataset (JSON) and comprehensive quality report (Markdown).
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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

from src.similarity_search import VectorStoreRetriever, RetrievedChunk
from src.citation_engine import (
    generate_cited_answer,
    verify_cited_answer,
    extract_citations_from_text,
    build_citation_map
)


# ---------------------------------------------------------------------------
# Task 1: Labelled Benchmark Test Set & Data Models
# ---------------------------------------------------------------------------
@dataclass
class TestQueryItem:
    """Represents a benchmark test query with ground-truth facts and expected sources."""

    test_id: str
    query: str
    category: str  # Factual Policy, Procedural Security, Conversational Follow-Up, Out-Of-Domain Fallback, Complex Multi-Part
    expected_answer: str
    expected_keywords: List[str]
    expected_sources: List[str]
    is_out_of_domain: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


BENCHMARK_TEST_SET: List[TestQueryItem] = [
    TestQueryItem(
        test_id="eval_q01_pto_accrual",
        query="How many days of paid time off do employees get each year, and can unused PTO be rolled over into the next year?",
        category="Factual Policy",
        expected_answer="Employees accrue 18 days of paid time off per year at 1.5 days per month. Up to 5 unused PTO days can be rolled over into the next calendar year.",
        expected_keywords=["18 days", "1.5 days", "5 days", "roll over", "rollover"],
        expected_sources=["employee_benefits.md"],
        is_out_of_domain=False,
        notes="Standard policy question regarding PTO accrual and rollover limits."
    ),
    TestQueryItem(
        test_id="eval_q02_sick_leave",
        query="What is the policy for taking sick leave and when is a medical certificate required?",
        category="Factual Policy",
        expected_answer="Employees receive 10 dedicated sick days per calendar year. A medical certificate is required for absences extending beyond 3 consecutive working days.",
        expected_keywords=["10 dedicated sick days", "3 consecutive", "medical certificate", "healthcare practitioner"],
        expected_sources=["employee_benefits.md"],
        is_out_of_domain=False,
        notes="Evaluates retrieval of sick leave entitlement and documentation rules."
    ),
    TestQueryItem(
        test_id="eval_q03_remote_security",
        query="What are the network encryption and VPN requirements for connecting remotely to company resources?",
        category="Procedural Security",
        expected_answer="Remote workers must use WPA3 enterprise WiFi encryption and connect via the corporate WireGuard VPN tunnel with multi-factor authentication.",
        expected_keywords=["vpn", "encryption", "multi-factor", "wpa3", "wireguard", "mfa"],
        expected_sources=["remote_work_policy.md", "security_guidelines.txt"],
        is_out_of_domain=False,
        notes="Evaluates multi-source procedural security requirements."
    ),
    TestQueryItem(
        test_id="eval_q04_equipment_stipend",
        query="What equipment does the company provide for remote workers and what is the reimbursement stipend?",
        category="Factual Policy",
        expected_answer="The company provides a standardized laptop and monitor. Remote employees receive a one-time $500 home office equipment stipend.",
        expected_keywords=["laptop", "monitor", "$500", "stipend", "home office"],
        expected_sources=["remote_work_policy.md"],
        is_out_of_domain=False,
        notes="Evaluates reimbursement stipend amount retrieval."
    ),
    TestQueryItem(
        test_id="eval_q05_mars_travel_fallback",
        query="What is the company policy regarding interplanetary travel subsidies to Mars colonies?",
        category="Out-Of-Domain Fallback",
        expected_answer="I don't have access to this information in the verified company guidelines.",
        expected_keywords=["don't have access", "contact hr", "it helpdesk"],
        expected_sources=[],
        is_out_of_domain=True,
        notes="Out-of-domain query testing refusal to hallucinate non-existent policies."
    ),
    TestQueryItem(
        test_id="eval_q06_password_policy",
        query="What are the minimum password length requirements and is SMS authentication permitted?",
        category="Procedural Security",
        expected_answer="Passwords must be at least 14 characters long with uppercase, lowercase, numbers, and symbols. SMS-based 2FA is disallowed; hardware security keys or authenticator apps are required.",
        expected_keywords=["14 characters", "sms", "disallowed", "authenticator app", "hardware"],
        expected_sources=["security_guidelines.txt"],
        is_out_of_domain=False,
        notes="Evaluates password length and disallowed SMS authentication rules."
    ),
    TestQueryItem(
        test_id="eval_q07_stock_options_fallback",
        query="What is the vesting schedule and exercise window for executive stock option grants?",
        category="Out-Of-Domain Fallback",
        expected_answer="I don't have access to this information in the verified company guidelines.",
        expected_keywords=["don't have access", "contact hr"],
        expected_sources=[],
        is_out_of_domain=True,
        notes="Unanswerable executive compensation query testing fallback safeguard."
    ),
    TestQueryItem(
        test_id="eval_q08_parental_leave",
        query="How many weeks of fully paid parental leave are provided for primary caregivers?",
        category="Factual Policy",
        expected_answer="Eligible employees receive 12 weeks of fully paid parental leave for primary caregivers following the birth or adoption of a child.",
        expected_keywords=["12 weeks", "parental leave", "primary caregiver", "paid"],
        expected_sources=["employee_benefits.md"],
        is_out_of_domain=False,
        notes="Evaluates parental leave benefit details."
    )
]


# ---------------------------------------------------------------------------
# Data Models for Scoring & Reports (Tasks 2, 3, 4, 5)
# ---------------------------------------------------------------------------
@dataclass
class AnswerQualityScore:
    """Correctness and context grounding evaluation scores."""

    correctness_score: float  # 0.0 to 1.0
    grounding_score: float  # 0.0 to 1.0
    matched_keywords: List[str]
    missing_keywords: List[str]
    supported_claims_count: int
    unsupported_claims_count: int
    correctness_notes: str
    grounding_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CitationAccuracyCheck:
    """Precision, recall, and validity check for answer citations."""

    citation_precision: float  # 0.0 to 1.0
    citation_recall: float  # 0.0 to 1.0
    citations_found: List[str]
    invalid_citations: List[str]
    expected_sources_cited: List[str]
    missing_expected_sources: List[str]
    is_citation_accurate: bool
    citation_notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationFailureCase:
    """Detailed diagnostic log of notable failure cases."""

    test_id: str
    query: str
    category: str
    failure_type: str  # Retrieval Miss, Partial Grounding, Citation Misalignment, Hallucinated Claim, Refusal Failure
    severity: str  # High, Medium, Low
    observed_issue: str
    likely_cause: str
    recommended_fix: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ItemEvaluationResult:
    """Complete evaluation result for a single test set item."""

    item: TestQueryItem
    generated_answer: str
    is_fallback: bool
    retrieved_chunks_count: int
    quality_score: AnswerQualityScore
    citation_check: CitationAccuracyCheck
    failure_case: Optional[EvaluationFailureCase]
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "test_id": self.item.test_id,
            "query": self.item.query,
            "category": self.item.category,
            "is_out_of_domain": self.item.is_out_of_domain,
            "generated_answer": self.generated_answer,
            "is_fallback": self.is_fallback,
            "retrieved_chunks_count": self.retrieved_chunks_count,
            "correctness_score": self.quality_score.correctness_score,
            "grounding_score": self.quality_score.grounding_score,
            "citation_precision": self.citation_check.citation_precision,
            "citation_recall": self.citation_check.citation_recall,
            "is_citation_accurate": self.citation_check.is_citation_accurate,
            "latency_ms": self.latency_ms,
            "quality_details": self.quality_score.to_dict(),
            "citation_details": self.citation_check.to_dict(),
            "failure_case": self.failure_case.to_dict() if self.failure_case else None
        }
        return data


# ---------------------------------------------------------------------------
# Task 2: Correctness & Context Grounding Scoring Engine
# ---------------------------------------------------------------------------
def score_correctness(answer: str, item: TestQueryItem) -> Tuple[float, List[str], List[str], str]:
    """
    Task 2: Scores answer correctness against expected ground-truth facts & keywords.
    Returns (correctness_score, matched_keywords, missing_keywords, notes).
    """
    ans_lower = answer.lower()

    if item.is_out_of_domain:
        if "don't have access" in ans_lower or "no relevant" in ans_lower or "please contact hr" in ans_lower:
            return 1.0, ["correct_fallback_refusal"], [], "System correctly refused out-of-domain query without hallucinating."
        else:
            return 0.0, [], ["expected_fallback_refusal"], "System failed to refuse out-of-domain query and generated ungrounded claims."

    if not item.expected_keywords:
        return 1.0, [], [], "No specific ground-truth keywords specified."

    matched = []
    missing = []
    for kw in item.expected_keywords:
        # Check if keyword or core parts appear in answer text
        kw_parts = kw.lower().split()
        if any(part in ans_lower for part in kw_parts):
            matched.append(kw)
        else:
            missing.append(kw)

    ratio = len(matched) / max(1, len(item.expected_keywords))
    if ratio >= 0.8:
        score = 1.0
    elif ratio >= 0.5:
        score = 0.75
    elif ratio > 0.0:
        score = 0.50
    else:
        score = 0.0

    notes = f"Matched {len(matched)}/{len(item.expected_keywords)} expected key facts."
    return score, matched, missing, notes


def score_grounding(
    answer: str,
    context_text: str,
    item: TestQueryItem
) -> Tuple[float, int, int, str]:
    """
    Task 2: Scores grounding (context faithfulness) by verifying that answer claims
    are present in the retrieved context block.
    Returns (grounding_score, supported_count, unsupported_count, notes).
    """
    if item.is_out_of_domain or "don't have access" in answer.lower():
        return 1.0, 1, 0, "Fallback response is 100% grounded (safe refusal)."

    if not context_text or "No relevant internal documents" in context_text:
        return 0.0, 0, 1, "Context was empty but system generated claims."

    # Extract sentences / claims
    claims = [s.strip() for s in re.split(r'[.\n]', answer) if len(s.strip()) > 15 and not s.strip().startswith("[")]

    if not claims:
        return 1.0, 1, 0, "No complex claims extracted."

    context_lower = context_text.lower()
    supported = 0
    unsupported = 0

    for claim in claims:
        # Check term overlap between claim and context
        words = [w for w in re.findall(r'\b[a-zA-Z0-9]{4,}\b', claim.lower()) if w not in ["with", "from", "that", "this", "have"]]
        if not words:
            supported += 1
            continue
        
        matches = sum(1 for w in words if w in context_lower)
        overlap = matches / len(words)
        if overlap >= 0.4:
            supported += 1
        else:
            unsupported += 1

    score = supported / max(1, supported + unsupported)
    score = round(score, 4)
    notes = f"Grounding check: {supported} supported claims, {unsupported} unsupported claims."
    return score, supported, unsupported, notes


# ---------------------------------------------------------------------------
# Task 3: Citation Accuracy Checking Engine
# ---------------------------------------------------------------------------
def check_citation_accuracy(
    answer: str,
    citation_map: Dict[str, Dict[str, Any]],
    item: TestQueryItem
) -> CitationAccuracyCheck:
    """
    Task 3: Checks whether citations point to real retrieved chunks that actually support
    the answer claims, measures precision/recall, and detects hallucinated tags (e.g. [99]).
    """
    cited_tags = extract_citations_from_text(answer)

    if item.is_out_of_domain or "don't have access" in answer.lower():
        return CitationAccuracyCheck(
            citation_precision=1.0,
            citation_recall=1.0,
            citations_found=[],
            invalid_citations=[],
            expected_sources_cited=[],
            missing_expected_sources=[],
            is_citation_accurate=True,
            citation_notes="Safe fallback response without citations."
        )

    invalid_tags = [tag for tag in cited_tags if tag not in citation_map]

    # Calculate Citation Precision (valid cited tags / total cited tags)
    if cited_tags:
        precision = (len(cited_tags) - len(invalid_tags)) / len(cited_tags)
    else:
        precision = 1.0 if not item.expected_sources else 0.0

    # Calculate Citation Recall (expected sources cited / total expected sources)
    cited_doc_names = set()
    for tag in cited_tags:
        if tag in citation_map:
            doc_name = os.path.basename(citation_map[tag]["source_document"]).lower()
            cited_doc_names.add(doc_name)

    expected_found = []
    expected_missing = []
    for exp_src in item.expected_sources:
        exp_clean = exp_src.lower()
        if any(exp_clean in c_doc or c_doc in exp_clean for c_doc in cited_doc_names):
            expected_found.append(exp_src)
        else:
            expected_missing.append(exp_src)

    if item.expected_sources:
        recall = len(expected_found) / len(item.expected_sources)
    else:
        recall = 1.0

    is_accurate = (len(invalid_tags) == 0) and (precision >= 0.8) and (recall >= 0.5)

    notes = (
        f"Citations: {len(cited_tags)} found, {len(invalid_tags)} invalid. "
        f"Expected Sources Recall: {len(expected_found)}/{len(item.expected_sources)}."
    )

    return CitationAccuracyCheck(
        citation_precision=round(precision, 4),
        citation_recall=round(recall, 4),
        citations_found=cited_tags,
        invalid_citations=invalid_tags,
        expected_sources_cited=expected_found,
        missing_expected_sources=expected_missing,
        is_citation_accurate=is_accurate,
        citation_notes=notes
    )


# ---------------------------------------------------------------------------
# Task 4: Failure Diagnostic & Categorization Engine
# ---------------------------------------------------------------------------
def diagnose_failure_case(
    item: TestQueryItem,
    quality_score: AnswerQualityScore,
    citation_check: CitationAccuracyCheck,
    is_fallback: bool
) -> Optional[EvaluationFailureCase]:
    """
    Task 4: Identifies notable failures, categorizes root causes, and recommends fixes.
    """
    # Case 1: Out-of-Domain Refusal Failure
    if item.is_out_of_domain and not is_fallback:
        return EvaluationFailureCase(
            test_id=item.test_id,
            query=item.query,
            category=item.category,
            failure_type="Refusal Failure (Hallucinated Out-of-Domain Answer)",
            severity="High",
            observed_issue="System attempted to answer an unanswerable query instead of issuing fallback refusal.",
            likely_cause="Similarity threshold score was set too low or system prompt fallback rules were bypassed.",
            recommended_fix="Increase similarity score threshold to >= 0.35 and strengthen fallback rules in prompt."
        )

    # Case 2: Incorrect / Low Factual Coverage
    if quality_score.correctness_score < 0.70 and not item.is_out_of_domain:
        return EvaluationFailureCase(
            test_id=item.test_id,
            query=item.query,
            category=item.category,
            failure_type="Retrieval Miss / Incorrect Coverage",
            severity="High" if quality_score.correctness_score < 0.5 else "Medium",
            observed_issue=f"Answer missed key expected ground-truth facts: {quality_score.missing_keywords}",
            likely_cause="Top-k retrieval missed essential chunk context or chunk granularity lost key facts.",
            recommended_fix="Increase top-k retrieval parameter (e.g. k=5) or refine semantic embedding model."
        )

    # Case 3: Invalid / Hallucinated Citation Markers
    if citation_check.invalid_citations:
        return EvaluationFailureCase(
            test_id=item.test_id,
            query=item.query,
            category=item.category,
            failure_type="Citation Misalignment / Hallucinated Tag",
            severity="Medium",
            observed_issue=f"Generated answer referenced non-existent citation tags: {citation_check.invalid_citations}",
            likely_cause="Generative LLM hallucinated bracket indices not present in injected context.",
            recommended_fix="Apply strict post-processing regex validation to prune invalid citation markers."
        )

    # Case 4: Low Grounding / Unsupported Claims
    if quality_score.grounding_score < 0.75 and not item.is_out_of_domain:
        return EvaluationFailureCase(
            test_id=item.test_id,
            query=item.query,
            category=item.category,
            failure_type="Partial Grounding / Extrapolated Claim",
            severity="Medium",
            observed_issue=f"Answer contained {quality_score.unsupported_claims_count} unsupported claims.",
            likely_cause="Generator extrapolated beyond injected context details.",
            recommended_fix="Lower temperature parameter (e.g. 0.0 - 0.1) and enforce strict grounding system prompt."
        )

    return None


# ---------------------------------------------------------------------------
# Task 2, 3, 4 & 5: Master RAG Evaluator Suite
# ---------------------------------------------------------------------------
def evaluate_rag_system(
    test_set: List[TestQueryItem] = BENCHMARK_TEST_SET,
    retriever: Optional[VectorStoreRetriever] = None,
    vector_store_path: str = "data/results/embedded_chunks.json"
) -> Dict[str, Any]:
    """
    Executes the full evaluation suite across the benchmark test set, scores correctness,
    grounding, and citation accuracy, categorizes failures, and exports results.
    """
    if retriever is None:
        retriever = VectorStoreRetriever(vector_store_path=vector_store_path)

    evaluated_items: List[ItemEvaluationResult] = []
    failures: List[EvaluationFailureCase] = []

    for item in test_set:
        start_t = time.time()
        
        # Retrieve chunks & generate answer with citations
        res = generate_cited_answer(
            query=item.query,
            retrieved_chunks=retriever.retrieve_top_k(query=item.query, k=3),
            score_threshold=0.35
        )
        elapsed_ms = (time.time() - start_t) * 1000.0

        ans_text = res["answer"]
        is_fb = res["is_fallback"]
        retrieved_cnt = len(res.get("returned_sources", []))
        context_text = "\n".join([s.get("source_text_snippet", "") for s in res.get("returned_sources", [])])
        cit_map = res.get("citation_map", {})

        # Task 2: Score Correctness & Grounding
        corr_score, matched_kw, missing_kw, corr_notes = score_correctness(ans_text, item)
        grnd_score, supp_cnt, unsupp_cnt, grnd_notes = score_grounding(ans_text, context_text, item)
        q_score = AnswerQualityScore(
            correctness_score=corr_score,
            grounding_score=grnd_score,
            matched_keywords=matched_kw,
            missing_keywords=missing_kw,
            supported_claims_count=supp_cnt,
            unsupported_claims_count=unsupp_cnt,
            correctness_notes=corr_notes,
            grounding_notes=grnd_notes
        )

        # Task 3: Check Citation Accuracy
        cit_check = check_citation_accuracy(ans_text, cit_map, item)

        # Task 4: Failure Case Diagnosis
        fail_case = diagnose_failure_case(item, q_score, cit_check, is_fb)
        if fail_case:
            failures.append(fail_case)

        evaluated_items.append(ItemEvaluationResult(
            item=item,
            generated_answer=ans_text,
            is_fallback=is_fb,
            retrieved_chunks_count=retrieved_cnt,
            quality_score=q_score,
            citation_check=cit_check,
            failure_case=fail_case,
            latency_ms=round(elapsed_ms, 2)
        ))

    # Calculate overall summary metrics
    total_q = len(evaluated_items)
    avg_corr = sum(it.quality_score.correctness_score for it in evaluated_items) / max(1, total_q)
    avg_grnd = sum(it.quality_score.grounding_score for it in evaluated_items) / max(1, total_q)
    avg_prec = sum(it.citation_check.citation_precision for it in evaluated_items) / max(1, total_q)
    avg_rec = sum(it.citation_check.citation_recall for it in evaluated_items) / max(1, total_q)
    
    fb_items = [it for it in evaluated_items if it.item.is_out_of_domain]
    fb_acc = sum(1 for it in fb_items if it.is_fallback) / max(1, len(fb_items)) if fb_items else 1.0

    overall_score = round((avg_corr * 0.40) + (avg_grnd * 0.40) + (avg_prec * 0.10) + (avg_rec * 0.10), 4)

    summary_data = {
        "evaluation_name": "Full RAG Answer Quality & Citation Accuracy Evaluation",
        "timestamp": datetime.datetime.now().isoformat(),
        "total_queries": total_q,
        "overall_quality_score": overall_score,
        "metrics_summary": {
            "average_correctness_score": round(avg_corr, 4),
            "average_grounding_score": round(avg_grnd, 4),
            "average_citation_precision": round(avg_prec, 4),
            "average_citation_recall": round(avg_rec, 4),
            "fallback_accuracy_rate": round(fb_acc, 4)
        },
        "notable_failures_count": len(failures),
        "failures_breakdown": [f.to_dict() for f in failures],
        "scored_results": [it.to_dict() for it in evaluated_items]
    }

    return summary_data


# ---------------------------------------------------------------------------
# Task 5: Export Evaluation Datasets & Markdown Summary Report
# ---------------------------------------------------------------------------
def run_evaluation_demo(
    output_dir: str = "data",
    vector_store_path: str = "data/results/embedded_chunks.json"
) -> Dict[str, Any]:
    """
    Task 5: Executes full evaluation suite, exports serialized JSON and Markdown report,
    and prints formatted console results.
    """
    summary = evaluate_rag_system(vector_store_path=vector_store_path)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    json_path = out_path / "rag_evaluation_results.json"
    report_path = out_path / "rag_evaluation_report.md"

    # Export JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Export Markdown Report
    ms = summary["metrics_summary"]
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Full RAG System Evaluation & Answer Quality Scoring Report\n\n")
        f.write(f"**Overall Quality Score**: `{summary['overall_quality_score'] * 100:.1f}%`  \n")
        f.write(f"**Total Queries Evaluated**: `{summary['total_queries']}`  \n")
        f.write(f"**Timestamp**: `{summary['timestamp']}`  \n\n")
        f.write("---\n\n")

        f.write("## 1. Executive Quality Summary\n\n")
        f.write("| Evaluation Metric | Score | Target Threshold | Status |\n")
        f.write("| :--- | :---: | :---: | :---: |\n")
        f.write(f"| **Factual Correctness** | `{ms['average_correctness_score'] * 100:.1f}%` | 85.0% | {'✅ Pass' if ms['average_correctness_score']>=0.85 else '⚠️ Needs Review'} |\n")
        f.write(f"| **Context Grounding** | `{ms['average_grounding_score'] * 100:.1f}%` | 90.0% | {'✅ Pass' if ms['average_grounding_score']>=0.90 else '⚠️ Needs Review'} |\n")
        f.write(f"| **Citation Precision** | `{ms['average_citation_precision'] * 100:.1f}%` | 90.0% | {'✅ Pass' if ms['average_citation_precision']>=0.90 else '⚠️ Needs Review'} |\n")
        f.write(f"| **Citation Recall** | `{ms['average_citation_recall'] * 100:.1f}%` | 80.0% | {'✅ Pass' if ms['average_citation_recall']>=0.80 else '⚠️ Needs Review'} |\n")
        f.write(f"| **Fallback Accuracy** | `{ms['fallback_accuracy_rate'] * 100:.1f}%` | 100.0% | {'✅ Pass' if ms['fallback_accuracy_rate']==1.0 else '⚠️ Needs Review'} |\n\n")
        f.write("---\n\n")

        f.write("## 2. Test Set Benchmark Results\n\n")
        for res in summary["scored_results"]:
            f.write(f"### `{res['test_id']}`: *\"{res['query']}\"*\n\n")
            f.write(f"- **Category**: {res['category']} | **Fallback**: `{res['is_fallback']}`  \n")
            f.write(f"- **Correctness**: `{res['correctness_score'] * 100:.1f}%` | **Grounding**: `{res['grounding_score'] * 100:.1f}%` | **Citation Precision**: `{res['citation_precision'] * 100:.1f}%`  \n\n")
            f.write(f"**Generated Answer**:\n> {res['generated_answer'].replace(chr(10), '  \n> ')}\n\n")
            f.write(f"**Citations Found**: `{res['citation_details']['citations_found']}`  \n")
            f.write("\n---\n\n")

        f.write("## 3. Notable Failures & Root-Cause Diagnosis\n\n")
        if summary["failures_breakdown"]:
            for fail in summary["failures_breakdown"]:
                f.write(f"### ❌ Failure Case: `{fail['test_id']}` ({fail['failure_type']})\n\n")
                f.write(f"- **Severity**: `{fail['severity']}`  \n")
                f.write(f"- **Observed Issue**: {fail['observed_issue']}  \n")
                f.write(f"- **Likely Cause**: {fail['likely_cause']}  \n")
                f.write(f"- **Recommended Fix**: {fail['recommended_fix']}  \n\n")
        else:
            f.write("No critical failure cases observed across the benchmark test set. All quality thresholds met.\n\n")

    print_verification_output(summary)
    return summary


# ---------------------------------------------------------------------------
# CLI Console Formatter
# ---------------------------------------------------------------------------
def print_verification_output(summary: Dict[str, Any]):
    """Prints formatted evaluation output to CLI."""
    console = Console() if RICH_AVAILABLE else None
    ms = summary["metrics_summary"]

    if console:
        console.print(Panel.fit(
            "[bold cyan]Full RAG System Evaluation & Quality Scoring Engine[/bold cyan]\n"
            "[dim]Benchmark Test Set -> Correctness & Grounding Scoring -> Citation Checks -> Failure Summary[/dim]",
            border_style="cyan"
        ))
        console.print(f"\n[bold yellow]▶ Overall Quality Score[/bold yellow]: [bold green]{summary['overall_quality_score'] * 100:.1f}%[/bold green]")
        console.print(f"[bold yellow]▶ Queries Evaluated[/bold yellow]: {summary['total_queries']}")
        console.print(f"[bold yellow]▶ Correctness[/bold yellow]: {ms['average_correctness_score']*100:.1f}% | [bold yellow]Grounding[/bold yellow]: {ms['average_grounding_score']*100:.1f}% | [bold yellow]Fallback Accuracy[/bold yellow]: {ms['fallback_accuracy_rate']*100:.1f}%\n")

        for res in summary["scored_results"][:3]:
            console.print(Panel(
                f"[bold yellow]Test ID[/bold yellow]: {res['test_id']}\n"
                f"[bold yellow]Query[/bold yellow]: {res['query']}\n\n"
                f"[bold green]Answer[/bold green]:\n{res['generated_answer']}\n\n"
                f"[bold cyan]Correctness[/bold cyan]: {res['correctness_score']*100:.0f}% | "
                f"[bold cyan]Grounding[/bold cyan]: {res['grounding_score']*100:.0f}% | "
                f"[bold cyan]Citation Precision[/bold cyan]: {res['citation_precision']*100:.0f}%",
                title=f"Sample Evaluated Query: {res['category']}",
                border_style="white"
            ))
    else:
        print("================================================================================")
        print(" Full RAG System Evaluation Results ")
        print("================================================================================")
        print(f"Overall Quality Score: {summary['overall_quality_score'] * 100:.1f}%")
        print(f"Queries Evaluated    : {summary['total_queries']}")
        print(f"Average Correctness  : {ms['average_correctness_score']*100:.1f}%")
        print(f"Average Grounding    : {ms['average_grounding_score']*100:.1f}%")
        print(f"Fallback Accuracy    : {ms['fallback_accuracy_rate']*100:.1f}%")
        print("--------------------------------------------------------------------------------")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Full RAG Evaluation & Answer Quality Scoring Engine.")
    parser.add_argument("--demo", action="store_true", help="Run benchmark evaluation across test set")
    parser.add_argument("--inspect", action="store_true", help="Print verbose failure analysis and diagnostics")
    args = parser.parse_args()

    res = run_evaluation_demo()
    if args.inspect and res.get("failures_breakdown"):
        print("\n--- Failure Diagnostics Summary ---")
        for f in res["failures_breakdown"]:
            print(f"[{f['severity']}] {f['test_id']} - {f['failure_type']}: {f['observed_issue']}")


if __name__ == "__main__":
    main()

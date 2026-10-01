import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.services.investigation_service import investigation_service
from backend.models.schemas import (
    EvaluationSummary,
    EvaluationResultItem,
    EvaluationRunResponse,
    ClassMetric,
    ConfusionMatrixData
)
from backend.utils.logger import get_logger

logger = get_logger("evaluation_service")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVALUATION_DATASET_FILE = DATA_DIR / "evaluation_dataset.json"
LATEST_EVALUATION_FILE = DATA_DIR / "latest_evaluation.json"

CLASSES = ["CURRENT", "OUTDATED", "CONFLICTING", "UNCERTAIN"]


class EvaluationService:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def load_dataset(self) -> List[Dict[str, Any]]:
        if not EVALUATION_DATASET_FILE.exists():
            logger.warning(f"Evaluation dataset file not found at {EVALUATION_DATASET_FILE}")
            return []
        try:
            with open(EVALUATION_DATASET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading evaluation dataset: {e}")
            return []

    def run_evaluation(self, db: Session) -> EvaluationRunResponse:
        dataset = self.load_dataset()
        if not dataset:
            raise ValueError("Evaluation dataset is empty or missing.")

        logger.info(f"Starting automated evaluation benchmark across {len(dataset)} test cases...")
        start_overall = time.perf_counter()

        results: List[EvaluationResultItem] = []
        for item in dataset:
            case_id = item.get("id", "KG-000")
            claim = item.get("claim", "")
            expected = item.get("expected_verdict", "UNCERTAIN").strip().upper()
            reason = item.get("reason", "")

            try:
                inv_resp = investigation_service.investigate_claim(claim=claim, db=db)
                predicted = inv_resp.classification.strip().upper()
                is_correct = (predicted == expected)

                retrieved_docs = list({
                    ev.source for ev in inv_resp.evidences if ev.source
                })

                results.append(EvaluationResultItem(
                    id=case_id,
                    claim=claim,
                    expected_verdict=expected,
                    predicted_verdict=predicted,
                    confidence=inv_resp.confidence,
                    is_correct=is_correct,
                    evidence_count=len(inv_resp.evidences),
                    research_occurred=inv_resp.research_occurred,
                    execution_time_ms=inv_resp.execution_time_ms,
                    reason=reason,
                    explanation=inv_resp.explanation,
                    retrieved_documents=retrieved_docs
                ))
            except Exception as e:
                logger.error(f"Error running test case {case_id}: {e}")
                results.append(EvaluationResultItem(
                    id=case_id,
                    claim=claim,
                    expected_verdict=expected,
                    predicted_verdict="ERROR",
                    confidence=0.0,
                    is_correct=False,
                    evidence_count=0,
                    research_occurred=False,
                    execution_time_ms=0.0,
                    reason=reason,
                    explanation=f"Execution error: {str(e)}",
                    retrieved_documents=[]
                ))

        summary = self.calculate_metrics(results)
        response = EvaluationRunResponse(summary=summary, results=results)

        # Cache latest run to disk
        try:
            with open(LATEST_EVALUATION_FILE, "w", encoding="utf-8") as f:
                json.dump(response.model_dump(), f, indent=2, default=str)
            logger.info("Successfully cached evaluation benchmark results to latest_evaluation.json")
        except Exception as e:
            logger.warning(f"Could not cache evaluation results to disk: {e}")

        total_sec = round(time.perf_counter() - start_overall, 2)
        logger.info(f"Evaluation benchmark finished in {total_sec}s with Accuracy: {summary.overall_accuracy}%")
        return response

    def calculate_metrics(self, results: List[EvaluationResultItem]) -> EvaluationSummary:
        total = len(results)
        if total == 0:
            return EvaluationSummary(
                total_test_cases=0,
                correct_predictions=0,
                incorrect_predictions=0,
                overall_accuracy=0.0,
                average_confidence=0.0,
                average_execution_time_ms=0.0,
                total_researches_triggered=0,
                class_metrics=[],
                confusion_matrix=ConfusionMatrixData(labels=CLASSES, matrix=[[0]*4 for _ in range(4)]),
                last_run_timestamp=datetime.utcnow().isoformat()
            )

        correct = sum(1 for r in results if r.is_correct)
        incorrect = total - correct
        accuracy = round((correct / total) * 100.0, 2)
        avg_confidence = round(sum(r.confidence for r in results) / total, 2)
        avg_time = round(sum(r.execution_time_ms for r in results) / total, 2)
        total_researches = sum(1 for r in results if r.research_occurred)

        # 4x4 Confusion Matrix
        # Row = Expected, Col = Predicted
        label_to_idx = {lbl: i for i, lbl in enumerate(CLASSES)}
        matrix = [[0 for _ in range(len(CLASSES))] for _ in range(len(CLASSES))]

        for r in results:
            exp_idx = label_to_idx.get(r.expected_verdict)
            pred_idx = label_to_idx.get(r.predicted_verdict)
            if exp_idx is not None and pred_idx is not None:
                matrix[exp_idx][pred_idx] += 1

        # Class Metrics
        class_metrics: List[ClassMetric] = []
        for i, cls_name in enumerate(CLASSES):
            tp = matrix[i][i]
            fp = sum(matrix[row][i] for row in range(len(CLASSES))) - tp
            fn = sum(matrix[i][col] for col in range(len(CLASSES))) - tp
            support = sum(matrix[i][col] for col in range(len(CLASSES)))

            precision = round((tp / (tp + fp) * 100.0), 2) if (tp + fp) > 0 else 0.0
            recall = round((tp / (tp + fn) * 100.0), 2) if (tp + fn) > 0 else 0.0
            f1 = round((2 * precision * recall / (precision + recall)), 2) if (precision + recall) > 0 else 0.0

            class_metrics.append(ClassMetric(
                verdict=cls_name,
                precision=precision,
                recall=recall,
                f1_score=f1,
                support=support
            ))

        return EvaluationSummary(
            total_test_cases=total,
            correct_predictions=correct,
            incorrect_predictions=incorrect,
            overall_accuracy=accuracy,
            average_confidence=avg_confidence,
            average_execution_time_ms=avg_time,
            total_researches_triggered=total_researches,
            class_metrics=class_metrics,
            confusion_matrix=ConfusionMatrixData(labels=CLASSES, matrix=matrix),
            last_run_timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )

    def get_latest_data(self) -> Optional[EvaluationRunResponse]:
        if not LATEST_EVALUATION_FILE.exists():
            return None
        try:
            with open(LATEST_EVALUATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return EvaluationRunResponse(**data)
        except Exception as e:
            logger.warning(f"Error loading cached evaluation: {e}")
            return None

    def export_report_markdown(self) -> str:
        latest = self.get_latest_data()
        if not latest:
            return "# KnowledgeGuard AI — Evaluation Report\n\nNo evaluation has been executed yet. Run an evaluation from the dashboard."

        s = latest.summary
        md = []
        md.append("# KNOWLEDGEGUARD AI — EMPIRICAL EVALUATION REPORT")
        md.append(f"**Evaluation Timestamp:** {s.last_run_timestamp or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Architecture:** Single LangGraph Agent + Single Generative LLM + ChromaDB RAG\n")
        md.append("---")
        md.append("## 1. Executive Performance Summary\n")
        md.append(f"- **Total Test Cases:** {s.total_test_cases}")
        md.append(f"- **Correct Predictions:** {s.correct_predictions}")
        md.append(f"- **Incorrect Predictions:** {s.incorrect_predictions}")
        md.append(f"- **Overall Accuracy:** {s.overall_accuracy}%")
        md.append(f"- **Average Model Confidence:** {s.average_confidence}%")
        md.append(f"- **Average Investigation Latency:** {s.average_execution_time_ms} ms")
        md.append(f"- **Secondary Re-Search Triggered:** {s.total_researches_triggered} cases\n")

        md.append("---")
        md.append("## 2. Per-Class Quantitative Metrics\n")
        md.append("| Target Verdict | Precision (%) | Recall (%) | F1-Score (%) | Support |")
        md.append("| :--- | :---: | :---: | :---: | :---: |")
        for cm in s.class_metrics:
            md.append(f"| **{cm.verdict}** | {cm.precision}% | {cm.recall}% | {cm.f1_score}% | {cm.support} |")

        md.append("\n---")
        md.append("## 3. Confusion Matrix\n")
        md.append("```text")
        md.append("                   PREDICTED")
        md.append("                CURR  OUTD  CONF  UNCT")
        for i, label in enumerate(s.confusion_matrix.labels):
            row = s.confusion_matrix.matrix[i]
            md.append(f"EXPECTED {label[:4]:<4}   {row[0]:4d}  {row[1]:4d}  {row[2]:4d}  {row[3]:4d}")
        md.append("```\n")

        md.append("---")
        md.append("## 4. Detailed Test Case Audit Trail\n")
        md.append("| ID | Claim | Expected | Predicted | Confidence | Status | Docs Retrieved |")
        md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :--- |")
        for r in latest.results:
            status_symbol = "PASSED" if r.is_correct else "FAILED"
            docs_str = ", ".join(r.retrieved_documents[:2]) if r.retrieved_documents else "None"
            md.append(f"| {r.id} | {r.claim[:50]}... | `{r.expected_verdict}` | `{r.predicted_verdict}` | {r.confidence:.1f}% | **{status_symbol}** | {docs_str} |")

        md.append("\n---")
        md.append("## 5. System Limitations & Reliability Notes\n")
        md.append("1. **Semantic Ambiguity:** Vector similarity (Cosine/L2) captures topic closeness but does not guarantee logical relevance without LLM reasoning.")
        md.append("2. **Metadata Dependency:** Temporal classification requires accurate document effective dates and version tags in source documents.")
        md.append("3. **Bounded Knowledge:** Claims regarding technologies not indexed in ChromaDB will and should resolve to UNCERTAIN to prevent hallucination.")
        md.append("4. **Human Verification:** All CONFLICTING or UNCERTAIN classifications require engineering operator review before altering production architectures.")

        return "\n".join(md)


evaluation_service = EvaluationService()

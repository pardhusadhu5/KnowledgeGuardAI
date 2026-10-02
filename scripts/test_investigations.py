import sys
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database.db import SessionLocal
from backend.services.investigation_service import InvestigationService

TEST_CLAIMS = [
    {
        "id": "query_1_temporal_incident_handling",
        "claim": "Is NIST SP 800-61 Revision 2 the current authoritative standard for computer security incident handling?",
        "expected_verdict": "OUTDATED / CONFLICTING",
        "context": "NIST SP 800-61 Rev 2 (2012) is superseded by NIST SP 800-61 Rev 3 IPD (2024)."
    },
    {
        "id": "query_2_csf_function_comparison",
        "claim": "Does NIST Cybersecurity Framework (CSF) 2.0 introduce the GOVERN function in addition to the original five functions in CSF 1.1?",
        "expected_verdict": "CURRENT",
        "context": "NIST CSF 1.1 had 5 functions (Identify, Protect, Detect, Respond, Recover); CSF 2.0 officially introduced GOVERN (GV) as the 6th core function."
    },
    {
        "id": "query_3_ai_rmf_functions",
        "claim": "What are the core functions of the NIST Artificial Intelligence Risk Management Framework (AI RMF 1.0)?",
        "expected_verdict": "CURRENT",
        "context": "NIST AI 100-1 defines four core functions: GOVERN, MAP, MEASURE, and MANAGE."
    },
    {
        "id": "query_4_csf_scope_outdated",
        "claim": "The NIST Cybersecurity Framework applies exclusively to critical infrastructure organizations as specified in CSF version 1.1.",
        "expected_verdict": "OUTDATED",
        "context": "CSF 1.1 was targeted at critical infrastructure, but CSF 2.0 expanded the scope to all organizations regardless of size or sector."
    }
]

def run_tests():
    db = SessionLocal()
    service = InvestigationService()
    results = []

    print("=" * 80)
    print("RUNNING KNOWLEDGEGUARD AI AGENT VERIFICATION SUITE")
    print("=" * 80)

    for idx, test in enumerate(TEST_CLAIMS, 1):
        claim = test["claim"]
        print(f"\n--- [Test {idx}/{len(TEST_CLAIMS)}] {test['id']} ---")
        print(f"Claim: \"{claim}\"")
        print(f"Expected: {test['expected_verdict']}")
        print("Invoking LangGraph Agent -> RAG -> ChromaDB -> LLM...")

        start_time = time.perf_counter()
        try:
            resp = service.investigate_claim(claim=claim, db=db)
            duration = time.perf_counter() - start_time

            print(f"Result:")
            print(f"  Classification: [{resp.classification}]")
            print(f"  Confidence: {resp.confidence}%")
            print(f"  Human Review Required: {resp.human_verification_required}")
            print(f"  Execution Time: {duration:.2f}s ({resp.execution_time_ms}ms)")
            print(f"  Reasoning / Summary: {resp.explanation[:200]}...")
            print(f"  Evidence Retrieved: {len(resp.evidences)} chunks across {resp.unique_documents} document(s)")
            for e_idx, ev in enumerate(resp.evidences[:3], 1):
                print(f"    Evidence #{e_idx}: [{ev.source}] Version: {ev.version} (Date: {ev.date}) | Score: {ev.relevance_score:.3f}")
                print(f"      Text: {ev.evidence_text[:120].strip()}...")

            results.append({
                "test_id": test["id"],
                "claim": claim,
                "expected": test["expected_verdict"],
                "classification": resp.classification,
                "confidence": resp.confidence,
                "human_verification_required": resp.human_verification_required,
                "execution_time_s": round(duration, 2),
                "unique_documents": resp.unique_documents,
                "evidence_count": len(resp.evidences),
                "explanation": resp.explanation,
                "top_evidence": [
                    {
                        "source": ev.source,
                        "version": ev.version,
                        "date": ev.date,
                        "relevance_score": ev.relevance_score,
                        "snippet": ev.evidence_text[:180].strip()
                    }
                    for ev in resp.evidences[:3]
                ]
            })

        except Exception as e:
            print(f"  [ERROR] Investigation failed: {e}")
            results.append({
                "test_id": test["id"],
                "claim": claim,
                "error": str(e)
            })

    output_file = BASE_DIR / "data" / "knowledge_base" / "test_investigation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Verification complete. Results saved to: {output_file}")
    print("=" * 80)
    db.close()

if __name__ == "__main__":
    run_tests()

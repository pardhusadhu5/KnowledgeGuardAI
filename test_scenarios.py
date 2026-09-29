from backend.database.db import SessionLocal
from backend.services.investigation_service import investigation_service

def run_tests():
    db = SessionLocal()
    test_cases = [
        ("Is API v2 still recommended?", "OUTDATED"),
        ("Is Python 3.12 supported?", "CURRENT"),
        ("What authentication protocol is required?", "CONFLICTING"),
        ("Is quantum encryption mandated for all internal APIs?", "UNCERTAIN")
    ]

    all_passed = True
    print("\n--- RUNNING SCENARIO VERIFICATION TESTS ---")
    for claim, expected in test_cases:
        res = investigation_service.investigate_claim(claim, db)
        passed = (res.classification == expected)
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] Claim: '{claim}' -> Result: {res.classification} (Expected: {expected})")
        print(f"       Confidence: {res.confidence}% | Human Review: {res.human_verification_required}")
        print(f"       Explanation: {res.explanation[:90]}...")
        if not passed:
            all_passed = False

    print(f"\nFinal Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}\n")
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

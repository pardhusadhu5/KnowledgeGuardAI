import re
from typing import List, Dict, Any
from backend.rag.vector_store import vector_store
from backend.utils.logger import get_logger

logger = get_logger("agent_tools")


def search_knowledge(query: str, n_results: int = 6, max_distance: float = 1.25) -> List[Dict[str, Any]]:
    """Tool: Searches vector database for semantic matches against query, filtering distant outliers."""
    logger.info(f"Tool search_knowledge invoked for: '{query}'")
    results = vector_store.search(query=query, n_results=n_results)
    # Filter out distant unrelated chunks
    filtered = [r for r in results if r.get("distance") is None or r.get("distance") <= max_distance]
    return filtered if filtered else (results[:2] if results else [])


def retrieve_evidence(query: str, fallback_terms: List[str] = None) -> List[Dict[str, Any]]:
    """Tool: Retrieves chunk evidence and combines primary and fallback search queries if needed."""
    logger.info(f"Tool retrieve_evidence invoked for: '{query}'")
    hits = search_knowledge(query, n_results=5)
    
    # If primary search returned few hits, search using extracted keywords
    if len(hits) < 2 and fallback_terms:
        for term in fallback_terms:
            sub_hits = search_knowledge(term, n_results=3)
            # Avoid duplicates
            existing_texts = {h["chunk_text"] for h in hits}
            for sh in sub_hits:
                if sh["chunk_text"] not in existing_texts:
                    hits.append(sh)
                    existing_texts.add(sh["chunk_text"])
    return hits


def compare_evidence(evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tool: Compares temporal and semantic differences across retrieved evidence chunks."""
    if not evidence_list:
        return {
            "comparison_summary": "No evidence retrieved to perform comparison.",
            "temporal_ordering": [],
            "has_version_shift": False
        }

    # Sort evidence chronologically if date/version exists
    sorted_ev = sorted(
        evidence_list,
        key=lambda x: (str(x.get("date", "")), str(x.get("version", "")))
    )

    sources = list({e.get("source", "Document") for e in sorted_ev})
    versions = list({e.get("version", "N/A") for e in sorted_ev if e.get("version")})

    summary = f"Analyzed {len(sorted_ev)} evidence chunk(s) across {len(sources)} source document(s)."
    if len(versions) > 1:
        summary += f" Detected version evolution across versions: {', '.join(versions)}."

    return {
        "comparison_summary": summary,
        "sorted_evidence": sorted_ev,
        "has_version_shift": len(versions) > 1
    }


def analyze_claim(claim: str) -> Dict[str, Any]:
    """Tool: Analyzes claim syntax, extracting key entities and search keywords."""
    clean = claim.strip()
    # Preserve tokens including version numbers like v2, v3, 3.12
    tokens = re.findall(r"[A-Za-z0-9\.]+", clean)
    stopwords = {"what", "when", "where", "which", "still", "does", "with", "this", "that", "the", "are", "for", "all", "is", "a", "an", "to"}
    keywords = [t for t in tokens if t.lower() not in stopwords]
    
    # Entities
    entities = []
    lower_claim = clean.lower()
    if "api" in lower_claim:
        entities.append("API")
    if "python" in lower_claim:
        entities.append("Python")
    if "auth" in lower_claim or "key" in lower_claim or "oauth" in lower_claim:
        entities.append("Authentication")
    if "quantum" in lower_claim or "encrypt" in lower_claim:
        entities.append("Cryptography")

    return {
        "clean_claim": clean,
        "keywords": keywords,
        "entities": entities,
        "alternative_queries": [
            clean,
            f"{' '.join(keywords[:4])}"
        ]
    }



def generate_report(
    claim: str,
    classification: str,
    explanation: str,
    confidence: float,
    recommendation: str,
    human_verification_required: bool
) -> Dict[str, Any]:
    """Tool: Assembles the final structured investigation verdict."""
    return {
        "claim": claim,
        "classification": classification,
        "explanation": explanation,
        "confidence": confidence,
        "recommendation": recommendation,
        "human_verification_required": human_verification_required
    }

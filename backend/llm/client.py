import json
import re
from typing import List, Dict, Any, Optional
from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.llm.prompts import SYSTEM_INVESTIGATION_PROMPT, USER_INVESTIGATION_TEMPLATE

logger = get_logger("llm_client")


class LLMClient:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.provider = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "openai"
        self.model = settings.LLM_MODEL or "gpt-4o-mini"
        self.base_url = settings.LLM_BASE_URL or None

    def has_active_api_key(self) -> bool:
        return bool(
            self.api_key 
            and len(self.api_key.strip()) > 5 
            and not self.api_key.strip().startswith("your_")
        )

    def reason_over_evidence(
        self,
        claim: str,
        evidence_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sends the retrieved evidence to the one generative LLM for deep reasoning and classification.
        Strictly observes the anti-fake requirement: does not hardcode classifications based on keywords.
        """
        if not evidence_items:
            return {
                "classification": "UNCERTAIN",
                "reasoning": "No relevant evidence was retrieved from the knowledge base for this claim. The system cannot verify or refute it without source documentation.",
                "comparison": "Baseline claim has no matching references in the active knowledge repository.",
                "confidence": 0.95,
                "recommendation": "Ingest relevant documentation into the Knowledge Base before re-evaluating this claim.",
                "human_verification_required": True,
                "model_used": "system-evaluator"
            }

        # Format evidence for the prompt with all metadata (source, version, date, document_id)
        formatted_pieces = []
        for i, ev in enumerate(evidence_items, 1):
            source = ev.get("source", "Unknown")
            version = ev.get("version", "N/A")
            date = ev.get("date", "N/A")
            filename = ev.get("filename", "")
            doc_id = ev.get("document_id", "")
            text = ev.get("chunk_text", "")
            formatted_pieces.append(
                f"[Evidence #{i}]\n- Document ID: {doc_id}\n- Filename: {filename}\n- Source: {source}\n- Version: {version}\n- Date: {date}\n- Text: \"{text}\""
            )
        evidence_formatted = "\n\n".join(formatted_pieces)

        # 1. Real Generative LLM API Call
        if self.has_active_api_key():
            try:
                result = self._call_generative_llm(claim, evidence_formatted)
                if result:
                    result["model_used"] = f"{self.provider}:{self.model}"
                    return result
            except Exception as e:
                logger.error(f"Error calling LLM provider '{self.provider}': {e}. Falling back to error handling safe verdict.")
                return {
                    "classification": "UNCERTAIN",
                    "reasoning": f"LLM API call failed with error: {str(e)}. In accordance with safety policies, uncertain classification is returned rather than guessing.",
                    "comparison": "Unable to complete semantic reasoning due to upstream LLM API failure.",
                    "confidence": 0.50,
                    "recommendation": "Verify API key, rate limits, and network connectivity in .env.",
                    "human_verification_required": True,
                    "model_used": "error-handler"
                }

        # 2. Informative Fallback when API key is unconfigured
        logger.warning("No active LLM_API_KEY configured in .env.")
        return {
            "classification": "UNCERTAIN",
            "reasoning": "Generative LLM API key is not configured in .env. KnowledgeGuard AI adheres to strict anti-fake requirements: knowledge classification is genuinely performed by an LLM and cannot be hardcoded or simulated. Please add your LLM API key (e.g., Groq free tier or OpenAI) to .env to enable full autonomous reasoning.",
            "comparison": f"Retrieved {len(evidence_items)} candidate evidence chunk(s) from ChromaDB, awaiting LLM inference.",
            "confidence": 0.60,
            "recommendation": "Set LLM_API_KEY in .env (Groq free tier or OpenAI) and re-run investigation.",
            "human_verification_required": True,
            "model_used": "unconfigured-api-key"
        }

    def _call_generative_llm(self, claim: str, evidence_formatted: str) -> Optional[Dict[str, Any]]:
        from openai import OpenAI
        
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        elif self.provider == "groq":
            client_kwargs["base_url"] = "https://api.groq.com/openai/v1"

        client = OpenAI(**client_kwargs)
        prompt = USER_INVESTIGATION_TEMPLATE.format(claim=claim, evidence_formatted=evidence_formatted)

        # Call chat completion
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_INVESTIGATION_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"} if "gpt" in self.model or "groq" in self.provider else None
        )

        content = response.choices[0].message.content
        if not content:
            return None

        # Clean JSON markdown fences
        clean_json = re.sub(r"^```(?:json)?\s*", "", content.strip())
        clean_json = re.sub(r"\s*```$", "", clean_json.strip())
        data = json.loads(clean_json)

        # Normalize confidence to decimal (0.0 to 1.0)
        raw_conf = data.get("confidence", 0.85)
        if isinstance(raw_conf, (int, float)):
            conf_val = raw_conf / 100.0 if raw_conf > 1.0 else float(raw_conf)
        else:
            try:
                conf_val = float(str(raw_conf).replace("%", ""))
                conf_val = conf_val / 100.0 if conf_val > 1.0 else conf_val
            except Exception:
                conf_val = 0.85

        # Normalize classification
        cls_val = str(data.get("classification", "UNCERTAIN")).strip().upper()
        if cls_val not in ["CURRENT", "OUTDATED", "CONFLICTING", "UNCERTAIN"]:
            cls_val = "UNCERTAIN"

        return {
            "classification": cls_val,
            "reasoning": data.get("reasoning", data.get("explanation", "Reasoning generated by LLM.")),
            "comparison": data.get("comparison", "Comparison of retrieved evidence."),
            "confidence": round(conf_val, 2),
            "recommendation": data.get("recommendation", "Review findings with domain experts."),
            "human_verification_required": bool(data.get("human_verification_required", True))
        }


llm_client = LLMClient()

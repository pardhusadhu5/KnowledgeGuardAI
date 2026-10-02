import os
import json
import re
from typing import List, Dict, Any, Optional
from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.llm.prompts import SYSTEM_INVESTIGATION_PROMPT, USER_INVESTIGATION_TEMPLATE

logger = get_logger("llm_client")


class LLMClient:
    def __init__(self):
        self.base_url = settings.LLM_BASE_URL or None

    @property
    def provider(self) -> str:
        key = self.get_api_key()
        groq_k = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
        gemini_k = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        openai_k = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if key and groq_k and key == groq_k:
            return "groq"
        if key and gemini_k and key == gemini_k:
            return "gemini"
        if key and openai_k and key == openai_k:
            return "openai"
        return (settings.LLM_PROVIDER or "groq").lower()

    @property
    def model(self) -> str:
        prov = self.provider
        if settings.LLM_MODEL and settings.LLM_MODEL != "gemini-1.5-flash":
            return settings.LLM_MODEL
        if prov == "groq":
            return "openai/gpt-oss-120b"
        elif prov == "gemini":
            return "gemini-1.5-flash"
        return "gpt-4o-mini"

    def get_api_key(self) -> str:
        return settings.get_effective_api_key()

    def has_active_api_key(self) -> bool:
        key = self.get_api_key()
        return bool(
            key 
            and len(key.strip()) > 5 
            and not key.strip().startswith("your_")
        )

    def reason_over_evidence(
        self,
        claim: str,
        evidence_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sends the retrieved evidence to the one generative LLM (Gemini, OpenAI, or Groq)
        for evidence-bound reasoning and classification.
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
            page = ev.get("page", 1)
            text = ev.get("chunk_text", "")
            formatted_pieces.append(
                f"[Evidence #{i}]\n- Document ID: {doc_id}\n- Filename: {filename}\n- Page: {page}\n- Source: {source}\n- Version: {version}\n- Date: {date}\n- Text: \"{text}\""
            )
        evidence_formatted = "\n\n".join(formatted_pieces)

        # 1. Real Generative LLM API Call
        if self.has_active_api_key():
            try:
                if self.provider == "gemini":
                    result = self._call_gemini(claim, evidence_formatted)
                else:
                    result = self._call_openai_compatible(claim, evidence_formatted)

                if result:
                    result["model_used"] = f"{self.provider}:{self.model}"
                    return result
            except Exception as e:
                logger.error(f"Error calling LLM provider '{self.provider}': {e}. Returning safe error verdict.")
                return {
                    "classification": "UNCERTAIN",
                    "reasoning": f"LLM API call failed with error: {str(e)}. In accordance with safety policies, UNCERTAIN classification is returned rather than guessing.",
                    "comparison": "Unable to complete semantic reasoning due to upstream LLM API communication failure.",
                    "confidence": 0.50,
                    "recommendation": "Verify GEMINI_API_KEY / LLM_API_KEY in .env and check network connectivity.",
                    "human_verification_required": True,
                    "model_used": "error-handler"
                }

        # 2. Informative Safe Fallback when API key is unconfigured
        logger.warning(f"No active API key configured in .env for provider '{self.provider}'.")
        return {
            "classification": "UNCERTAIN",
            "reasoning": f"Generative LLM API key for '{self.provider}' is not configured in .env. In accordance with KnowledgeGuard AI anti-fake verification rules, classifications must be generated by a real generative LLM. Please set GEMINI_API_KEY or LLM_API_KEY in .env to perform live reasoning.",
            "comparison": f"Retrieved {len(evidence_items)} candidate evidence chunk(s) from ChromaDB, awaiting LLM inference.",
            "confidence": 0.60,
            "recommendation": "Configure GEMINI_API_KEY in .env and re-run investigation.",
            "human_verification_required": True,
            "model_used": "unconfigured-api-key"
        }

    def _call_gemini(self, claim: str, evidence_formatted: str) -> Optional[Dict[str, Any]]:
        from google import genai
        from google.genai import types

        api_key = self.get_api_key()
        client = genai.Client(api_key=api_key)
        prompt = USER_INVESTIGATION_TEMPLATE.format(claim=claim, evidence_formatted=evidence_formatted)

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INVESTIGATION_PROMPT,
                temperature=0.0,
                response_mime_type="application/json"
            )
        )

        content = response.text
        if not content:
            return None

        return self._parse_json_result(content)

    def _call_openai_compatible(self, claim: str, evidence_formatted: str) -> Optional[Dict[str, Any]]:
        from openai import OpenAI
        
        api_key = self.get_api_key()
        client_kwargs = {"api_key": api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        elif self.provider == "groq":
            client_kwargs["base_url"] = "https://api.groq.com/openai/v1"

        client = OpenAI(**client_kwargs)
        prompt = USER_INVESTIGATION_TEMPLATE.format(claim=claim, evidence_formatted=evidence_formatted)

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

        return self._parse_json_result(content)

    def _parse_json_result(self, content: str) -> Dict[str, Any]:
        # Strip markdown fences
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

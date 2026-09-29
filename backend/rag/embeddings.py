import math
import re
from typing import List
from backend.utils.logger import get_logger

logger = get_logger("embeddings")

# High-reliability embedding function:
# If chromadb default or sentence-transformers is available, use it.
# Otherwise, provide a fast TF-IDF / character n-gram cosine embedding representation
# so the system NEVER crashes even without internet connection or model downloads.

class LocalFallbackEmbedding:
    """Deterministic, zero-dependency embedding generator based on subword hashing & TF weighting."""
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _hash_token(self, token: str, seed: int = 0) -> int:
        h = seed
        for char in token:
            h = (h * 31 + ord(char)) & 0xFFFFFFFF
        return h

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return vec
        
        for token in tokens:
            idx1 = self._hash_token(token, 17) % self.dim
            idx2 = self._hash_token(token, 31) % self.dim
            vec[idx1] += 1.0
            vec[idx2] += 0.5
            
            # Bigrams
            if len(token) >= 3:
                for i in range(len(token) - 2):
                    sub = token[i:i+3]
                    idx_sub = self._hash_token(sub, 53) % self.dim
                    vec[idx_sub] += 0.3

        # Normalize L2
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


def get_embedding_function():
    try:
        from chromadb.utils import embedding_functions
        # Default chromadb embedding uses all-MiniLM-L6-v2 via onnxruntime
        ef = embedding_functions.DefaultEmbeddingFunction()
        # Test a dummy string to see if weights can be loaded
        test_res = ef(["test"])
        if test_res and len(test_res[0]) > 0:
            logger.info("ChromaDB default embedding function successfully initialized.")
            return ef
    except Exception as e:
        logger.warning(f"Default Chroma embedding unavailable ({e}). Using resilient internal embedding.")
    
    return LocalFallbackEmbedding()

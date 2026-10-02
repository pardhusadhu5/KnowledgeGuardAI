import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.rag.embeddings import get_embedding_function

logger = get_logger("vector_store")

COLLECTION_NAME = settings.COLLECTION_NAME


class VectorStoreManager:
    def __init__(self):
        self._initialized = False
        self.client = None
        self.embedding_function = None
        self.collection = None

    def _ensure_initialized(self):
        if self._initialized and self.collection is not None:
            return
        logger.info("Initializing ChromaDB vector store and embedding engine...")
        if settings.CHROMA_SERVER_HOST:
            headers = {"X-Chroma-Token": settings.CHROMA_AUTH_TOKEN} if settings.CHROMA_AUTH_TOKEN else None
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_SERVER_HOST,
                port=settings.CHROMA_SERVER_PORT,
                ssl=settings.CHROMA_SERVER_SSL,
                headers=headers,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            logger.info(f"Initialized ChromaDB HttpClient connected to {settings.CHROMA_SERVER_HOST}:{settings.CHROMA_SERVER_PORT}")
        else:
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            logger.info(f"Initialized ChromaDB PersistentClient at: {settings.CHROMA_PERSIST_DIR}")
        self.embedding_function = get_embedding_function()
        self._get_or_create_collection()
        self._initialized = True

    def _get_or_create_collection(self):
        try:
            # Check if embedding function has __call__ or embed_documents
            if hasattr(self.embedding_function, "__call__"):
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=self.embedding_function
                )
            else:
                # Custom embedding class
                class ChromaEmbeddingAdapter:
                    def __init__(self, fn):
                        self.fn = fn
                    def __call__(self, input: List[str]) -> List[List[float]]:
                        return self.fn.embed_documents(input)
                    def embed_query(self, input: str) -> List[float]:
                        return self.fn.embed_query(input)

                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    embedding_function=ChromaEmbeddingAdapter(self.embedding_function)
                )
            logger.info(f"Connected to ChromaDB collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error accessing collection {COLLECTION_NAME}: {e}")
            raise

    def add_chunks_with_metadata(
        self,
        chunk_ids: List[str],
        chunks: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        if not chunks:
            return []
        self._ensure_initialized()

        clean_metas = []
        for m in metadatas:
            clean_m = {
                "document_id": int(m.get("document_id", 0)),
                "chunk_index": int(m.get("chunk_index", 0)),
                "page": int(m.get("page", 1)),
                "source": str(m.get("source", "Document")),
                "version": str(m.get("version", "1.0")),
                "topic": str(m.get("topic", "General")),
                "document_date": str(m.get("document_date", "")),
                "filename": str(m.get("filename", "")),
            }
            clean_metas.append(clean_m)

        # Use upsert to guarantee idempotency and avoid duplicate embeddings on retry
        self.collection.upsert(
            ids=chunk_ids,
            documents=chunks,
            metadatas=clean_metas
        )
        return chunk_ids

    def add_chunks(
        self,
        document_id: int,
        chunks: List[str],
        base_metadata: Dict[str, Any]
    ) -> List[str]:
        if not chunks:
            return []
        self._ensure_initialized()

        ids = [f"doc_{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = []
        for i in range(len(chunks)):
            meta = {
                "document_id": int(document_id),
                "chunk_index": int(i),
                "page": int(base_metadata.get("page", 1)),
                "source": str(base_metadata.get("source", "Document")),
                "version": str(base_metadata.get("version", "1.0")),
                "topic": str(base_metadata.get("topic", "General")),
                "document_date": str(base_metadata.get("document_date", "")),
                "filename": str(base_metadata.get("filename", "")),
            }
            metadatas.append(meta)

        self.collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas
        )
        logger.info(f"Indexed {len(chunks)} chunks for document_id={document_id} into ChromaDB")
        return ids

    def search(
        self,
        query: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        total_items = self.collection.count()
        if total_items == 0:
            return []

        limit = min(n_results, total_items)
        kwargs: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        try:
            results = self.collection.query(**kwargs)
        except Exception as e:
            logger.warning(f"ChromaDB search error with filter: {e}. Retrying without filter.")
            kwargs.pop("where", None)
            results = self.collection.query(**kwargs)

        items = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            chunk_ids = results["ids"][0] if results.get("ids") else [None] * len(docs)

            for doc, meta, dist, cid in zip(docs, metas, distances, chunk_ids):
                # Convert distance to a normalized similarity score (0.0 to 1.0)
                relevance_score = max(0.0, min(1.0, 1.0 - (dist / 2.0))) if dist is not None else 0.8
                page_val = meta.get("page", 1)
                try:
                    page_num = int(page_val)
                except Exception:
                    page_num = 1

                items.append({
                    "chunk_id_str": cid,
                    "document_id": meta.get("document_id"),
                    "chunk_text": doc,
                    "source": meta.get("source", "Document"),
                    "version": meta.get("version", "1.0"),
                    "date": meta.get("document_date", ""),
                    "topic": meta.get("topic", "General"),
                    "filename": meta.get("filename", ""),
                    "page": page_num,
                    "relevance_score": round(relevance_score, 4),
                    "distance": dist
                })

        return items

    def delete_document_chunks(self, document_id: int):
        try:
            self._ensure_initialized()
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector chunks for document_id={document_id}")
        except Exception as e:
            logger.warning(f"Failed to delete Chroma chunks for doc {document_id}: {e}")

    def count(self) -> int:
        try:
            self._ensure_initialized()
            return self.collection.count()
        except Exception as e:
            logger.warning(f"Error querying ChromaDB count: {e}")
            return 0

    def reset_collection(self):
        try:
            self._ensure_initialized()
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._get_or_create_collection()


vector_store = VectorStoreManager()

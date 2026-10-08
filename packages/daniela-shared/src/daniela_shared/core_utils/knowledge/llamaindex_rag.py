"""
LlamaIndex RAG Integration for Daniela OS
Semantic search and retrieval over Daniela's knowledge vault (12,480 memory nodes).
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import qdrant_client
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.llms import (
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
    MessageRole,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import DocxReader, FlatReader, PyMuPDFReader
from llama_index.vector_stores.qdrant import QdrantVectorStore


class LiteLLMGenericLLM(CustomLLM):
    """Minimal OpenAI-compatible chat client for any LiteLLM-routed model.

    Avoids llama_index OpenAI model-name validation so gateway model
    names (e.g. deepseek-coder-1b) work. No extra dependencies (httpx).
    """

    model_name: str = "deepseek-coder-1b"
    api_base: str = "http://localhost:4000/v1"
    api_key: str = "sk-aig-master-key"
    temperature: float = 0.1
    max_tokens: int = 2048
    request_timeout: float = 120.0

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=8192,
            num_output=self.max_tokens,
            model_name=self.model_name,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, messages: list[ChatMessage], stream: bool = False) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": [
                {"role": m.role.value, "content": m.content} for m in messages
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

    def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResponse:
        with httpx.Client(timeout=self.request_timeout) as client:
            resp = client.post(
                f"{self.api_base}/chat/completions",
                json=self._payload(messages),
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]["message"]
        msg = ChatMessage(role=MessageRole.ASSISTANT, content=choice.get("content", ""))
        return ChatResponse(message=msg, raw=data)

    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        return CompletionResponse(
            text=self.chat([ChatMessage(role=MessageRole.USER, content=prompt)]).message.content or ""
        )

    def stream_chat(
        self, messages: list[ChatMessage], **kwargs: Any
    ) -> ChatResponseGen:
        yield self.chat(messages, **kwargs)

    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        yield self.complete(prompt, **kwargs)


@dataclass
class RAGConfig:
    """Configuration for LlamaIndex RAG system."""
    # LLM (LiteLLM gateway - override via env)
    llm_model: str = field(default_factory=lambda: os.getenv("RAG_LLM_MODEL", "deepseek-coder-1b"))
    llm_temperature: float = 0.1
    llm_base_url: str = field(default_factory=lambda: os.getenv("LITELLM_BASE_URL", "http://localhost:4000/v1"))
    llm_api_key: str = field(default_factory=lambda: os.getenv("LITELLM_API_KEY", "sk-aig-master-key"))

    # Embeddings
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_dim: int = 384

    # Vector Store (Qdrant - override via env for Docker)
    qdrant_host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    qdrant_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    qdrant_collection: str = "daniela_knowledge"

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval (MiniLM cosine scores for short docs are typically 0.3-0.6)
    similarity_top_k: int = 10
    similarity_cutoff: float = 0.3

    # Response
    response_mode: str = "compact"


class DanielaRAG:
    """
    LlamaIndex RAG system for Daniela's knowledge vault.
    Provides semantic search, document ingestion, and query answering.
    """

    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()
        self._init_settings()
        self._init_vector_store()
        self._init_index()
        self._init_query_engine()

    def _init_settings(self) -> None:
        """Initialize global LlamaIndex settings."""
        # Custom client: no model-name validation, works with any
        # LiteLLM-routed model (local Ollama or cloud).
        Settings.llm = LiteLLMGenericLLM(
            model_name=self.config.llm_model,
            api_base=self.config.llm_base_url,
            api_key=self.config.llm_api_key,
            temperature=self.config.llm_temperature,
        )
        Settings.embed_model = HuggingFaceEmbedding(
            model_name=self.config.embed_model,
        )
        Settings.node_parser = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

    def _init_vector_store(self) -> None:
        """Initialize Qdrant vector store."""
        self.qdrant_client = qdrant_client.QdrantClient(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port,
        )

        # Create collection if not exists
        try:
            self.qdrant_client.get_collection(self.config.qdrant_collection)
        except Exception:
            self.qdrant_client.create_collection(
                collection_name=self.config.qdrant_collection,
                vectors_config=qdrant_client.models.VectorParams(
                    size=self.config.embed_dim,
                    distance=qdrant_client.models.Distance.COSINE,
                ),
            )

        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.config.qdrant_collection,
        )
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store,
            docstore=SimpleDocumentStore(),
        )

    def _init_index(self) -> None:
        """Initialize or load the vector index."""
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context,
            )
        except Exception:
            # Create empty index
            self.index = VectorStoreIndex(
                [],
                storage_context=self.storage_context,
            )

    def _init_query_engine(self) -> None:
        """Initialize query engine with retriever and synthesizer."""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=self.config.similarity_top_k,
        )

        response_synthesizer = get_response_synthesizer(
            response_mode=self.config.response_mode,
        )

        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=self.config.similarity_cutoff),
            ],
        )

    # ==================== DOCUMENT INGESTION ====================

    def add_documents(
        self,
        documents: list[Document],
        show_progress: bool = True,
    ) -> int:
        """Add documents to the index."""
        # Create ingestion pipeline.
        # NOTE: TitleExtractor/KeywordExtractor intentionally omitted - they
        # call the LLM per document (slow on 1B local models) and pollute
        # metadata with model rambling. Chunk + embed only.
        pipeline = IngestionPipeline(
            transformations=[
                SentenceSplitter(
                    chunk_size=self.config.chunk_size,
                    chunk_overlap=self.config.chunk_overlap,
                ),
                Settings.embed_model,
            ],
            vector_store=self.vector_store,
            docstore=self.storage_context.docstore,
        )

        # Run pipeline
        nodes = pipeline.run(documents=documents, show_progress=show_progress)
        return len(nodes)

    def add_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Add a single text document."""
        doc = Document(
            text=text,
            metadata=metadata or {},
            doc_id=doc_id or f"doc_{datetime.utcnow().isoformat()}",
        )
        self.add_documents([doc])
        return doc.doc_id

    def add_file(self, file_path: str | Path) -> list[str]:
        """Add a file (PDF, DOCX, TXT, MD) to the index."""
        path = Path(file_path)

        # Select reader based on extension
        readers = {
            ".pdf": PyMuPDFReader(),
            ".docx": DocxReader(),
            ".txt": FlatReader(),
            ".md": FlatReader(),
        }

        reader = readers.get(path.suffix.lower())
        if not reader:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        documents = reader.load_data(path)
        for doc in documents:
            doc.metadata.update({
                "source_file": str(path),
                "file_name": path.name,
                "file_type": path.suffix,
                "ingested_at": datetime.utcnow().isoformat(),
            })

        self.add_documents(documents)
        return [doc.doc_id for doc in documents]

    def add_memory_nodes(
        self,
        nodes: list[dict[str, Any]],
        namespace: str = "memory",
    ) -> int:
        """Add Daniela's memory nodes as documents."""
        documents = []
        for node in nodes:
            doc = Document(
                text=node.get("content", ""),
                metadata={
                    "namespace": namespace,
                    "node_id": node.get("id"),
                    "memory_type": node.get("type", "semantic"),
                    "importance": node.get("importance", 0.5),
                    "tags": node.get("tags", []),
                    "timestamp": node.get("timestamp", datetime.utcnow().isoformat()),
                    **node.get("metadata", {}),
                },
                doc_id=node.get("id", f"mem_{datetime.utcnow().isoformat()}"),
            )
            documents.append(doc)

        self.add_documents(documents)
        return len(documents)

    # ==================== QUERY ====================

    def query(self, question: str) -> dict[str, Any]:
        """Query the RAG system."""
        response = self.query_engine.query(question)

        return {
            "answer": str(response),
            "sources": [
                {
                    "text": node.text[:500],
                    "score": node.score,
                    "metadata": node.metadata,
                }
                for node in response.source_nodes
            ],
            "metadata": getattr(response, "metadata", {}),
        }

    def query_stream(self, question: str):
        """Stream query response."""
        streaming_engine = self.query_engine._as_query_engine(streaming=True)
        return streaming_engine.query(question)

    def retrieve(self, question: str, top_k: int | None = None) -> list[dict]:
        """Retrieve relevant nodes without synthesis."""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k or self.config.similarity_top_k,
        )
        nodes = retriever.retrieve(question)

        return [
            {
                "text": node.text,
                "score": node.score,
                "metadata": node.metadata,
            }
            for node in nodes
        ]

    # ==================== MANAGEMENT ====================

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        try:
            self.index.delete_ref_doc(doc_id, delete_from_docstore=True)
            return True
        except Exception:
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics (defensive across qdrant-client versions)."""
        total_vectors = 0
        try:
            collection_info = self.qdrant_client.get_collection(self.config.qdrant_collection)
            total_vectors = (
                getattr(collection_info, "vectors_count", None)
                or getattr(getattr(collection_info, "result", None), "vectors_count", None)
                or getattr(getattr(collection_info, "result", None), "points_count", None)
                or 0
            )
        except Exception:
            total_vectors = 0
        try:
            indexed = len(self.storage_context.docstore.docs)
        except Exception:
            indexed = 0
        return {
            "total_vectors": total_vectors,
            "indexed_documents": indexed,
            "collection_name": self.config.qdrant_collection,
            "embed_model": self.config.embed_model,
            "llm_model": self.config.llm_model,
        }

    def rebuild_index(self) -> None:
        """Rebuild index from docstore."""
        docs = list(self.storage_context.docstore.docs.values())
        self.index = VectorStoreIndex.from_documents(
            docs,
            storage_context=self.storage_context,
        )
        self._init_query_engine()


# Global instances (one per Qdrant collection).
# Convention: each NotebookLM notebook lives in its own collection
# named f"nb_{slug}"; the default vault collection is "daniela_knowledge".
DEFAULT_COLLECTION = os.getenv("RAG_COLLECTION", "daniela_knowledge")
NOTEBOOK_PREFIX = "nb_"

_rag_cache: dict[str, DanielaRAG] = {}


def get_rag(collection: str | None = None) -> DanielaRAG:
    """Get (or create) the RAG instance for a collection."""
    key = collection or DEFAULT_COLLECTION
    if key not in _rag_cache:
        cfg = RAGConfig()
        cfg.qdrant_collection = key
        _rag_cache[key] = DanielaRAG(cfg)
    return _rag_cache[key]


def list_collections() -> list[str]:
    """List Qdrant collections visible to RAG (best effort)."""
    try:
        client = qdrant_client.QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )
        cols = client.get_collections()
        names = [c.name for c in getattr(cols, "collections", []) or []]
        client.close()
        return sorted(names)
    except Exception:
        return sorted(_rag_cache.keys())


def notebook_collection(notebook: str) -> str:
    """Map a notebook display name to its Qdrant collection.

    Must match notebooklm_ingest.notebook_slug: NFKD -> ascii (accents and
    ñ removed) then non-alnum collapsed, so scoped context lookups hit the
    collections the ingestor actually created.
    """
    slug = unicodedata.normalize("NFKD", notebook).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug).strip("-").lower()[:80] or "general"
    return f"{NOTEBOOK_PREFIX}{slug}"


def assemble_context(question: str, collections: list[str], top_k: int = 5) -> dict[str, Any]:
    """Retrieve from several collections and assemble one context block.

    This is what Daniela calls to "get context from the notebooks":
    one query, many notebooks, cited sources back.
    """
    blocks: list[str] = []
    sources: list[dict[str, Any]] = []
    for collection in collections:
        try:
            hits = get_rag(collection).retrieve(question, top_k)
        except Exception as e:
            sources.append({"collection": collection, "error": str(e)})
            continue
        for h in hits:
            label = h.get("metadata", {}).get("note") or h.get("metadata", {}).get("source", "?")
            blocks.append(f"[{collection} | {label} | score={h.get('score', 0):.2f}]\n{h.get('text', '')}")
            sources.append({
                "collection": collection,
                "score": h.get("score"),
                "note": h.get("metadata", {}).get("note"),
                "source": h.get("metadata", {}).get("source"),
            })
    context = "\n\n---\n\n".join(blocks)
    return {"context": context, "sources": sources, "collections": collections}


# Convenience functions (collection=None -> default vault)
def add_knowledge(
    text: str, metadata: dict | None = None, collection: str | None = None,
) -> str:
    """Add knowledge to Daniela's vault (or a notebook collection)."""
    return get_rag(collection).add_text(text, metadata)


def query_knowledge(question: str, collection: str | None = None) -> dict[str, Any]:
    """Query Daniela's knowledge vault (or a notebook collection)."""
    return get_rag(collection).query(question)


def search_knowledge(
    question: str, top_k: int = 10, collection: str | None = None,
) -> list[dict]:
    """Search knowledge without synthesis."""
    return get_rag(collection).retrieve(question, top_k)


def ingest_memory_nodes(nodes: list[dict], namespace: str = "memory") -> int:
    """Ingest Daniela's memory nodes into RAG."""
    return get_rag().add_memory_nodes(nodes, namespace)


def ingest_file(file_path: str | Path) -> list[str]:
    """Ingest a file into knowledge vault."""
    return get_rag().add_file(file_path)

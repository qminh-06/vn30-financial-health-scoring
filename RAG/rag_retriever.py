"""RAG Retriever — production module cho FastAPI pipeline.

Cách dùng trong ai_analysis/analyze.py:
    from RAG.rag_retriever import build_rag_context, RAG_VERSION

    context = build_rag_context(ratios)   # str — inject vào prompt
    # Nếu pgvector chưa được build → trả về "" và log warning, không crash

Tham số tune: chỉnh RAGConfig trong RAG/config.py, không sửa file này.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings
    from langchain_core.vectorstores import VectorStoreRetriever

from RAG.config import RAGConfig

logger = logging.getLogger(__name__)

RAG_VERSION = "v1"

# Lazy-loaded singletons — khởi tạo một lần khi FastAPI nhận request đầu tiên
# ---------------------------------------------------------------------------
_retriever: VectorStoreRetriever | None = None
_active_config: RAGConfig | None = None


def _build_embedding_model(cfg: RAGConfig) -> Embeddings:
    """Factory trả về embedding model theo cfg.embedding.provider."""
    e = cfg.embedding
    provider = e.provider.lower()

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=e.model_name, dimensions=e.dimensions)

    if provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=e.model_name,
            google_api_key=os.environ["GEMINI_API_KEY"],
        )

    if provider == "cohere":
        from langchain_cohere import CohereEmbeddings
        return CohereEmbeddings(
            model=e.model_name,
            cohere_api_key=os.environ["COHERE_API_KEY"],
        )

    if provider == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=e.model_name)

    raise ValueError(f"Unknown embedding provider: {provider!r}")


def _load_retriever(cfg: RAGConfig) -> VectorStoreRetriever | None:
    """Kết nối pgvector và trả về retriever. None nếu không kết nối được."""
    global _retriever, _active_config

    if _retriever is not None:
        return _retriever

    try:
        from langchain_postgres import PGVector

        embedding_model = _build_embedding_model(cfg)

        vs = cfg.vector_store
        vectorstore = PGVector(
            embeddings=embedding_model,
            collection_name=vs.collection_name,
            connection=vs.connection_string,
            distance_strategy=vs.distance_strategy,
        )

        r = cfg.retrieval
        _retriever = vectorstore.as_retriever(
            search_type=r.search_type,
            search_kwargs={
                "k": r.top_k,
                "fetch_k": r.fetch_k,
                "lambda_mult": r.mmr_lambda,
            },
        )
        _active_config = cfg
        logger.info(
            "RAG retriever ready — collection=%s, embedding=%s/%s, search=%s k=%d",
            vs.collection_name,
            cfg.embedding.provider,
            cfg.embedding.model_name,
            r.search_type,
            r.top_k,
        )
        return _retriever

    except Exception as exc:
        logger.warning("RAG retriever unavailable: %s", exc)
        return None


def _ratios_to_query(ratios: dict) -> str:
    """Chuyển dict ratios thành câu query ngắn để retrieve context phù hợp."""
    parts = [f"{k}={v:.4f}" for k, v in ratios.items() if isinstance(v, (int, float))]
    return ", ".join(parts) + " — ngưỡng đánh giá tài chính VN30"


def _build_context_block(docs: list, cfg: RAGConfig) -> str:
    """Nối các chunk thành context string, cắt bớt nếu vượt max_context_tokens."""
    p = cfg.prompt
    max_chars = p.max_context_tokens * 4  # ước tính 4 char/token
    sections: list[str] = []
    total = 0

    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        # DB docs có ticker/year trong metadata — hiển thị rõ hơn
        ticker = doc.metadata.get("ticker", "")
        year = doc.metadata.get("year", "")
        label = source + (f" | {ticker} {year}" if ticker else "")
        block = f"[Nguồn: {label}]\n{doc.page_content.strip()}"

        if total + len(block) > max_chars:
            break
        sections.append(block)
        total += len(block)

    return p.chunk_separator.join(sections)


# Public API
# ---------------------------------------------------------------------------

def build_rag_context(ratios: dict, cfg: RAGConfig | None = None) -> str:
    """Retrieve và trả về context string để inject vào LLM prompt.

    Args:
        ratios: dict từ ratio_engine.compute.compute_all_ratios()
        cfg:    RAGConfig tuỳ chỉnh; None = dùng default RAGConfig()

    Returns:
        Context string sẵn sàng inject vào prompt.
        Trả về "" nếu pgvector chưa được build hoặc kết nối thất bại.
    """
    if cfg is None:
        cfg = RAGConfig()

    retriever = _load_retriever(cfg)
    if retriever is None:
        return ""

    query = _ratios_to_query(ratios)
    try:
        docs = retriever.invoke(query)
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        return ""

    if not docs:
        return ""

    return _build_context_block(docs, cfg)


def reset_retriever() -> None:
    """Buộc khởi tạo lại retriever (dùng sau khi rebuild vector store)."""
    global _retriever, _active_config
    _retriever = None
    _active_config = None
    logger.info("RAG retriever reset — will reinitialise on next call")

"""
RAG pipeline configuration.

Tất cả tham số có thể tune được tập trung ở đây, phân theo từng bước trong pipeline:
    1. Loading
    2. Chunking
    3. Embedding
    4. Vector store (pgvector)
    5. Retrieval & reranking
    6. Prompt

Cách dùng:
    from RAG.config import RAGConfig
    cfg = RAGConfig()            # dùng mặc định
    cfg.chunking.chunk_size      # truy cập tham số

Mỗi sub-class tương ứng một bước trong notebook
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# 1. Loading
# ---------------------------------------------------------------------------
@dataclass
class LoadingConfig:
    """Cấu hình nguồn dữ liệu đầu vào."""

    # Thư mục chứa file phi cấu trúc (.md, .txt, .pdf)
    knowledge_base_dir: str = str(Path(__file__).parent / "knowledge_base")

    # Glob pattern để quét file
    text_glob: str = "**/*.{md,txt}"
    pdf_glob: str = "**/*.pdf"

    # PDF loader backend: "pypdf" | "pdfminer" | "unstructured"
    # pypdf: nhẹ, đủ dùng cho báo cáo tài chính dạng text-based
    # unstructured: mạnh hơn nhưng cần cài thêm dependencies
    pdf_loader_backend: Literal["pypdf", "pdfminer", "unstructured"] = "pypdf"

    # Encoding mặc định cho TextLoader
    text_encoding: str = "utf-8"

    # Số worker khi load song song
    num_workers: int = 4


# 2. Chunking
# ---------------------------------------------------------------------------

@dataclass
class ChunkingConfig:
    """Cấu hình chunking — tham số nhạy cảm nhất với chất lượng retrieval."""

    # Kích thước chunk tính theo số ký tự
    # Tăng nếu context cần rộng hơn; giảm nếu retrieval bị noise
    chunk_size: int = 1200

    # Overlap giữa các chunk liền kề
    # Giữ khoảng 15–20% chunk_size để không mất context ở biên
    chunk_overlap: int = 200

    # Thêm start_index vào metadata — cần cho traceability (đã tắt = mất info)
    add_start_index: bool = True

    strip_whitespace: bool = True
    keep_separator: bool = True

    # Separator ưu tiên Markdown structure — tránh cắt giữa heading
    separators: list[str] = field(default_factory=lambda: [
        r"\n#{1,6} ",       # Headings H1–H6
        r"\n```[\w-]*\n",   # Code blocks
        r"\n\|.*\|\n",      # Markdown table rows
        r"\n>\s",           # Blockquotes
        r"\n\*\*\*+\n",     # Horizontal rules ***
        r"\n---+\n",
        r"\n___+\n",
        r"\n\n",            # Paragraph break
        r"\n",
        r"\t",
        r" ",
        r"",
    ])

    is_separator_regex: bool = True


# 3. Embedding
# ---------------------------------------------------------------------------

@dataclass
class EmbeddingConfig:
    """Cấu hình embedding model.

    LLM/embedding chưa xác định — dùng provider và model_name làm
    điểm trung tâm để swap dễ dàng.
    Các giá trị hợp lệ hiện tại:
        provider="openai"   model_name="text-embedding-3-small" | "text-embedding-3-large"
        provider="google"   model_name="models/text-embedding-004"
        provider="cohere"   model_name="embed-multilingual-v3.0"
        provider="huggingface" model_name="<model_id>"  (local, không cần API key)
    """

    provider: str = "openai"
    model_name: str = "text-embedding-3-small"

    # Số chiều vector — phải khớp với cột vector trong pgvector
    # text-embedding-3-small: 1536 | text-embedding-004: 768 | multilingual-e5: 768
    dimensions: int = 1536

    # Batch size khi embed nhiều chunk
    batch_size: int = 512


# ---------------------------------------------------------------------------
# 4. Vector store (pgvector)
# ---------------------------------------------------------------------------

@dataclass
class VectorStoreConfig:
    """Cấu hình kết nối pgvector."""

    # Lấy từ env nếu không truyền trực tiếp
    connection_string: str = field(
        default_factory=lambda: os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/vn30_fhs",
        )
    )

    # Tên collection / table trong pgvector
    collection_name: str = "vn30_financial_kb"

    # Metric tính khoảng cách: "cosine" | "euclidean" | "inner_product"
    # cosine phù hợp nhất với embedding dạng text
    distance_strategy: Literal["cosine", "euclidean", "inner_product"] = "cosine"

    # Pre-delete collection khi upsert toàn bộ (rebuild)
    pre_delete_collection: bool = False


# 5. Retrieval & reranking
# ---------------------------------------------------------------------------

@dataclass
class RetrievalConfig:
    """Cấu hình retrieval và reranking."""

    # Số chunk trả về sau retrieval (k)
    top_k: int = 5

    # Số chunk fetch trước khi MMR rerank
    # fetch_k nên >= top_k * 2~3 để MMR có đủ candidates
    fetch_k: int = 12

    # search_type: "similarity" | "mmr" | "similarity_score_threshold"
    # mmr: tránh trả về chunk trùng nội dung (phù hợp knowledge base tài chính)
    search_type: Literal["similarity", "mmr", "similarity_score_threshold"] = "mmr"

    # Chỉ dùng khi search_type="similarity_score_threshold"
    score_threshold: float = 0.7

    # Lambda cho MMR: 1.0 = pure similarity, 0.0 = pure diversity
    mmr_lambda: float = 0.5

    # Reranker model (None = không rerank)
    # Ví dụ: "cross-encoder/ms-marco-MiniLM-L-6-v2" (local)
    #         "cohere-rerank-multilingual-v3.0" (API)
    reranker_model: str | None = None


# 6. Prompt
# ---------------------------------------------------------------------------

@dataclass
class PromptConfig:
    """Cấu hình prompt engineering cho LLM."""

    # Version để track thay đổi prompt trong evaluation_results
    version: str = "v1"

    # Số token tối đa dành cho RAG context trong prompt
    # Giúp tránh vượt context window của LLM
    max_context_tokens: int = 2000

    # Header section trong prompt
    rag_section_header: str = "## Ngưỡng tham chiếu từ knowledge base VN30"
    data_section_header: str = "## Chỉ số tài chính theo năm"

    # Separator giữa các chunk trong context block
    chunk_separator: str = "\n\n---\n\n"


# Root config — điểm truy cập duy nhất
# ---------------------------------------------------------------------------

@dataclass
class RAGConfig:
    """Root config, tập hợp toàn bộ pipeline.

    Ví dụ thay đổi một tham số:
        cfg = RAGConfig()
        cfg.chunking.chunk_size = 800        # thử chunk nhỏ hơn
        cfg.retrieval.top_k = 6              # lấy nhiều chunk hơn
        cfg.embedding.model_name = "..."     # đổi embedding model
    """

    loading: LoadingConfig = field(default_factory=LoadingConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)

    def summary(self) -> dict:
        """Trả về dict tóm tắt các tham số key — tiện log vào evaluation_results."""
        return {
            "embedding_provider": self.embedding.provider,
            "embedding_model": self.embedding.model_name,
            "embedding_dimensions": self.embedding.dimensions,
            "chunk_size": self.chunking.chunk_size,
            "chunk_overlap": self.chunking.chunk_overlap,
            "search_type": self.retrieval.search_type,
            "top_k": self.retrieval.top_k,
            "fetch_k": self.retrieval.fetch_k,
            "reranker": self.retrieval.reranker_model,
            "prompt_version": self.prompt.version,
            "distance_strategy": self.vector_store.distance_strategy,
        }

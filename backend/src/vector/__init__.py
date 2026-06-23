"""向量数据库模块 - 提供 FAISS / Chroma 抽象层与工厂。"""
from src.vector.db import (
    ChromaAdapter,
    DEFAULT_DIMENSION,
    FAISSAdapter,
    SUPPORTED_COLLECTIONS,
    VectorDB,
    VectorDBFactory,
    get_vector_db,
)

__all__ = [
    "VectorDB",
    "FAISSAdapter",
    "ChromaAdapter",
    "VectorDBFactory",
    "get_vector_db",
    "DEFAULT_DIMENSION",
    "SUPPORTED_COLLECTIONS",
]

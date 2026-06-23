"""长期记忆模块 - 基于向量数据库存储和检索语义记忆。"""
import hashlib
import uuid
from typing import Any, Dict, List, Optional

from src.memory.schemas import MemoryItem
from src.monitoring.logger import Logger
from src.vector.db import DEFAULT_DIMENSION, VectorDB, VectorDBFactory

logger = Logger()

# 长期记忆使用的默认集合名称
DEFAULT_COLLECTION = "conversation_memory"


def _text_to_vector(text: str, dimension: int = DEFAULT_DIMENSION) -> List[float]:
    """将文本通过哈希方法转换为固定维度向量。

    这是一个用于测试的简单实现，不依赖外部嵌入模型。
    相同文本会生成相同的向量，不同文本生成不同向量。
    实际使用时应替换为真实嵌入模型（如 OpenAI text-embedding-ada-002）。

    Args:
        text: 输入文本。
        dimension: 向量维度。

    Returns:
        L2 归一化的浮点向量列表。
    """
    vector: List[float] = []
    for i in range(dimension):
        # 使用文本和维度索引组合生成确定性哈希
        hash_input = f"{text}:{i}".encode("utf-8")
        hash_bytes = hashlib.sha256(hash_input).digest()
        # 取前 8 字节转为整数，映射到 [-1, 1] 区间
        value = int.from_bytes(hash_bytes[:8], "big") / 0xFFFFFFFFFFFFFFFF
        value = value * 2.0 - 1.0
        vector.append(value)

    # L2 归一化，使相同文本得到相同的单位向量
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


class LongTermMemory:
    """长期记忆，基于向量数据库进行语义存储与检索。"""

    def __init__(
        self,
        vector_db: Optional[VectorDB] = None,
        collection_name: str = DEFAULT_COLLECTION,
    ) -> None:
        """初始化长期记忆。

        Args:
            vector_db: 向量数据库实例，未提供时通过 VectorDBFactory 创建。
            collection_name: 使用的集合名称，默认为 conversation_memory。
        """
        if vector_db is None:
            vector_db = VectorDBFactory.create()
        self.vector_db = vector_db
        self.collection_name = collection_name
        # 确保集合存在（create_collection 为幂等操作）
        self.vector_db.create_collection(self.collection_name)
        logger.info(
            f"长期记忆已初始化: collection={self.collection_name} "
            f"dimension={self.vector_db.dimension}"
        )

    def add(self, content: str, metadata: Dict[str, Any]) -> str:
        """添加长期记忆到向量库。

        Args:
            content: 记忆内容文本。
            metadata: 附加元数据（如 session_id、role 等）。

        Returns:
            生成的记忆 ID。
        """
        memory_id = str(uuid.uuid4())
        # 将内容存入 metadata 以便检索时恢复
        stored_metadata = {**metadata, "content": content}
        vector = _text_to_vector(content, self.vector_db.dimension)
        self.vector_db.add_vectors(
            collection_name=self.collection_name,
            ids=[memory_id],
            vectors=[vector],
            metadatas=[stored_metadata],
        )
        logger.info(f"长期记忆已添加: id={memory_id} content_len={len(content)}")
        return memory_id

    def search(self, query: str, limit: int = 5) -> List[MemoryItem]:
        """向量相似性搜索。

        Args:
            query: 查询文本。
            limit: 返回结果数量上限。

        Returns:
            匹配的记忆项列表，按相似度从高到低排序。
        """
        query_vector = _text_to_vector(query, self.vector_db.dimension)
        results = self.vector_db.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            top_k=limit,
        )
        items: List[MemoryItem] = []
        for r in results:
            meta = r.get("metadata", {}) or {}
            items.append(
                MemoryItem(
                    id=r.get("id"),
                    content=meta.get("content", ""),
                    metadata=meta,
                    score=r.get("score"),
                )
            )
        logger.info(f"长期记忆搜索: query='{query}' limit={limit} hits={len(items)}")
        return items

    def delete(self, ids: List[str]) -> None:
        """根据 ID 列表删除长期记忆。

        Args:
            ids: 要删除的记忆 ID 列表。
        """
        self.vector_db.delete_vectors(
            collection_name=self.collection_name,
            ids=ids,
        )
        logger.info(f"长期记忆已删除: count={len(ids)}")

    def update(self, id: str, content: str, metadata: Dict[str, Any]) -> None:
        """更新长期记忆（先删除后添加，保持相同 ID）。

        Args:
            id: 要更新的记忆 ID。
            content: 新的记忆内容。
            metadata: 新的元数据。
        """
        self.delete([id])
        stored_metadata = {**metadata, "content": content}
        vector = _text_to_vector(content, self.vector_db.dimension)
        self.vector_db.add_vectors(
            collection_name=self.collection_name,
            ids=[id],
            vectors=[vector],
            metadatas=[stored_metadata],
        )
        logger.info(f"长期记忆已更新: id={id}")

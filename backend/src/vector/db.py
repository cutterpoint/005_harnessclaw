"""向量数据库抽象层 - 支持 FAISS 和 Chroma 两种后端。"""
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.core.config import settings
from src.monitoring.logger import logger

# 默认向量维度（OpenAI text-embedding-ada-002 / text-embedding-3-small 兼容）
DEFAULT_DIMENSION = 1536

# 支持的集合名称
SUPPORTED_COLLECTIONS = (
    "conversation_memory",      # 对话记忆
    "skill_knowledge",          # 技能知识
    "document_embeddings",      # 文档嵌入
)

# 容错导入 faiss / numpy
try:
    import numpy as np  # noqa: F401
    _NUMPY_AVAILABLE = True
except ImportError:
    np = None  # type: ignore
    _NUMPY_AVAILABLE = False

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    _CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None  # type: ignore
    ChromaSettings = None  # type: ignore
    _CHROMA_AVAILABLE = False


class VectorDB(ABC):
    """向量数据库抽象基类，定义统一接口。"""

    def __init__(
        self,
        store_path: str,
        dimension: int = DEFAULT_DIMENSION,
    ) -> None:
        self.store_path = store_path
        self.dimension = dimension
        # 确保存储目录存在
        if store_path:
            os.makedirs(store_path, exist_ok=True)

    @abstractmethod
    def create_collection(self, collection_name: str) -> None:
        """创建集合。"""
        raise NotImplementedError

    @abstractmethod
    def add_vectors(
        self,
        collection_name: str,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """添加向量到集合。"""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """相似性搜索，返回 top_k 结果。"""
        raise NotImplementedError

    @abstractmethod
    def delete_vectors(self, collection_name: str, ids: List[str]) -> None:
        """根据 ID 删除向量。"""
        raise NotImplementedError

    @abstractmethod
    def save(self, collection_name: str) -> None:
        """保存集合索引到磁盘。"""
        raise NotImplementedError

    @abstractmethod
    def load(self, collection_name: str) -> None:
        """从磁盘加载集合索引。"""
        raise NotImplementedError


class FAISSAdapter(VectorDB):
    """基于 faiss-cpu 的向量数据库适配器。

    每个 collection 对应一个 faiss 索引 + 一个元数据 JSON 文件。
    使用 L2 距离（平方欧氏距离）进行相似性度量。
    由于 IndexFlatL2 不支持原生删除，在内存中保留原始向量副本以便重建索引。
    """

    def __init__(
        self,
        store_path: str,
        dimension: int = DEFAULT_DIMENSION,
    ) -> None:
        if not _FAISS_AVAILABLE:
            raise ImportError(
                "faiss 未安装，请运行 `pip install faiss-cpu` 后重试。"
            )
        if not _NUMPY_AVAILABLE:
            raise ImportError(
                "numpy 未安装，请运行 `pip install numpy` 后重试。"
            )
        super().__init__(store_path, dimension)
        # collection_name -> {"index": faiss.Index, "ids": List[str],
        #                     "metadatas": List[Dict], "vectors": List[List[float]]}
        self._collections: Dict[str, Dict[str, Any]] = {}

    def create_collection(self, collection_name: str) -> None:
        """创建一个空的 FAISS 索引集合。"""
        if collection_name in self._collections:
            logger.debug(f"FAISS 集合已存在: {collection_name}")
            return

        # 使用 IndexFlatL2：精确搜索，L2 距离，适合中小规模数据
        index = faiss.IndexFlatL2(self.dimension)
        self._collections[collection_name] = {
            "index": index,
            "ids": [],
            "metadatas": [],
            "vectors": [],
        }
        logger.info(f"FAISS 集合已创建: {collection_name} (dim={self.dimension})")

    def add_vectors(
        self,
        collection_name: str,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """向集合添加向量。"""
        if collection_name not in self._collections:
            self.create_collection(collection_name)

        if len(ids) != len(vectors):
            raise ValueError("ids 与 vectors 数量不一致")

        if metadatas is None:
            metadatas = [{} for _ in ids]
        elif len(metadatas) != len(ids):
            raise ValueError("metadatas 与 ids 数量不一致")

        collection = self._collections[collection_name]
        np_vectors = np.array(vectors, dtype=np.float32)
        # 维度校验
        if np_vectors.shape[1] != self.dimension:
            raise ValueError(
                f"向量维度不匹配: 期望 {self.dimension}, 实际 {np_vectors.shape[1]}"
            )

        collection["index"].add(np_vectors)
        collection["ids"].extend(ids)
        collection["metadatas"].extend(metadatas)
        collection["vectors"].extend(vectors)
        logger.info(
            f"FAISS 添加向量: collection={collection_name} count={len(ids)}"
        )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """相似性搜索，返回 top_k 结果。"""
        if collection_name not in self._collections:
            logger.warning(f"FAISS 集合不存在: {collection_name}")
            return []

        collection = self._collections[collection_name]
        index = collection["index"]
        if index.ntotal == 0:
            return []

        # 限制 top_k 不超过已有向量数
        k = min(top_k, index.ntotal)
        query = np.array([query_vector], dtype=np.float32)
        distances, indices = index.search(query, k)

        results: List[Dict[str, Any]] = []
        ids = collection["ids"]
        metadatas = collection["metadatas"]
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            results.append({
                "id": ids[idx],
                "score": float(dist),
                "metadata": metadatas[idx],
                "rank": rank,
            })
        return results

    def delete_vectors(self, collection_name: str, ids: List[str]) -> None:
        """删除向量。FAISS IndexFlatL2 不支持原生删除，采用重建索引方式。"""
        if collection_name not in self._collections:
            logger.warning(f"FAISS 集合不存在: {collection_name}")
            return

        collection = self._collections[collection_name]
        existing_ids: List[str] = collection["ids"]
        existing_metas: List[Dict[str, Any]] = collection["metadatas"]
        existing_vectors: List[List[float]] = collection["vectors"]

        id_set = set(ids)
        keep_positions = [
            i for i, cid in enumerate(existing_ids) if cid not in id_set
        ]
        if len(keep_positions) == len(existing_ids):
            logger.debug(f"FAISS 未找到要删除的向量: {collection_name}")
            return

        # 基于保留的向量重建索引
        new_index = faiss.IndexFlatL2(self.dimension)
        if keep_positions:
            kept_vectors = np.array(
                [existing_vectors[i] for i in keep_positions],
                dtype=np.float32,
            )
            new_index.add(kept_vectors)
            collection["ids"] = [existing_ids[i] for i in keep_positions]
            collection["metadatas"] = [existing_metas[i] for i in keep_positions]
            collection["vectors"] = [existing_vectors[i] for i in keep_positions]
        else:
            collection["ids"] = []
            collection["metadatas"] = []
            collection["vectors"] = []

        collection["index"] = new_index
        logger.info(
            f"FAISS 删除向量: collection={collection_name} "
            f"deleted={len(ids)} remaining={len(collection['ids'])}"
        )

    def save(self, collection_name: str) -> None:
        """保存集合索引和元数据到磁盘。"""
        if collection_name not in self._collections:
            raise KeyError(f"FAISS 集合不存在: {collection_name}")

        collection = self._collections[collection_name]
        index_path = os.path.join(self.store_path, f"{collection_name}.index")
        meta_path = os.path.join(self.store_path, f"{collection_name}.meta.json")

        faiss.write_index(collection["index"], index_path)
        meta_payload = {
            "dimension": self.dimension,
            "ids": collection["ids"],
            "metadatas": collection["metadatas"],
            "vectors": collection["vectors"],
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_payload, f, ensure_ascii=False)

        logger.info(f"FAISS 集合已保存: {collection_name} -> {index_path}")

    def load(self, collection_name: str) -> None:
        """从磁盘加载集合索引和元数据。"""
        index_path = os.path.join(self.store_path, f"{collection_name}.index")
        meta_path = os.path.join(self.store_path, f"{collection_name}.meta.json")

        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            logger.warning(
                f"FAISS 集合文件不存在，将创建空集合: {collection_name}"
            )
            self.create_collection(collection_name)
            return

        index = faiss.read_index(index_path)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_payload = json.load(f)

        self._collections[collection_name] = {
            "index": index,
            "ids": meta_payload.get("ids", []),
            "metadatas": meta_payload.get("metadatas", []),
            "vectors": meta_payload.get("vectors", []),
        }
        logger.info(f"FAISS 集合已加载: {collection_name} <- {index_path}")


class ChromaAdapter(VectorDB):
    """基于 chromadb 的向量数据库适配器。"""

    def __init__(
        self,
        store_path: str,
        dimension: int = DEFAULT_DIMENSION,
    ) -> None:
        if not _CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb 未安装，请运行 `pip install chromadb` 后重试。"
            )
        super().__init__(store_path, dimension)
        # 持久化客户端：数据落盘到 store_path
        self._client = chromadb.PersistentClient(
            path=store_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # collection_name -> chromadb.Collection
        self._collections: Dict[str, Any] = {}

    def create_collection(self, collection_name: str) -> None:
        """创建集合（如已存在则获取引用）。"""
        if collection_name in self._collections:
            logger.debug(f"Chroma 集合已存在: {collection_name}")
            return

        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"dimension": self.dimension},
        )
        self._collections[collection_name] = collection
        logger.info(f"Chroma 集合已创建: {collection_name}")

    def add_vectors(
        self,
        collection_name: str,
        ids: List[str],
        vectors: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """向集合添加向量。"""
        if collection_name not in self._collections:
            self.create_collection(collection_name)

        if len(ids) != len(vectors):
            raise ValueError("ids 与 vectors 数量不一致")

        if metadatas is None:
            metadatas = [{} for _ in ids]
        elif len(metadatas) != len(ids):
            raise ValueError("metadatas 与 ids 数量不一致")

        # Chroma 要求 metadata 值为基本类型，确保非空
        safe_metas = [
            meta if meta else {"_placeholder": True} for meta in metadatas
        ]

        collection = self._collections[collection_name]
        collection.add(
            ids=ids,
            embeddings=vectors,
            metadatas=safe_metas,
        )
        logger.info(
            f"Chroma 添加向量: collection={collection_name} count={len(ids)}"
        )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """相似性搜索，返回 top_k 结果。"""
        if collection_name not in self._collections:
            logger.warning(f"Chroma 集合不存在: {collection_name}")
            return []

        collection = self._collections[collection_name]
        if collection.count() == 0:
            return []

        result = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
        )

        results: List[Dict[str, Any]] = []
        ids_list = result.get("ids", [[]])
        dists_list = result.get("distances", [[]])
        metas_list = result.get("metadatas", [[]])

        for rank, (cid, dist, meta) in enumerate(
            zip(ids_list[0], dists_list[0], metas_list[0])
        ):
            # 移除占位 metadata
            clean_meta = {
                k: v for k, v in (meta or {}).items() if k != "_placeholder"
            }
            results.append({
                "id": cid,
                "score": float(dist),
                "metadata": clean_meta,
                "rank": rank,
            })
        return results

    def delete_vectors(self, collection_name: str, ids: List[str]) -> None:
        """根据 ID 删除向量。"""
        if collection_name not in self._collections:
            logger.warning(f"Chroma 集合不存在: {collection_name}")
            return

        collection = self._collections[collection_name]
        collection.delete(ids=ids)
        logger.info(
            f"Chroma 删除向量: collection={collection_name} count={len(ids)}"
        )

    def save(self, collection_name: str) -> None:
        """保存集合。Chroma PersistentClient 自动持久化，此处仅记录日志。"""
        if collection_name not in self._collections:
            raise KeyError(f"Chroma 集合不存在: {collection_name}")
        # PersistentClient 自动落盘，无需显式保存
        logger.info(f"Chroma 集合已持久化: {collection_name}")

    def load(self, collection_name: str) -> None:
        """加载集合。PersistentClient 启动时已加载，此处获取引用。"""
        if collection_name in self._collections:
            return
        try:
            collection = self._client.get_collection(name=collection_name)
            self._collections[collection_name] = collection
            logger.info(f"Chroma 集合已加载: {collection_name}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Chroma 集合加载失败，将创建: {collection_name} ({e})")
            self.create_collection(collection_name)


class VectorDBFactory:
    """向量数据库工厂类，根据配置创建适配器实例。"""

    @staticmethod
    def create(
        db_type: Optional[str] = None,
        store_path: Optional[str] = None,
        dimension: int = DEFAULT_DIMENSION,
    ) -> VectorDB:
        """创建向量数据库适配器。

        Args:
            db_type: 数据库类型 ("faiss" 或 "chroma")，默认从 settings.VECTOR_DB_TYPE 读取。
            store_path: 存储路径，默认从 settings.VECTOR_STORE_PATH 读取。
            dimension: 向量维度，默认 1536。

        Returns:
            VectorDB 实例。

        Raises:
            ValueError: 不支持的数据库类型。
            ImportError: 对应依赖未安装。
        """
        db_type = (db_type or settings.VECTOR_DB_TYPE).lower()
        store_path = store_path or settings.VECTOR_STORE_PATH

        if db_type == "faiss":
            logger.info(f"创建 FAISS 适配器: path={store_path} dim={dimension}")
            return FAISSAdapter(store_path=store_path, dimension=dimension)
        elif db_type == "chroma":
            logger.info(f"创建 Chroma 适配器: path={store_path} dim={dimension}")
            return ChromaAdapter(store_path=store_path, dimension=dimension)
        else:
            raise ValueError(
                f"不支持的向量数据库类型: {db_type} (仅支持 'faiss' / 'chroma')"
            )

    @staticmethod
    def available_backends() -> List[str]:
        """返回当前可用的后端列表。"""
        backends: List[str] = []
        if _FAISS_AVAILABLE and _NUMPY_AVAILABLE:
            backends.append("faiss")
        if _CHROMA_AVAILABLE:
            backends.append("chroma")
        return backends


def get_vector_db(
    collection_name: str,
    dimension: int = DEFAULT_DIMENSION,
) -> VectorDB:
    """便捷函数：创建适配器并确保指定集合存在。

    Args:
        collection_name: 集合名称（应在 SUPPORTED_COLLECTIONS 中）。
        dimension: 向量维度。

    Returns:
        已创建/加载指定集合的 VectorDB 实例。
    """
    if collection_name not in SUPPORTED_COLLECTIONS:
        logger.warning(
            f"集合名 '{collection_name}' 不在支持列表中: {SUPPORTED_COLLECTIONS}"
        )

    db = VectorDBFactory.create(dimension=dimension)
    db.create_collection(collection_name)
    return db

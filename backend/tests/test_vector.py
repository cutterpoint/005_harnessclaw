"""向量数据库模块单元测试。

由于 faiss / chromadb / numpy 可能在环境中未安装，
相关测试用例使用 pytest.importorskip / skipif 进行容错跳过。
测试使用临时目录隔离，确保可重复运行。
"""
import os
import shutil
import tempfile
from typing import Generator, List

import pytest

from src.vector.db import (
    DEFAULT_DIMENSION,
    SUPPORTED_COLLECTIONS,
    VectorDB,
    VectorDBFactory,
)


# ---------------------------------------------------------------------------
# 辅助函数（需在装饰器使用前定义）
# ---------------------------------------------------------------------------

def _importable(module_name: str) -> bool:
    """判断模块是否可导入，用于 skipif 条件。"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


def _make_vectors(count: int, dim: int = DEFAULT_DIMENSION) -> List[List[float]]:
    """生成 count 个 dim 维的确定性向量。"""
    vectors = []
    for i in range(count):
        # 每个向量由不同基址构成，保证彼此可区分
        vectors.append([float((i + j) % 7) * 0.1 for j in range(dim)])
    return vectors


# ---------------------------------------------------------------------------
# 公共夹具
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_store_path() -> Generator[str, None, None]:
    """提供临时向量存储目录，测试结束后清理。"""
    tmp_dir = tempfile.mkdtemp(prefix="vector_test_")
    try:
        yield tmp_dir
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 抽象基类与配置
# ---------------------------------------------------------------------------

class TestVectorDBAbstract:
    """测试抽象基类与常量定义。"""

    def test_vector_db_is_abstract(self) -> None:
        """VectorDB 应为抽象基类，不能直接实例化。"""
        with pytest.raises(TypeError):
            VectorDB(store_path="/tmp/should_not_exist", dimension=8)  # type: ignore[abstract]

    def test_supported_collections(self) -> None:
        """支持的集合应包含设计文档要求的三类。"""
        assert "conversation_memory" in SUPPORTED_COLLECTIONS
        assert "skill_knowledge" in SUPPORTED_COLLECTIONS
        assert "document_embeddings" in SUPPORTED_COLLECTIONS

    def test_default_dimension(self) -> None:
        """默认向量维度应为 1536。"""
        assert DEFAULT_DIMENSION == 1536


# ---------------------------------------------------------------------------
# 工厂模式
# ---------------------------------------------------------------------------

class TestFactory:
    """测试 VectorDBFactory 工厂类。"""

    def test_factory_create_faiss(self, temp_store_path: str) -> None:
        """工厂应能根据 db_type='faiss' 创建 FAISSAdapter。"""
        pytest.importorskip("faiss")
        pytest.importorskip("numpy")
        from src.vector.db import FAISSAdapter
        db = VectorDBFactory.create(
            db_type="faiss", store_path=temp_store_path, dimension=8
        )
        assert isinstance(db, FAISSAdapter)
        assert db.dimension == 8
        assert db.store_path == temp_store_path

    def test_factory_create_chroma(self, temp_store_path: str) -> None:
        """工厂应能根据 db_type='chroma' 创建 ChromaAdapter。"""
        pytest.importorskip("chromadb")
        from src.vector.db import ChromaAdapter
        db = VectorDBFactory.create(
            db_type="chroma", store_path=temp_store_path, dimension=8
        )
        assert isinstance(db, ChromaAdapter)
        assert db.dimension == 8

    def test_factory_invalid_type(self, temp_store_path: str) -> None:
        """不支持的数据库类型应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不支持的向量数据库类型"):
            VectorDBFactory.create(
                db_type="redis", store_path=temp_store_path
            )

    def test_factory_available_backends(self) -> None:
        """available_backends 应返回当前可用后端列表。"""
        backends = VectorDBFactory.available_backends()
        assert isinstance(backends, list)
        # 验证返回的后端确实可导入
        for backend in backends:
            if backend == "faiss":
                assert _importable("faiss") and _importable("numpy")
            elif backend == "chroma":
                assert _importable("chromadb")


# ---------------------------------------------------------------------------
# FAISS 适配器测试
# ---------------------------------------------------------------------------

_FAISS_AVAILABLE = _importable("faiss") and _importable("numpy")


@pytest.mark.skipif(
    not _FAISS_AVAILABLE,
    reason="faiss 或 numpy 未安装，跳过 FAISS 相关测试",
)
class TestFAISSAdapter:
    """FAISS 适配器功能测试。"""

    def _make_adapter(self, store_path: str, dim: int = 8) -> "FAISSAdapter":
        from src.vector.db import FAISSAdapter
        return FAISSAdapter(store_path=store_path, dimension=dim)

    def test_create_collection(self, temp_store_path: str) -> None:
        """创建集合后应能通过集合名校验。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        # 重复创建不应报错
        db.create_collection("conversation_memory")
        assert "conversation_memory" in db._collections

    def test_add_vectors(self, temp_store_path: str) -> None:
        """添加向量后索引应包含对应数量。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("skill_knowledge")
        ids = ["v1", "v2", "v3"]
        vectors = _make_vectors(3, dim=8)
        db.add_vectors("skill_knowledge", ids, vectors)
        assert db._collections["skill_knowledge"]["index"].ntotal == 3
        assert db._collections["skill_knowledge"]["ids"] == ids

    def test_add_vectors_dimension_mismatch(self, temp_store_path: str) -> None:
        """向量维度不匹配应抛出 ValueError。"""
        db = self._make_adapter(temp_store_path, dim=8)
        db.create_collection("document_embeddings")
        with pytest.raises(ValueError, match="向量维度不匹配"):
            db.add_vectors(
                "document_embeddings",
                ["v1"],
                [[0.1] * 4],  # 维度错误
            )

    def test_search(self, temp_store_path: str) -> None:
        """相似性搜索应返回 top_k 结果，且自身查询排在最前。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        ids = ["a", "b", "c"]
        vectors = _make_vectors(3, dim=8)
        db.add_vectors("conversation_memory", ids, vectors)
        # 用第一个向量作为查询，应返回自身且 score 最小(L2 距离为 0)
        results = db.search("conversation_memory", vectors[0], top_k=3)
        assert len(results) == 3
        assert results[0]["id"] == "a"
        assert results[0]["score"] == pytest.approx(0.0, abs=1e-6)

    def test_search_empty_collection(self, temp_store_path: str) -> None:
        """空集合搜索应返回空列表。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        results = db.search("conversation_memory", [0.0] * 8, top_k=5)
        assert results == []

    def test_search_nonexistent_collection(self, temp_store_path: str) -> None:
        """搜索不存在的集合应返回空列表而非报错。"""
        db = self._make_adapter(temp_store_path)
        results = db.search("not_exist", [0.0] * 8, top_k=5)
        assert results == []

    def test_delete_vectors(self, temp_store_path: str) -> None:
        """删除向量后索引应相应减少。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        ids = ["a", "b", "c"]
        vectors = _make_vectors(3, dim=8)
        db.add_vectors("conversation_memory", ids, vectors)

        db.delete_vectors("conversation_memory", ["b"])
        assert db._collections["conversation_memory"]["index"].ntotal == 2
        assert "b" not in db._collections["conversation_memory"]["ids"]

        # 删除后搜索不应再返回已删除的 id
        results = db.search("conversation_memory", vectors[1], top_k=5)
        result_ids = [r["id"] for r in results]
        assert "b" not in result_ids

    def test_delete_all_vectors(self, temp_store_path: str) -> None:
        """删除全部向量后索引应为空。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        ids = ["a", "b"]
        vectors = _make_vectors(2, dim=8)
        db.add_vectors("conversation_memory", ids, vectors)
        db.delete_vectors("conversation_memory", ["a", "b"])
        assert db._collections["conversation_memory"]["index"].ntotal == 0

    def test_save_load(self, temp_store_path: str) -> None:
        """保存后重新加载应恢复向量与元数据。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("skill_knowledge")
        ids = ["x1", "x2"]
        vectors = _make_vectors(2, dim=8)
        metadatas = [{"source": "doc1"}, {"source": "doc2"}]
        db.add_vectors("skill_knowledge", ids, vectors, metadatas)
        db.save("skill_knowledge")

        # 索引文件应已生成
        assert os.path.exists(
            os.path.join(temp_store_path, "skill_knowledge.index")
        )
        assert os.path.exists(
            os.path.join(temp_store_path, "skill_knowledge.meta.json")
        )

        # 新建适配器加载
        db2 = self._make_adapter(temp_store_path)
        db2.load("skill_knowledge")
        assert db2._collections["skill_knowledge"]["index"].ntotal == 2
        assert db2._collections["skill_knowledge"]["ids"] == ["x1", "x2"]
        assert db2._collections["skill_knowledge"]["metadatas"] == metadatas

        # 加载后搜索应正常工作
        results = db2.search("skill_knowledge", vectors[0], top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "x1"

    def test_load_nonexistent(self, temp_store_path: str) -> None:
        """加载不存在的集合文件应创建空集合而非报错。"""
        db = self._make_adapter(temp_store_path)
        db.load("conversation_memory")
        assert "conversation_memory" in db._collections
        assert db._collections["conversation_memory"]["index"].ntotal == 0


# ---------------------------------------------------------------------------
# Chroma 适配器测试
# ---------------------------------------------------------------------------

_CHROMA_AVAILABLE = _importable("chromadb")


@pytest.mark.skipif(
    not _CHROMA_AVAILABLE,
    reason="chromadb 未安装，跳过 Chroma 相关测试",
)
class TestChromaAdapter:
    """Chroma 适配器功能测试。"""

    def _make_adapter(self, store_path: str, dim: int = 8) -> "ChromaAdapter":
        from src.vector.db import ChromaAdapter
        return ChromaAdapter(store_path=store_path, dimension=dim)

    def test_create_collection(self, temp_store_path: str) -> None:
        """创建集合后应能通过集合名校验。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        db.create_collection("conversation_memory")  # 重复创建不报错
        assert "conversation_memory" in db._collections

    def test_add_vectors(self, temp_store_path: str) -> None:
        """添加向量后集合计数应正确。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("skill_knowledge")
        ids = ["v1", "v2", "v3"]
        vectors = _make_vectors(3, dim=8)
        db.add_vectors("skill_knowledge", ids, vectors)
        assert db._collections["skill_knowledge"].count() == 3

    def test_search(self, temp_store_path: str) -> None:
        """相似性搜索应返回 top_k 结果。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        ids = ["a", "b", "c"]
        vectors = _make_vectors(3, dim=8)
        db.add_vectors("conversation_memory", ids, vectors)
        results = db.search("conversation_memory", vectors[0], top_k=2)
        assert len(results) == 2
        # 自身查询应排第一
        assert results[0]["id"] == "a"

    def test_delete_vectors(self, temp_store_path: str) -> None:
        """删除向量后集合计数应相应减少。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("conversation_memory")
        ids = ["a", "b", "c"]
        vectors = _make_vectors(3, dim=8)
        db.add_vectors("conversation_memory", ids, vectors)
        db.delete_vectors("conversation_memory", ["b"])
        assert db._collections["conversation_memory"].count() == 2
        # 搜索结果不应包含已删除 id
        results = db.search("conversation_memory", vectors[1], top_k=5)
        result_ids = [r["id"] for r in results]
        assert "b" not in result_ids

    def test_save_load(self, temp_store_path: str) -> None:
        """Chroma 持久化后重新打开应能加载集合。"""
        db = self._make_adapter(temp_store_path)
        db.create_collection("skill_knowledge")
        ids = ["x1", "x2"]
        vectors = _make_vectors(2, dim=8)
        db.add_vectors("skill_knowledge", ids, vectors)
        db.save("skill_knowledge")

        # 新建适配器（指向同一持久化路径）加载集合
        db2 = self._make_adapter(temp_store_path)
        db2.load("skill_knowledge")
        assert db2._collections["skill_knowledge"].count() == 2

        results = db2.search("skill_knowledge", vectors[0], top_k=2)
        assert len(results) == 2

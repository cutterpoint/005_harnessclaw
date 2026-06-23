"""记忆系统模块单元测试。

短期记忆使用内存 SQLite，长期记忆使用临时目录的 FAISS 向量库。
测试结束后自动清理临时文件，确保可重复运行。
"""
import os
import shutil
import tempfile
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import models  # noqa: F401 确保模型被注册到 Base.metadata
from src.db.database import Base
from src.memory import LongTermMemory, MemorySystem, ShortTermMemory
from src.vector.db import FAISSAdapter, VectorDB

# 测试用向量维度（小维度以提升性能）
TEST_DIMENSION = 8


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _importable(module_name: str) -> bool:
    """判断模块是否可导入，用于 skipif 条件。"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


_FAISS_AVAILABLE = _importable("faiss") and _importable("numpy")


# ---------------------------------------------------------------------------
# 公共夹具
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """创建内存 SQLite 数据库会话，每个测试函数独立隔离。"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def temp_store_path() -> Generator[str, None, None]:
    """提供临时向量存储目录，测试结束后清理。"""
    tmp_dir = tempfile.mkdtemp(prefix="memory_test_")
    try:
        yield tmp_dir
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def vector_db(temp_store_path: str) -> "FAISSAdapter":
    """创建测试用 FAISS 向量数据库实例。"""
    db = FAISSAdapter(store_path=temp_store_path, dimension=TEST_DIMENSION)
    db.create_collection("conversation_memory")
    return db


# ---------------------------------------------------------------------------
# 短期记忆测试
# ---------------------------------------------------------------------------

class TestShortTermMemory:
    """短期记忆功能测试。"""

    def test_short_term_add_and_get(self, db_session):
        """测试添加和获取短期记忆。"""
        memory = ShortTermMemory(db_session)

        # 添加消息
        memory.add(session_id=1, role="user", content="你好，世界")
        memory.add(session_id=1, role="assistant", content="你好！有什么可以帮你的？")

        # 获取全部消息
        all_messages = memory.get_all(session_id=1)
        assert len(all_messages) == 2

        # 验证字段
        assert all_messages[0]["role"] == "user"
        assert all_messages[0]["content"] == "你好，世界"
        assert all_messages[0]["session_id"] == 1
        assert all_messages[0]["id"] is not None
        assert all_messages[0]["created_at"] is not None

        assert all_messages[1]["role"] == "assistant"
        assert all_messages[1]["content"] == "你好！有什么可以帮你的？"

    def test_short_term_get_recent(self, db_session):
        """测试获取最近消息。"""
        memory = ShortTermMemory(db_session)

        # 添加 5 条消息
        for i in range(5):
            memory.add(session_id=1, role="user", content=f"消息{i}")

        # 获取最近 3 条
        recent = memory.get_recent(session_id=1, limit=3)
        assert len(recent) == 3
        # 应返回最后 3 条（消息2、消息3、消息4），按时间正序排列
        assert recent[0]["content"] == "消息2"
        assert recent[1]["content"] == "消息3"
        assert recent[2]["content"] == "消息4"

        # 获取超过总量的消息应返回全部
        all_recent = memory.get_recent(session_id=1, limit=100)
        assert len(all_recent) == 5

        # 不同会话隔离
        memory.add(session_id=2, role="user", content="另一个会话")
        assert len(memory.get_recent(session_id=1, limit=100)) == 5
        assert len(memory.get_recent(session_id=2, limit=100)) == 1

    def test_short_term_search(self, db_session):
        """测试关键词搜索消息。"""
        memory = ShortTermMemory(db_session)

        memory.add(session_id=1, role="user", content="Python 是一门编程语言")
        memory.add(session_id=1, role="assistant", content="是的，Python 很流行")
        memory.add(session_id=1, role="user", content="Java 也是编程语言")

        # 搜索包含 "Python" 的消息
        results = memory.search(session_id=1, keyword="Python")
        assert len(results) == 2
        contents = [r["content"] for r in results]
        assert "Python 是一门编程语言" in contents
        assert "是的，Python 很流行" in contents

        # 搜索不存在的关键词
        empty = memory.search(session_id=1, keyword="不存在的内容")
        assert len(empty) == 0

        # 搜索 "编程语言"
        results2 = memory.search(session_id=1, keyword="编程语言")
        assert len(results2) == 2

    def test_short_term_clear(self, db_session):
        """测试清除会话消息。"""
        memory = ShortTermMemory(db_session)

        # 添加消息到两个会话
        memory.add(session_id=1, role="user", content="会话1消息1")
        memory.add(session_id=1, role="user", content="会话1消息2")
        memory.add(session_id=2, role="user", content="会话2消息1")

        # 清除会话 1
        memory.clear(session_id=1)

        # 会话 1 应为空
        assert len(memory.get_all(session_id=1)) == 0
        # 会话 2 不受影响
        assert len(memory.get_all(session_id=2)) == 1


# ---------------------------------------------------------------------------
# 长期记忆测试（依赖 faiss）
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _FAISS_AVAILABLE,
    reason="faiss 或 numpy 未安装，跳过长期记忆相关测试",
)
class TestLongTermMemory:
    """长期记忆功能测试。"""

    def test_long_term_add_and_search(self, vector_db):
        """测试添加和搜索长期记忆。"""
        memory = LongTermMemory(vector_db)

        # 添加记忆
        memory_id = memory.add(
            content="Python 是一门解释型编程语言",
            metadata={"topic": "编程", "role": "assistant"},
        )
        assert memory_id is not None
        assert isinstance(memory_id, str)

        # 用相同内容搜索，应返回该记忆且 score 最优
        results = memory.search(query="Python 是一门解释型编程语言", limit=5)
        assert len(results) >= 1

        # 验证返回的记忆项
        item = results[0]
        assert item.id == memory_id
        assert item.content == "Python 是一门解释型编程语言"
        assert item.metadata.get("topic") == "编程"
        assert item.score is not None

        # 用不同内容搜索也应能返回结果
        results2 = memory.search(query="Java 编程", limit=5)
        assert len(results2) >= 1

    def test_long_term_delete(self, vector_db):
        """测试删除长期记忆。"""
        memory = LongTermMemory(vector_db)

        # 添加多条记忆
        id1 = memory.add(content="记忆内容一", metadata={"index": 1})
        id2 = memory.add(content="记忆内容二", metadata={"index": 2})
        id3 = memory.add(content="记忆内容三", metadata={"index": 3})

        # 搜索应返回全部
        results = memory.search(query="记忆内容", limit=10)
        assert len(results) == 3

        # 删除 id2
        memory.delete([id2])

        # 搜索应返回 2 条，且不包含 id2
        results_after = memory.search(query="记忆内容", limit=10)
        assert len(results_after) == 2
        remaining_ids = [r.id for r in results_after]
        assert id1 in remaining_ids
        assert id3 in remaining_ids
        assert id2 not in remaining_ids

        # 删除全部
        memory.delete([id1, id3])
        results_empty = memory.search(query="记忆内容", limit=10)
        assert len(results_empty) == 0


# ---------------------------------------------------------------------------
# 记忆系统测试（依赖 faiss）
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not _FAISS_AVAILABLE,
    reason="faiss 或 numpy 未安装，跳过记忆系统相关测试",
)
class TestMemorySystem:
    """记忆系统整合测试。"""

    def test_memory_system_add(self, db_session, vector_db):
        """测试记忆系统添加（同时写入短期和长期）。"""
        system = MemorySystem(db_session, vector_db)

        # 添加记忆
        system.add(
            session_id=1,
            role="user",
            content="如何学习 Python？",
        )
        system.add(
            session_id=1,
            role="assistant",
            content="建议从基础语法开始学习 Python。",
        )

        # 短期记忆应有 2 条
        recent = system.get_recent(session_id=1, limit=10)
        assert len(recent) == 2
        assert recent[0]["content"] == "如何学习 Python？"
        assert recent[1]["content"] == "建议从基础语法开始学习 Python。"

        # 长期记忆也应能搜索到
        long_results = system.search_long_term(query="如何学习 Python？", limit=5)
        assert len(long_results) >= 1
        assert any(r.content == "如何学习 Python？" for r in long_results)

    def test_memory_system_retrieve(self, db_session, vector_db):
        """测试记忆系统检索（短期+长期融合）。"""
        system = MemorySystem(db_session, vector_db)

        # 添加多条记忆
        system.add(session_id=1, role="user", content="Python 编程入门")
        system.add(session_id=1, role="assistant", content="Python 是一门易学的语言")
        system.add(session_id=1, role="user", content="Java 编程指南")

        # 检索包含 "Python" 的记忆
        results = system.retrieve(
            query="Python",
            session_id=1,
            limit=5,
        )

        # 应同时包含短期和长期结果
        assert len(results) > 0
        sources = [r["source"] for r in results]
        assert "short_term" in sources
        assert "long_term" in sources

        # 短期记忆结果应包含 content 字段
        short_items = [r for r in results if r["source"] == "short_term"]
        for item in short_items:
            assert "content" in item
            assert "Python" in item["content"]

        # 长期记忆结果应包含 id、content、score 字段
        long_items = [r for r in results if r["source"] == "long_term"]
        for item in long_items:
            assert "id" in item
            assert "content" in item
            assert "score" in item

        # 不提供 session_id 时仅返回长期记忆
        results_no_session = system.retrieve(query="Python", limit=5)
        sources_no_session = [r["source"] for r in results_no_session]
        assert "long_term" in sources_no_session
        assert "short_term" not in sources_no_session

    def test_memory_system_clear_session(self, db_session, vector_db):
        """测试清除会话短期记忆（长期记忆不受影响）。"""
        system = MemorySystem(db_session, vector_db)

        # 添加记忆
        system.add(session_id=1, role="user", content="测试消息一")
        system.add(session_id=1, role="user", content="测试消息二")

        # 确认短期和长期都有数据
        assert len(system.get_recent(session_id=1, limit=10)) == 2
        assert len(system.search_long_term(query="测试消息", limit=10)) >= 2

        # 清除会话短期记忆
        system.clear_session(session_id=1)

        # 短期记忆应为空
        assert len(system.get_recent(session_id=1, limit=10)) == 0

        # 长期记忆应不受影响
        long_results = system.search_long_term(query="测试消息", limit=10)
        assert len(long_results) >= 2

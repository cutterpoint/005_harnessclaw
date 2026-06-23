"""数据库模型定义，对应系统设计文档中的所有表结构。"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
)
from sqlalchemy.sql import func
from src.db.database import Base


class User(Base):
    """用户表 - 存储用户账户信息。"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Session(Base):
    """会话表 - 管理用户对话会话。"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_key = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(100))
    status = Column(String(20), default="active")  # active/archived/deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Message(Base):
    """消息表 - 存储对话消息记录。"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # system/user/assistant/tool
    content = Column(Text, nullable=False)
    tool_call = Column(Text)  # JSON 格式的工具调用信息
    tool_call_id = Column(String(100))  # 工具调用ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Skill(Base):
    """技能表 - 存储技能定义。"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    prompt = Column(Text)  # 技能提示词模板
    is_enabled = Column(Boolean, default=True)
    training_data = Column(Text)  # JSON 格式的训练数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SkillExecution(Base):
    """技能执行记录表。"""
    __tablename__ = "skill_executions"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    input_data = Column(Text)  # JSON 输入
    output_data = Column(Text)  # JSON 输出
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    execution_time = Column(Float)  # 执行时间(秒)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Tool(Base):
    """工具表 - 存储工具定义。"""
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    function_name = Column(String(100), nullable=False)
    module_path = Column(String(255), nullable=False)
    parameters = Column(Text, nullable=False)  # JSON 参数定义
    return_type = Column(String(50))
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ToolExecution(Base):
    """工具执行记录表。"""
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    arguments = Column(Text)  # JSON 调用参数
    result = Column(Text)  # JSON 执行结果
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    execution_time = Column(Float)  # 执行时间(秒)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Workflow(Base):
    """工作流表 - 存储工作流定义。"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    definition = Column(Text, nullable=False)  # JSON 工作流定义
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class WorkflowExecution(Base):
    """工作流执行记录表。"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    inputs = Column(Text)  # JSON 输入参数
    outputs = Column(Text)  # JSON 输出结果
    status = Column(String(20), nullable=False)  # pending/running/completed/failed
    error = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class LLMConfig(Base):
    """LLM配置表 - 存储大模型API配置。"""
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    api_key = Column(String(255), nullable=False)
    api_base = Column(String(255), nullable=False)
    model_name = Column(String(100), nullable=False)
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.7)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemLog(Base):
    """系统操作日志表 - 记录用户操作和系统事件。"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    log_type = Column(String(50), nullable=False)  # operation/event/error
    module = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)  # JSON 详细信息
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ExternalLog(Base):
    """外部交互日志表 - 记录外部API调用和工具执行。"""
    __tablename__ = "external_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    service_name = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    request_url = Column(String(500))
    request_method = Column(String(10))
    request_body = Column(Text)
    response_status = Column(Integer)
    response_body = Column(Text)
    latency_ms = Column(Integer)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class LLMLog(Base):
    """LLM交互日志表 - 记录大模型调用和Token消耗。"""
    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    model_name = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    request_messages = Column(Text, nullable=False)  # JSON 请求消息
    response_content = Column(Text)
    tool_calls = Column(Text)  # JSON 工具调用
    latency_ms = Column(Integer)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    cost_usd = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

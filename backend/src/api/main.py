"""FastAPI 应用入口 - 注册所有路由并初始化数据库。"""
from fastapi import FastAPI

from src.api.routes import (
    agent,
    auth,
    llm,
    logs,
    sessions,
    skills,
    tools,
    workflows,
)
from src.db.database import init_db
from src.ws.server import router as ws_router

app = FastAPI(title="HarnessClaw API", version="1.0.0")

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(
    sessions.router, prefix="/api/v1/sessions", tags=["sessions"]
)
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["skills"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(
    workflows.router, prefix="/api/v1/workflows", tags=["workflows"]
)
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["logs"])
app.include_router(ws_router, tags=["websocket"])


@app.on_event("startup")
def startup() -> None:
    """应用启动时初始化数据库。"""
    init_db()


@app.get("/")
def root() -> dict:
    """根路径健康检查。"""
    return {
        "code": 0,
        "message": "success",
        "data": {"service": "HarnessClaw API", "version": "1.0.0"},
    }

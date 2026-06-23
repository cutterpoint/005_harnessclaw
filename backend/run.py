"""HarnessClaw 后端服务启动入口。"""
import uvicorn
from src.core.config import settings


def main() -> None:
    """启动 FastAPI 服务。"""
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()

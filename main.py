import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response
from app.core.config import settings
from app.core.middleware import TimingMiddleware, LoggingMiddleware, setup_cors_middleware
from app.core.exception import setup_exception_handlers
from app.db.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.agent import router as agent_router
from app.api.app import router as app_router
# 导入模型，确保 SQLAlchemy 能识别并创建表
from app.models import User  # noqa: F401

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时执行
    logger.info("Starting application...")
    try:
        # 初始化数据库（可选，根据需要启用）
        await init_db()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shut down successfully")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="FastAPI application with database and Redis support",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# 设置中间件（注意顺序：后添加的先执行）
app.add_middleware(LoggingMiddleware)
app.add_middleware(TimingMiddleware)
setup_cors_middleware(app)  # CORS 中间件最后添加

# 设置异常处理器
setup_exception_handlers(app)

# 注册路由
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(user_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_router, prefix=settings.API_V1_PREFIX)
app.include_router(app_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Hello World",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
    }


@app.get("/healthz")
async def healthz():
    """
    健康检查接口
    返回服务状态
    """
    return {"status": "ok", "message": "Service is healthy"}


@app.get("/favicon.ico")
async def favicon():
    """
    处理 favicon 请求
    返回 204 No Content，避免 404 错误
    """
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
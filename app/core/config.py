import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "guyi-code-mother"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://guyi:guyi123@localhost:5432/guyi-code-mother"
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # 应用配置
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, production, testing
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS 配置
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # LLM 配置
    DASHSCOPE_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""
    
    # 工作区配置
    WORKSPACE_BASE_PATH: str = ""  # workspace_path 的前缀路径，完整路径为: WORKSPACE_BASE_PATH/user_id_app_id_app_name
    
    def get_workspace_path(self, user_id: str, app_id: str, app_name: str) -> str:
        """
        构建完整的工作区路径
        
        Args:
            user_id: 用户ID
            app_id: 应用ID
            app_name: 应用名称
            
        Returns:
            完整的工作区路径: WORKSPACE_BASE_PATH/user_id_app_id_app_name
        """
        if not self.WORKSPACE_BASE_PATH:
            raise ValueError("WORKSPACE_BASE_PATH 未配置")
        
        # 将三个属性用下划线连接作为目录名
        workspace_dir_name = f"{user_id}_{app_id}_{app_name}"
        
        # 构建完整路径，使用 os.path.join 确保跨平台兼容
        full_path = os.path.join(self.WORKSPACE_BASE_PATH, workspace_dir_name)
        return os.path.normpath(full_path)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # 如果 .env 文件不存在，不会报错，使用默认值


# 创建全局配置实例
settings = Settings()


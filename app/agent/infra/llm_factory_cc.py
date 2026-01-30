"""
Claude SDK LLM 工厂类 - 创建 Claude SDK 客户端配置
"""
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_claude_model_config() -> Dict[str, Any]:
    """
    获取 Claude 模型配置
    
    Returns:
        Claude 模型配置字典，包含：
        - model_name: 模型名称
        - api_base: API Base URL
        - api_key: API Key
    """
    return {
        "model_name": settings.CLAUDE_MODEL,
        "api_base": settings.CLAUDE_API_BASE_URL or None,  # 如果为空则使用默认
        "api_key": settings.CLAUDE_API_KEY,
    }


def validate_claude_config() -> bool:
    """
    验证 Claude 配置是否完整
    
    Returns:
        True 如果配置完整，False 否则
    """
    if not settings.CLAUDE_API_KEY:
        logger.warning("Claude API Key 未配置")
        return False
    
    if not settings.CLAUDE_MODEL:
        logger.warning("Claude Model 未配置")
        return False
    
    return True


"""
Agent Service 工厂类 - 统一创建 Agent Service 实例
支持 LangChain 和 Claude SDK 两种实现
"""
import logging
from typing import Literal, Optional
from app.agent.service.base_agent_service import BaseAgentService
from app.agent.service.agent_service import create_agent_service as create_langchain_agent_service
from app.agent.service.agent_service_cc import create_claude_agent_service
from app.core.config import settings

logger = logging.getLogger(__name__)

# Agent 类型
AgentType = Literal["langchain", "claude"]


def create_agent_service(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str,
    agent_type: Optional[AgentType] = None,
    debug: bool = False
) -> BaseAgentService:
    """
    创建 Agent Service 实例（统一工厂方法）
    
    根据 agent_type 参数选择创建 LangChain 或 Claude SDK Agent Service
    
    Args:
        workspace_path: 工作区路径（所有文件操作都在此目录下进行）
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        agent_type: Agent 类型，"langchain" 或 "claude"，如果为 None 则使用配置中的默认值
        debug: 是否开启调试模式
        
    Returns:
        BaseAgentService 实例（LangChain 或 Claude SDK 实现）
    """
    # 如果没有指定 agent_type，从配置读取默认值
    if agent_type is None:
        agent_type = getattr(settings, "DEFAULT_AGENT_TYPE", "langchain")
    
    # 验证 agent_type
    if agent_type not in ["langchain", "claude"]:
        logger.warning(f"无效的 agent_type: {agent_type}，使用默认值 'langchain'")
        agent_type = "langchain"
    
    # 根据类型创建对应的 Agent Service
    if agent_type == "claude":
        logger.info(f"创建 Claude SDK Agent Service - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
        return create_claude_agent_service(
            workspace_path=workspace_path,
            user_id=user_id,
            app_id=app_id,
            app_name=app_name,
            debug=debug
        )
    else:  # langchain (默认)
        logger.info(f"创建 LangChain Agent Service - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
        return create_langchain_agent_service(
            workspace_path=workspace_path,
            user_id=user_id,
            app_id=app_id,
            app_name=app_name,
            debug=debug
        )


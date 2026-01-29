"""
Agent工厂类 - 统一创建和管理Agent实例
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from langchain.agents import create_agent
from app.agent.infra.llm_factory import get_llm
from app.agent.tools.file_tools import get_file_tools

logger = logging.getLogger(__name__)


def _load_prompt_template(prompt_file: str) -> str:
    """
    加载提示词模板文件
    
    Args:
        prompt_file: 提示词文件路径（相对于 app/agent/prompt 目录）
        
    Returns:
        提示词内容
    """
    prompt_path = Path(__file__).parent.parent / "prompt" / prompt_file
    if not prompt_path.exists():
        raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")
    
    return prompt_path.read_text(encoding='utf-8')


def _build_system_prompt(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str
) -> str:
    """
    构建系统提示词，替换占位符
    
    Args:
        workspace_path: 工作区路径
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        
    Returns:
        完整的系统提示词
    """
    # 加载两个提示词文件
    important_principle = _load_prompt_template("001_important_principle.md")
    main_rule = _load_prompt_template("lc_coder_main_rule.md")
    
    # 替换占位符
    system_prompt = f"{important_principle}\n\n{main_rule}"
    system_prompt = system_prompt.replace("{workspace_path}", workspace_path)
    system_prompt = system_prompt.replace("{user_id}", user_id)
    system_prompt = system_prompt.replace("{app_id}", app_id)
    system_prompt = system_prompt.replace("{app_name}", app_name)
    
    return system_prompt


def create_agent_graph(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str,
    debug: bool = False
) -> Any:
    """
    创建Agent实例（使用LangGraph）
    
    Args:
        workspace_path: 工作区路径（所有文件操作都在此目录下进行）
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        debug: 是否开启调试模式
        
    Returns:
        CompiledStateGraph实例（LangGraph Agent）
    """
    # 获取LLM实例
    llm = get_llm()
    
    # 获取工具列表（需要绑定workspace_path）
    tools = get_file_tools(workspace_path)
    
    # 构建系统提示词
    system_prompt = _build_system_prompt(
        workspace_path=workspace_path,
        user_id=user_id,
        app_id=app_id,
        app_name=app_name
    )
    
    # 使用新的 create_agent API 创建 Agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        debug=debug
    )
    
    logger.info(f"✓ Agent已创建 - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
    
    return agent


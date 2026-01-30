"""
Claude SDK Agent 工厂类 - 创建 Claude SDK Agent 实例
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.agent.infra.llm_factory_cc import get_claude_model_config, validate_claude_config
from app.core.config import settings

logger = logging.getLogger(__name__)

# 尝试导入 Claude SDK
try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
    )
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    logger.warning("claude_agent_sdk 未安装，Claude SDK Agent 功能将不可用")
    CLAUDE_SDK_AVAILABLE = False
    ClaudeSDKClient = None
    ClaudeAgentOptions = None


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


def _get_plugins_config() -> List[Dict[str, str]]:
    """
    获取插件配置列表，扫描插件目录下的所有插件
    
    Returns:
        插件配置列表
    """
    plugins = []
    
    plugins_dir = Path(settings.CLAUDE_PLUGINS_DIR)
    if not plugins_dir.exists():
        logger.info(f"Claude 插件目录不存在: {plugins_dir}，跳过插件加载")
        return plugins
    
    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir():
            plugin_json = plugin_path / ".claude-plugin" / "plugin.json"
            if plugin_json.exists():
                plugins.append({
                    "type": "local",
                    "path": str(plugin_path)
                })
                logger.info(f"找到 Claude 插件: {plugin_path.name}")
    
    logger.info(f"已加载 {len(plugins)} 个 Claude 插件")
    return plugins


def create_claude_agent_options(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str,
    agent_session_id: Optional[str] = None,
    tools: Optional[List[str]] = None,
    disallowed_tools: Optional[List[str]] = None,
) -> ClaudeAgentOptions:
    """
    创建 Claude Agent 配置选项
    
    Args:
        workspace_path: 工作区路径
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        agent_session_id: Agent 会话ID（用于恢复会话）
        tools: 允许的工具列表（可选）
        disallowed_tools: 禁止的工具列表（可选）
        
    Returns:
        ClaudeAgentOptions 对象
    """
    if not CLAUDE_SDK_AVAILABLE:
        raise ImportError("claude_agent_sdk 未安装，无法创建 Claude Agent")
    
    # 验证配置
    if not validate_claude_config():
        raise ValueError("Claude 配置不完整，请检查 CLAUDE_API_KEY 和 CLAUDE_MODEL")
    
    # 获取模型配置
    model_config = get_claude_model_config()
    
    # 构建系统提示词
    system_prompt_text = _build_system_prompt(
        workspace_path=workspace_path,
        user_id=user_id,
        app_id=app_id,
        app_name=app_name
    )
    
    # 构建系统提示词配置
    sys_prompt_cfg = {
        "type": "preset",
        "preset": "claude_code",
        "append": system_prompt_text
    }
    
    # 从工具适配层获取文件工具列表
    from app.agent.tools.tool_adapter_cc import get_file_tools_for_claude
    file_tools = get_file_tools_for_claude(workspace_path)
    
    # 默认允许的工具列表（Claude 内置工具）
    default_allowed_tools = [
        # Claude 内置工具（基础工具）
        "Skill", "Task", "TodoWrite",
        "WebFetch", "WebSearch",
    ]
    
    # 合并文件工具和用户提供的工具
    allowed_tools = default_allowed_tools + file_tools
    if tools:
        allowed_tools = allowed_tools + tools
    
    # 默认禁止的工具
    default_disallowed_tools = ['Bash(git commit:*)']
    disallowed_tools_list = default_disallowed_tools
    if disallowed_tools:
        disallowed_tools_list = default_disallowed_tools + disallowed_tools
    
    # 创建配置选项
    options = ClaudeAgentOptions(
        # 全局配置
        setting_sources=['user', 'project'],
        permission_mode=settings.CLAUDE_PERMISSION_MODE,
        max_turns=settings.CLAUDE_MAX_TURNS,
        
        # 模型配置
        system_prompt=sys_prompt_cfg,
        model=model_config["model_name"],
        env={
            'ANTHROPIC_BASE_URL': model_config["api_base"] or "",
            'ANTHROPIC_API_KEY': model_config["api_key"],
            'ANTHROPIC_AUTH_TOKEN': model_config["api_key"],
            "ANTHROPIC_MODEL": model_config["model_name"],
            "ANTHROPIC_SMALL_FAST_MODEL": model_config["model_name"]
        },
        
        # 工具配置
        mcp_servers={},  # 暂时不配置 MCP 服务器，后续可以扩展
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools_list,
        
        # 工作区配置
        cwd=workspace_path,
        
        # 插件配置
        plugins=_get_plugins_config(),
        
        # 恢复会话
        resume=agent_session_id,
    )
    
    logger.info(f"✓ Claude Agent 配置已创建 - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
    
    return options


def create_claude_agent_client(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str,
    agent_session_id: Optional[str] = None,
    tools: Optional[List[str]] = None,
    disallowed_tools: Optional[List[str]] = None,
) -> ClaudeSDKClient:
    """
    创建 Claude SDK Agent 客户端
    
    Args:
        workspace_path: 工作区路径（所有文件操作都在此目录下进行）
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        agent_session_id: Agent 会话ID（用于恢复会话）
        tools: 允许的工具列表（可选）
        disallowed_tools: 禁止的工具列表（可选）
        
    Returns:
        ClaudeSDKClient 实例
    """
    if not CLAUDE_SDK_AVAILABLE:
        raise ImportError("claude_agent_sdk 未安装，无法创建 Claude Agent")
    
    # 创建配置选项
    options = create_claude_agent_options(
        workspace_path=workspace_path,
        user_id=user_id,
        app_id=app_id,
        app_name=app_name,
        agent_session_id=agent_session_id,
        tools=tools,
        disallowed_tools=disallowed_tools,
    )
    
    # 创建客户端
    client = ClaudeSDKClient(options=options)
    
    logger.info(f"✓ Claude Agent 客户端已创建 - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
    
    return client


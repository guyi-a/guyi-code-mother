"""
工具适配层 - 将 LangChain 工具转换为 Claude SDK 工具格式

注意：
- Claude SDK 使用内置工具（Read, Write, Edit, Bash, Glob, Grep 等）和 MCP 工具
- 现有的文件工具（mkdir, write_file, read_file 等）可以通过以下方式使用：
  1. 使用 Claude SDK 内置工具（Read, Write, Edit）
  2. 通过 MCP 服务器提供自定义工具
  3. 通过 Bash 工具执行命令

本文件提供工具映射和适配说明。
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


# Claude SDK 内置工具映射
CLAUDE_BUILTIN_TOOLS = [
    # 文件操作
    "Read",      # 读取文件（对应 read_file）
    "Write",      # 写入文件（对应 write_file）
    "Edit",       # 编辑文件（对应部分 write_file 功能）
    "MultiEdit",  # 多文件编辑
    
    # 目录和文件系统
    "Glob",       # 文件匹配（对应 glob_files）
    "Grep",       # 文本搜索（对应 grep_search）
    
    # 系统操作
    "Bash",       # 执行 bash 命令（可用于 mkdir, list_dir 等）
    
    # 其他
    "Skill",      # 技能工具
    "Task",       # 任务工具
    "TodoWrite",  # TODO 工具
    "WebFetch",   # 网页获取
    "WebSearch",  # 网页搜索
]


def get_claude_tool_mapping() -> Dict[str, str]:
    """
    获取 LangChain 工具到 Claude SDK 工具的映射
    
    Returns:
        工具映射字典：{langchain_tool_name: claude_tool_name}
    """
    return {
        "read_file": "Read",
        "write_file": "Write",
        "mkdir": "Bash",  # 通过 Bash 执行 mkdir 命令
        "list_dir": "Bash",  # 通过 Bash 执行 ls 命令
        "grep_search": "Grep",
        "glob_files": "Glob",
    }


def get_file_tools_for_claude(workspace_path: str) -> List[str]:
    """
    获取 Claude SDK 可用的文件工具列表
    
    注意：Claude SDK 使用内置工具，不需要像 LangChain 那样创建工具对象。
    只需要在 allowed_tools 中列出工具名称即可。
    
    Args:
        workspace_path: 工作区路径（用于文档说明）
        
    Returns:
        工具名称列表
    """
    # Claude SDK 内置的文件操作工具
    tools = [
        "Read",      # 读取文件
        "Write",     # 写入文件
        "Edit",      # 编辑文件
        "MultiEdit", # 多文件编辑
        "Glob",      # 文件匹配
        "Grep",      # 文本搜索
        "Bash",      # Bash 命令（可用于 mkdir, list_dir 等）
    ]
    
    logger.info(f"Claude SDK 文件工具已配置 - workspace: {workspace_path}")
    return tools


def convert_tool_description_to_claude(
    langchain_tool_name: str,
    langchain_description: str
) -> str:
    """
    将 LangChain 工具描述转换为 Claude SDK 工具描述格式
    
    注意：Claude SDK 使用内置工具，通常不需要自定义描述。
    此函数主要用于文档和说明。
    
    Args:
        langchain_tool_name: LangChain 工具名称
        langchain_description: LangChain 工具描述
        
    Returns:
        Claude SDK 工具描述（如果有对应工具）
    """
    mapping = get_claude_tool_mapping()
    claude_tool = mapping.get(langchain_tool_name)
    
    if not claude_tool:
        return f"无对应的 Claude SDK 工具: {langchain_tool_name}"
    
    descriptions = {
        "Read": "读取文件内容。Claude SDK 内置工具，可直接使用。",
        "Write": "写入文件内容。Claude SDK 内置工具，可直接使用。",
        "Edit": "编辑文件内容。Claude SDK 内置工具，可直接使用。",
        "Grep": "在文件中搜索文本。Claude SDK 内置工具，可直接使用。",
        "Glob": "使用 glob 模式匹配文件。Claude SDK 内置工具，可直接使用。",
        "Bash": "执行 bash 命令。可用于创建目录、列出目录等操作。",
    }
    
    return descriptions.get(claude_tool, f"使用 Claude SDK 工具: {claude_tool}")


def get_workspace_aware_tools_info(workspace_path: str) -> Dict[str, Any]:
    """
    获取工作区相关的工具信息（用于文档和说明）
    
    Args:
        workspace_path: 工作区路径
        
    Returns:
        工具信息字典
    """
    return {
        "workspace_path": workspace_path,
        "available_tools": get_file_tools_for_claude(workspace_path),
        "tool_mapping": get_claude_tool_mapping(),
        "note": (
            "Claude SDK 使用内置工具，所有文件操作都在工作区路径下进行。"
            "工具会自动处理路径验证，确保操作限制在工作区内。"
        )
    }


# 工具使用示例（用于文档）
TOOL_USAGE_EXAMPLES = {
    "read_file": {
        "langchain": "read_file(file_path='src/main.py')",
        "claude": "使用 Read 工具：Read('src/main.py')",
        "note": "Claude SDK 的 Read 工具会自动处理工作区路径"
    },
    "write_file": {
        "langchain": "write_file(file_path='src/main.py', content='...')",
        "claude": "使用 Write 工具：Write('src/main.py', content='...')",
        "note": "Claude SDK 的 Write 工具会自动处理工作区路径"
    },
    "mkdir": {
        "langchain": "mkdir(dir_path='src/components')",
        "claude": "使用 Bash 工具：Bash('mkdir -p src/components')",
        "note": "通过 Bash 工具执行 mkdir 命令，路径会自动限制在工作区内"
    },
    "list_dir": {
        "langchain": "list_dir(dir_path='src')",
        "claude": "使用 Bash 工具：Bash('ls src') 或使用 Glob 工具：Glob('src/*')",
        "note": "可以使用 Bash 或 Glob 工具来列出目录"
    },
    "grep_search": {
        "langchain": "grep_search(search_path='src', pattern='def main')",
        "claude": "使用 Grep 工具：Grep('def main', 'src')",
        "note": "Claude SDK 的 Grep 工具功能类似，但参数格式可能不同"
    },
    "glob_files": {
        "langchain": "glob_files(search_path='src', pattern='*.py')",
        "claude": "使用 Glob 工具：Glob('src/**/*.py')",
        "note": "Claude SDK 的 Glob 工具支持 glob 模式匹配"
    },
}


"""
Claude SDK Agent 服务 - 使用 Claude SDK 封装大模型 Agent
支持异步和流式调用
"""
import logging
import re
import traceback
from pathlib import Path
from typing import List, Dict, Optional, AsyncIterator, Any
from app.agent.service.base_agent_service import BaseAgentService
from app.agent.infra.agent_factory_cc import (
    create_claude_agent_client,
    CLAUDE_SDK_AVAILABLE,
)
from app.agent.models.message import (
    MessageType,
    MessageSubType,
    StreamingMessage,
    InitMessageMetadata,
)
from app.agent.context.memory_store import get_memory_store
from app.core.config import settings

logger = logging.getLogger(__name__)

# 尝试导入 Claude SDK 消息类型
try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        AssistantMessage,
        SystemMessage,
        ResultMessage,
        UserMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
    )
    CLAUDE_MESSAGE_TYPES_AVAILABLE = True
except ImportError:
    logger.warning("claude_agent_sdk 消息类型未导入，部分功能可能不可用")
    CLAUDE_MESSAGE_TYPES_AVAILABLE = False
    AssistantMessage = None
    SystemMessage = None
    ResultMessage = None
    UserMessage = None
    TextBlock = None
    ToolUseBlock = None
    ToolResultBlock = None


class ClaudeAgentService(BaseAgentService):
    """
    Claude SDK Agent 服务类
    
    继承 BaseAgentService，实现统一的接口
    """
    
    def __init__(
        self,
        workspace_path: str,
        user_id: str,
        app_id: str,
        app_name: str,
        debug: bool = False
    ):
        """
        初始化 Claude Agent 服务
        
        Args:
            workspace_path: 工作区路径（所有文件操作都在此目录下进行）
            user_id: 用户ID
            app_id: 应用ID
            app_name: 应用名称
            debug: 是否开启调试模式
        """
        super().__init__(workspace_path, user_id, app_id, app_name, debug)
        
        if not CLAUDE_SDK_AVAILABLE:
            logger.error("claude_agent_sdk 未安装，Claude Agent 服务不可用")
            self.client = None
            return
        
        # 获取会话ID（从 Redis）
        self.memory_store = get_memory_store()
        self.agent_session_id = None
        
        # 客户端将在首次调用时初始化
        self.client: Optional[ClaudeSDKClient] = None
        self._connected = False
        
        logger.info(f"✓ Claude Agent 服务已初始化 - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
    
    async def _ensure_workspace_exists(self) -> None:
        """确保工作区目录存在，不存在则创建"""
        try:
            path = Path(self.workspace_path)
            if not path.exists():
                logger.warning(f"工作区目录不存在: {self.workspace_path}，正在创建...")
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"工作区目录已创建: {self.workspace_path}")
        except Exception as e:
            logger.error(f"创建工作区目录失败: {self.workspace_path}: {e}")
    
    async def _connect(self) -> None:
        """连接 Claude 客户端，只对当前 session 保持连接"""
        if self._connected and self.client:
            return
        
        if not CLAUDE_SDK_AVAILABLE:
            raise ImportError("claude_agent_sdk 未安装，无法连接")
        
        try:
            # 获取会话ID（如果存在）
            self.agent_session_id = await self.memory_store.get_session_id(
                self.user_id,
                self.app_id
            )
            
            # 创建客户端
            self.client = create_claude_agent_client(
                workspace_path=self.workspace_path,
                user_id=self.user_id,
                app_id=self.app_id,
                app_name=self.app_name,
                agent_session_id=self.agent_session_id,
            )
            
            # 连接客户端
            try:
                await self.client.connect()
                self._connected = True
                logger.info(f"✓ Claude 客户端已连接 - user: {self.user_id}, app: {self.app_id}")
            except Exception as e:
                # 如果 resume session 失败，尝试重新连接（不恢复会话）
                logger.warning(f"Claude 客户端连接失败（尝试恢复会话）: {e}，尝试重新连接...")
                self.agent_session_id = None
                self.client = create_claude_agent_client(
                    workspace_path=self.workspace_path,
                    user_id=self.user_id,
                    app_id=self.app_id,
                    app_name=self.app_name,
                    agent_session_id=None,
                )
                await self.client.connect()
                self._connected = True
                logger.info(f"✓ Claude 客户端已重新连接 - user: {self.user_id}, app: {self.app_id}")
        except Exception as e:
            logger.error(f"连接 Claude 客户端失败: {e}", exc_info=True)
            self.client = None
            self._connected = False
            raise
    
    async def _disconnect(self) -> None:
        """断开 Claude 客户端连接"""
        if not self._connected or not self.client:
            return
        
        try:
            await self.client.disconnect()
            self._connected = False
            logger.info(f"✓ Claude 客户端已断开 - user: {self.user_id}, app: {self.app_id}")
        except Exception as e:
            logger.error(f"断开 Claude 客户端连接失败: {e}", exc_info=True)
    
    def _filter_content(self, content: str) -> str:
        """
        过滤文本内容，先按行过滤移除匹配正则模式的行，再进行字符串替换
        
        Args:
            content: 原始内容
            
        Returns:
            过滤后的内容
        """
        if not content:
            return ""
        
        # 过滤 "(no content)" 内容
        if content.strip() == "(no content)":
            return ""
        
        # TODO: 从配置读取过滤规则
        # 这里先使用简单的过滤逻辑
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            # 简单的过滤规则示例
            if not re.search(r'^\s*$', line):  # 保留非空行
                clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def _construct_query(self, messages: List[Dict]) -> str:
        """
        从消息列表构建查询字符串
        
        Args:
            messages: 消息列表
            
        Returns:
            查询字符串（最后一条用户消息）
        """
        # 获取最后一条用户消息
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
    
    async def ainvoke(self, messages: List[Dict], **kwargs: Any) -> str:
        """
        异步非流式调用 Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给 Agent
            
        Returns:
            Agent 回复文本
        """
        if not CLAUDE_SDK_AVAILABLE:
            return "抱歉，Claude SDK 未安装，Agent 服务暂不可用。"
        
        try:
            # 确保工作区存在
            await self._ensure_workspace_exists()
            
            # 连接客户端
            await self._connect()
            
            if not self.client:
                return "抱歉，Agent 服务暂不可用，请检查配置。"
            
            # 构建查询
            query = self._construct_query(messages)
            if not query:
                return "请输入您的问题。"
            
            # 调用 Agent
            await self.client.query(query)
            
            # 收集响应
            full_response = ""
            async for message in self.client.receive_response():
                if CLAUDE_MESSAGE_TYPES_AVAILABLE:
                    if isinstance(message, SystemMessage):
                        # 处理初始化消息，获取 session_id
                        if hasattr(message, 'subtype') and message.subtype == "init":
                            if hasattr(message, 'data') and message.data and "session_id" in message.data:
                                self.agent_session_id = message.data["session_id"]
                                # 保存到 Redis
                                await self.memory_store.save_session_id(
                                    self.user_id,
                                    self.app_id,
                                    self.agent_session_id
                                )
                                logger.info(f"✓ 已保存 Claude 会话ID: {self.agent_session_id}")
                    
                    elif isinstance(message, AssistantMessage):
                        # 处理助手消息
                        if hasattr(message, 'content'):
                            for content_block in message.content:
                                if isinstance(content_block, TextBlock):
                                    if hasattr(content_block, 'text'):
                                        full_response += content_block.text
                    
                    elif isinstance(message, ResultMessage):
                        # 结果消息是响应的结束
                        if hasattr(message, 'result'):
                            result_text = self._filter_content(str(message.result))
                            if result_text:
                                full_response += result_text
                        break
            
            # 断开连接
            await self._disconnect()
            
            # 过滤内容
            filtered_response = self._filter_content(full_response)
            
            return filtered_response.strip() if filtered_response else "抱歉，未收到有效回复。"
            
        except Exception as e:
            logger.error(f"Claude Agent 调用失败: {e}", exc_info=True)
            await self._disconnect()
            return f"抱歉，对话过程中出现错误：{str(e)}"
    
    async def stream(self, messages: List[Dict], **kwargs: Any) -> AsyncIterator[str]:
        """
        流式调用 Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给 Agent
            
        Yields:
            Agent 回复的文本片段（逐字或逐词）
        """
        if not CLAUDE_SDK_AVAILABLE:
            yield "抱歉，Claude SDK 未安装，Agent 服务暂不可用。"
            return
        
        try:
            # 确保工作区存在
            await self._ensure_workspace_exists()
            
            # 连接客户端
            await self._connect()
            
            if not self.client:
                yield "抱歉，Agent 服务暂不可用，请检查配置。"
                return
            
            # 构建查询
            query = self._construct_query(messages)
            if not query:
                yield "请输入您的问题。"
                return
            
            # 调用 Agent
            await self.client.query(query)
            
            # 流式处理响应
            full_response = ""
            async for message in self.client.receive_response():
                if CLAUDE_MESSAGE_TYPES_AVAILABLE:
                    if isinstance(message, SystemMessage):
                        # 处理初始化消息，获取 session_id
                        if hasattr(message, 'subtype') and message.subtype == "init":
                            if hasattr(message, 'data') and message.data and "session_id" in message.data:
                                self.agent_session_id = message.data["session_id"]
                                # 保存到 Redis
                                await self.memory_store.save_session_id(
                                    self.user_id,
                                    self.app_id,
                                    self.agent_session_id
                                )
                                logger.info(f"✓ 已保存 Claude 会话ID: {self.agent_session_id}")
                    
                    elif isinstance(message, AssistantMessage):
                        # 处理助手消息
                        if hasattr(message, 'content'):
                            for content_block in message.content:
                                if isinstance(content_block, TextBlock):
                                    if hasattr(content_block, 'text'):
                                        text = content_block.text
                                        # 提取新增的内容
                                        if len(text) > len(full_response):
                                            new_content = text[len(full_response):]
                                            full_response = text
                                            filtered = self._filter_content(new_content)
                                            if filtered:
                                                yield filtered
                                
                                elif isinstance(content_block, ToolUseBlock):
                                    # 工具调用（可选：可以 yield 工具调用信息）
                                    tool_name = getattr(content_block, 'name', '')
                                    logger.debug(f"工具调用: {tool_name}")
                    
                    elif isinstance(message, ResultMessage):
                        # 结果消息是响应的结束
                        if hasattr(message, 'result'):
                            result_text = self._filter_content(str(message.result))
                            if result_text and len(result_text) > len(full_response):
                                new_content = result_text[len(full_response):]
                                full_response = result_text
                                if new_content:
                                    yield new_content
                        break
            
            # 断开连接
            await self._disconnect()
            
        except Exception as e:
            logger.error(f"Claude Agent 流式调用失败: {e}", exc_info=True)
            await self._disconnect()
            yield f"抱歉，对话过程中出现错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查 Agent 服务是否可用"""
        return CLAUDE_SDK_AVAILABLE and self.client is not None
    
    async def interrupt(self) -> bool:
        """
        中断当前会话
        
        Returns:
            True 如果中断成功，False 否则
        """
        try:
            if self.client and self._connected:
                await self.client.interrupt()
                logger.info(f"✓ 已中断 Claude 会话 - user: {self.user_id}, app: {self.app_id}")
                return True
            else:
                logger.warning(f"无法中断会话：客户端未连接")
                return False
        except Exception as e:
            logger.error(f"中断 Claude 会话失败: {e}")
            return False


def create_claude_agent_service(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str,
    debug: bool = False
) -> ClaudeAgentService:
    """
    创建 Claude Agent 服务实例
    
    Args:
        workspace_path: 工作区路径（所有文件操作都在此目录下进行）
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        debug: 是否开启调试模式
        
    Returns:
        ClaudeAgentService 实例
    """
    return ClaudeAgentService(
        workspace_path=workspace_path,
        user_id=user_id,
        app_id=app_id,
        app_name=app_name,
        debug=debug
    )


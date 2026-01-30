"""
Agent服务 - 使用LangChain create_agent封装大模型Agent
支持异步和流式调用
"""
import logging
from typing import List, Dict, Optional, AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from app.agent.service.base_agent_service import BaseAgentService

logger = logging.getLogger(__name__)


class AgentService(BaseAgentService):
    """Agent服务类 - 封装LangChain Agent调用"""
    
    def __init__(
        self,
        workspace_path: str,
        user_id: str,
        app_id: str,
        app_name: str,
        debug: bool = False
    ):
        """
        初始化Agent服务
        
        Args:
            workspace_path: 工作区路径（所有文件操作都在此目录下进行）
            user_id: 用户ID
            app_id: 应用ID
            app_name: 应用名称
            debug: 是否开启调试模式
        """
        from app.agent.infra.agent_factory import create_agent_graph
        
        # 使用agent_factory创建Agent
        self.agent = create_agent_graph(
            workspace_path=workspace_path,
            user_id=user_id,
            app_id=app_id,
            app_name=app_name,
            debug=debug
        )
        
        self.workspace_path = workspace_path
        self.user_id = user_id
        self.app_id = app_id
        self.app_name = app_name
        
        logger.info(f"✓ Agent服务已初始化 - workspace: {workspace_path}, user: {user_id}, app: {app_id}")
    
    def _convert_messages(self, messages: List[Dict]) -> List[BaseMessage]:
        """
        将消息字典列表转换为LangChain Message对象
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            
        Returns:
            LangChain Message对象列表
        """
        langchain_messages = []
        
        # 转换消息
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        return langchain_messages
    
    async def ainvoke(self, messages: List[Dict], **kwargs: Any) -> str:
        """
        异步非流式调用Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给Agent
            
        Returns:
            Agent回复文本
        """
        if not self.agent:
            return "抱歉，Agent服务暂不可用，请检查配置。"
        
        try:
            # 转换消息格式为 LangChain 格式
            langchain_messages = self._convert_messages(messages)
            
            if not langchain_messages:
                return "请输入您的问题。"
            
            # 准备输入 - LangChain 1.0+ 使用 messages 作为输入
            agent_input = {"messages": langchain_messages}
            agent_input.update(kwargs)
            
            # 异步调用Agent
            result = await self.agent.ainvoke(agent_input)
            
            # 提取回复内容
            if isinstance(result, dict):
                # LangChain 1.0+ 返回 messages 列表
                if "messages" in result:
                    messages_list = result["messages"]
                    # 获取最后一条 AI 消息
                    for msg in reversed(messages_list):
                        if isinstance(msg, AIMessage):
                            return msg.content.strip() if msg.content else ""
                # 兼容旧格式
                output = result.get("output", "")
                if output:
                    return output.strip()
                return str(result).strip()
            elif isinstance(result, str):
                return result.strip()
            else:
                return str(result).strip()
                
        except Exception as e:
            logger.error(f"Agent调用失败: {e}", exc_info=True)
            return f"抱歉，对话过程中出现错误：{str(e)}"
    
    async def stream(self, messages: List[Dict], **kwargs: Any) -> AsyncIterator[str]:
        """
        流式调用Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给Agent
            
        Yields:
            Agent回复的文本片段（逐字或逐词）
        """
        if not self.agent:
            yield "抱歉，Agent服务暂不可用，请检查配置。"
            return
        
        try:
            # 转换消息格式为 LangChain 格式
            langchain_messages = self._convert_messages(messages)
            
            if not langchain_messages:
                yield "请输入您的问题。"
                return
            
            # 准备输入 - LangChain 1.0+ 使用 messages 作为输入
            agent_input = {"messages": langchain_messages}
            agent_input.update(kwargs)
            
            # 流式调用Agent
            full_output = ""
            async for chunk in self.agent.astream(agent_input, stream_mode="messages"):
                # 处理元组格式 (AIMessage, metadata)
                if isinstance(chunk, tuple) and len(chunk) > 0:
                    chunk = chunk[0]  # 取第一个元素（AIMessage）
                
                # 处理 AIMessage 对象
                if isinstance(chunk, AIMessage):
                    if chunk.content and isinstance(chunk.content, str):
                        content = chunk.content
                        # 提取新增的内容
                        if len(content) > len(full_output):
                            new_content = content[len(full_output):]
                            full_output = content
                            yield new_content
                # 处理字典格式
                elif isinstance(chunk, dict):
                    # 检查是否有messages键（LangChain格式）
                    if "messages" in chunk:
                        for msg in chunk["messages"]:
                            if isinstance(msg, AIMessage) and msg.content:
                                content = msg.content
                                if isinstance(content, str):
                                    # 提取新增的内容
                                    if len(content) > len(full_output):
                                        new_content = content[len(full_output):]
                                        full_output = content
                                        yield new_content
                    # 兼容旧格式
                    elif "output" in chunk:
                        output = chunk["output"]
                        if isinstance(output, str) and len(output) > len(full_output):
                            new_content = output[len(full_output):]
                            full_output = output
                            yield new_content
                # 处理字符串
                elif isinstance(chunk, str):
                    if len(chunk) > len(full_output):
                        new_content = chunk[len(full_output):]
                        full_output = chunk
                        yield new_content
                # 处理其他Message对象
                elif hasattr(chunk, "content"):
                    content = chunk.content
                    if isinstance(content, str) and len(content) > len(full_output):
                        new_content = content[len(full_output):]
                        full_output = content
                        yield new_content
                        
        except Exception as e:
            logger.error(f"Agent流式调用失败: {e}", exc_info=True)
            yield f"抱歉，对话过程中出现错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查Agent服务是否可用"""
        return self.agent is not None


def create_agent_service(
    workspace_path: str,
    user_id: str,
    app_id: str,
    app_name: str,
    debug: bool = False
) -> AgentService:
    """
    创建Agent服务实例
    
    Args:
        workspace_path: 工作区路径（所有文件操作都在此目录下进行）
        user_id: 用户ID
        app_id: 应用ID
        app_name: 应用名称
        debug: 是否开启调试模式
        
    Returns:
        AgentService实例
    """
    return AgentService(
        workspace_path=workspace_path,
        user_id=user_id,
        app_id=app_id,
        app_name=app_name,
        debug=debug
    )


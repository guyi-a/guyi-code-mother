"""
Agent 服务抽象基类
统一 LangChain 和 Claude SDK 两种实现的接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, AsyncIterator, Any, Optional
from app.agent.models.message import Message


class BaseAgentService(ABC):
    """
    Agent 服务抽象基类
    
    所有 Agent 实现（LangChain、Claude SDK）都应该继承此类
    并实现统一的接口方法
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
        初始化 Agent 服务
        
        Args:
            workspace_path: 工作区路径（所有文件操作都在此目录下进行）
            user_id: 用户ID
            app_id: 应用ID
            app_name: 应用名称
            debug: 是否开启调试模式
        """
        self.workspace_path = workspace_path
        self.user_id = user_id
        self.app_id = app_id
        self.app_name = app_name
        self.debug = debug
    
    @abstractmethod
    async def ainvoke(self, messages: List[Dict], **kwargs: Any) -> str:
        """
        异步非流式调用 Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给 Agent
            
        Returns:
            Agent 回复文本
        """
        pass
    
    @abstractmethod
    async def stream(self, messages: List[Dict], **kwargs: Any) -> AsyncIterator[str]:
        """
        流式调用 Agent
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            **kwargs: 其他参数，会传递给 Agent
            
        Yields:
            Agent 回复的文本片段（逐字或逐词）
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查 Agent 服务是否可用
        
        Returns:
            True 如果服务可用，False 否则
        """
        pass
    
    def _convert_messages_to_unified(self, messages: List[Dict]) -> List[Message]:
        """
        将消息字典列表转换为统一消息模型
        
        Args:
            messages: 消息字典列表
            
        Returns:
            统一消息列表
        """
        from app.agent.models.message import convert_messages_from_dict
        return convert_messages_from_dict(messages)
    
    def _convert_messages_from_unified(self, messages: List[Message]) -> List[Dict]:
        """
        将统一消息模型转换为消息字典列表
        
        Args:
            messages: 统一消息列表
            
        Returns:
            消息字典列表
        """
        return [msg.to_dict() for msg in messages]


"""
统一消息模型 - 支持 LangChain 和 Claude SDK 两种实现
"""
from enum import Enum
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel

# LangChain 消息类型
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    BaseMessage as LangChainBaseMessage,
)


class MessageType(str, Enum):
    """消息类型枚举"""
    SYSTEM_MESSAGE = "system_message"
    ASSISTANT_MESSAGE = "assistant_message"
    RESULT_MESSAGE = "result_message"
    ERROR_MESSAGE = "error_message"
    USER_MESSAGE = "user_message"


class MessageSubType(str, Enum):
    """消息子类型枚举"""
    INIT = "init"
    TEXT = "text"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    ERROR = "error"


@dataclass
class Message:
    """
    统一的消息模型
    
    用于在 LangChain 和 Claude SDK 之间转换消息格式
    """
    role: str  # "user", "assistant", "system"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_langchain(self) -> LangChainBaseMessage:
        """
        转换为 LangChain 消息格式
        
        Returns:
            LangChain Message 对象
        """
        if self.role == "system":
            return SystemMessage(content=self.content)
        elif self.role == "user":
            return HumanMessage(content=self.content)
        elif self.role == "assistant":
            return AIMessage(content=self.content)
        else:
            # 默认作为用户消息处理
            return HumanMessage(content=self.content)
    
    @classmethod
    def from_langchain(cls, msg: LangChainBaseMessage) -> "Message":
        """
        从 LangChain 消息创建统一消息
        
        Args:
            msg: LangChain Message 对象
            
        Returns:
            Message 对象
        """
        if isinstance(msg, SystemMessage):
            role = "system"
        elif isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        else:
            role = "user"  # 默认
        
        content = msg.content if hasattr(msg, "content") else str(msg)
        
        return cls(
            role=role,
            content=content,
            metadata={}
        )
    
    def to_claude_format(self) -> Dict[str, str]:
        """
        转换为 Claude SDK 格式（字典）
        
        Returns:
            Claude SDK 消息字典
        """
        return {
            "role": self.role,
            "content": self.content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """
        从字典创建消息
        
        Args:
            data: 消息字典，格式: {"role": "user", "content": "..."}
            
        Returns:
            Message 对象
        """
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            消息字典
        """
        return {
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata
        }


class InitMessageMetadata(BaseModel):
    """初始化消息元数据（Claude SDK 特有）"""
    agent_session_id: Optional[str] = None


@dataclass
class StreamingMessage:
    """
    流式消息模型
    
    用于统一处理 LangChain 和 Claude SDK 的流式响应
    """
    type: MessageType
    subtype: MessageSubType
    content: str = ""
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            消息字典
        """
        result = {
            "type": self.type.value,
            "subtype": self.subtype.value,
            "content": self.content,
        }
        
        if self.tool_name:
            result["tool_name"] = self.tool_name
        if self.tool_input:
            result["tool_input"] = self.tool_input
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result


def convert_messages_to_langchain(messages: List[Message]) -> List[LangChainBaseMessage]:
    """
    将统一消息列表转换为 LangChain 消息列表
    
    Args:
        messages: 统一消息列表
        
    Returns:
        LangChain 消息列表
    """
    return [msg.to_langchain() for msg in messages]


def convert_messages_from_langchain(messages: List[LangChainBaseMessage]) -> List[Message]:
    """
    从 LangChain 消息列表创建统一消息列表
    
    Args:
        messages: LangChain 消息列表
        
    Returns:
        统一消息列表
    """
    return [Message.from_langchain(msg) for msg in messages]


def convert_messages_to_claude(messages: List[Message]) -> List[Dict[str, str]]:
    """
    将统一消息列表转换为 Claude SDK 格式
    
    Args:
        messages: 统一消息列表
        
    Returns:
        Claude SDK 消息列表
    """
    return [msg.to_claude_format() for msg in messages]


def convert_messages_from_dict(messages: List[Dict[str, Any]]) -> List[Message]:
    """
    从字典列表创建统一消息列表
    
    Args:
        messages: 消息字典列表，格式: [{"role": "user", "content": "..."}, ...]
        
    Returns:
        统一消息列表
    """
    return [Message.from_dict(msg) for msg in messages]


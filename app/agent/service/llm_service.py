"""
LLM服务 - 使用LangChain封装大模型调用
"""
import logging
from typing import List, Dict, Optional, AsyncIterator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务类 - 封装LangChain大模型调用"""
    
    def __init__(self):
        """
        初始化LLM服务
        """
        from app.agent.infra.llm_factory import get_llm
        self.llm = get_llm()
        
        logger.info("✓ LLM服务已初始化")
    
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
    
    async def ainvoke(self, messages: List[Dict]) -> str:
        """
        异步非流式调用LLM
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            
        Returns:
            AI回复文本
        """
        if not self.llm:
            return "抱歉，AI服务暂不可用，请检查配置。"
        
        try:
            # 转换消息格式
            langchain_messages = self._convert_messages(messages)
            
            # 异步调用大模型
            response = await self.llm.ainvoke(langchain_messages)
            
            # 提取回复内容
            if hasattr(response, 'content'):
                return response.content.strip()
            elif isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
        except Exception as e:
            logger.error(f"LLM调用失败: {e}", exc_info=True)
            return f"抱歉，对话过程中出现错误：{str(e)}"
    
    async def stream(self, messages: List[Dict]) -> AsyncIterator[str]:
        """
        流式调用LLM
        
        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}, ...]
            
        Yields:
            AI回复的文本片段（逐字或逐词）
        """
        if not self.llm:
            yield "抱歉，AI服务暂不可用，请检查配置。"
            return
        
        try:
            # 转换消息格式
            langchain_messages = self._convert_messages(messages)
            
            # 流式调用大模型（使用astream进行异步流式调用）
            async for chunk in self.llm.astream(langchain_messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk
                else:
                    # 如果chunk是AIMessage对象，提取content
                    if hasattr(chunk, 'content'):
                        yield chunk.content
        except Exception as e:
            logger.error(f"LLM流式调用失败: {e}", exc_info=True)
            yield f"抱歉，对话过程中出现错误：{str(e)}"
    
    def is_available(self) -> bool:
        """检查LLM服务是否可用"""
        return self.llm is not None


# 全局单例
_llm_service_instance: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    获取LLM服务单例
    
    Returns:
        LLMService实例
    """
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance


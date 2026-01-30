from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Agent对话请求体
    """
    message: str = Field(..., min_length=1, description="用户消息")
    chat_id: str = Field(..., description="对话ID")
    app_id: str = Field(..., description="应用ID")
    app_name: str = Field(..., description="应用名称")
    agent_type: Optional[str] = Field(None, description="Agent类型：langchain 或 claude，如果不提供则使用配置中的默认值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "创建一个网站",
                "chat_id": "chat_123456",
                "app_id": "app_001",
                "app_name": "my_website"
            }
        }


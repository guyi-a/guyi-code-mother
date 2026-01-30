from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    """
    Agent对话响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: dict = Field(None, description="响应数据")
    ai_reply: str = Field(None, description="AI回复内容")
    chat_id: str = Field(None, description="对话ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": None,
                "ai_reply": "好的，我来帮你创建一个网站...",
                "chat_id": "chat_123456"
            }
        }


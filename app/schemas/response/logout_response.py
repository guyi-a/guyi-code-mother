from pydantic import BaseModel, Field


class LogoutResponse(BaseModel):
    """
    用户下线响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("退出成功", description="响应消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "退出成功"
            }
        }


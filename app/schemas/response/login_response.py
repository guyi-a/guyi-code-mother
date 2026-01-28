from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.response.register_response import UserInfo


class LoginResponse(BaseModel):
    """
    用户登录响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("登录成功", description="响应消息")
    data: UserInfo = Field(..., description="用户信息")
    token: str = Field(..., description="访问令牌")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "登录成功",
                "data": {
                    "id": 1,
                    "userAccount": "testuser",
                    "userName": "测试用户",
                    "userAvatar": None,
                    "userProfile": None,
                    "userRole": "user",
                    "createTime": "2026-01-28T12:00:00"
                },
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.response.register_response import UserInfo


class UserListResponse(BaseModel):
    """
    用户列表响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: list[UserInfo] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": [
                    {
                        "id": 1,
                        "userAccount": "testuser",
                        "userName": "测试用户",
                        "userAvatar": None,
                        "userProfile": None,
                        "userRole": "user",
                        "createTime": "2026-01-28T12:00:00"
                    }
                ],
                "total": 1
            }
        }


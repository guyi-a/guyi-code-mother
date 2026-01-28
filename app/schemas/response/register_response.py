from datetime import datetime
from pydantic import BaseModel, Field


class UserInfo(BaseModel):
    """
    用户信息（响应体中的用户数据部分）
    """
    id: int = Field(..., description="用户ID")
    userAccount: str = Field(..., description="账号")
    userName: str | None = Field(None, description="用户昵称")
    userAvatar: str | None = Field(None, description="用户头像")
    userProfile: str | None = Field(None, description="用户简介")
    userRole: str = Field(..., description="用户角色：user/admin")
    createTime: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True  # 允许从 ORM 对象创建


class RegisterResponse(BaseModel):
    """
    用户注册响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("注册成功", description="响应消息")
    data: UserInfo = Field(..., description="用户信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "注册成功",
                "data": {
                    "id": 1,
                    "userAccount": "testuser",
                    "userName": "测试用户",
                    "userAvatar": None,
                    "userProfile": None,
                    "userRole": "user",
                    "createTime": "2026-01-28T12:00:00"
                }
            }
        }


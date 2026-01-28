from pydantic import BaseModel, Field


class UpdateUserRequest(BaseModel):
    """
    更新用户信息请求体
    """
    userName: str | None = Field(None, max_length=256, description="用户昵称")
    userAvatar: str | None = Field(None, max_length=1024, description="用户头像URL")
    userProfile: str | None = Field(None, max_length=512, description="用户简介")
    userPassword: str | None = Field(None, min_length=6, max_length=512, description="新密码（可选）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "userName": "新昵称",
                "userAvatar": "https://example.com/avatar.jpg",
                "userProfile": "这是我的简介",
                "userPassword": None
            }
        }


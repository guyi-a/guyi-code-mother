from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    """
    创建用户请求体（管理员使用）
    """
    userAccount: str = Field(..., min_length=4, max_length=256, description="账号，4-256个字符")
    userPassword: str = Field(..., min_length=6, max_length=512, description="密码，6-512个字符")
    userName: str | None = Field(None, max_length=256, description="用户昵称，可选")
    userAvatar: str | None = Field(None, max_length=1024, description="用户头像URL，可选")
    userProfile: str | None = Field(None, max_length=512, description="用户简介，可选")
    userRole: str = Field("user", description="用户角色：user/admin，默认为user")
    
    class Config:
        json_schema_extra = {
            "example": {
                "userAccount": "newuser",
                "userPassword": "123456",
                "userName": "新用户",
                "userAvatar": None,
                "userProfile": None,
                "userRole": "user"
            }
        }


from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    用户登录请求体
    """
    userAccount: str = Field(..., min_length=4, max_length=256, description="账号")
    userPassword: str = Field(..., min_length=6, max_length=512, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "userAccount": "testuser",
                "userPassword": "123456"
            }
        }


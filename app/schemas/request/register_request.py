from pydantic import BaseModel, Field, model_validator


class RegisterRequest(BaseModel):
    """
    用户注册请求体
    """
    userAccount: str = Field(..., min_length=4, max_length=256, description="账号，4-256个字符")
    userPassword: str = Field(..., min_length=6, max_length=512, description="密码，6-512个字符")
    checkPassword: str = Field(..., min_length=6, max_length=512, description="确认密码，必须与密码一致")
    userName: str | None = Field(None, max_length=256, description="用户昵称，可选")
    userAvatar: str | None = Field(None, max_length=1024, description="用户头像URL，可选")
    userProfile: str | None = Field(None, max_length=512, description="用户简介，可选")
    
    @model_validator(mode="after")
    def validate_passwords_match(self):
        """
        验证确认密码是否与密码一致
        """
        if self.checkPassword != self.userPassword:
            raise ValueError("密码和确认密码不一致")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "userAccount": "testuser",
                "userPassword": "123456",
                "checkPassword": "123456",
                "userName": "测试用户",
                "userAvatar": None,
                "userProfile": None
            }
        }


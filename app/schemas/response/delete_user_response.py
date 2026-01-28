from pydantic import BaseModel, Field


class DeleteUserResponse(BaseModel):
    """
    删除用户响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("删除成功", description="响应消息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "删除成功"
            }
        }


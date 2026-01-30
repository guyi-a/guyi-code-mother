from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.response.app_response import AppInfo


class AppListResponse(BaseModel):
    """
    应用列表响应体
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: list[AppInfo] = Field(..., description="应用列表")
    total: int = Field(..., description="总数量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": [
                    {
                        "id": 1,
                        "appName": "我的网站",
                        "cover": "https://example.com/cover.jpg",
                        "initPrompt": "创建一个网站",
                        "codeGenType": "static",
                        "deployKey": "app_001",
                        "deployedTime": None,
                        "priority": 0,
                        "userId": 1,
                        "editTime": "2026-01-28T12:00:00",
                        "createTime": "2026-01-28T12:00:00",
                        "updateTime": "2026-01-28T12:00:00"
                    }
                ],
                "total": 1
            }
        }


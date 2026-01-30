from datetime import datetime
from pydantic import BaseModel, Field


class AppInfo(BaseModel):
    """
    应用信息（响应体中的应用数据部分）
    """
    id: int = Field(..., description="应用ID")
    appName: str | None = Field(None, description="应用名称")
    cover: str | None = Field(None, description="应用封面")
    initPrompt: str | None = Field(None, description="应用初始化的 prompt")
    codeGenType: str | None = Field(None, description="代码生成类型（枚举）")
    deployKey: str | None = Field(None, description="部署标识")
    deployedTime: datetime | None = Field(None, description="部署时间")
    priority: int = Field(0, description="优先级")
    userId: int = Field(..., description="创建用户id")
    editTime: datetime = Field(..., description="编辑时间")
    createTime: datetime = Field(..., description="创建时间")
    updateTime: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True  # 允许从 ORM 对象创建


class AppResponse(BaseModel):
    """
    应用信息响应体（单个应用）
    """
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: AppInfo = Field(..., description="应用信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "操作成功",
                "data": {
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
            }
        }


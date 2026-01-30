from pydantic import BaseModel, Field


class UpdateAppRequest(BaseModel):
    """
    更新应用信息请求体
    """
    appName: str | None = Field(None, max_length=256, description="应用名称")
    cover: str | None = Field(None, max_length=512, description="应用封面URL")
    initPrompt: str | None = Field(None, description="应用初始化的 prompt")
    codeGenType: str | None = Field(None, max_length=64, description="代码生成类型（枚举）")
    deployKey: str | None = Field(None, max_length=64, description="部署标识，需唯一")
    priority: int | None = Field(None, ge=0, description="优先级")
    
    class Config:
        json_schema_extra = {
            "example": {
                "appName": "更新后的应用名称",
                "cover": "https://example.com/new-cover.jpg",
                "initPrompt": "更新后的 prompt",
                "codeGenType": "static",
                "deployKey": "app_001",
                "priority": 1
            }
        }


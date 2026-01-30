from pydantic import BaseModel, Field


class CreateAppRequest(BaseModel):
    """
    创建应用请求体
    """
    appName: str | None = Field(None, max_length=256, description="应用名称，可选")
    cover: str | None = Field(None, max_length=512, description="应用封面URL，可选")
    initPrompt: str | None = Field(None, description="应用初始化的 prompt，可选")
    codeGenType: str | None = Field(None, max_length=64, description="代码生成类型（枚举），可选")
    deployKey: str | None = Field(None, max_length=64, description="部署标识，可选，需唯一")
    priority: int = Field(0, ge=0, description="优先级，默认为0")
    
    class Config:
        json_schema_extra = {
            "example": {
                "appName": "我的网站",
                "cover": "https://example.com/cover.jpg",
                "initPrompt": "创建一个网站",
                "codeGenType": "static",
                "deployKey": "app_001",
                "priority": 0
            }
        }


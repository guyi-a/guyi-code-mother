from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Integer, SmallInteger, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.db.database import Base


class App(Base):
    """
    应用模型
    对应数据库中的 app 表
    """
    __tablename__ = "app"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    
    # 应用基本信息
    appName = Column(String(256), nullable=True, comment="应用名称")
    cover = Column(String(512), nullable=True, comment="应用封面")
    initPrompt = Column(Text, nullable=True, comment="应用初始化的 prompt")
    codeGenType = Column(String(64), nullable=True, comment="代码生成类型（枚举）")
    deployKey = Column(String(64), nullable=True, unique=True, comment="部署标识")
    deployedTime = Column(DateTime, nullable=True, comment="部署时间")
    priority = Column(Integer, nullable=False, default=0, comment="优先级")
    
    # 用户关联
    userId = Column(BigInteger, nullable=False, comment="创建用户id")
    
    # 时间字段
    editTime = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="编辑时间")
    createTime = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updateTime = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    # 软删除标记
    isDelete = Column(SmallInteger, nullable=False, default=0, comment="是否删除")
    
    # 唯一约束和索引
    __table_args__ = (
        UniqueConstraint("deployKey", name="uk_deployKey"),
        Index("idx_appName", "appName"),
        Index("idx_userId", "userId"),
    )
    
    def __repr__(self):
        return f"<App(id={self.id}, appName='{self.appName}', userId={self.userId})>"


from datetime import datetime
from sqlalchemy import Column, BigInteger, String, SmallInteger, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """
    用户模型
    对应数据库中的 user 表
    """
    __tablename__ = "user"
    
    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    
    # 用户账号信息
    userAccount = Column(String(256), nullable=False, unique=True, comment="账号")
    userPassword = Column(String(512), nullable=False, comment="密码")
    userName = Column(String(256), nullable=True, comment="用户昵称")
    userAvatar = Column(String(1024), nullable=True, comment="用户头像")
    userProfile = Column(String(512), nullable=True, comment="用户简介")
    userRole = Column(String(256), nullable=False, default="user", comment="用户角色：user/admin")
    
    # 时间字段
    editTime = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="编辑时间")
    createTime = Column(DateTime, nullable=False, server_default=func.current_timestamp(), comment="创建时间")
    updateTime = Column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    # 软删除标记
    isDelete = Column(SmallInteger, nullable=False, default=0, comment="是否删除")
    
    # 唯一约束
    __table_args__ = (
        UniqueConstraint("userAccount", name="uk_userAccount"),
        Index("idx_userName", "userName"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, userAccount='{self.userAccount}', userName='{self.userName}')>"


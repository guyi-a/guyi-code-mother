from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.request.register_request import RegisterRequest
from app.schemas.request.update_user_request import UpdateUserRequest
from app.schemas.request.create_user_request import CreateUserRequest
from app.utils.security import get_password_hash


class UserCRUD:
    """
    用户 CRUD 操作
    """
    
    async def get_by_account(self, db: AsyncSession, user_account: str) -> User | None:
        """
        根据账号查询用户
        
        Args:
            db: 数据库会话
            user_account: 用户账号
            
        Returns:
            User | None: 用户对象，如果不存在则返回 None
        """
        result = await db.execute(
            select(User).filter(
                User.userAccount == user_account,
                User.isDelete == 0
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        """
        根据ID查询用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            User | None: 用户对象，如果不存在则返回 None
        """
        result = await db.execute(
            select(User).filter(
                User.id == user_id,
                User.isDelete == 0
            )
        )
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, register_data: RegisterRequest) -> User:
        """
        创建新用户（注册）
        
        Args:
            db: 数据库会话
            register_data: 注册请求数据
            
        Returns:
            User: 创建的用户对象
        """
        # 哈希密码
        hashed_password = get_password_hash(register_data.userPassword)
        
        # 创建用户对象
        new_user = User(
            userAccount=register_data.userAccount,
            userPassword=hashed_password,
            userName=register_data.userName,
            userAvatar=register_data.userAvatar,
            userProfile=register_data.userProfile,
            userRole="user",  # 默认角色为 user
            isDelete=0
        )
        
        # 添加到数据库
        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
        except Exception:
            await db.rollback()
            raise
        
        return new_user
    
    async def is_account_exists(self, db: AsyncSession, user_account: str) -> bool:
        """
        检查账号是否已存在
        
        Args:
            db: 数据库会话
            user_account: 用户账号
            
        Returns:
            bool: 如果账号已存在返回 True，否则返回 False
        """
        user = await self.get_by_account(db, user_account)
        return user is not None
    
    async def update(
        self, 
        db: AsyncSession, 
        user_id: int, 
        update_data: UpdateUserRequest
    ) -> User | None:
        """
        更新用户信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            update_data: 更新数据
            
        Returns:
            User | None: 更新后的用户对象，如果用户不存在则返回 None
        """
        # 查询用户
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
        
        # 更新字段（只更新提供的字段）
        if update_data.userName is not None:
            user.userName = update_data.userName
        if update_data.userAvatar is not None:
            user.userAvatar = update_data.userAvatar
        if update_data.userProfile is not None:
            user.userProfile = update_data.userProfile
        if update_data.userPassword is not None:
            user.userPassword = get_password_hash(update_data.userPassword)
        
        # 提交更改
        try:
            await db.commit()
            await db.refresh(user)
        except Exception:
            await db.rollback()
            raise
        
        return user
    
    async def create_by_admin(
        self, 
        db: AsyncSession, 
        create_data: CreateUserRequest
    ) -> User:
        """
        管理员创建用户
        
        Args:
            db: 数据库会话
            create_data: 创建用户数据
            
        Returns:
            User: 创建的用户对象
        """
        # 哈希密码
        hashed_password = get_password_hash(create_data.userPassword)
        
        # 创建用户对象
        new_user = User(
            userAccount=create_data.userAccount,
            userPassword=hashed_password,
            userName=create_data.userName,
            userAvatar=create_data.userAvatar,
            userProfile=create_data.userProfile,
            userRole=create_data.userRole,
            isDelete=0
        )
        
        # 添加到数据库
        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
        except Exception:
            await db.rollback()
            raise
        
        return new_user
    
    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        """
        软删除用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            bool: 删除成功返回 True，用户不存在返回 False
        """
        user = await self.get_by_id(db, user_id)
        if not user:
            return False
        
        # 软删除
        try:
            user.isDelete = 1
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        
        return True
    
    async def get_list(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        user_account: str | None = None,
        user_name: str | None = None
    ) -> list[User]:
        """
        获取用户列表（支持分页和筛选）
        
        Args:
            db: 数据库会话
            skip: 跳过数量（用于分页）
            limit: 返回数量限制
            user_account: 账号筛选（可选）
            user_name: 用户名筛选（可选）
            
        Returns:
            list[User]: 用户列表
        """
        query = select(User).filter(User.isDelete == 0)
        
        # 添加筛选条件
        if user_account:
            query = query.filter(User.userAccount.like(f"%{user_account}%"))
        if user_name:
            query = query.filter(User.userName.like(f"%{user_name}%"))
        
        # 添加排序和分页
        query = query.order_by(User.createTime.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        db: AsyncSession,
        user_account: str | None = None,
        user_name: str | None = None
    ) -> int:
        """
        统计用户数量
        
        Args:
            db: 数据库会话
            user_account: 账号筛选（可选）
            user_name: 用户名筛选（可选）
            
        Returns:
            int: 用户数量
        """
        query = select(func.count(User.id)).filter(User.isDelete == 0)
        
        # 添加筛选条件
        if user_account:
            query = query.filter(User.userAccount.like(f"%{user_account}%"))
        if user_name:
            query = query.filter(User.userName.like(f"%{user_name}%"))
        
        result = await db.execute(query)
        return result.scalar() or 0


# 创建 CRUD 实例
user_crud = UserCRUD()


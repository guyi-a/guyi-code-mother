from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.app import App
from app.schemas.request.create_app_request import CreateAppRequest
from app.schemas.request.update_app_request import UpdateAppRequest


class AppCRUD:
    """
    应用 CRUD 操作
    """
    
    async def get_by_id(self, db: AsyncSession, app_id: int) -> App | None:
        """
        根据ID查询应用
        
        Args:
            db: 数据库会话
            app_id: 应用ID
            
        Returns:
            App | None: 应用对象，如果不存在则返回 None
        """
        result = await db.execute(
            select(App).filter(
                App.id == app_id,
                App.isDelete == 0
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_deploy_key(self, db: AsyncSession, deploy_key: str) -> App | None:
        """
        根据部署标识查询应用
        
        Args:
            db: 数据库会话
            deploy_key: 部署标识
            
        Returns:
            App | None: 应用对象，如果不存在则返回 None
        """
        result = await db.execute(
            select(App).filter(
                App.deployKey == deploy_key,
                App.isDelete == 0
            )
        )
        return result.scalar_one_or_none()
    
    async def create(
        self, 
        db: AsyncSession, 
        create_data: CreateAppRequest,
        user_id: int
    ) -> App:
        """
        创建新应用
        
        Args:
            db: 数据库会话
            create_data: 创建应用数据
            user_id: 创建用户ID
            
        Returns:
            App: 创建的应用对象
        """
        # 创建应用对象
        new_app = App(
            appName=create_data.appName,
            cover=create_data.cover,
            initPrompt=create_data.initPrompt,
            codeGenType=create_data.codeGenType,
            deployKey=create_data.deployKey,
            priority=create_data.priority,
            userId=user_id,
            isDelete=0
        )
        
        # 添加到数据库
        try:
            db.add(new_app)
            await db.commit()
            await db.refresh(new_app)
        except Exception:
            await db.rollback()
            raise
        
        return new_app
    
    async def is_deploy_key_exists(self, db: AsyncSession, deploy_key: str) -> bool:
        """
        检查部署标识是否已存在
        
        Args:
            db: 数据库会话
            deploy_key: 部署标识
            
        Returns:
            bool: 如果部署标识已存在返回 True，否则返回 False
        """
        if not deploy_key:
            return False
        app = await self.get_by_deploy_key(db, deploy_key)
        return app is not None
    
    async def update(
        self, 
        db: AsyncSession, 
        app_id: int, 
        update_data: UpdateAppRequest
    ) -> App | None:
        """
        更新应用信息
        
        Args:
            db: 数据库会话
            app_id: 应用ID
            update_data: 更新数据
            
        Returns:
            App | None: 更新后的应用对象，如果应用不存在则返回 None
        """
        # 查询应用
        app = await self.get_by_id(db, app_id)
        if not app:
            return None
        
        # 更新字段（只更新提供的字段）
        if update_data.appName is not None:
            app.appName = update_data.appName
        if update_data.cover is not None:
            app.cover = update_data.cover
        if update_data.initPrompt is not None:
            app.initPrompt = update_data.initPrompt
        if update_data.codeGenType is not None:
            app.codeGenType = update_data.codeGenType
        if update_data.deployKey is not None:
            app.deployKey = update_data.deployKey
        if update_data.priority is not None:
            app.priority = update_data.priority
        
        # 提交更改
        try:
            await db.commit()
            await db.refresh(app)
        except Exception:
            await db.rollback()
            raise
        
        return app
    
    async def delete(self, db: AsyncSession, app_id: int) -> bool:
        """
        软删除应用
        
        Args:
            db: 数据库会话
            app_id: 应用ID
            
        Returns:
            bool: 删除成功返回 True，应用不存在返回 False
        """
        app = await self.get_by_id(db, app_id)
        if not app:
            return False
        
        # 软删除
        try:
            app.isDelete = 1
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        
        return True
    
    async def get_list(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 10,
        app_name: str | None = None,
        code_gen_type: str | None = None
    ) -> list[App]:
        """
        获取应用列表（支持分页和筛选）
        
        Args:
            db: 数据库会话
            user_id: 用户ID筛选（可选，如果提供则只返回该用户的应用）
            skip: 跳过数量（用于分页）
            limit: 返回数量限制
            app_name: 应用名称筛选（可选，模糊匹配）
            code_gen_type: 代码生成类型筛选（可选）
            
        Returns:
            list[App]: 应用列表
        """
        query = select(App).filter(App.isDelete == 0)
        
        # 添加筛选条件
        if user_id is not None:
            query = query.filter(App.userId == user_id)
        if app_name:
            query = query.filter(App.appName.like(f"%{app_name}%"))
        if code_gen_type:
            query = query.filter(App.codeGenType == code_gen_type)
        
        # 添加排序和分页（按优先级降序，然后按创建时间降序）
        query = query.order_by(App.priority.desc(), App.createTime.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        db: AsyncSession,
        user_id: int | None = None,
        app_name: str | None = None,
        code_gen_type: str | None = None
    ) -> int:
        """
        统计应用数量
        
        Args:
            db: 数据库会话
            user_id: 用户ID筛选（可选）
            app_name: 应用名称筛选（可选）
            code_gen_type: 代码生成类型筛选（可选）
            
        Returns:
            int: 应用数量
        """
        query = select(func.count(App.id)).filter(App.isDelete == 0)
        
        # 添加筛选条件
        if user_id is not None:
            query = query.filter(App.userId == user_id)
        if app_name:
            query = query.filter(App.appName.like(f"%{app_name}%"))
        if code_gen_type:
            query = query.filter(App.codeGenType == code_gen_type)
        
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def update_deployed_time(
        self,
        db: AsyncSession,
        app_id: int,
        deployed_time: datetime | None = None
    ) -> App | None:
        """
        更新应用的部署时间
        
        Args:
            db: 数据库会话
            app_id: 应用ID
            deployed_time: 部署时间，如果为None则使用当前时间
            
        Returns:
            App | None: 更新后的应用对象，如果应用不存在则返回 None
        """
        app = await self.get_by_id(db, app_id)
        if not app:
            return None
        
        app.deployedTime = deployed_time if deployed_time else datetime.now()
        
        try:
            await db.commit()
            await db.refresh(app)
        except Exception:
            await db.rollback()
            raise
        
        return app


# 创建 CRUD 实例
app_crud = AppCRUD()


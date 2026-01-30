import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, check_app_owner_or_admin
from app.core.exception import NotFoundException, BadRequestException, ForbiddenException
from app.core.config import settings
from app.models.user import User
from app.crud import app_crud
from app.schemas.request import CreateAppRequest, UpdateAppRequest
from app.schemas.response import (
    AppResponse,
    AppListResponse,
    DeleteAppResponse,
    AppInfo
)
from app.agent.service.agent_service import create_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apps", tags=["应用管理"])


@router.get("", response_model=AppListResponse, summary="获取应用列表")
async def get_apps(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    app_name: Optional[str] = Query(None, description="应用名称筛选（模糊匹配）"),
    code_gen_type: Optional[str] = Query(None, description="代码生成类型筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选（仅管理员可用）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用列表
    
    普通用户只能查看自己的应用，管理员可以查看任何人的应用。
    
    - **skip**: 跳过数量（用于分页）
    - **limit**: 返回数量限制（1-100）
    - **app_name**: 应用名称筛选（可选，模糊匹配）
    - **code_gen_type**: 代码生成类型筛选（可选）
    - **user_id**: 用户ID筛选（可选，仅管理员可用，用于查看指定用户的应用）
    """
    # 权限控制：普通用户只能查看自己的应用，管理员可以查看任何人的应用
    filter_user_id = None
    if current_user.userRole == "admin":
        # 管理员可以使用 user_id 参数查看指定用户的应用，如果不提供则查看所有应用
        filter_user_id = user_id
    else:
        # 普通用户只能查看自己的应用
        filter_user_id = current_user.id
    
    # 获取应用列表
    apps = await app_crud.get_list(
        db=db,
        user_id=filter_user_id,
        skip=skip,
        limit=limit,
        app_name=app_name,
        code_gen_type=code_gen_type
    )
    
    # 获取总数
    total = await app_crud.count(
        db=db,
        user_id=filter_user_id,
        app_name=app_name,
        code_gen_type=code_gen_type
    )
    
    # 转换为响应格式
    app_list = [
        AppInfo(
            id=app.id,
            appName=app.appName,
            cover=app.cover,
            initPrompt=app.initPrompt,
            codeGenType=app.codeGenType,
            deployKey=app.deployKey,
            deployedTime=app.deployedTime,
            priority=app.priority,
            userId=app.userId,
            editTime=app.editTime,
            createTime=app.createTime,
            updateTime=app.updateTime
        )
        for app in apps
    ]
    
    return AppListResponse(
        code=200,
        message="获取成功",
        data=app_list,
        total=total
    )


@router.post("", response_model=AppResponse, summary="创建应用")
async def create_app(
    create_data: CreateAppRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建应用
    
    需要登录后才能调用。应用将关联到当前登录用户。
    
    - **appName**: 应用名称（可选）
    - **cover**: 应用封面URL（可选）
    - **initPrompt**: 应用初始化的 prompt（可选）
    - **codeGenType**: 代码生成类型（可选）
    - **deployKey**: 部署标识（可选，需唯一）
    - **priority**: 优先级（默认0）
    """
    # 如果提供了 deployKey，检查是否已存在
    if create_data.deployKey:
        if await app_crud.is_deploy_key_exists(db, create_data.deployKey):
            raise BadRequestException("部署标识已存在，请使用其他标识")
    
    # 创建应用（使用当前用户的ID）
    new_app = await app_crud.create(db, create_data, user_id=current_user.id)
    
    # 构建响应数据
    app_info = AppInfo(
        id=new_app.id,
        appName=new_app.appName,
        cover=new_app.cover,
        initPrompt=new_app.initPrompt,
        codeGenType=new_app.codeGenType,
        deployKey=new_app.deployKey,
        deployedTime=new_app.deployedTime,
        priority=new_app.priority,
        userId=new_app.userId,
        editTime=new_app.editTime,
        createTime=new_app.createTime,
        updateTime=new_app.updateTime
    )
    
    return AppResponse(
        code=200,
        message="创建成功",
        data=app_info
    )


@router.get("/{app_id}", response_model=AppResponse, summary="获取应用详情")
async def get_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取应用详情
    
    只能查看自己的应用，管理员可以查看任何应用。
    
    - **app_id**: 应用ID
    """
    # 查询应用
    app = await app_crud.get_by_id(db, app_id)
    if not app:
        raise NotFoundException("应用不存在")
    
    # 检查权限：只能查看自己的应用，管理员可以查看任何应用
    check_app_owner_or_admin(app.userId, current_user)
    
    # 构建响应数据
    app_info = AppInfo(
        id=app.id,
        appName=app.appName,
        cover=app.cover,
        initPrompt=app.initPrompt,
        codeGenType=app.codeGenType,
        deployKey=app.deployKey,
        deployedTime=app.deployedTime,
        priority=app.priority,
        userId=app.userId,
        editTime=app.editTime,
        createTime=app.createTime,
        updateTime=app.updateTime
    )
    
    return AppResponse(
        code=200,
        message="获取成功",
        data=app_info
    )


@router.put("/{app_id}", response_model=AppResponse, summary="更新应用信息")
async def update_app(
    app_id: int,
    update_data: UpdateAppRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新应用信息
    
    只能更新自己的应用，管理员可以更新任何应用。
    
    - **app_id**: 应用ID
    - **appName**: 应用名称（可选）
    - **cover**: 应用封面URL（可选）
    - **initPrompt**: 应用初始化的 prompt（可选）
    - **codeGenType**: 代码生成类型（可选）
    - **deployKey**: 部署标识（可选，需唯一）
    - **priority**: 优先级（可选）
    """
    # 查询应用
    app = await app_crud.get_by_id(db, app_id)
    if not app:
        raise NotFoundException("应用不存在")
    
    # 检查权限：只能更新自己的应用，管理员可以更新任何应用
    check_app_owner_or_admin(app.userId, current_user)
    
    # 如果提供了新的 deployKey，检查是否与其他应用冲突（排除当前应用）
    if update_data.deployKey and update_data.deployKey != app.deployKey:
        existing_app = await app_crud.get_by_deploy_key(db, update_data.deployKey)
        if existing_app and existing_app.id != app_id:
            raise BadRequestException("部署标识已存在，请使用其他标识")
    
    # 更新应用信息
    updated_app = await app_crud.update(db, app_id, update_data)
    if not updated_app:
        raise NotFoundException("应用不存在")
    
    # 构建响应数据
    app_info = AppInfo(
        id=updated_app.id,
        appName=updated_app.appName,
        cover=updated_app.cover,
        initPrompt=updated_app.initPrompt,
        codeGenType=updated_app.codeGenType,
        deployKey=updated_app.deployKey,
        deployedTime=updated_app.deployedTime,
        priority=updated_app.priority,
        userId=updated_app.userId,
        editTime=updated_app.editTime,
        createTime=updated_app.createTime,
        updateTime=updated_app.updateTime
    )
    
    return AppResponse(
        code=200,
        message="更新成功",
        data=app_info
    )


@router.post("/{app_id}/generate", response_model=AppResponse, summary="生成应用代码")
async def generate_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成应用代码
    
    根据应用的 initPrompt 触发 Agent 生成应用代码。
    只能生成自己的应用。
    
    - **app_id**: 应用ID
    """
    # 查询应用
    app = await app_crud.get_by_id(db, app_id)
    if not app:
        raise NotFoundException("应用不存在")
    
    # 检查权限：只能生成自己的应用（管理员也只能生成自己的应用）
    if app.userId != current_user.id:
        raise ForbiddenException("只能生成自己的应用")
    
    # 检查是否有 initPrompt
    if not app.initPrompt:
        raise BadRequestException("应用未设置初始化 prompt，请先设置 initPrompt")
    
    # 检查是否有 appName（用于构建工作区路径）
    if not app.appName:
        raise BadRequestException("应用未设置名称，请先设置 appName")
    
    try:
        # 构建工作区路径
        user_id_str = str(current_user.id)
        app_id_str = str(app.id)
        workspace_path = settings.get_workspace_path(user_id_str, app_id_str, app.appName)
        
        # 创建 Agent 服务
        agent_service = create_agent_service(
            workspace_path=workspace_path,
            user_id=user_id_str,
            app_id=app_id_str,
            app_name=app.appName,
            debug=settings.DEBUG
        )
        
        if not agent_service.is_available():
            raise BadRequestException("Agent服务暂不可用，请检查配置")
        
        # 使用 initPrompt 作为消息调用 Agent
        messages = [
            {
                "role": "user",
                "content": app.initPrompt
            }
        ]
        
        # 调用 Agent 生成代码
        ai_reply = await agent_service.ainvoke(messages)
        
        # 更新应用的部署时间
        from datetime import datetime
        updated_app = await app_crud.update_deployed_time(db, app_id, datetime.now())
        
        if not updated_app:
            raise NotFoundException("应用不存在")
        
        # 构建响应数据
        app_info = AppInfo(
            id=updated_app.id,
            appName=updated_app.appName,
            cover=updated_app.cover,
            initPrompt=updated_app.initPrompt,
            codeGenType=updated_app.codeGenType,
            deployKey=updated_app.deployKey,
            deployedTime=updated_app.deployedTime,
            priority=updated_app.priority,
            userId=updated_app.userId,
            editTime=updated_app.editTime,
            createTime=updated_app.createTime,
            updateTime=updated_app.updateTime
        )
        
        return AppResponse(
            code=200,
            message="应用代码生成成功",
            data=app_info
        )
        
    except ValueError as e:
        logger.error(f"生成应用代码失败: {e}", exc_info=True)
        raise BadRequestException(f"工作区路径配置错误: {str(e)}")
    except Exception as e:
        logger.error(f"生成应用代码失败: {e}", exc_info=True)
        raise BadRequestException(f"生成应用代码失败: {str(e)}")


@router.delete("/{app_id}", response_model=DeleteAppResponse, summary="删除应用")
async def delete_app(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除应用（软删除）
    
    只能删除自己的应用，管理员可以删除任何应用。
    
    - **app_id**: 应用ID
    """
    # 查询应用
    app = await app_crud.get_by_id(db, app_id)
    if not app:
        raise NotFoundException("应用不存在")
    
    # 检查权限：只能删除自己的应用，管理员可以删除任何应用
    check_app_owner_or_admin(app.userId, current_user)
    
    # 删除应用（软删除）
    success = await app_crud.delete(db, app_id)
    if not success:
        raise NotFoundException("应用不存在")
    
    return DeleteAppResponse(
        code=200,
        message="删除成功"
    )


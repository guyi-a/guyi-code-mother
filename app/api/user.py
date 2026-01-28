from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, require_admin, check_owner_or_admin
from app.core.exception import NotFoundException, BadRequestException
from app.models.user import User
from app.crud import user_crud
from app.schemas.request import CreateUserRequest, UpdateUserRequest
from app.schemas.response import (
    UserResponse, 
    UserListResponse, 
    DeleteUserResponse,
    UserInfo
)

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的信息
    
    需要登录后才能调用。
    """
    user_info = UserInfo(
        id=current_user.id,
        userAccount=current_user.userAccount,
        userName=current_user.userName,
        userAvatar=current_user.userAvatar,
        userProfile=current_user.userProfile,
        userRole=current_user.userRole,
        createTime=current_user.createTime
    )
    
    return UserResponse(
        code=200,
        message="获取成功",
        data=user_info
    )


@router.get("", response_model=UserListResponse, summary="获取用户列表")
async def get_users(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    user_account: Optional[str] = Query(None, description="账号筛选（模糊匹配）"),
    user_name: Optional[str] = Query(None, description="用户名筛选（模糊匹配）"),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户列表
    
    需要管理员权限。
    
    - **skip**: 跳过数量（用于分页）
    - **limit**: 返回数量限制（1-100）
    - **user_account**: 账号筛选（可选，模糊匹配）
    - **user_name**: 用户名筛选（可选，模糊匹配）
    """
    # 获取用户列表
    users = await user_crud.get_list(
        db=db,
        skip=skip,
        limit=limit,
        user_account=user_account,
        user_name=user_name
    )
    
    # 获取总数
    total = await user_crud.count(
        db=db,
        user_account=user_account,
        user_name=user_name
    )
    
    # 转换为响应格式
    user_list = [
        UserInfo(
            id=user.id,
            userAccount=user.userAccount,
            userName=user.userName,
            userAvatar=user.userAvatar,
            userProfile=user.userProfile,
            userRole=user.userRole,
            createTime=user.createTime
        )
        for user in users
    ]
    
    return UserListResponse(
        code=200,
        message="获取成功",
        data=user_list,
        total=total
    )


@router.get("/{user_id}", response_model=UserResponse, summary="获取单个用户信息")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个用户信息
    
    本人或管理员可以查看。
    
    - **user_id**: 用户ID
    """
    # 检查权限：本人或管理员
    check_owner_or_admin(user_id, current_user)
    
    # 查询用户
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    
    user_info = UserInfo(
        id=user.id,
        userAccount=user.userAccount,
        userName=user.userName,
        userAvatar=user.userAvatar,
        userProfile=user.userProfile,
        userRole=user.userRole,
        createTime=user.createTime
    )
    
    return UserResponse(
        code=200,
        message="获取成功",
        data=user_info
    )


@router.post("", response_model=UserResponse, summary="创建用户")
async def create_user(
    create_data: CreateUserRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    创建用户
    
    需要管理员权限。
    """
    # 检查账号是否已存在
    if await user_crud.is_account_exists(db, create_data.userAccount):
        raise BadRequestException("账号已存在")
    
    # 验证角色
    if create_data.userRole not in ["user", "admin"]:
        raise BadRequestException("用户角色只能是 user 或 admin")
    
    # 创建用户
    new_user = await user_crud.create_by_admin(db, create_data)
    
    user_info = UserInfo(
        id=new_user.id,
        userAccount=new_user.userAccount,
        userName=new_user.userName,
        userAvatar=new_user.userAvatar,
        userProfile=new_user.userProfile,
        userRole=new_user.userRole,
        createTime=new_user.createTime
    )
    
    return UserResponse(
        code=200,
        message="创建成功",
        data=user_info
    )


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    update_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息
    
    本人或管理员可以更新。
    
    - **user_id**: 用户ID
    """
    # 检查权限：本人或管理员
    check_owner_or_admin(user_id, current_user)
    
    # 更新用户信息
    updated_user = await user_crud.update(db, user_id, update_data)
    if not updated_user:
        raise NotFoundException("用户不存在")
    
    user_info = UserInfo(
        id=updated_user.id,
        userAccount=updated_user.userAccount,
        userName=updated_user.userName,
        userAvatar=updated_user.userAvatar,
        userProfile=updated_user.userProfile,
        userRole=updated_user.userRole,
        createTime=updated_user.createTime
    )
    
    return UserResponse(
        code=200,
        message="更新成功",
        data=user_info
    )


@router.delete("/{user_id}", response_model=DeleteUserResponse, summary="删除用户")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（软删除）
    
    需要管理员权限。
    
    - **user_id**: 用户ID
    """
    # 检查用户是否存在
    user = await user_crud.get_by_id(db, user_id)
    if not user:
        raise NotFoundException("用户不存在")
    
    # 删除用户
    success = await user_crud.delete(db, user_id)
    if not success:
        raise NotFoundException("用户不存在")
    
    return DeleteUserResponse(
        code=200,
        message="删除成功"
    )


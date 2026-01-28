from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user
from app.core.exception import BadRequestException, UnauthorizedException
from app.models.user import User
from app.crud import user_crud
from app.schemas.request import RegisterRequest, LoginRequest
from app.schemas.response import RegisterResponse, LoginResponse, LogoutResponse, UserInfo
from app.utils.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=RegisterResponse, summary="用户注册")
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口
    
    - **userAccount**: 账号（4-256个字符）
    - **userPassword**: 密码（6-512个字符）
    - **checkPassword**: 确认密码（必须与密码一致）
    - **userName**: 用户昵称（可选）
    - **userAvatar**: 用户头像URL（可选）
    - **userProfile**: 用户简介（可选）
    """
    # 检查账号是否已存在
    if await user_crud.is_account_exists(db, register_data.userAccount):
        raise BadRequestException("账号已存在")
    
    # 创建新用户
    new_user = await user_crud.create(db, register_data)
    
    # 构建响应数据
    user_info = UserInfo(
        id=new_user.id,
        userAccount=new_user.userAccount,
        userName=new_user.userName,
        userAvatar=new_user.userAvatar,
        userProfile=new_user.userProfile,
        userRole=new_user.userRole,
        createTime=new_user.createTime
    )
    
    return RegisterResponse(
        code=200,
        message="注册成功",
        data=user_info
    )


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口
    
    - **userAccount**: 账号
    - **userPassword**: 密码
    """
    # 查询用户
    user = await user_crud.get_by_account(db, login_data.userAccount)
    
    if not user:
        raise UnauthorizedException("账号或密码错误")
    
    # 验证密码
    if not verify_password(login_data.userPassword, user.userPassword):
        raise UnauthorizedException("账号或密码错误")
    
    # 生成访问令牌
    token = create_access_token(data={"sub": str(user.id), "userAccount": user.userAccount})
    
    # 构建响应数据
    user_info = UserInfo(
        id=user.id,
        userAccount=user.userAccount,
        userName=user.userName,
        userAvatar=user.userAvatar,
        userProfile=user.userProfile,
        userRole=user.userRole,
        createTime=user.createTime
    )
    
    return LoginResponse(
        code=200,
        message="登录成功",
        data=user_info,
        token=token
    )


@router.post("/logout", response_model=LogoutResponse, summary="用户下线")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    用户下线接口
    
    需要登录后才能调用。
    
    注意：由于使用 JWT token，服务端无法主动使 token 失效。
    客户端需要删除本地存储的 token。
    如果需要真正的下线功能，建议使用 Redis 存储 token 黑名单。
    """
    return LogoutResponse(
        code=200,
        message="退出成功"
    )


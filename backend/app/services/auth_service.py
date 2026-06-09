"""
AI4Edu 认证 Service
处理用户注册、登录、Token刷新等业务逻辑
"""
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.core.exceptions import UnauthorizedException, ValidationException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
)


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession):
        """初始化认证服务"""
        self.db = db

    async def authenticate(self, request: LoginRequest, client_ip: Optional[str] = None) -> LoginResponse:
        """
        用户认证

        Args:
            request: 登录请求
            client_ip: 客户端IP

        Returns:
            LoginResponse: 登录响应

        Raises:
            UnauthorizedException: 邮箱或密码错误
        """
        # 查询用户
        result = await self.db.execute(select(User).where(User.email == request.email))
        user = result.scalars().first()

        if not user:
            raise UnauthorizedException(message="邮箱或密码错误")

        # 验证密码
        if not verify_password(request.password, user.password_hash):
            raise UnauthorizedException(message="邮箱或密码错误")

        # 检查账号状态
        if not user.is_active:
            raise UnauthorizedException(message="账号已禁用，请联系管理员")

        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        if client_ip:
            user.last_login_ip = client_ip
        await self.db.commit()

        # 生成 Token
        access_token, refresh_token = self._create_tokens(user)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user_id=user.id,
            nickname=user.nickname,
            role=user.role,
            avatar_url=user.avatar_url,
            onboarding_completed=user.onboarding_completed,
        )

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        """
        用户注册

        Args:
            request: 注册请求

        Returns:
            RegisterResponse: 注册响应

        Raises:
            ValidationException: 邮箱已存在
        """
        # 检查邮箱唯一性
        existing = await self.db.execute(select(User).where(User.email == request.email))
        if existing.scalars().first():
            raise ValidationException(message="该邮箱已注册")

        # 验证角色：教师需要邀请码
        if request.role == "teacher" and not request.invite_code:
            raise ValidationException(message="教师注册需要邀请码")

        # 验证邀请码（简单实现，生产环境应查数据库）
        if request.invite_code and request.invite_code != settings.SECRET_KEY[:8]:
            raise ValidationException(message="邀请码无效")

        # 创建用户
        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            nickname=request.nickname,
            role=request.role,
            school=request.school,
            grade=request.grade,
            default_scene="classroom",
            locale="zh-CN",
            onboarding_completed=False,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 生成 Token
        access_token, refresh_token = self._create_tokens(user)

        return RegisterResponse(
            user_id=user.id,
            email=user.email,
            nickname=user.nickname,
            access_token=access_token,
            refresh_token=refresh_token,
            onboarding_completed=user.onboarding_completed,
        )

    async def refresh_access_token(self, request: RefreshRequest) -> RefreshResponse:
        """
        刷新 Access Token

        Args:
            request: 刷新Token请求

        Returns:
            RefreshResponse: 新的Token

        Raises:
            UnauthorizedException: Refresh Token无效
        """
        payload = decode_refresh_token(request.refresh_token)
        if payload is None:
            raise UnauthorizedException(message="Refresh Token无效或已过期")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(message="Token格式错误")

        # 检查用户是否存在且活跃
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()
        if not user or not user.is_active:
            raise UnauthorizedException(message="用户不存在或已禁用")

        new_access_token = create_access_token(data={"sub": user.id, "role": user.role})
        new_refresh_token = create_refresh_token(data={"sub": user.id})

        return RefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def get_current_user_info(self, user_id: int) -> dict:
        """
        获取当前用户信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 用户信息

        Raises:
            UnauthorizedException: 用户不存在
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if not user:
            raise UnauthorizedException(message="用户不存在")

        return {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "role": user.role,
            "grade": user.grade,
            "school": user.school,
            "default_scene": user.default_scene,
            "locale": user.locale,
            "onboarding_completed": user.onboarding_completed,
            "created_at": user.created_at,
        }

    def _create_tokens(self, user: User) -> Tuple[str, str]:
        """
        为用户生成 Access Token 和 Refresh Token

        Args:
            user: 用户对象

        Returns:
            Tuple[str, str]: (access_token, refresh_token)
        """
        token_data = {
            "sub": user.id,
            "role": user.role,
        }
        if user.tenant_id:
            token_data["tenant_id"] = user.tenant_id

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": user.id})
        return access_token, refresh_token

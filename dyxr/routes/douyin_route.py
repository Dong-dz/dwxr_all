from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import (
    get_current_user, get_client_ip, get_user_agent, auth_middleware
)
from schemas.userSche import (
    DouyinLoginRequest, DouyinLoginResponse,
    UserResponse, UserProfile, UserUpdate,
    RefreshTokenResponse, LogoutResponse, ErrorResponse
)
from services.douyin_login_service import douyin_login_service
from services.user_service import user_service
from utils.jwt_utils import mask_sensitive_data
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["用户管理"],
    responses={
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        401: {"model": ErrorResponse, "description": "未授权"},
        403: {"model": ErrorResponse, "description": "禁止访问"},
        404: {"model": ErrorResponse, "description": "资源不存在"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)


@router.post("/apps/login", response_model=DouyinLoginResponse, summary="抖音小程序登录")
async def douyin_mini_app_login(
    request: Request,
    login_data: DouyinLoginRequest,
    db: Session = Depends(get_db)
):
    """
    抖音小程序登录接口

    - **code**: 小程序调用tt.login()获取的临时登录凭证

    返回用户令牌和基本信息
    """
    try:
        # 获取客户端信息
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # 检查请求频率限制
        if not await auth_middleware.check_rate_limit(ip_address):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )

        # 处理登录
        response, error = await douyin_login_service.process_login(
            db=db,
            login_request=login_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务暂时不可用"
        )


@router.get("/profile", response_model=UserProfile, summary="获取用户资料")
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的详细资料

    需要Bearer Token认证
    """
    try:
        openid = current_user.get("openid")
        if not openid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户凭证"
            )

        profile = user_service.get_user_profile(db, openid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在或已被禁用"
            )

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败"
        )


@router.put("/profile", response_model=UserResponse, summary="更新用户资料")
async def update_user_profile(
    user_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户的资料信息

    需要Bearer Token认证
    """
    try:
        openid = current_user.get("openid")
        if not openid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户凭证"
            )

        updated_user = user_service.update_user(db, openid, user_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return UserResponse.from_orm(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户资料失败"
        )


@router.post("/logout", response_model=LogoutResponse, summary="用户登出")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出，清除会话

    需要Bearer Token认证
    """
    try:
        openid = current_user.get("openid")
        token = current_user.get("token")

        if not openid or not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的用户凭证"
            )

        success = douyin_login_service.logout_user(db, openid, token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="登出失败"
            )

        return LogoutResponse()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出服务暂时不可用"
        )


@router.post("/refresh-token", response_model=RefreshTokenResponse, summary="刷新令牌")
async def refresh_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    刷新用户访问令牌

    需要Bearer Token认证
    """
    try:
        token = current_user.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )

        new_token = douyin_login_service.refresh_user_token(token)
        if not new_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="令牌刷新失败"
            )

        return RefreshTokenResponse(token=new_token)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新服务暂时不可用"
        )


@router.get("/", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    skip: int = 0,
    limit: int = 10,
    status: int = None,
    user_type: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户列表（管理员功能）

    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数限制
    - **status**: 用户状态过滤
    - **user_type**: 用户类型过滤

    需要管理员权限
    """
    try:
        # 检查权限（这里简化处理，实际应该检查用户角色）
        session_data = current_user.get("session_data", {})
        user_quanxian = session_data.get("quanxian")

        if user_quanxian != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

        users = user_service.get_users(
            db=db,
            skip=skip,
            limit=min(limit, 100),  # 限制最大返回数量
            status=status,
            user_type=user_type
        )

        # 脱敏处理
        result = []
        for user in users:
            user_response = UserResponse.from_orm(user)
            user_response.openid = mask_sensitive_data(user_response.openid)
            result.append(user_response)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/search", response_model=List[UserResponse], summary="搜索用户")
async def search_users(
    keyword: str,
    skip: int = 0,
    limit: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    搜索用户（管理员功能）

    - **keyword**: 搜索关键词
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数限制

    需要管理员权限
    """
    try:
        # 检查权限
        session_data = current_user.get("session_data", {})
        user_quanxian = session_data.get("quanxian")

        if user_quanxian != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

        if not keyword or len(keyword.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="搜索关键词不能为空"
            )

        users = user_service.search_users(
            db=db,
            keyword=keyword.strip(),
            skip=skip,
            limit=min(limit, 100)
        )

        # 脱敏处理
        result = []
        for user in users:
            user_response = UserResponse.from_orm(user)
            user_response.openid = mask_sensitive_data(user_response.openid)
            result.append(user_response)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索用户失败"
        )


@router.delete("/{openid}", summary="删除用户")
async def delete_user(
    openid: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除指定用户（管理员功能）

    - **openid**: 要删除的用户openid

    需要管理员权限
    """
    try:
        # 检查权限
        session_data = current_user.get("session_data", {})
        user_quanxian = session_data.get("quanxian")

        if user_quanxian != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

        # 不允许删除自己
        current_openid = current_user.get("openid")
        if current_openid == openid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )

        success = user_service.delete_user(db, openid)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return {"message": "用户删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

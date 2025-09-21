"""
抖音小程序用户管理API路由
"""
import uuid
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlmodel import Session

from app.api.deps_douyin import (
    SessionDep, RedisDep, CurrentDouyinUser, CurrentAdminUser,
    get_client_ip, get_user_agent, check_rate_limit
)
from app.models import (
    DouyinLoginRequest, DouyinLoginResponse, DouyinUserPublic, DouyinUserUpdate,
    RefreshTokenResponse, LogoutResponse, Message
)
from app.services.douyin_login_service import douyin_login_service
from app.services.douyin_crud import douyin_user_crud

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/douyin",
    tags=["抖音小程序"],
)

@router.post("/login", response_model=DouyinLoginResponse, summary="抖音小程序登录")
async def douyin_login(
    request: Request,
    login_data: DouyinLoginRequest,
    session: SessionDep,
    redis_client: RedisDep
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
        if not check_rate_limit(redis_client, ip_address):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )

        # 处理登录
        response, error = await douyin_login_service.process_login(
            session=session,
            redis_client=redis_client,
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


@router.get("/profile", response_model=DouyinUserPublic, summary="获取用户资料")
async def get_user_profile(
    current_user: CurrentDouyinUser,
    session: SessionDep
):
    """
    获取当前用户的详细资料

    需要Bearer Token认证
    """
    try:
        user = current_user["user"]
        return DouyinUserPublic.model_validate(user)

    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户资料失败"
        )


@router.put("/profile", response_model=DouyinUserPublic, summary="更新用户资料")
async def update_user_profile(
    user_data: DouyinUserUpdate,
    current_user: CurrentDouyinUser,
    session: SessionDep
):
    """
    更新当前用户的资料信息

    需要Bearer Token认证
    """
    try:
        user = current_user["user"]
        
        updated_user = douyin_user_crud.update(session, user, user_data)
        return DouyinUserPublic.model_validate(updated_user)

    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户资料失败"
        )


@router.post("/logout", response_model=LogoutResponse, summary="用户登出")
async def logout(
    current_user: CurrentDouyinUser,
    session: SessionDep,
    redis_client: RedisDep
):
    """
    用户登出，清除会话

    需要Bearer Token认证
    """
    try:
        openid = current_user["openid"]
        token = current_user["token"]

        success = douyin_login_service.logout_user(session, redis_client, openid, token)
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
    current_user: CurrentDouyinUser,
    redis_client: RedisDep
):
    """
    刷新用户访问令牌

    需要Bearer Token认证
    """
    try:
        token = current_user["token"]
        
        new_token = douyin_login_service.refresh_user_token(redis_client, token)
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


@router.get("/users", response_model=List[DouyinUserPublic], summary="获取用户列表")
async def get_users(
    session: SessionDep,
    current_user: CurrentAdminUser,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制"),
    status: Optional[bool] = Query(None, description="用户状态过滤"),
    user_type: Optional[str] = Query(None, description="用户类型过滤")
):
    """
    获取用户列表（管理员功能）

    需要管理员权限
    """
    try:
        users = douyin_user_crud.get_multi(
            session=session,
            skip=skip,
            limit=limit,
            status=status,
            user_type=user_type
        )

        # 脱敏处理
        result = []
        for user in users:
            user_public = DouyinUserPublic.model_validate(user)
            # 对openid进行脱敏
            user_public.openid = douyin_login_service.mask_sensitive_data(user_public.openid)
            result.append(user_public)

        return result

    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/users/search", response_model=List[DouyinUserPublic], summary="搜索用户")
async def search_users(
    session: SessionDep,
    current_user: CurrentAdminUser,
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制")
):
    """
    搜索用户（管理员功能）

    需要管理员权限
    """
    try:
        users = douyin_user_crud.search(
            session=session,
            keyword=keyword.strip(),
            skip=skip,
            limit=limit
        )

        # 脱敏处理
        result = []
        for user in users:
            user_public = DouyinUserPublic.model_validate(user)
            user_public.openid = douyin_login_service.mask_sensitive_data(user_public.openid)
            result.append(user_public)

        return result

    except Exception as e:
        logger.error(f"Search users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索用户失败"
        )


@router.delete("/users/{user_id}", response_model=Message, summary="删除用户")
async def delete_user(
    user_id: str,
    session: SessionDep,
    current_user: CurrentAdminUser
):
    """
    删除指定用户（管理员功能）

    需要管理员权限
    """
    try:
        # 不允许删除自己
        current_user_obj = current_user["user"]
        if str(current_user_obj.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账户"
            )

        # 查找要删除的用户
        try:
            user_uuid = uuid.UUID(user_id)
            user = douyin_user_crud.get_by_id(session, user_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的用户ID格式"
            )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        success = douyin_user_crud.delete(session, user)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户失败"
            )

        return Message(message="用户删除成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )
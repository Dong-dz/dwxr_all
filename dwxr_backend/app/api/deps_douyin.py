"""
抖音小程序相关的依赖注入
"""
import uuid
import logging
from collections.abc import Generator
from typing import Annotated, Union, Dict, Any

import jwt
import redis
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, DouyinUser, DouyinLoginLog

logger = logging.getLogger(__name__)

# 自定义Bearer认证器
douyin_bearer = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]

# Redis连接
def get_redis_client():
    """获取Redis客户端"""
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # 测试连接
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="会话服务暂时不可用"
        )

RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]

def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    """获取用户代理"""
    return request.headers.get("User-Agent", "unknown")

def verify_jwt_token(token: str) -> Union[Dict[str, Any], None]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except InvalidTokenError:
        return None

def get_session_data(redis_client: redis.Redis, token: str) -> Union[Dict[str, Any], None]:
    """从Redis获取会话数据"""
    try:
        session_key = f"session:{token}"
        session_data = redis_client.hgetall(session_key)
        
        if not session_data:
            return None
        
        return session_data
    except Exception as e:
        logger.error(f"Failed to get session data: {str(e)}")
        return None

def check_rate_limit(redis_client: redis.Redis, ip_address: str) -> bool:
    """检查请求频率限制"""
    try:
        rate_key = f"rate_limit:{ip_address}"
        current_requests = redis_client.get(rate_key)
        
        if current_requests is None:
            # 首次请求
            redis_client.setex(rate_key, settings.RATE_LIMIT_WINDOW, 1)
            return True
        
        current_count = int(current_requests)
        if current_count >= settings.LOGIN_RATE_LIMIT:
            return False
        
        # 增加计数
        redis_client.incr(rate_key)
        return True
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {str(e)}")
        # 出错时允许请求
        return True

def get_current_douyin_user(
    session: SessionDep,
    redis_client: RedisDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(douyin_bearer)]
) -> Dict[str, Any]:
    """获取当前抖音用户信息"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # 验证JWT令牌
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取会话数据
    session_data = get_session_data(redis_client, token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    openid = session_data.get("openid")
    if not openid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的会话数据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证用户是否存在且活跃
    statement = select(DouyinUser).where(DouyinUser.openid == openid)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    # 返回用户信息和会话数据
    return {
        "token": token,
        "openid": openid,
        "unionid": session_data.get("unionid"),
        "user": user,
        "session_data": session_data
    }

CurrentDouyinUser = Annotated[Dict[str, Any], Depends(get_current_douyin_user)]

def get_current_admin_user(current_user: CurrentDouyinUser) -> Dict[str, Any]:
    """验证当前用户是否为管理员"""
    session_data = current_user.get("session_data", {})
    permission = session_data.get("permission", "user")
    
    if permission not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user

CurrentAdminUser = Annotated[Dict[str, Any], Depends(get_current_admin_user)]

def create_login_log(
    session: Session,
    openid: str,
    ip_address: str,
    user_agent: str,
    login_result: int = 1,
    error_message: Union[str, None] = None
) -> None:
    """创建登录日志"""
    try:
        login_log = DouyinLoginLog(
            openid=openid,
            ip_address=ip_address,
            user_agent=user_agent,
            login_result=login_result,
            error_message=error_message
        )
        session.add(login_log)
        session.commit()
        logger.info(f"Login log created for user: {openid}")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create login log: {str(e)}")
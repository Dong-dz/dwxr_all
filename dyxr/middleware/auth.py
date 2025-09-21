from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import asyncio
import redis
from utils.jwt_utils import JWTManager
from database import get_redis
from config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer令牌方案
security = HTTPBearer()


class AuthMiddleware:
    """认证中间件"""

    def __init__(self):
        self.redis_client = None

    def get_redis_client(self):
        """获取Redis客户端"""
        if not self.redis_client:
            self.redis_client = get_redis()
        return self.redis_client

    async def get_redis_client_with_retry(self, max_retries: int = 3):
        """获取Redis客户端（带重试机制）"""
        for attempt in range(max_retries):
            try:
                if not self.redis_client:
                    self.redis_client = get_redis()
                # 测试连接
                self.redis_client.ping()
                return self.redis_client
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("Redis connection failed after all retries")
                    return None
                await asyncio.sleep(0.5 * (attempt + 1))
        return None

    async def verify_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证会话（增强版）

        Args:
            token: JWT令牌

        Returns:
            会话数据
        """
        try:
            # 验证JWT令牌
            payload = JWTManager.verify_token(token)
            if not payload:
                logger.info("JWT token verification failed")
                return None

            # 获取Redis客户端（带重试）
            redis_client = await self.get_redis_client_with_retry()
            if not redis_client:
                # Redis不可用时的降级处理
                logger.warning("Redis unavailable, using JWT-only verification")
                return {
                    "token": token,
                    "openid": payload.get("openid"),
                    "unionid": payload.get("unionid"),
                    "session_data": {},
                    "fallback_mode": True
                }

            # 从Redis检查会话
            session_key = f"session:{token}"
            try:
                session_data = redis_client.hgetall(session_key)
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                # Redis连接错误时的降级处理
                return {
                    "token": token,
                    "openid": payload.get("openid"),
                    "unionid": payload.get("unionid"),
                    "session_data": {},
                    "fallback_mode": True
                }

            if not session_data:
                logger.info(f"Session not found in Redis: {session_key}")
                return None

            # 更新最后活跃时间
            try:
                user_active_key = f"user:active:{payload.get('openid')}"
                redis_client.setex(
                    user_active_key,
                    settings.user_active_expire_seconds,
                    str(int(datetime.utcnow().timestamp()))
                )
            except Exception as e:
                logger.warning(f"Failed to update user activity: {e}")

            return {
                "token": token,
                "openid": payload.get("openid"),
                "unionid": payload.get("unionid"),
                "session_data": session_data
            }

        except Exception as e:
            logger.error(f"Unexpected error in session verification: {str(e)}")
            return None

    async def check_rate_limit(self, ip_address: str) -> bool:
        """
        检查请求频率限制（异步增强版）

        Args:
            ip_address: IP地址

        Returns:
            是否允许请求
        """
        try:
            redis_client = await self.get_redis_client_with_retry()
            if not redis_client:
                logger.warning("Redis unavailable for rate limiting, allowing request")
                return True

            rate_limit_key = f"rate_limit:{ip_address}"

            # 使用Redis pipeline提高性能
            pipe = redis_client.pipeline()
            pipe.get(rate_limit_key)
            pipe.ttl(rate_limit_key)

            try:
                current_count, ttl = pipe.execute()
            except redis.ConnectionError as e:
                logger.error(f"Redis pipeline execution failed: {e}")
                return True  # Redis错误时允许请求

            if current_count is None:
                redis_client.setex(rate_limit_key, settings.rate_limit_window, 1)
                return True

            # 安全地转换为int
            try:
                count_value = int(current_count)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid rate limit counter value: {current_count}, error: {e}")
                redis_client.delete(rate_limit_key)  # 清除无效数据
                return True

            if count_value >= settings.login_rate_limit:
                logger.warning(f"Rate limit exceeded for IP: {ip_address}")
                return False

            redis_client.incr(rate_limit_key)
            return True

        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            return True  # 出错时允许请求


# 全局认证中间件实例
auth_middleware = AuthMiddleware()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    获取当前用户信息（依赖注入）- 增强版

    Args:
        credentials: HTTP认证凭据

    Returns:
        用户信息

    Raises:
        HTTPException: 认证失败
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        session_info = await auth_middleware.verify_session(credentials.credentials)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return session_info

    except HTTPException:
        raise  # 重新抛出HTTP异常
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authentication error"
        )


async def get_current_user_optional(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    获取当前用户信息（可选）

    Args:
        request: HTTP请求对象

    Returns:
        用户信息或None
    """
    authorization: Optional[str] = request.headers.get("Authorization")
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None

    if not token:
        return None

    try:
        return await auth_middleware.verify_session(token)
    except Exception as e:
        logger.error(f"Error in get_current_user_optional: {str(e)}")
        return None


def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址

    Args:
        request: HTTP请求对象

    Returns:
        IP地址
    """
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 返回直接连接的IP
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """
    获取用户代理字符串

    Args:
        request: HTTP请求对象

    Returns:
        用户代理字符串
    """
    return request.headers.get("User-Agent", "unknown")

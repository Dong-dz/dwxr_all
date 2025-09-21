"""
抖音小程序登录服务
"""
import httpx
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, Union

import jwt
import redis
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    DouyinUser, DouyinUserCreate, DouyinLoginRequest, DouyinLoginResponse,
    DouyinUserPublic, RefreshTokenResponse, LogoutResponse
)
from app.api.deps_douyin import create_login_log

logger = logging.getLogger(__name__)

class DouyinLoginService:
    """抖音小程序登录服务"""
    
    def __init__(self):
        self.auth_url = settings.DOUYIN_AUTH_URL
        self.app_id = settings.DOUYIN_APP_ID
        self.app_secret = settings.DOUYIN_APP_SECRET
    
    async def exchange_code_for_session(self, code: str) -> Optional[Dict[str, Any]]:
        """
        使用code换取抖音用户信息
        
        Args:
            code: 小程序端调用tt.login()获取的临时登录凭证
            
        Returns:
            抖音返回的用户信息
        """
        try:
            params = {
                "appid": self.app_id,
                "secret": self.app_secret,
                "code": code
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.auth_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # 检查抖音API返回的错误
                if data.get("error"):
                    logger.error(f"Douyin API error: {data}")
                    return None
                
                # 验证必要字段
                if not data.get("openid"):
                    logger.error(f"Missing openid in response: {data}")
                    return None
                
                return data
                
        except httpx.TimeoutException:
            logger.error("Timeout when calling Douyin API")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error when calling Douyin API: {e}")
        except Exception as e:
            logger.error(f"Unexpected error when calling Douyin API: {str(e)}")
        
        return None
    
    def create_or_update_user(
        self, 
        session: Session, 
        openid: str, 
        unionid: Optional[str] = None,
        session_key: Optional[str] = None
    ) -> DouyinUser:
        """
        创建或更新用户信息
        
        Args:
            session: 数据库会话
            openid: 用户openid
            unionid: 用户unionid
            session_key: 会话密钥
            
        Returns:
            用户对象
        """
        try:
            # 查找现有用户
            statement = select(DouyinUser).where(DouyinUser.openid == openid)
            user = session.exec(statement).first()
            
            if user:
                # 更新现有用户
                user.unionid = unionid
                user.last_login_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()
                logger.info(f"Updated existing user: {openid}")
            else:
                # 创建新用户
                user_data = DouyinUserCreate(
                    openid=openid,
                    unionid=unionid,
                    name=f"用户{openid[-6:]}",  # 默认昵称
                    user_type="normal",
                    permission="user",
                    level="1",
                    uuid=str(uuid.uuid4()),
                    is_active=True
                )
                
                user = DouyinUser.model_validate(user_data)
                user.last_login_at = datetime.utcnow()
                session.add(user)
                logger.info(f"Created new user: {openid}")
            
            session.commit()
            session.refresh(user)
            return user
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create/update user: {str(e)}")
            raise
    
    def create_jwt_token(self, openid: str, unionid: Optional[str] = None) -> str:
        """
        创建JWT令牌
        
        Args:
            openid: 用户openid
            unionid: 用户unionid
            
        Returns:
            JWT令牌
        """
        try:
            now = datetime.utcnow()
            expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
            
            payload = {
                "sub": openid,
                "unionid": unionid,
                "iat": now,
                "exp": expire,
                "type": "douyin_access"
            }
            
            token = jwt.encode(
                payload, 
                settings.SECRET_KEY, 
                algorithm=settings.JWT_ALGORITHM
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create JWT token: {str(e)}")
            raise
    
    def create_session(
        self,
        redis_client: redis.Redis,
        token: str,
        openid: str,
        unionid: Optional[str],
        session_key: Optional[str],
        user_data: Dict[str, Any]
    ) -> bool:
        """
        创建Redis会话
        
        Args:
            redis_client: Redis客户端
            token: JWT令牌
            openid: 用户openid
            unionid: 用户unionid
            session_key: 会话密钥
            user_data: 用户数据
            
        Returns:
            是否成功
        """
        try:
            session_key_redis = f"session:{token}"
            
            session_data = {
                "openid": openid,
                "unionid": unionid or "",
                "session_key": session_key or "",
                "created_at": datetime.utcnow().isoformat(),
                **user_data
            }
            
            # 设置会话数据，过期时间
            redis_client.hset(session_key_redis, mapping=session_data)
            redis_client.expire(session_key_redis, settings.SESSION_EXPIRE_SECONDS)
            
            logger.info(f"Session created for user: {openid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return False
    
    def delete_session(self, redis_client: redis.Redis, token: str) -> bool:
        """
        删除Redis会话
        
        Args:
            redis_client: Redis客户端
            token: JWT令牌
            
        Returns:
            是否成功
        """
        try:
            session_key = f"session:{token}"
            result = redis_client.delete(session_key)
            
            if result:
                logger.info(f"Session deleted for token: {token[:20]}...")
                return True
            else:
                logger.warning(f"Session not found for token: {token[:20]}...")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False
    
    def mask_sensitive_data(self, data: str, mask_length: int = 6) -> str:
        """
        脱敏处理敏感数据
        
        Args:
            data: 原始数据
            mask_length: 保留长度
            
        Returns:
            脱敏后的数据
        """
        if not data or len(data) <= mask_length:
            return data
        
        return data[:mask_length] + "*" * (len(data) - mask_length)
    
    async def process_login(
        self,
        session: Session,
        redis_client: redis.Redis,
        login_request: DouyinLoginRequest,
        ip_address: str,
        user_agent: str
    ) -> Tuple[Optional[DouyinLoginResponse], Optional[str]]:
        """
        处理用户登录流程
        
        Args:
            session: 数据库会话
            redis_client: Redis客户端
            login_request: 登录请求
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            (登录响应, 错误信息)
        """
        openid = None
        try:
            # 1. 调用抖音API换取用户信息
            douyin_data = await self.exchange_code_for_session(login_request.code)
            if not douyin_data:
                error_msg = "Failed to exchange code with Douyin API"
                return None, error_msg
            
            openid = douyin_data.get("openid")
            unionid = douyin_data.get("unionid")
            session_key = douyin_data.get("session_key")
            
            # 2. 创建或更新用户
            user = self.create_or_update_user(session, openid, unionid, session_key)
            
            # 3. 生成JWT令牌
            token = self.create_jwt_token(openid, unionid)
            
            # 4. 创建Redis会话
            user_data = {
                "name": user.name or "",
                "user_type": user.user_type,
                "permission": user.permission,
                "level": user.level,
                "uuid": user.uuid,
                "avatar_url": user.avatar_url or "",
                "phone": user.phone or ""
            }
            
            session_created = self.create_session(
                redis_client=redis_client,
                token=token,
                openid=openid,
                unionid=unionid,
                session_key=session_key,
                user_data=user_data
            )
            
            if not session_created:
                error_msg = "Failed to create session"
                create_login_log(session, openid, ip_address, user_agent, 0, error_msg)
                return None, error_msg
            
            # 5. 记录成功登录日志
            create_login_log(session, openid, ip_address, user_agent, 1)
            
            # 6. 构造响应
            user_public = DouyinUserPublic.model_validate(user)
            
            response = DouyinLoginResponse(
                token=token,
                openid=self.mask_sensitive_data(openid),
                unionid=self.mask_sensitive_data(unionid) if unionid else None,
                user_info=user_public
            )
            
            logger.info(f"User login successful: {openid}")
            return response, None
            
        except Exception as e:
            error_msg = f"Login process failed: {str(e)}"
            logger.error(error_msg)
            
            # 记录失败日志
            if openid:
                create_login_log(session, openid, ip_address, user_agent, 0, error_msg)
            
            return None, error_msg
    
    def logout_user(
        self, 
        session: Session,
        redis_client: redis.Redis, 
        openid: str, 
        token: str
    ) -> bool:
        """
        用户登出
        
        Args:
            session: 数据库会话
            redis_client: Redis客户端
            openid: 用户openid
            token: JWT令牌
            
        Returns:
            是否成功
        """
        try:
            # 删除Redis会话
            session_deleted = self.delete_session(redis_client, token)
            
            if session_deleted:
                logger.info(f"User logout successful: {openid}")
                return True
            else:
                logger.warning(f"Failed to delete session for user: {openid}")
                return False
                
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    def refresh_user_token(
        self, 
        redis_client: redis.Redis,
        current_token: str
    ) -> Optional[str]:
        """
        刷新用户令牌
        
        Args:
            redis_client: Redis客户端
            current_token: 当前令牌
            
        Returns:
            新令牌或None
        """
        try:
            # 获取当前会话数据
            session_key = f"session:{current_token}"
            session_data = redis_client.hgetall(session_key)
            
            if not session_data:
                return None
            
            openid = session_data.get("openid")
            unionid = session_data.get("unionid")
            
            # 生成新令牌
            new_token = self.create_jwt_token(openid, unionid)
            
            # 创建新会话
            session_created = self.create_session(
                redis_client=redis_client,
                token=new_token,
                openid=openid,
                unionid=unionid,
                session_key=session_data.get("session_key"),
                user_data={
                    key: value for key, value in session_data.items()
                    if key not in ["openid", "unionid", "session_key", "created_at"]
                }
            )
            
            if session_created:
                # 删除旧会话
                self.delete_session(redis_client, current_token)
                logger.info(f"Token refreshed for user: {openid}")
                return new_token
            
            return None
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None


# 全局登录服务实例
douyin_login_service = DouyinLoginService()
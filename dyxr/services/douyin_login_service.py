import httpx
import uuid
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models.userModel import User, LoginLog
from schemas.userSche import DouyinLoginRequest, DouyinLoginResponse, UserCreate
from services.session_service import session_manager
from utils.jwt_utils import create_session_token, mask_sensitive_data
from config import settings

logger = logging.getLogger(__name__)


class DouyinLoginService:
    """抖音小程序登录服务"""
    
    def __init__(self):
        self.auth_url = settings.douyin_auth_url
        self.app_id = settings.douyin_app_id
        self.app_secret = settings.douyin_app_secret
    
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
        db: Session, 
        openid: str, 
        unionid: Optional[str] = None,
        session_key: Optional[str] = None
    ) -> User:
        """
        创建或更新用户信息
        
        Args:
            db: 数据库会话
            openid: 用户openid
            unionid: 用户unionid
            session_key: 会话密钥
            
        Returns:
            用户对象
        """
        try:
            # 查找现有用户
            user = db.query(User).filter(User.openid == openid).first()
            
            if user:
                # 更新现有用户
                user.unionid = unionid
                user.last_login_at = datetime.utcnow()
                user.updated_at = datetime.utcnow()
                logger.info(f"Updated existing user: {openid}")
            else:
                # 创建新用户
                user = User(
                    openid=openid,
                    unionid=unionid,
                    name=f"用户{openid[-6:]}",  # 默认昵称
                    type="normal",
                    quanxian="user",
                    dengji="1",
                    uuid=str(uuid.uuid4()),
                    status=1,
                    last_login_at=datetime.utcnow()
                )
                db.add(user)
                logger.info(f"Created new user: {openid}")
            
            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create/update user: {str(e)}")
            raise
    
    def create_login_log(
        self, 
        db: Session, 
        openid: str, 
        ip_address: str,
        user_agent: str,
        login_result: int = 1,
        error_message: Optional[str] = None
    ) -> None:
        """
        记录登录日志
        
        Args:
            db: 数据库会话
            openid: 用户openid
            ip_address: IP地址
            user_agent: 用户代理
            login_result: 登录结果
            error_message: 错误信息
        """
        try:
            login_log = LoginLog(
                openid=openid,
                ip_address=ip_address,
                user_agent=user_agent,
                login_result=login_result,
                error_message=error_message
            )
            db.add(login_log)
            db.commit()
            logger.info(f"Login log recorded for user: {openid}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create login log: {str(e)}")
    
    async def process_login(
        self,
        db: Session,
        login_request: DouyinLoginRequest,
        ip_address: str,
        user_agent: str
    ) -> Tuple[Optional[DouyinLoginResponse], Optional[str]]:
        """
        处理用户登录流程
        
        Args:
            db: 数据库会话
            login_request: 登录请求
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            (登录响应, 错误信息)
        """
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
            user = self.create_or_update_user(db, openid, unionid, session_key)
            
            # 3. 生成JWT令牌
            token = create_session_token(openid, unionid)
            
            # 4. 创建Redis会话
            user_data = {
                "name": user.name,
                "type": user.type,
                "quanxian": user.quanxian,
                "dengji": user.dengji,
                "uuid": user.uuid
            }
            
            session_created = session_manager.create_session(
                token=token,
                openid=openid,
                unionid=unionid,
                session_key=session_key,
                user_data=user_data
            )
            
            if not session_created:
                error_msg = "Failed to create session"
                self.create_login_log(db, openid, ip_address, user_agent, 0, error_msg)
                return None, error_msg
            
            # 5. 记录成功登录日志
            self.create_login_log(db, openid, ip_address, user_agent, 1)
            
            # 6. 构造响应
            response = DouyinLoginResponse(
                token=token,
                openid=mask_sensitive_data(openid),
                unionid=mask_sensitive_data(unionid) if unionid else None
            )
            
            logger.info(f"User login successful: {openid}")
            return response, None
            
        except Exception as e:
            error_msg = f"Login process failed: {str(e)}"
            logger.error(error_msg)
            
            # 记录失败日志
            if 'openid' in locals():
                self.create_login_log(db, openid, ip_address, user_agent, 0, error_msg)
            
            return None, error_msg
    
    def logout_user(self, db: Session, openid: str, token: str) -> bool:
        """
        用户登出
        
        Args:
            db: 数据库会话
            openid: 用户openid
            token: JWT令牌
            
        Returns:
            是否成功
        """
        try:
            # 删除Redis会话
            session_deleted = session_manager.delete_session(token)
            
            if session_deleted:
                logger.info(f"User logout successful: {openid}")
                return True
            else:
                logger.warning(f"Failed to delete session for user: {openid}")
                return False
                
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False
    
    def refresh_user_token(self, token: str) -> Optional[str]:
        """
        刷新用户令牌
        
        Args:
            token: 当前令牌
            
        Returns:
            新令牌或None
        """
        try:
            # 获取当前会话数据
            session_data = session_manager.get_session(token)
            if not session_data:
                return None
            
            openid = session_data.get("openid")
            unionid = session_data.get("unionid")
            
            # 生成新令牌
            new_token = create_session_token(openid, unionid)
            
            # 创建新会话
            session_created = session_manager.create_session(
                token=new_token,
                openid=openid,
                unionid=unionid,
                session_key=session_data.get("session_key"),
                user_data=session_data.get("user_data")
            )
            
            if session_created:
                # 删除旧会话
                session_manager.delete_session(token)
                logger.info(f"Token refreshed for user: {openid}")
                return new_token
            
            return None
            
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return None


# 全局登录服务实例
douyin_login_service = DouyinLoginService()
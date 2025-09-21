import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from database import get_redis
from config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """Redis会话管理器"""

    def __init__(self):
        self.redis_client = get_redis()

    def create_session(
        self,
        token: str,
        openid: str,
        unionid: Optional[str] = None,
        session_key: Optional[str] = None,
        user_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建用户会话

        Args:
            token: JWT令牌
            openid: 用户openid
            unionid: 用户unionid
            session_key: 抖音返回的session_key
            user_data: 用户基本信息

        Returns:
            是否创建成功
        """
        try:
            session_data = {
                "openid": openid,
                "unionid": unionid or "",
                "session_key": session_key or "",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(seconds=settings.session_expire_seconds)).isoformat(),
                "user_data": json.dumps(user_data or {}, ensure_ascii=False)
            }

            # 存储会话数据
            redis_key = f"session:{token}"
            self.redis_client.hset(redis_key, mapping=session_data)
            self.redis_client.expire(
                redis_key, settings.session_expire_seconds)

            # 设置用户活跃状态
            user_active_key = f"user:active:{openid}"
            self.redis_client.setex(
                user_active_key,
                settings.user_active_expire_seconds,
                str(int(datetime.utcnow().timestamp()))
            )

            logger.info(f"Session created for user: {openid}")
            return True

        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return False

    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据

        Args:
            token: JWT令牌

        Returns:
            会话数据
        """
        try:
            redis_key = f"session:{token}"
            session_data = self.redis_client.hgetall(redis_key)

            if not session_data:
                return None

            # 解析用户数据
            user_data = {}
            if session_data.get("user_data"):
                try:
                    user_data = json.loads(session_data["user_data"])
                except json.JSONDecodeError:
                    pass

            return {
                "openid": session_data.get("openid"),
                "unionid": session_data.get("unionid"),
                "session_key": session_data.get("session_key"),
                "created_at": session_data.get("created_at"),
                "expires_at": session_data.get("expires_at"),
                "user_data": user_data
            }

        except Exception as e:
            logger.error(f"Failed to get session: {str(e)}")
            return None

    def delete_session(self, token: str) -> bool:
        """
        删除会话

        Args:
            token: JWT令牌

        Returns:
            是否删除成功
        """
        try:
            # 获取会话数据
            session_data = self.get_session(token)
            if session_data:
                openid = session_data.get("openid")

                # 删除会话数据
                redis_key = f"session:{token}"
                self.redis_client.delete(redis_key)

                # 删除用户活跃状态
                if openid:
                    user_active_key = f"user:active:{openid}"
                    self.redis_client.delete(user_active_key)

                logger.info(f"Session deleted for user: {openid}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False

    def refresh_session(self, token: str) -> bool:
        """
        刷新会话

        Args:
            token: JWT令牌

        Returns:
            是否刷新成功
        """
        try:
            redis_key = f"session:{token}"

            # 检查会话是否存在
            if not self.redis_client.exists(redis_key):
                return False

            # 更新过期时间
            new_expires_at = (datetime.utcnow(
            ) + timedelta(seconds=settings.session_expire_seconds)).isoformat()
            self.redis_client.hset(redis_key, "expires_at", new_expires_at)
            self.redis_client.expire(
                redis_key, settings.session_expire_seconds)

            # 更新用户活跃状态
            session_data = self.get_session(token)
            if session_data and session_data.get("openid"):
                user_active_key = f"user:active:{session_data['openid']}"
                self.redis_client.setex(
                    user_active_key,
                    settings.user_active_expire_seconds,
                    str(int(datetime.utcnow().timestamp()))
                )

            return True

        except Exception as e:
            logger.error(f"Failed to refresh session: {str(e)}")
            return False

    def is_user_active(self, openid: str) -> bool:
        """
        检查用户是否活跃

        Args:
            openid: 用户openid

        Returns:
            是否活跃
        """
        try:
            user_active_key = f"user:active:{openid}"
            return self.redis_client.exists(user_active_key) > 0

        except Exception as e:
            logger.error(f"Failed to check user active status: {str(e)}")
            return False

    def get_user_sessions(self, openid: str) -> list:
        """
        获取用户的所有会话

        Args:
            openid: 用户openid

        Returns:
            会话列表
        """
        try:
            sessions = []
            # 扫描所有会话
            for key in self.redis_client.scan_iter("session:*"):
                session_data = self.redis_client.hgetall(key)
                if session_data.get("openid") == openid:
                    token = key.replace("session:", "")
                    sessions.append({
                        "token": token,
                        "created_at": session_data.get("created_at"),
                        "expires_at": session_data.get("expires_at")
                    })

            return sessions

        except Exception as e:
            logger.error(f"Failed to get user sessions: {str(e)}")
            return []

    def delete_user_sessions(self, openid: str) -> bool:
        """
        删除用户的所有会话

        Args:
            openid: 用户openid

        Returns:
            是否删除成功
        """
        try:
            deleted_count = 0
            # 扫描并删除用户的所有会话
            for key in self.redis_client.scan_iter("session:*"):
                session_data = self.redis_client.hgetall(key)
                if session_data.get("openid") == openid:
                    self.redis_client.delete(key)
                    deleted_count += 1

            # 删除用户活跃状态
            user_active_key = f"user:active:{openid}"
            self.redis_client.delete(user_active_key)

            logger.info(f"Deleted {deleted_count} sessions for user: {openid}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user sessions: {str(e)}")
            return False

    def update_session_data(self, token: str, user_data: Dict[str, Any]) -> bool:
        """
        更新会话中的用户数据

        Args:
            token: JWT令牌
            user_data: 新的用户数据

        Returns:
            是否更新成功
        """
        try:
            redis_key = f"session:{token}"

            # 检查会话是否存在
            if not self.redis_client.exists(redis_key):
                return False

            # 更新用户数据
            serialized_data = json.dumps(user_data, ensure_ascii=False)
            self.redis_client.hset(redis_key, "user_data", serialized_data)

            return True

        except Exception as e:
            logger.error(f"Failed to update session data: {str(e)}")
            return False


# 全局会话管理器实例
session_manager = SessionManager()

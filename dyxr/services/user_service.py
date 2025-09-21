import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.userModel import User
from schemas.userSche import UserCreate, UserUpdate, UserProfile
from services.session_service import session_manager

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务"""

    def get_user_by_openid(
        self, db: Session, openid: str
    ) -> Optional[User]:
        """
        根据openid获取用户

        Args:
            db: 数据库会话
            openid: 用户openid

        Returns:
            用户对象或None
        """
        try:
            return db.query(User).filter(User.openid == openid).first()
        except Exception as e:
            logger.error(f"Failed to get user by openid: {str(e)}")
            return None

    def get_user_by_unionid(
        self, db: Session, unionid: str
    ) -> Optional[User]:
        """
        根据unionid获取用户

        Args:
            db: 数据库会话
            unionid: 用户unionid

        Returns:
            用户对象或None
        """
        try:
            return db.query(User).filter(User.unionid == unionid).first()
        except Exception as e:
            logger.error(f"Failed to get user by unionid: {str(e)}")
            return None

    def get_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[int] = None,
        user_type: Optional[str] = None,
    ) -> List[User]:
        """
        获取用户列表

        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回的记录数
            status: 用户状态过滤
            user_type: 用户类型过滤

        Returns:
            用户列表
        """
        try:
            query = db.query(User)

            # 应用过滤条件
            if status is not None:
                query = query.filter(User.status == status)

            if user_type:
                query = query.filter(User.type == user_type)

            return query.offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    def search_users(
        self, db: Session, keyword: str, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        搜索用户

        Args:
            db: 数据库会话
            keyword: 搜索关键词
            skip: 跳过的记录数
            limit: 限制返回的记录数

        Returns:
            用户列表
        """
        try:
            search_pattern = f"%{keyword}%"
            query = db.query(User).filter(
                or_(
                    User.name.like(search_pattern),
                    User.openid.like(search_pattern),
                    User.phone.like(search_pattern),
                )
            )

            return query.offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(f"Failed to search users: {str(e)}")
            return []

    def create_user(
        self, db: Session, user_data: UserCreate
    ) -> Optional[User]:
        """
        创建用户

        Args:
            db: 数据库会话
            user_data: 用户创建数据

        Returns:
            创建的用户对象或None
        """
        try:
            # 检查用户是否已存在
            existing_user = self.get_user_by_openid(db, user_data.openid)
            if existing_user:
                logger.warning(f"User already exists: {user_data.openid}")
                return None

            # 创建新用户
            db_user = User(
                openid=user_data.openid,
                unionid=user_data.unionid,
                name=user_data.name,
                type=user_data.type,
                quanxian=user_data.quanxian,
                dengji=user_data.dengji,
                uuid=user_data.uuid,
                avatar_url=user_data.avatar_url,
                phone=user_data.phone,
                status=user_data.status,
            )

            db.add(db_user)
            db.commit()
            db.refresh(db_user)

            logger.info(f"User created: {user_data.openid}")
            return db_user

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            return None

    def update_user(
        self, db: Session, openid: str, user_data: UserUpdate
    ) -> Optional[User]:
        """
        更新用户信息

        Args:
            db: 数据库会话
            openid: 用户openid
            user_data: 更新数据

        Returns:
            更新后的用户对象或None
        """
        try:
            user = self.get_user_by_openid(db, openid)
            if not user:
                return None

            # 更新字段
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)

            user.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(user)

            # 更新Redis中的用户数据
            self._update_session_user_data(openid, update_data)

            logger.info(f"User updated: {openid}")
            return user

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update user: {str(e)}")
            return None

    def delete_user(self, db: Session, openid: str) -> bool:
        """
        删除用户

        Args:
            db: 数据库会话
            openid: 用户openid

        Returns:
            是否删除成功
        """
        try:
            user = self.get_user_by_openid(db, openid)
            if not user:
                return False

            # 删除用户的所有会话
            session_manager.delete_user_sessions(openid)

            # 软删除：设置状态为禁用
            user.status = 0
            user.updated_at = datetime.utcnow()

            db.commit()

            logger.info(f"User deleted(soft): {openid}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete user: {str(e)}")
            return False

    def hard_delete_user(self, db: Session, openid: str) -> bool:
        """
        硬删除用户（物理删除）

        Args:
            db: 数据库会话
            openid: 用户openid

        Returns:
            是否删除成功
        """
        try:
            user = self.get_user_by_openid(db, openid)
            if not user:
                return False

            # 删除用户的所有会话
            session_manager.delete_user_sessions(openid)

            # 物理删除
            db.delete(user)
            db.commit()

            logger.info(f"User hard deleted: {openid}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to hard delete user: {str(e)}")
            return False

    def activate_user(self, db: Session, openid: str) -> bool:
        """
        激活用户

        Args:
            db: 数据库会话
            openid: 用户openid

        Returns:
            是否激活成功
        """
        try:
            user = self.get_user_by_openid(db, openid)
            if not user:
                return False

            user.status = 1
            user.updated_at = datetime.utcnow()

            db.commit()

            logger.info(f"User activated: {openid}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to activate user: {str(e)}")
            return False

    def get_user_profile(
        self, db: Session, openid: str
    ) -> Optional[UserProfile]:
        """
        获取用户资料

        Args:
            db: 数据库会话
            openid: 用户openid

        Returns:
            用户资料或None
        """
        try:
            user = self.get_user_by_openid(db, openid)
            if not user or user.status != 1:
                return None

            return UserProfile(
                openid=user.openid,
                name=user.name,
                type=user.type,
                quanxian=user.quanxian,
                dengji=user.dengji,
                uuid=user.uuid,
            )

        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            return None

    def update_last_login(self, db: Session, openid: str) -> bool:
        """
        更新用户最后登录时间

        Args:
            db: 数据库会话
            openid: 用户openid

        Returns:
            是否更新成功
        """
        try:
            user = self.get_user_by_openid(db, openid)
            if not user:
                return False

            user.last_login_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update last login: {str(e)}")
            return False

    def get_user_count(
        self, db: Session, status: Optional[int] = None
    ) -> int:
        """
        获取用户总数

        Args:
            db: 数据库会话
            status: 用户状态过滤

        Returns:
            用户总数
        """
        try:
            query = db.query(User)

            if status is not None:
                query = query.filter(User.status == status)

            return query.count()

        except Exception as e:
            logger.error(f"Failed to get user count: {str(e)}")
            return 0

    def _update_session_user_data(
        self, openid: str, update_data: Dict[str, Any]
    ) -> None:
        """
        更新Redis会话中的用户数据

        Args:
            openid: 用户openid
            update_data: 更新的数据
        """
        try:
            # 获取用户的所有会话
            user_sessions = session_manager.get_user_sessions(openid)

            for session in user_sessions:
                token = session.get("token")
                if token:
                    # 获取当前会话数据
                    session_data = session_manager.get_session(token)
                    if session_data and session_data.get("user_data"):
                        # 更新用户数据
                        user_data = session_data["user_data"]
                        user_data.update(update_data)
                        session_manager.update_session_data(
                            token, user_data
                        )

        except Exception as e:
            logger.error(f"Failed to update session user data: {str(e)}")


# 全局用户服务实例
user_service = UserService()

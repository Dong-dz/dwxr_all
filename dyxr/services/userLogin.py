from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.userModel import User
from typing import Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_by_id(db: Session, openid: str) -> Optional[User]:
    try:
        user = db.query(User).filter(User.openid == openid).first()
        if user:
            logger.info(f"根据openid找到用户: {user.name}")
        else:
            logger.info(f"根据openid未找到用户: {openid} ")
        return user
    except SQLAlchemyError as e:
        logger.error(f"根据openid查询用户失败: {str(e)}")
        raise

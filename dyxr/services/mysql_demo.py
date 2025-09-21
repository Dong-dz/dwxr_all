# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from models.userModel import User
# from database import get_db
# from typing import Optional
# from schemas.userSche import UserCreate  # 添加导入
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
#
# def get_user_by_id(db: Session, openid: str) -> Optional[User]:
#     """
#     根据ID获取用户
#
#     Args:
#         db: 数据库会话
#         openid: 用户ID
#
#     Returns:
#         User: 用户对象，如果未找到返回None
#     """
#     try:
#         user = db.query(User).filter(User.openid == openid).first()
#         if user:
#             logger.info(f"找到用户: {user.name}")
#         else:
#             logger.info(f"未找到ID为 {openid} 的用户")
#         return user
#     except SQLAlchemyError as e:
#         logger.error(f"查询用户失败: {str(e)}")
#         raise
#
#
# def get_user_by_username(db: Session, username: str) -> Optional[User]:
#     """
#     根据用户名获取用户
#
#     Args:
#         db: 数据库会话
#         username: 用户名
#
#     Returns:
#         User: 用户对象，如果未找到返回None
#     """
#     try:
#         user = db.query(User).filter(User.name == username).first()  # 修改为使用name字段
#         if user:
#             logger.info(f"找到用户: {user.name}")
#         else:
#             logger.info(f"未找到用户名为 {username} 的用户")
#         return user
#     except SQLAlchemyError as e:
#         logger.error(f"查询用户失败: {str(e)}")
#         raise
#
#
# def update_user(db: Session, openid: str, update_data: dict) -> Optional[User]:
#     """
#     更新用户信息
#
#     Args:
#         db: 数据库会话
#         openid: 用户ID
#         update_data: 要更新的字段和值字典
#
#     Returns:
#         User: 更新后的用户对象
#     """
#     try:
#         user = db.query(User).filter(User.openid == openid).first()
#         if not user:
#             logger.info(f"未找到ID为 {openid} 的用户")
#             return None
#
#         for key, value in update_data.items():
#             if hasattr(user, key):
#                 setattr(user, key, value)
#
#         db.commit()
#         db.refresh(user)
#         logger.info(f"用户更新成功: {user.name}")
#         return user
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"更新用户失败: {str(e)}")
#         raise
#
#
# def delete_user(db: Session, openid: str) -> bool:
#     """
#     删除用户
#
#     Args:
#         db: 数据库会话
#         openid: 用户ID
#
#     Returns:
#         bool: 删除成功返回True，否则返回False
#     """
#     try:
#         user = db.query(User).filter(User.openid == openid).first()
#         if not user:
#             logger.info(f"未找到ID为 {openid} 的用户")
#             return False
#
#         db.delete(user)
#         db.commit()
#         logger.info(f"用户删除成功: {user.name}")
#         return True
#     except SQLAlchemyError as e:
#         db.rollback()
#         logger.error(f"删除用户失败: {str(e)}")
#         raise
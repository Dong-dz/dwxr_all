from datetime import datetime
from database import Base
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text, BigInteger, Index
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    openid = Column(String(100), primary_key=True, index=True, comment="用户OpenID")
    unionid = Column(String(100), index=True, comment="用户UnionID")
    name = Column(String(100), comment="用户昵称")
    type = Column(String(100), comment="用户类型")
    quanxian = Column(String(100), comment="用户权限")
    dengji = Column(String(100), comment="用户等级")
    uuid = Column(String(100), nullable=False, comment="UUID")
    avatar_url = Column(String(500), comment="头像URL")
    phone = Column(String(20), comment="手机号")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    last_login_at = Column(DateTime, comment="最后登录时间")
    status = Column(Integer, default=1, comment="用户状态：1-正常，0-禁用")

    __table_args__ = (
        Index('idx_unionid', 'unionid'),
        Index('idx_created_at', 'created_at'),
        Index('idx_last_login', 'last_login_at'),
    )


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=False, index=True, comment="用户OpenID")
    login_time = Column(DateTime, default=func.now(), comment="登录时间")
    ip_address = Column(String(45), comment="登录IP地址")
    user_agent = Column(Text, comment="用户代理信息")
    login_result = Column(Integer, default=1, comment="登录结果：1-成功，0-失败")
    error_message = Column(String(500), comment="错误信息")
    
    __table_args__ = (
        Index('idx_login_openid', 'openid'),
        Index('idx_login_time', 'login_time'),
    )

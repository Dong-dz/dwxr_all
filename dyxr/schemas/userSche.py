from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime


class DouyinLoginRequest(BaseModel):
    """抖音小程序登录请求"""
    code: str
    
    @validator('code')
    def validate_code(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('code不能为空')
        return v


class DouyinLoginResponse(BaseModel):
    """抖音小程序登录响应"""
    errCode: int = 0
    errMsg: str = "success"
    token: str
    openid: str
    unionid: Optional[str] = None


class UserBase(BaseModel):
    """用户基础信息"""
    openid: str
    name: Optional[str] = None
    type: Optional[str] = None
    quanxian: Optional[str] = None
    dengji: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """用户创建模型"""
    unionid: Optional[str] = None
    uuid: str
    status: Optional[int] = 1


class UserUpdate(BaseModel):
    """用户更新模型"""
    name: Optional[str] = None
    type: Optional[str] = None
    quanxian: Optional[str] = None
    dengji: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[int] = None


class UserResponse(UserBase):
    """用户响应模型"""
    unionid: Optional[str] = None
    uuid: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    status: int = 1

    class Config:
        orm_mode = True


class UserProfile(BaseModel):
    """用户资料信息"""
    openid: str
    name: Optional[str] = None
    type: Optional[str] = None
    quanxian: Optional[str] = None
    dengji: Optional[str] = None
    uuid: str

    class Config:
        orm_mode = True


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    token: str
    expires_in: int = 7200


class LogoutResponse(BaseModel):
    """登出响应"""
    errCode: int = 0
    errMsg: str = "success"


class LoginLogCreate(BaseModel):
    """登录日志创建模型"""
    openid: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_result: int = 1
    error_message: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    errCode: int
    errMsg: str
    detail: Optional[str] = None
    timestamp: Optional[datetime] = None
    request_id: Optional[str] = None
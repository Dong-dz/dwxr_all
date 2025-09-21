import uuid
from datetime import datetime
from typing import Optional, Union, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# ======= 抖音小程序相关模型 =======

# 抖音用户基础模型
class DouyinUserBase(SQLModel):
    openid: str = Field(max_length=100, index=True)
    unionid: Union[str, None] = Field(default=None, max_length=100, index=True)
    name: Union[str, None] = Field(default=None, max_length=100)
    user_type: str = Field(default="normal", max_length=100)
    permission: str = Field(default="user", max_length=100)
    level: str = Field(default="1", max_length=100)
    uuid: str = Field(max_length=100)
    avatar_url: Union[str, None] = Field(default=None, max_length=500)
    phone: Union[str, None] = Field(default=None, max_length=20)
    is_active: bool = Field(default=True)


# 抖音用户创建模型
class DouyinUserCreate(DouyinUserBase):
    pass


# 抖音用户更新模型
class DouyinUserUpdate(SQLModel):
    name: Union[str, None] = Field(default=None, max_length=100)
    avatar_url: Union[str, None] = Field(default=None, max_length=500)
    phone: Union[str, None] = Field(default=None, max_length=20)


# 抖音用户数据库模型
class DouyinUser(DouyinUserBase, table=True):
    __tablename__ = "douyin_users"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Union[datetime, None] = Field(default=None)
    
    # 关联标点信息
    biaodian_items: List["BiaodianItem"] = Relationship(back_populates="owner", cascade_delete=True)


# 抖音用户公开信息模型
class DouyinUserPublic(DouyinUserBase):
    id: uuid.UUID
    created_at: datetime
    last_login_at: Union[datetime, None]


# 标点信息基础模型
class BiaodianItemBase(SQLModel):
    latitude: str = Field(max_length=100)
    longitude: str = Field(max_length=100)
    beizhu: Union[str, None] = Field(default=None, max_length=100)
    weather: Union[str, None] = Field(default=None, max_length=100)
    zhuangbei: Union[str, None] = Field(default=None, max_length=100)
    fishing_type: int = Field(description="钓鱼类型：1-台钓，2-路亚，3-其他")
    yuhuo: Union[str, None] = Field(default=None, max_length=100)
    tuijian: str = Field(max_length=100, description="推荐指数")
    is_public: bool = Field(default=False, description="是否公开：True-公开，False-私密")
    city: Union[str, None] = Field(default=None, max_length=100)
    province: Union[str, None] = Field(default=None, max_length=100)
    title: Union[str, None] = Field(default=None, max_length=100)


# 标点信息创建模型
class BiaodianItemCreate(BiaodianItemBase):
    pass


# 标点信息更新模型
class BiaodianItemUpdate(SQLModel):
    latitude: Union[str, None] = Field(default=None, max_length=100)
    longitude: Union[str, None] = Field(default=None, max_length=100)
    beizhu: Union[str, None] = Field(default=None, max_length=100)
    weather: Union[str, None] = Field(default=None, max_length=100)
    zhuangbei: Union[str, None] = Field(default=None, max_length=100)
    fishing_type: Union[int, None] = Field(default=None)
    yuhuo: Union[str, None] = Field(default=None, max_length=100)
    tuijian: Union[str, None] = Field(default=None, max_length=100)
    is_public: Union[bool, None] = Field(default=None)
    city: Union[str, None] = Field(default=None, max_length=100)
    province: Union[str, None] = Field(default=None, max_length=100)
    title: Union[str, None] = Field(default=None, max_length=100)


# 标点信息数据库模型
class BiaodianItem(BiaodianItemBase, table=True):
    __tablename__ = "biaodian_items"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关联抖音用户
    owner_id: uuid.UUID = Field(foreign_key="douyin_users.id", nullable=False, ondelete="CASCADE")
    owner: Union[DouyinUser, None] = Relationship(back_populates="biaodian_items")
    
    # 兼容旧系统的openid字段
    openid: Union[str, None] = Field(default=None, max_length=100, index=True)


# 标点信息公开模型
class BiaodianItemPublic(BiaodianItemBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID


# 标点信息列表返回模型
class BiaodianItemsPublic(SQLModel):
    data: List[BiaodianItemPublic]
    count: int


# 登录日志模型
class DouyinLoginLog(SQLModel, table=True):
    __tablename__ = "douyin_login_logs"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    openid: str = Field(max_length=100, index=True)
    ip_address: Union[str, None] = Field(default=None, max_length=45)
    user_agent: Union[str, None] = Field(default=None, max_length=500)
    login_result: int = Field(default=1, description="登录结果：1-成功，0-失败")
    error_message: Union[str, None] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# 抖音登录请求模型
class DouyinLoginRequest(SQLModel):
    code: str = Field(description="抖音小程序临时登录凭证")


# 抖音登录响应模型
class DouyinLoginResponse(SQLModel):
    token: str
    openid: str
    unionid: Union[str, None] = None
    user_info: Union[DouyinUserPublic, None] = None


# 令牌刷新响应模型
class RefreshTokenResponse(SQLModel):
    token: str


# 登出响应模型
class LogoutResponse(SQLModel):
    message: str = "登出成功"

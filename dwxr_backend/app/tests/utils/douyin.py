"""
抖音小程序测试工具函数
"""
import uuid
from typing import Dict, Any
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import DouyinUser, DouyinUserCreate
from app.services.douyin_crud import douyin_user_crud


def create_test_douyin_user(db: Session, openid: str = None) -> DouyinUser:
    """创建测试用的抖音用户"""
    if openid is None:
        openid = f"test_openid_{uuid.uuid4().hex[:8]}"
    
    user_in = DouyinUserCreate(
        openid=openid,
        unionid=f"test_unionid_{uuid.uuid4().hex[:8]}",
        name=f"测试用户{openid[-6:]}",
        user_type="normal",
        permission="user",
        level="1",
        uuid=str(uuid.uuid4()),
        is_active=True
    )
    
    return douyin_user_crud.create(db, user_in)


def create_test_admin_user(db: Session, openid: str = None) -> DouyinUser:
    """创建测试用的管理员用户"""
    if openid is None:
        openid = f"admin_openid_{uuid.uuid4().hex[:8]}"
    
    user_in = DouyinUserCreate(
        openid=openid,
        unionid=f"admin_unionid_{uuid.uuid4().hex[:8]}",
        name=f"管理员{openid[-6:]}",
        user_type="admin",
        permission="admin",
        level="10",
        uuid=str(uuid.uuid4()),
        is_active=True
    )
    
    return douyin_user_crud.create(db, user_in)


def mock_douyin_api_response(openid: str = None, unionid: str = None) -> Dict[str, Any]:
    """模拟抖音API响应"""
    if openid is None:
        openid = f"mock_openid_{uuid.uuid4().hex[:8]}"
    
    if unionid is None:
        unionid = f"mock_unionid_{uuid.uuid4().hex[:8]}"
    
    return {
        "openid": openid,
        "unionid": unionid,
        "session_key": f"session_key_{uuid.uuid4().hex[:16]}"
    }


def mock_redis_client() -> Mock:
    """模拟Redis客户端"""
    redis_mock = Mock()
    redis_mock.ping.return_value = True
    redis_mock.hgetall.return_value = {}
    redis_mock.hset.return_value = True
    redis_mock.expire.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.incr.return_value = 1
    return redis_mock


def get_douyin_token_headers(
    client: TestClient, 
    openid: str,
    permission: str = "user"
) -> Dict[str, str]:
    """获取抖音用户的认证头"""
    # 这里模拟生成JWT令牌的过程
    # 实际实现中需要调用真实的令牌生成服务
    mock_token = f"mock_jwt_token_{openid}_{permission}"
    
    return {"Authorization": f"Bearer {mock_token}"}


def get_douyin_admin_token_headers(client: TestClient, openid: str = None) -> Dict[str, str]:
    """获取抖音管理员的认证头"""
    if openid is None:
        openid = f"admin_{uuid.uuid4().hex[:8]}"
    
    return get_douyin_token_headers(client, openid, "admin")
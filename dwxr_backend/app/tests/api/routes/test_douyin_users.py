"""
测试抖音用户API路由
"""
import uuid
from unittest.mock import patch, Mock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import DouyinLoginRequest
from app.tests.utils.douyin import (
    create_test_douyin_user, 
    create_test_admin_user,
    mock_douyin_api_response,
    get_douyin_token_headers,
    get_douyin_admin_token_headers
)


class TestDouyinLogin:
    """抖音登录API测试"""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: TestClient, db: Session):
        """测试登录成功"""
        login_data = {"code": "test_code_123"}
        mock_response = mock_douyin_api_response()
        
        with patch('app.services.douyin_login_service.douyin_login_service.process_login') as mock_login:
            from app.models import DouyinLoginResponse, DouyinUserPublic
            
            # 创建模拟响应
            user_info = DouyinUserPublic(
                id=uuid.uuid4(),
                openid="masked_openid",
                unionid="masked_unionid",
                name="测试用户",
                user_type="normal",
                permission="user",
                level="1",
                uuid=str(uuid.uuid4()),
                avatar_url=None,
                phone=None,
                is_active=True,
                created_at="2024-01-01T00:00:00",
                last_login_at=None
            )
            
            response_data = DouyinLoginResponse(
                token="jwt_token_example",
                openid="masked_openid",
                unionid="masked_unionid",
                user_info=user_info
            )
            
            mock_login.return_value = (response_data, None)
            
            response = client.post("/api/v1/douyin/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "openid" in data
        assert "user_info" in data
    
    def test_login_invalid_code(self, client: TestClient, db: Session):
        """测试登录失败"""
        login_data = {"code": "invalid_code"}
        
        with patch('app.services.douyin_login_service.douyin_login_service.process_login') as mock_login:
            mock_login.return_value = (None, "Failed to exchange code with Douyin API")
            
            response = client.post("/api/v1/douyin/login", json=login_data)
        
        assert response.status_code == 400
        assert "Failed to exchange code with Douyin API" in response.json()["detail"]
    
    def test_login_rate_limit(self, client: TestClient, db: Session):
        """测试登录频率限制"""
        login_data = {"code": "test_code"}
        
        with patch('app.api.deps_douyin.check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = False
            
            response = client.post("/api/v1/douyin/login", json=login_data)
        
        assert response.status_code == 429
        assert "请求过于频繁" in response.json()["detail"]


class TestDouyinUserProfile:
    """抖音用户资料API测试"""
    
    def test_get_profile_success(self, client: TestClient, db: Session):
        """测试获取用户资料成功"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user, "openid": user.openid}
            
            response = client.get("/api/v1/douyin/profile", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["openid"] == user.openid
        assert data["name"] == user.name
    
    def test_get_profile_unauthorized(self, client: TestClient):
        """测试未认证获取用户资料"""
        response = client.get("/api/v1/douyin/profile")
        
        assert response.status_code == 401
    
    def test_update_profile_success(self, client: TestClient, db: Session):
        """测试更新用户资料成功"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        update_data = {
            "name": "新用户名",
            "avatar_url": "https://example.com/new_avatar.jpg",
            "phone": "13900139000"
        }
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user, "openid": user.openid}
            
            with patch('app.services.douyin_crud.douyin_user_crud.update') as mock_update:
                # 模拟更新后的用户
                updated_user = user
                updated_user.name = update_data["name"]
                mock_update.return_value = updated_user
                
                response = client.put("/api/v1/douyin/profile", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新用户名"
    
    def test_update_profile_unauthorized(self, client: TestClient):
        """测试未认证更新用户资料"""
        update_data = {"name": "新用户名"}
        
        response = client.put("/api/v1/douyin/profile", json=update_data)
        
        assert response.status_code == 401


class TestDouyinUserLogout:
    """抖音用户登出API测试"""
    
    def test_logout_success(self, client: TestClient, db: Session):
        """测试登出成功"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {
                "user": user,
                "openid": user.openid,
                "token": "test_token"
            }
            
            with patch('app.services.douyin_login_service.douyin_login_service.logout_user') as mock_logout:
                mock_logout.return_value = True
                
                response = client.post("/api/v1/douyin/logout", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "登出成功"
    
    def test_logout_failure(self, client: TestClient, db: Session):
        """测试登出失败"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {
                "user": user,
                "openid": user.openid,
                "token": "test_token"
            }
            
            with patch('app.services.douyin_login_service.douyin_login_service.logout_user') as mock_logout:
                mock_logout.return_value = False
                
                response = client.post("/api/v1/douyin/logout", headers=headers)
        
        assert response.status_code == 400
        assert "登出失败" in response.json()["detail"]


class TestDouyinTokenRefresh:
    """抖音令牌刷新API测试"""
    
    def test_refresh_token_success(self, client: TestClient, db: Session):
        """测试令牌刷新成功"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {
                "user": user,
                "token": "old_token"
            }
            
            with patch('app.services.douyin_login_service.douyin_login_service.refresh_user_token') as mock_refresh:
                mock_refresh.return_value = "new_token"
                
                response = client.post("/api/v1/douyin/refresh-token", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "new_token"
    
    def test_refresh_token_failure(self, client: TestClient, db: Session):
        """测试令牌刷新失败"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {
                "user": user,
                "token": "old_token"
            }
            
            with patch('app.services.douyin_login_service.douyin_login_service.refresh_user_token') as mock_refresh:
                mock_refresh.return_value = None
                
                response = client.post("/api/v1/douyin/refresh-token", headers=headers)
        
        assert response.status_code == 400
        assert "令牌刷新失败" in response.json()["detail"]


class TestDouyinUserManagement:
    """抖音用户管理API测试（管理员功能）"""
    
    def test_get_users_as_admin(self, client: TestClient, db: Session):
        """测试管理员获取用户列表"""
        admin_user = create_test_admin_user(db)
        headers = get_douyin_admin_token_headers(client, admin_user.openid)
        
        # 创建一些测试用户
        test_users = [create_test_douyin_user(db) for _ in range(3)]
        
        with patch('app.api.deps_douyin.get_current_admin_user') as mock_auth:
            mock_auth.return_value = {"user": admin_user}
            
            with patch('app.services.douyin_crud.douyin_user_crud.get_multi') as mock_get_users:
                mock_get_users.return_value = test_users
                
                response = client.get("/api/v1/douyin/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_get_users_as_normal_user(self, client: TestClient, db: Session):
        """测试普通用户无法获取用户列表"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        response = client.get("/api/v1/douyin/users", headers=headers)
        
        assert response.status_code == 403
    
    def test_search_users_as_admin(self, client: TestClient, db: Session):
        """测试管理员搜索用户"""
        admin_user = create_test_admin_user(db)
        headers = get_douyin_admin_token_headers(client, admin_user.openid)
        
        with patch('app.api.deps_douyin.get_current_admin_user') as mock_auth:
            mock_auth.return_value = {"user": admin_user}
            
            with patch('app.services.douyin_crud.douyin_user_crud.search') as mock_search:
                mock_search.return_value = [create_test_douyin_user(db)]
                
                response = client.get("/api/v1/douyin/users/search?keyword=测试", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0
    
    def test_delete_user_as_admin(self, client: TestClient, db: Session):
        """测试管理员删除用户"""
        admin_user = create_test_admin_user(db)
        target_user = create_test_douyin_user(db)
        headers = get_douyin_admin_token_headers(client, admin_user.openid)
        
        with patch('app.api.deps_douyin.get_current_admin_user') as mock_auth:
            mock_auth.return_value = {"user": admin_user}
            
            with patch('app.services.douyin_crud.douyin_user_crud.get_by_id') as mock_get:
                mock_get.return_value = target_user
                
                with patch('app.services.douyin_crud.douyin_user_crud.delete') as mock_delete:
                    mock_delete.return_value = True
                    
                    response = client.delete(f"/api/v1/douyin/users/{target_user.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "用户删除成功"
    
    def test_delete_self_forbidden(self, client: TestClient, db: Session):
        """测试管理员不能删除自己"""
        admin_user = create_test_admin_user(db)
        headers = get_douyin_admin_token_headers(client, admin_user.openid)
        
        with patch('app.api.deps_douyin.get_current_admin_user') as mock_auth:
            mock_auth.return_value = {"user": admin_user}
            
            response = client.delete(f"/api/v1/douyin/users/{admin_user.id}", headers=headers)
        
        assert response.status_code == 400
        assert "不能删除自己的账户" in response.json()["detail"]
"""
测试抖音登录服务
"""
import uuid
from unittest.mock import Mock, patch, AsyncMock

import pytest
from sqlmodel import Session

from app.models import DouyinLoginRequest, DouyinUser, DouyinLoginLog
from app.services.douyin_login_service import DouyinLoginService
from app.tests.utils.douyin import mock_douyin_api_response, mock_redis_client


class TestDouyinLoginService:
    """抖音登录服务测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.service = DouyinLoginService()
        self.redis_mock = mock_redis_client()
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_session_success(self):
        """测试成功换取用户信息"""
        mock_response = mock_douyin_api_response()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response_obj
            
            result = await self.service.exchange_code_for_session("test_code")
            
            assert result is not None
            assert result["openid"] == mock_response["openid"]
            assert result["unionid"] == mock_response["unionid"]
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_session_api_error(self):
        """测试抖音API返回错误"""
        error_response = {"error": "invalid_code", "error_description": "code无效"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.json.return_value = error_response
            mock_response_obj.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response_obj
            
            result = await self.service.exchange_code_for_session("invalid_code")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_session_missing_openid(self):
        """测试响应缺少openid"""
        invalid_response = {"session_key": "test_session_key"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = Mock()
            mock_response_obj.json.return_value = invalid_response
            mock_response_obj.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response_obj
            
            result = await self.service.exchange_code_for_session("test_code")
            
            assert result is None
    
    def test_create_or_update_user_new_user(self, db: Session):
        """测试创建新用户"""
        openid = f"new_openid_{uuid.uuid4().hex[:8]}"
        unionid = f"new_unionid_{uuid.uuid4().hex[:8]}"
        
        user = self.service.create_or_update_user(db, openid, unionid)
        
        assert user is not None
        assert user.openid == openid
        assert user.unionid == unionid
        assert user.name == f"用户{openid[-6:]}"
        assert user.is_active is True
        assert user.last_login_at is not None
    
    def test_create_or_update_user_existing_user(self, db: Session):
        """测试更新现有用户"""
        # 先创建一个用户
        openid = f"existing_openid_{uuid.uuid4().hex[:8]}"
        original_unionid = f"original_unionid_{uuid.uuid4().hex[:8]}"
        
        original_user = self.service.create_or_update_user(db, openid, original_unionid)
        original_login_time = original_user.last_login_at
        
        # 更新用户
        new_unionid = f"new_unionid_{uuid.uuid4().hex[:8]}"
        updated_user = self.service.create_or_update_user(db, openid, new_unionid)
        
        assert updated_user.id == original_user.id
        assert updated_user.unionid == new_unionid
        assert updated_user.last_login_at > original_login_time
    
    def test_create_jwt_token(self):
        """测试创建JWT令牌"""
        openid = "test_openid"
        unionid = "test_unionid"
        
        token = self.service.create_jwt_token(openid, unionid)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_session_success(self):
        """测试成功创建会话"""
        token = "test_token"
        openid = "test_openid"
        unionid = "test_unionid"
        session_key = "test_session_key"
        user_data = {"name": "测试用户", "permission": "user"}
        
        result = self.service.create_session(
            self.redis_mock, token, openid, unionid, session_key, user_data
        )
        
        assert result is True
        self.redis_mock.hset.assert_called_once()
        self.redis_mock.expire.assert_called_once()
    
    def test_delete_session_success(self):
        """测试成功删除会话"""
        token = "test_token"
        self.redis_mock.delete.return_value = 1
        
        result = self.service.delete_session(self.redis_mock, token)
        
        assert result is True
        self.redis_mock.delete.assert_called_once_with(f"session:{token}")
    
    def test_delete_session_not_found(self):
        """测试删除不存在的会话"""
        token = "nonexistent_token"
        self.redis_mock.delete.return_value = 0
        
        result = self.service.delete_session(self.redis_mock, token)
        
        assert result is False
    
    def test_mask_sensitive_data(self):
        """测试敏感数据脱敏"""
        # 测试正常长度的数据
        data = "1234567890abcdef"
        masked = self.service.mask_sensitive_data(data, 6)
        assert masked == "123456**********"
        
        # 测试短数据
        short_data = "123"
        masked_short = self.service.mask_sensitive_data(short_data, 6)
        assert masked_short == "123"
        
        # 测试空数据
        empty_data = ""
        masked_empty = self.service.mask_sensitive_data(empty_data, 6)
        assert masked_empty == ""
    
    @pytest.mark.asyncio
    async def test_process_login_success(self, db: Session):
        """测试完整登录流程成功"""
        mock_response = mock_douyin_api_response()
        login_request = DouyinLoginRequest(code="test_code")
        ip_address = "192.168.1.100"
        user_agent = "test_agent"
        
        with patch.object(self.service, 'exchange_code_for_session', new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_response
            
            with patch.object(self.service, 'create_session') as mock_create_session:
                mock_create_session.return_value = True
                
                response, error = await self.service.process_login(
                    db, self.redis_mock, login_request, ip_address, user_agent
                )
        
        assert response is not None
        assert error is None
        assert response.token is not None
        assert response.openid is not None
        assert response.user_info is not None
    
    @pytest.mark.asyncio
    async def test_process_login_api_failure(self, db: Session):
        """测试登录流程中API调用失败"""
        login_request = DouyinLoginRequest(code="invalid_code")
        ip_address = "192.168.1.100"
        user_agent = "test_agent"
        
        with patch.object(self.service, 'exchange_code_for_session', new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = None
            
            response, error = await self.service.process_login(
                db, self.redis_mock, login_request, ip_address, user_agent
            )
        
        assert response is None
        assert error is not None
        assert "Failed to exchange code with Douyin API" in error
    
    @pytest.mark.asyncio
    async def test_process_login_session_creation_failure(self, db: Session):
        """测试登录流程中会话创建失败"""
        mock_response = mock_douyin_api_response()
        login_request = DouyinLoginRequest(code="test_code")
        ip_address = "192.168.1.100"
        user_agent = "test_agent"
        
        with patch.object(self.service, 'exchange_code_for_session', new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_response
            
            with patch.object(self.service, 'create_session') as mock_create_session:
                mock_create_session.return_value = False
                
                response, error = await self.service.process_login(
                    db, self.redis_mock, login_request, ip_address, user_agent
                )
        
        assert response is None
        assert error == "Failed to create session"
    
    def test_logout_user_success(self, db: Session):
        """测试用户登出成功"""
        openid = "test_openid"
        token = "test_token"
        
        with patch.object(self.service, 'delete_session') as mock_delete:
            mock_delete.return_value = True
            
            result = self.service.logout_user(db, self.redis_mock, openid, token)
        
        assert result is True
    
    def test_logout_user_failure(self, db: Session):
        """测试用户登出失败"""
        openid = "test_openid"
        token = "test_token"
        
        with patch.object(self.service, 'delete_session') as mock_delete:
            mock_delete.return_value = False
            
            result = self.service.logout_user(db, self.redis_mock, openid, token)
        
        assert result is False
    
    def test_refresh_user_token_success(self):
        """测试令牌刷新成功"""
        current_token = "current_token"
        session_data = {
            "openid": "test_openid",
            "unionid": "test_unionid",
            "session_key": "test_session_key",
            "name": "测试用户"
        }
        
        self.redis_mock.hgetall.return_value = session_data
        
        with patch.object(self.service, 'create_session') as mock_create:
            mock_create.return_value = True
            
            new_token = self.service.refresh_user_token(self.redis_mock, current_token)
        
        assert new_token is not None
        assert isinstance(new_token, str)
        assert new_token != current_token
    
    def test_refresh_user_token_no_session(self):
        """测试令牌刷新时无会话数据"""
        current_token = "nonexistent_token"
        self.redis_mock.hgetall.return_value = {}
        
        new_token = self.service.refresh_user_token(self.redis_mock, current_token)
        
        assert new_token is None
    
    def test_refresh_user_token_create_session_failure(self):
        """测试令牌刷新时新会话创建失败"""
        current_token = "current_token"
        session_data = {
            "openid": "test_openid",
            "unionid": "test_unionid",
            "session_key": "test_session_key"
        }
        
        self.redis_mock.hgetall.return_value = session_data
        
        with patch.object(self.service, 'create_session') as mock_create:
            mock_create.return_value = False
            
            new_token = self.service.refresh_user_token(self.redis_mock, current_token)
        
        assert new_token is None
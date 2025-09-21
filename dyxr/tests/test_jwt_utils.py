import pytest
import jwt
from datetime import datetime, timedelta
from utils.jwt_utils import JWTManager, create_session_token, mask_sensitive_data
from config import settings


class TestJWTManager:
    """JWT管理器测试"""
    
    def test_create_and_verify_token(self):
        """测试创建和验证令牌"""
        data = {"openid": "test_openid", "unionid": "test_unionid"}
        token = JWTManager.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌内容
        payload = JWTManager.verify_token(token)
        assert payload is not None
        assert payload["openid"] == "test_openid"
        assert payload["unionid"] == "test_unionid"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_verify_invalid_token(self):
        """测试验证无效令牌"""
        invalid_token = "invalid.token.string"
        payload = JWTManager.verify_token(invalid_token)
        assert payload is None
    
    def test_extract_openid_from_token(self):
        """测试从令牌中提取openid"""
        openid = "test_openid_123"
        data = {"openid": openid, "unionid": "test_unionid"}
        token = JWTManager.create_access_token(data)
        
        extracted_openid = JWTManager.extract_openid_from_token(token)
        assert extracted_openid == openid
    
    def test_is_token_expired(self):
        """测试检查令牌是否过期"""
        # 测试有效令牌
        data = {"openid": "test_openid"}
        token = JWTManager.create_access_token(data)
        assert JWTManager.is_token_expired(token) is False
        
        # 测试无效令牌
        invalid_token = "invalid.token"
        assert JWTManager.is_token_expired(invalid_token) is True


class TestHelperFunctions:
    """辅助函数测试"""
    
    def test_create_session_token(self):
        """测试创建会话令牌"""
        openid = "test_openid"
        unionid = "test_unionid"
        
        token = create_session_token(openid, unionid)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌内容
        payload = JWTManager.verify_token(token)
        assert payload is not None
        assert payload["openid"] == openid
        assert payload["unionid"] == unionid
        assert payload["type"] == "access_token"
    
    def test_mask_sensitive_data(self):
        """测试敏感数据脱敏"""
        # 测试正常长度的数据
        data = "1234567890"
        masked = mask_sensitive_data(data)
        assert masked == "123***890"
        
        # 测试自定义显示字符数
        masked = mask_sensitive_data(data, show_chars=2)
        assert masked == "12***90"
        
        # 测试短数据
        short_data = "123"
        masked = mask_sensitive_data(short_data)
        assert masked == "123"  # 不脱敏
        
        # 测试空数据
        empty_data = ""
        masked = mask_sensitive_data(empty_data)
        assert masked == ""
        
        # 测试None数据
        none_data = None
        masked = mask_sensitive_data(none_data)
        assert masked is None


if __name__ == "__main__":
    pytest.main([__file__])
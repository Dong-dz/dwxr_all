"""
测试抖音相关的数据模型
"""
import uuid
from datetime import datetime

import pytest
from sqlmodel import Session

from app.models import (
    DouyinUser, DouyinUserCreate, DouyinUserUpdate,
    BiaodianItem, BiaodianItemCreate, BiaodianItemUpdate,
    DouyinLoginLog, DouyinLoginRequest, DouyinLoginResponse
)


class TestDouyinUserModel:
    """抖音用户模型测试"""
    
    def test_create_douyin_user(self):
        """测试创建抖音用户"""
        user_data = DouyinUserCreate(
            openid="test_openid_123",
            unionid="test_unionid_123",
            name="测试用户",
            user_type="normal",
            permission="user",
            level="1",
            uuid=str(uuid.uuid4()),
            avatar_url="https://example.com/avatar.jpg",
            phone="13800138000",
            is_active=True
        )
        
        # 验证数据有效性
        assert user_data.openid == "test_openid_123"
        assert user_data.name == "测试用户"
        assert user_data.is_active is True
        assert user_data.permission == "user"
    
    def test_douyin_user_defaults(self):
        """测试抖音用户默认值"""
        user_data = DouyinUserCreate(
            openid="test_openid_456",
            uuid=str(uuid.uuid4())
        )
        
        assert user_data.user_type == "normal"
        assert user_data.permission == "user"
        assert user_data.level == "1"
        assert user_data.is_active is True
        assert user_data.unionid is None
        assert user_data.name is None
    
    def test_update_douyin_user(self):
        """测试更新抖音用户"""
        update_data = DouyinUserUpdate(
            name="新用户名",
            avatar_url="https://example.com/new_avatar.jpg",
            phone="13900139000"
        )
        
        assert update_data.name == "新用户名"
        assert update_data.avatar_url == "https://example.com/new_avatar.jpg"
        assert update_data.phone == "13900139000"


class TestBiaodianItemModel:
    """标点信息模型测试"""
    
    def test_create_biaodian_item(self):
        """测试创建标点信息"""
        item_data = BiaodianItemCreate(
            latitude="39.9042",
            longitude="116.4074",
            beizhu="北京天安门附近",
            weather="晴天",
            zhuangbei="台钓竿",
            fishing_type=1,
            yuhuo="鲫鱼2条",
            tuijian="5星",
            is_public=True,
            city="北京",
            province="北京市",
            title="天安门钓点"
        )
        
        assert item_data.latitude == "39.9042"
        assert item_data.longitude == "116.4074"
        assert item_data.fishing_type == 1
        assert item_data.is_public is True
        assert item_data.title == "天安门钓点"
    
    def test_biaodian_item_defaults(self):
        """测试标点信息默认值"""
        item_data = BiaodianItemCreate(
            latitude="39.9042",
            longitude="116.4074",
            fishing_type=2,
            tuijian="3星"
        )
        
        assert item_data.is_public is False
        assert item_data.beizhu is None
        assert item_data.weather is None
        assert item_data.city is None
    
    def test_update_biaodian_item(self):
        """测试更新标点信息"""
        update_data = BiaodianItemUpdate(
            beizhu="更新后的备注",
            weather="阴天",
            is_public=True,
            tuijian="4星"
        )
        
        assert update_data.beizhu == "更新后的备注"
        assert update_data.weather == "阴天"
        assert update_data.is_public is True
        assert update_data.tuijian == "4星"
    
    def test_fishing_type_validation(self):
        """测试钓鱼类型验证"""
        # 测试有效的钓鱼类型
        for fishing_type in [1, 2, 3]:
            item_data = BiaodianItemCreate(
                latitude="39.9042",
                longitude="116.4074",
                fishing_type=fishing_type,
                tuijian="5星"
            )
            assert item_data.fishing_type == fishing_type


class TestDouyinLoginLog:
    """抖音登录日志模型测试"""
    
    def test_create_login_log(self):
        """测试创建登录日志"""
        log_data = DouyinLoginLog(
            openid="test_openid_789",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0...",
            login_result=1,
            error_message=None
        )
        
        assert log_data.openid == "test_openid_789"
        assert log_data.ip_address == "192.168.1.100"
        assert log_data.login_result == 1
        assert log_data.error_message is None
        assert isinstance(log_data.created_at, datetime)
    
    def test_login_log_defaults(self):
        """测试登录日志默认值"""
        log_data = DouyinLoginLog(
            openid="test_openid_999"
        )
        
        assert log_data.login_result == 1
        assert log_data.ip_address is None
        assert log_data.user_agent is None
        assert log_data.error_message is None


class TestDouyinLoginModels:
    """抖音登录相关模型测试"""
    
    def test_login_request(self):
        """测试登录请求模型"""
        request_data = DouyinLoginRequest(
            code="test_code_123456"
        )
        
        assert request_data.code == "test_code_123456"
    
    def test_login_response(self):
        """测试登录响应模型"""
        response_data = DouyinLoginResponse(
            token="jwt_token_example",
            openid="masked_openid",
            unionid="masked_unionid",
            user_info=None
        )
        
        assert response_data.token == "jwt_token_example"
        assert response_data.openid == "masked_openid"
        assert response_data.unionid == "masked_unionid"
        assert response_data.user_info is None
    
    def test_login_response_with_user_info(self, db: Session):
        """测试包含用户信息的登录响应"""
        from app.models import DouyinUserPublic
        
        user_info = DouyinUserPublic(
            id=uuid.uuid4(),
            openid="test_openid",
            unionid="test_unionid",
            name="测试用户",
            user_type="normal",
            permission="user",
            level="1",
            uuid=str(uuid.uuid4()),
            avatar_url=None,
            phone=None,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login_at=None
        )
        
        response_data = DouyinLoginResponse(
            token="jwt_token_example",
            openid="masked_openid",
            unionid="masked_unionid",
            user_info=user_info
        )
        
        assert response_data.user_info is not None
        assert response_data.user_info.name == "测试用户"
        assert response_data.user_info.permission == "user"
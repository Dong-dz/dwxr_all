import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models.userModel import User
from services.user_service import UserService
from schemas.userSche import UserCreate, UserUpdate


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def test_db():
    """创建测试数据库"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    """创建数据库会话"""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def user_service():
    """创建用户服务实例"""
    return UserService()


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return UserCreate(
        openid="test_openid_001",
        unionid="test_unionid_001",
        name="测试用户",
        type="normal",
        quanxian="user",
        dengji="1",
        uuid=str(uuid.uuid4()),
        status=1
    )


class TestUserService:
    """用户服务测试"""
    
    def test_create_user(self, db_session, user_service, sample_user_data):
        """测试创建用户"""
        user = user_service.create_user(db_session, sample_user_data)
        
        assert user is not None
        assert user.openid == sample_user_data.openid
        assert user.name == sample_user_data.name
        assert user.type == sample_user_data.type
        assert user.status == 1
    
    def test_get_user_by_openid(self, db_session, user_service, sample_user_data):
        """测试根据openid获取用户"""
        # 先创建用户
        created_user = user_service.create_user(db_session, sample_user_data)
        assert created_user is not None
        
        # 获取用户
        user = user_service.get_user_by_openid(db_session, sample_user_data.openid)
        
        assert user is not None
        assert user.openid == sample_user_data.openid
        assert user.name == sample_user_data.name
    
    def test_get_user_by_openid_not_found(self, db_session, user_service):
        """测试获取不存在的用户"""
        user = user_service.get_user_by_openid(db_session, "nonexistent_openid")
        assert user is None
    
    def test_update_user(self, db_session, user_service, sample_user_data):
        """测试更新用户信息"""
        # 先创建用户
        created_user = user_service.create_user(db_session, sample_user_data)
        assert created_user is not None
        
        # 更新用户
        update_data = UserUpdate(
            name="更新后的用户名",
            type="vip",
            phone="13800138000"
        )
        
        updated_user = user_service.update_user(db_session, sample_user_data.openid, update_data)
        
        assert updated_user is not None
        assert updated_user.name == "更新后的用户名"
        assert updated_user.type == "vip"
        assert updated_user.phone == "13800138000"
    
    def test_delete_user(self, db_session, user_service, sample_user_data):
        """测试删除用户（软删除）"""
        # 先创建用户
        created_user = user_service.create_user(db_session, sample_user_data)
        assert created_user is not None
        
        # 删除用户
        success = user_service.delete_user(db_session, sample_user_data.openid)
        assert success is True
        
        # 验证用户状态
        user = user_service.get_user_by_openid(db_session, sample_user_data.openid)
        assert user is not None
        assert user.status == 0  # 软删除，状态变为0
    
    def test_activate_user(self, db_session, user_service, sample_user_data):
        """测试激活用户"""
        # 先创建用户并删除
        created_user = user_service.create_user(db_session, sample_user_data)
        assert created_user is not None
        
        user_service.delete_user(db_session, sample_user_data.openid)
        
        # 激活用户
        success = user_service.activate_user(db_session, sample_user_data.openid)
        assert success is True
        
        # 验证用户状态
        user = user_service.get_user_by_openid(db_session, sample_user_data.openid)
        assert user is not None
        assert user.status == 1  # 激活后状态变为1
    
    def test_get_user_profile(self, db_session, user_service, sample_user_data):
        """测试获取用户资料"""
        # 先创建用户
        created_user = user_service.create_user(db_session, sample_user_data)
        assert created_user is not None
        
        # 获取用户资料
        profile = user_service.get_user_profile(db_session, sample_user_data.openid)
        
        assert profile is not None
        assert profile.openid == sample_user_data.openid
        assert profile.name == sample_user_data.name
        assert profile.uuid == sample_user_data.uuid
    
    def test_get_users(self, db_session, user_service):
        """测试获取用户列表"""
        # 创建多个测试用户
        for i in range(3):
            user_data = UserCreate(
                openid=f"test_openid_{i}",
                unionid=f"test_unionid_{i}",
                name=f"测试用户{i}",
                type="normal",
                quanxian="user",
                dengji="1",
                uuid=str(uuid.uuid4()),
                status=1
            )
            user_service.create_user(db_session, user_data)
        
        # 获取用户列表
        users = user_service.get_users(db_session, skip=0, limit=10)
        
        assert len(users) >= 3
        assert all(user.status == 1 for user in users)
    
    def test_get_user_count(self, db_session, user_service):
        """测试获取用户总数"""
        # 获取当前用户数量
        initial_count = user_service.get_user_count(db_session)
        
        # 创建新用户
        user_data = UserCreate(
            openid="count_test_openid",
            unionid="count_test_unionid",
            name="计数测试用户",
            type="normal",
            quanxian="user",
            dengji="1",
            uuid=str(uuid.uuid4()),
            status=1
        )
        user_service.create_user(db_session, user_data)
        
        # 验证用户数量增加
        new_count = user_service.get_user_count(db_session)
        assert new_count == initial_count + 1


if __name__ == "__main__":
    pytest.main([__file__])
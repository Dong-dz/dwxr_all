"""
测试标点信息API路由
"""
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import BiaodianItem, BiaodianItemCreate
from app.tests.utils.douyin import (
    create_test_douyin_user,
    create_test_admin_user,
    get_douyin_token_headers,
    get_douyin_admin_token_headers
)


def create_test_biaodian_item(db: Session, owner: any, is_public: bool = True) -> BiaodianItem:
    """创建测试标点"""
    from app.services.douyin_crud import biaodian_item_crud
    
    item_data = BiaodianItemCreate(
        latitude="39.9042",
        longitude="116.4074",
        beizhu="测试标点",
        weather="晴天",
        zhuangbei="台钓竿",
        fishing_type=1,
        yuhuo="鲫鱼2条",
        tuijian="5星",
        is_public=is_public,
        city="北京",
        province="北京市",
        title="测试钓点"
    )
    
    return biaodian_item_crud.create(db, item_data, owner.id, owner.openid)


class TestBiaodianCreate:
    """标点创建API测试"""
    
    def test_create_biaodian_success(self, client: TestClient, db: Session):
        """测试创建标点成功"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        item_data = {
            "latitude": "39.9042",
            "longitude": "116.4074",
            "beizhu": "新建标点",
            "weather": "晴天",
            "fishing_type": 1,
            "tuijian": "5星",
            "is_public": True,
            "city": "北京",
            "title": "新钓点"
        }
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user, "openid": user.openid}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.create') as mock_create:
                mock_item = BiaodianItem(**item_data, id=uuid.uuid4(), owner_id=user.id)
                mock_create.return_value = mock_item
                
                response = client.post("/api/v1/biaodian", json=item_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["latitude"] == "39.9042"
        assert data["title"] == "新钓点"
    
    def test_create_biaodian_unauthorized(self, client: TestClient):
        """测试未认证创建标点"""
        item_data = {
            "latitude": "39.9042",
            "longitude": "116.4074",
            "fishing_type": 1,
            "tuijian": "5星"
        }
        
        response = client.post("/api/v1/biaodian", json=item_data)
        
        assert response.status_code == 401


class TestBiaodianGet:
    """标点获取API测试"""
    
    def test_get_user_biaodian_items(self, client: TestClient, db: Session):
        """测试获取用户标点列表"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        # 创建测试标点
        test_items = [create_test_biaodian_item(db, user) for _ in range(3)]
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.get_by_owner') as mock_get:
                mock_get.return_value = test_items
                
                response = client.get("/api/v1/biaodian", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["data"]) == 3
    
    def test_get_public_biaodian_items(self, client: TestClient, db: Session):
        """测试获取公开标点列表"""
        user = create_test_douyin_user(db)
        test_items = [create_test_biaodian_item(db, user, is_public=True) for _ in range(2)]
        
        with patch('app.services.douyin_crud.biaodian_item_crud.get_public_items') as mock_get:
            mock_get.return_value = test_items
            
            response = client.get("/api/v1/biaodian/public")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2
    
    def test_get_public_biaodian_with_filters(self, client: TestClient, db: Session):
        """测试带过滤条件获取公开标点"""
        response = client.get("/api/v1/biaodian/public?fishing_type=1&city=北京")
        
        assert response.status_code == 200
    
    def test_search_biaodian_items(self, client: TestClient, db: Session):
        """测试搜索标点"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.search_items') as mock_search:
                mock_search.return_value = []
                
                response = client.get("/api/v1/biaodian/search?keyword=测试", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
    
    def test_search_biaodian_without_auth(self, client: TestClient):
        """测试未认证搜索标点（仅公开）"""
        with patch('app.services.douyin_crud.biaodian_item_crud.search_items') as mock_search:
            mock_search.return_value = []
            
            response = client.get("/api/v1/biaodian/search?keyword=测试")
        
        assert response.status_code == 200
    
    def test_get_nearby_biaodian_items(self, client: TestClient):
        """测试获取附近标点"""
        with patch('app.services.douyin_crud.biaodian_item_crud.get_nearby_items') as mock_nearby:
            mock_nearby.return_value = []
            
            response = client.get("/api/v1/biaodian/nearby?latitude=39.9042&longitude=116.4074")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data


class TestBiaodianDetail:
    """标点详情API测试"""
    
    def test_get_public_biaodian_item(self, client: TestClient, db: Session):
        """测试获取公开标点详情"""
        user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, user, is_public=True)
        
        with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
            mock_get.return_value = item
            
            response = client.get(f"/api/v1/biaodian/{item.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(item.id)
    
    def test_get_private_biaodian_item_by_owner(self, client: TestClient, db: Session):
        """测试所有者获取私密标点详情"""
        user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, user, is_public=False)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
                mock_get.return_value = item
                
                response = client.get(f"/api/v1/biaodian/{item.id}", headers=headers)
        
        assert response.status_code == 200
    
    def test_get_private_biaodian_item_unauthorized(self, client: TestClient, db: Session):
        """测试未认证获取私密标点详情"""
        user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, user, is_public=False)
        
        with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
            mock_get.return_value = item
            
            response = client.get(f"/api/v1/biaodian/{item.id}")
        
        assert response.status_code == 401
    
    def test_get_nonexistent_biaodian_item(self, client: TestClient):
        """测试获取不存在的标点详情"""
        nonexistent_id = str(uuid.uuid4())
        
        with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get(f"/api/v1/biaodian/{nonexistent_id}")
        
        assert response.status_code == 404


class TestBiaodianUpdate:
    """标点更新API测试"""
    
    def test_update_biaodian_item_success(self, client: TestClient, db: Session):
        """测试更新标点成功"""
        user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, user)
        headers = get_douyin_token_headers(client, user.openid)
        
        update_data = {
            "beizhu": "更新后的备注",
            "weather": "阴天",
            "tuijian": "4星"
        }
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.check_ownership') as mock_check:
                mock_check.return_value = True
                
                with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
                    mock_get.return_value = item
                    
                    with patch('app.services.douyin_crud.biaodian_item_crud.update') as mock_update:
                        updated_item = item
                        updated_item.beizhu = update_data["beizhu"]
                        mock_update.return_value = updated_item
                        
                        response = client.put(f"/api/v1/biaodian/{item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["beizhu"] == "更新后的备注"
    
    def test_update_biaodian_item_not_owner(self, client: TestClient, db: Session):
        """测试非所有者更新标点"""
        owner = create_test_douyin_user(db)
        other_user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, owner)
        headers = get_douyin_token_headers(client, other_user.openid)
        
        update_data = {"beizhu": "恶意更新"}
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": other_user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.check_ownership') as mock_check:
                mock_check.return_value = False
                
                response = client.put(f"/api/v1/biaodian/{item.id}", json=update_data, headers=headers)
        
        assert response.status_code == 404
        assert "标点不存在或无权修改" in response.json()["detail"]


class TestBiaodianDelete:
    """标点删除API测试"""
    
    def test_delete_biaodian_item_success(self, client: TestClient, db: Session):
        """测试删除标点成功"""
        user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, user)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.check_ownership') as mock_check:
                mock_check.return_value = True
                
                with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
                    mock_get.return_value = item
                    
                    with patch('app.services.douyin_crud.biaodian_item_crud.delete') as mock_delete:
                        mock_delete.return_value = True
                        
                        response = client.delete(f"/api/v1/biaodian/{item.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "标点删除成功"
    
    def test_delete_biaodian_item_not_owner(self, client: TestClient, db: Session):
        """测试非所有者删除标点"""
        owner = create_test_douyin_user(db)
        other_user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, owner)
        headers = get_douyin_token_headers(client, other_user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": other_user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.check_ownership') as mock_check:
                mock_check.return_value = False
                
                response = client.delete(f"/api/v1/biaodian/{item.id}", headers=headers)
        
        assert response.status_code == 404


class TestBiaodianTogglePublic:
    """标点公开状态切换API测试"""
    
    def test_toggle_biaodian_public_success(self, client: TestClient, db: Session):
        """测试切换标点公开状态成功"""
        user = create_test_douyin_user(db)
        item = create_test_biaodian_item(db, user, is_public=False)
        headers = get_douyin_token_headers(client, user.openid)
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.check_ownership') as mock_check:
                mock_check.return_value = True
                
                with patch('app.services.douyin_crud.biaodian_item_crud.get_by_id') as mock_get:
                    mock_get.return_value = item
                    
                    with patch('app.services.douyin_crud.biaodian_item_crud.update') as mock_update:
                        updated_item = item
                        updated_item.is_public = True
                        mock_update.return_value = updated_item
                        
                        response = client.patch(f"/api/v1/biaodian/{item.id}/toggle-public", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"] is True


class TestBiaodianStatistics:
    """标点统计API测试"""
    
    def test_get_biaodian_statistics(self, client: TestClient, db: Session):
        """测试获取标点统计"""
        user = create_test_douyin_user(db)
        headers = get_douyin_token_headers(client, user.openid)
        
        mock_stats = {
            "total_count": 10,
            "public_count": 7,
            "private_count": 3,
            "type_stats": {1: 5, 2: 3, 3: 2},
            "city_stats": {"北京": 6, "上海": 4}
        }
        
        with patch('app.api.deps_douyin.get_current_douyin_user') as mock_auth:
            mock_auth.return_value = {"user": user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.get_statistics') as mock_stats_func:
                mock_stats_func.return_value = mock_stats
                
                response = client.get("/api/v1/biaodian/statistics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 10
        assert data["public_count"] == 7
        assert data["private_count"] == 3


class TestBiaodianAdminFeatures:
    """标点管理员功能测试"""
    
    def test_get_all_biaodian_items_as_admin(self, client: TestClient, db: Session):
        """测试管理员获取所有标点"""
        admin_user = create_test_admin_user(db)
        headers = get_douyin_admin_token_headers(client, admin_user.openid)
        
        with patch('app.api.deps_douyin.get_current_admin_user') as mock_auth:
            mock_auth.return_value = {"user": admin_user}
            
            with patch('app.services.douyin_crud.biaodian_item_crud.get_public_items') as mock_get:
                mock_get.return_value = []
                
                response = client.get("/api/v1/biaodian/admin/all", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data
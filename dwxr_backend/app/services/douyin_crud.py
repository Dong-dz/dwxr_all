"""
抖音用户和标点信息的CRUD操作
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlmodel import Session, select, or_, and_

from app.models import (
    DouyinUser, DouyinUserCreate, DouyinUserUpdate,
    BiaodianItem, BiaodianItemCreate, BiaodianItemUpdate
)

class DouyinUserCRUD:
    """抖音用户CRUD操作"""
    
    def get_by_openid(self, session: Session, openid: str) -> Optional[DouyinUser]:
        """根据openid获取用户"""
        statement = select(DouyinUser).where(DouyinUser.openid == openid)
        return session.exec(statement).first()
    
    def get_by_id(self, session: Session, user_id: uuid.UUID) -> Optional[DouyinUser]:
        """根据ID获取用户"""
        return session.get(DouyinUser, user_id)
    
    def create(self, session: Session, user_in: DouyinUserCreate) -> DouyinUser:
        """创建用户"""
        user = DouyinUser.model_validate(user_in)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    def update(
        self, 
        session: Session, 
        user: DouyinUser, 
        user_in: DouyinUserUpdate
    ) -> DouyinUser:
        """更新用户"""
        user_data = user_in.model_dump(exclude_unset=True)
        user_data["updated_at"] = datetime.utcnow()
        
        for field, value in user_data.items():
            setattr(user, field, value)
        
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    def get_multi(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[bool] = None,
        user_type: Optional[str] = None
    ) -> List[DouyinUser]:
        """获取用户列表"""
        statement = select(DouyinUser)
        
        # 添加过滤条件
        if status is not None:
            statement = statement.where(DouyinUser.is_active == status)
        
        if user_type:
            statement = statement.where(DouyinUser.user_type == user_type)
        
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())
    
    def search(
        self,
        session: Session,
        keyword: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[DouyinUser]:
        """搜索用户"""
        statement = select(DouyinUser).where(
            or_(
                DouyinUser.name.contains(keyword),
                DouyinUser.openid.contains(keyword),
                DouyinUser.phone.contains(keyword) if keyword.isdigit() else False
            )
        ).offset(skip).limit(limit)
        
        return list(session.exec(statement).all())
    
    def delete(self, session: Session, user: DouyinUser) -> bool:
        """删除用户（软删除）"""
        try:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            session.add(user)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False


class BiaodianItemCRUD:
    """标点信息CRUD操作"""
    
    def get_by_id(self, session: Session, item_id: uuid.UUID) -> Optional[BiaodianItem]:
        """根据ID获取标点"""
        return session.get(BiaodianItem, item_id)
    
    def create(
        self, 
        session: Session, 
        item_in: BiaodianItemCreate, 
        owner_id: uuid.UUID,
        openid: str
    ) -> BiaodianItem:
        """创建标点"""
        item_data = item_in.model_dump()
        item_data["owner_id"] = owner_id
        item_data["openid"] = openid
        
        item = BiaodianItem(**item_data)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    
    def update(
        self, 
        session: Session, 
        item: BiaodianItem, 
        item_in: BiaodianItemUpdate
    ) -> BiaodianItem:
        """更新标点"""
        item_data = item_in.model_dump(exclude_unset=True)
        item_data["updated_at"] = datetime.utcnow()
        
        for field, value in item_data.items():
            setattr(item, field, value)
        
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    
    def delete(self, session: Session, item: BiaodianItem) -> bool:
        """删除标点"""
        try:
            session.delete(item)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
    
    def get_by_owner(
        self,
        session: Session,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        is_public: Optional[bool] = None
    ) -> List[BiaodianItem]:
        """获取用户的标点列表"""
        statement = select(BiaodianItem).where(BiaodianItem.owner_id == owner_id)
        
        if is_public is not None:
            statement = statement.where(BiaodianItem.is_public == is_public)
        
        statement = statement.offset(skip).limit(limit).order_by(BiaodianItem.created_at.desc())
        return list(session.exec(statement).all())
    
    def get_public_items(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        fishing_type: Optional[int] = None,
        city: Optional[str] = None,
        province: Optional[str] = None
    ) -> List[BiaodianItem]:
        """获取公开的标点列表"""
        statement = select(BiaodianItem).where(BiaodianItem.is_public == True)
        
        # 添加过滤条件
        if fishing_type is not None:
            statement = statement.where(BiaodianItem.fishing_type == fishing_type)
        
        if city:
            statement = statement.where(BiaodianItem.city == city)
        
        if province:
            statement = statement.where(BiaodianItem.province == province)
        
        statement = statement.offset(skip).limit(limit).order_by(BiaodianItem.created_at.desc())
        return list(session.exec(statement).all())
    
    def search_items(
        self,
        session: Session,
        keyword: str,
        owner_id: Optional[uuid.UUID] = None,
        is_public_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[BiaodianItem]:
        """搜索标点"""
        statement = select(BiaodianItem)
        
        # 搜索条件
        search_conditions = [
            BiaodianItem.title.contains(keyword),
            BiaodianItem.beizhu.contains(keyword),
            BiaodianItem.city.contains(keyword),
            BiaodianItem.province.contains(keyword)
        ]
        
        statement = statement.where(or_(*search_conditions))
        
        # 权限过滤
        if is_public_only:
            statement = statement.where(BiaodianItem.is_public == True)
        elif owner_id:
            statement = statement.where(
                or_(
                    BiaodianItem.is_public == True,
                    BiaodianItem.owner_id == owner_id
                )
            )
        
        statement = statement.offset(skip).limit(limit).order_by(BiaodianItem.created_at.desc())
        return list(session.exec(statement).all())
    
    def get_nearby_items(
        self,
        session: Session,
        latitude: float,
        longitude: float,
        radius: float = 0.01,  # 约1公里
        is_public_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[BiaodianItem]:
        """获取附近的标点（简单的经纬度范围查询）"""
        # 简单的经纬度范围查询，实际应用中可以使用PostGIS等地理扩展
        lat_min = latitude - radius
        lat_max = latitude + radius
        lng_min = longitude - radius
        lng_max = longitude + radius
        
        statement = select(BiaodianItem).where(
            and_(
                BiaodianItem.latitude.between(str(lat_min), str(lat_max)),
                BiaodianItem.longitude.between(str(lng_min), str(lng_max))
            )
        )
        
        if is_public_only:
            statement = statement.where(BiaodianItem.is_public == True)
        
        statement = statement.offset(skip).limit(limit).order_by(BiaodianItem.created_at.desc())
        return list(session.exec(statement).all())
    
    def check_ownership(
        self, 
        session: Session, 
        item_id: uuid.UUID, 
        owner_id: uuid.UUID
    ) -> bool:
        """检查标点所有权"""
        statement = select(BiaodianItem).where(
            and_(
                BiaodianItem.id == item_id,
                BiaodianItem.owner_id == owner_id
            )
        )
        item = session.exec(statement).first()
        return item is not None
    
    def get_statistics(
        self, 
        session: Session, 
        owner_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """获取标点统计信息"""
        statement = select(BiaodianItem)
        
        if owner_id:
            statement = statement.where(BiaodianItem.owner_id == owner_id)
        
        items = list(session.exec(statement).all())
        
        total_count = len(items)
        public_count = sum(1 for item in items if item.is_public)
        private_count = total_count - public_count
        
        # 按钓鱼类型统计
        type_stats = {}
        for item in items:
            fishing_type = item.fishing_type
            type_stats[fishing_type] = type_stats.get(fishing_type, 0) + 1
        
        # 按城市统计
        city_stats = {}
        for item in items:
            city = item.city or "未知"
            city_stats[city] = city_stats.get(city, 0) + 1
        
        return {
            "total_count": total_count,
            "public_count": public_count,
            "private_count": private_count,
            "type_stats": type_stats,
            "city_stats": city_stats
        }


# 全局CRUD实例
douyin_user_crud = DouyinUserCRUD()
biaodian_item_crud = BiaodianItemCRUD()
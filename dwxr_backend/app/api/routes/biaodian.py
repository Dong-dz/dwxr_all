"""
标点信息管理API路由
"""
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.api.deps_douyin import SessionDep, CurrentDouyinUser, CurrentAdminUser
from app.models import (
    BiaodianItemCreate, BiaodianItemUpdate, BiaodianItemPublic, BiaodianItemsPublic,
    Message
)
from app.services.douyin_crud import biaodian_item_crud

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/biaodian",
    tags=["标点信息管理"],
)

@router.post("", response_model=BiaodianItemPublic, summary="创建标点")
async def create_biaodian_item(
    item_data: BiaodianItemCreate,
    session: SessionDep,
    current_user: CurrentDouyinUser
):
    """
    创建新的标点信息

    需要用户认证
    """
    try:
        user = current_user["user"]
        openid = current_user["openid"]
        
        item = biaodian_item_crud.create(
            session=session,
            item_in=item_data,
            owner_id=user.id,
            openid=openid
        )
        
        return BiaodianItemPublic.model_validate(item)

    except Exception as e:
        logger.error(f"Create biaodian item error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建标点失败"
        )


@router.get("", response_model=BiaodianItemsPublic, summary="获取标点列表")
async def get_biaodian_items(
    session: SessionDep,
    current_user: CurrentDouyinUser,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制"),
    is_public: Optional[bool] = Query(None, description="过滤公开/私密标点")
):
    """
    获取当前用户的标点列表

    需要用户认证
    """
    try:
        user = current_user["user"]
        
        items = biaodian_item_crud.get_by_owner(
            session=session,
            owner_id=user.id,
            skip=skip,
            limit=limit,
            is_public=is_public
        )
        
        items_public = [BiaodianItemPublic.model_validate(item) for item in items]
        
        return BiaodianItemsPublic(data=items_public, count=len(items_public))

    except Exception as e:
        logger.error(f"Get biaodian items error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取标点列表失败"
        )


@router.get("/public", response_model=BiaodianItemsPublic, summary="获取公开标点列表")
async def get_public_biaodian_items(
    session: SessionDep,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制"),
    fishing_type: Optional[int] = Query(None, description="钓鱼类型过滤"),
    city: Optional[str] = Query(None, description="城市过滤"),
    province: Optional[str] = Query(None, description="省份过滤")
):
    """
    获取公开的标点列表

    无需认证
    """
    try:
        items = biaodian_item_crud.get_public_items(
            session=session,
            skip=skip,
            limit=limit,
            fishing_type=fishing_type,
            city=city,
            province=province
        )
        
        items_public = [BiaodianItemPublic.model_validate(item) for item in items]
        
        return BiaodianItemsPublic(data=items_public, count=len(items_public))

    except Exception as e:
        logger.error(f"Get public biaodian items error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取公开标点列表失败"
        )


@router.get("/search", response_model=BiaodianItemsPublic, summary="搜索标点")
async def search_biaodian_items(
    session: SessionDep,
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制"),
    current_user: Optional[CurrentDouyinUser] = Depends()
):
    """
    搜索标点信息

    可选择用户认证（认证后可搜索自己的私密标点）
    """
    try:
        owner_id = None
        is_public_only = True
        
        if current_user:
            user = current_user["user"]
            owner_id = user.id
            is_public_only = False
        
        items = biaodian_item_crud.search_items(
            session=session,
            keyword=keyword.strip(),
            owner_id=owner_id,
            is_public_only=is_public_only,
            skip=skip,
            limit=limit
        )
        
        items_public = [BiaodianItemPublic.model_validate(item) for item in items]
        
        return BiaodianItemsPublic(data=items_public, count=len(items_public))

    except Exception as e:
        logger.error(f"Search biaodian items error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索标点失败"
        )


@router.get("/nearby", response_model=BiaodianItemsPublic, summary="获取附近标点")
async def get_nearby_biaodian_items(
    session: SessionDep,
    latitude: float = Query(..., description="纬度"),
    longitude: float = Query(..., description="经度"),
    radius: float = Query(0.01, ge=0.001, le=1.0, description="搜索半径（度）"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制")
):
    """
    获取附近的标点（仅公开标点）

    无需认证
    """
    try:
        items = biaodian_item_crud.get_nearby_items(
            session=session,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            is_public_only=True,
            skip=skip,
            limit=limit
        )
        
        items_public = [BiaodianItemPublic.model_validate(item) for item in items]
        
        return BiaodianItemsPublic(data=items_public, count=len(items_public))

    except Exception as e:
        logger.error(f"Get nearby biaodian items error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取附近标点失败"
        )


@router.get("/statistics", summary="获取标点统计")
async def get_biaodian_statistics(
    session: SessionDep,
    current_user: CurrentDouyinUser
):
    """
    获取用户的标点统计信息

    需要用户认证
    """
    try:
        user = current_user["user"]
        
        stats = biaodian_item_crud.get_statistics(session=session, owner_id=user.id)
        
        return stats

    except Exception as e:
        logger.error(f"Get biaodian statistics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取标点统计失败"
        )


@router.get("/{item_id}", response_model=BiaodianItemPublic, summary="获取标点详情")
async def get_biaodian_item(
    item_id: str,
    session: SessionDep,
    current_user: Optional[CurrentDouyinUser] = Depends()
):
    """
    获取标点详情

    公开标点无需认证，私密标点需要所有者认证
    """
    try:
        try:
            item_uuid = uuid.UUID(item_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的标点ID格式"
            )
        
        item = biaodian_item_crud.get_by_id(session, item_uuid)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="标点不存在"
            )
        
        # 检查访问权限
        if not item.is_public:
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="访问私密标点需要认证"
                )
            
            user = current_user["user"]
            if item.owner_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权访问此标点"
                )
        
        return BiaodianItemPublic.model_validate(item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get biaodian item error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取标点详情失败"
        )


@router.put("/{item_id}", response_model=BiaodianItemPublic, summary="更新标点")
async def update_biaodian_item(
    item_id: str,
    item_data: BiaodianItemUpdate,
    session: SessionDep,
    current_user: CurrentDouyinUser
):
    """
    更新标点信息

    需要用户认证且为标点所有者
    """
    try:
        try:
            item_uuid = uuid.UUID(item_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的标点ID格式"
            )
        
        user = current_user["user"]
        
        # 检查所有权
        if not biaodian_item_crud.check_ownership(session, item_uuid, user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="标点不存在或无权修改"
            )
        
        item = biaodian_item_crud.get_by_id(session, item_uuid)
        updated_item = biaodian_item_crud.update(session, item, item_data)
        
        return BiaodianItemPublic.model_validate(updated_item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update biaodian item error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新标点失败"
        )


@router.delete("/{item_id}", response_model=Message, summary="删除标点")
async def delete_biaodian_item(
    item_id: str,
    session: SessionDep,
    current_user: CurrentDouyinUser
):
    """
    删除标点信息

    需要用户认证且为标点所有者
    """
    try:
        try:
            item_uuid = uuid.UUID(item_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的标点ID格式"
            )
        
        user = current_user["user"]
        
        # 检查所有权
        if not biaodian_item_crud.check_ownership(session, item_uuid, user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="标点不存在或无权删除"
            )
        
        item = biaodian_item_crud.get_by_id(session, item_uuid)
        success = biaodian_item_crud.delete(session, item)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除标点失败"
            )
        
        return Message(message="标点删除成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete biaodian item error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除标点失败"
        )


@router.patch("/{item_id}/toggle-public", response_model=BiaodianItemPublic, summary="切换标点公开状态")
async def toggle_biaodian_public(
    item_id: str,
    session: SessionDep,
    current_user: CurrentDouyinUser
):
    """
    切换标点的公开/私密状态

    需要用户认证且为标点所有者
    """
    try:
        try:
            item_uuid = uuid.UUID(item_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的标点ID格式"
            )
        
        user = current_user["user"]
        
        # 检查所有权
        if not biaodian_item_crud.check_ownership(session, item_uuid, user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="标点不存在或无权修改"
            )
        
        item = biaodian_item_crud.get_by_id(session, item_uuid)
        
        # 切换公开状态
        update_data = BiaodianItemUpdate(is_public=not item.is_public)
        updated_item = biaodian_item_crud.update(session, item, update_data)
        
        return BiaodianItemPublic.model_validate(updated_item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle biaodian public error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换标点状态失败"
        )


# 管理员功能
@router.get("/admin/all", response_model=BiaodianItemsPublic, summary="获取所有标点（管理员）")
async def get_all_biaodian_items_admin(
    session: SessionDep,
    current_user: CurrentAdminUser,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数限制")
):
    """
    获取所有标点（管理员功能）

    需要管理员权限
    """
    try:
        items = biaodian_item_crud.get_public_items(
            session=session,
            skip=skip,
            limit=limit
        )
        
        # 管理员可以看到所有标点，包括私密标点
        # 这里为了简化，先使用get_public_items，实际应该有专门的方法
        
        items_public = [BiaodianItemPublic.model_validate(item) for item in items]
        
        return BiaodianItemsPublic(data=items_public, count=len(items_public))

    except Exception as e:
        logger.error(f"Get all biaodian items admin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取所有标点失败"
        )
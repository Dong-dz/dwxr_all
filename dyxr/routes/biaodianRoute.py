from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database import get_db
import logging
from typing import List
from schemas.biaodianSche import BiaoDianResponse
from services.biandianSele import get_user_by_openid
from services.biandianSele import get_biaodian_by_simi_pub
from services.biaodianAdd import create_biaodian
from schemas.biaodianSche import BiaoDianCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/biaodian",
    tags=["biaodian"]
)


@router.get("/{openid}", response_model=List[BiaoDianResponse])
# 根据openid查询标点
def get_user_by_id(openid: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"根据openid获取标点: {openid}")
        biaodian_user = get_user_by_openid(db, openid)
        if biaodian_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="根据openid未查询到标点"
            )
        return biaodian_user
    except Exception as e:
        logger.error(f"根据openid查询标点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询标点失败"
        )


@router.get("/simi/1", response_model=List[BiaoDianResponse])# 查询公开标点
def get_biaodian_by_simi(db: Session = Depends(get_db)):
    try:
        logger.info(f"获取公开标点")
        biaodian_simi = get_biaodian_by_simi_pub(db)
        if not biaodian_simi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未获取公开标点"
            )
        return biaodian_simi
    except Exception as e:
        logger.error(f"获取公开标点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取公开标点失败"
        )


@router.post("/add", response_model=BiaoDianResponse, status_code=status.HTTP_201_CREATED)
# 创建标点
def create_biaodian_endpoint(biaodian: BiaoDianCreate, db: Session = Depends(get_db)):
    try:
        db_biaodian = create_biaodian(db, biaodian)
        return db_biaodian
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except IntegrityError as e:
        logger.error(f"创建标点违反数据库约束: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="数据违反完整性约束"
        )
    except SQLAlchemyError as e:
        logger.error(f"创建标点数据库操作失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"创建标点失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建标点失败"
        )
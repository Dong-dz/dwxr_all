# file: services/biaodianAdd.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models.biaodianModel import Biaodian
from schemas.biaodianSche import BiaoDianCreate
from typing import Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_biaodian(db: Session, biaodian: BiaoDianCreate) -> dict:
    try:
        # 检查是否已存在相同 openid、latitude、longitude、simi 的标点
        existing_biaodian = db.query(Biaodian).filter(
   Biaodian.openid == biaodian.openid,
            Biaodian.latitude == biaodian.latitude,
            Biaodian.longitude == biaodian.longitude,
            Biaodian.simi == biaodian.simi
        ).first()

        if existing_biaodian:
            logger.info(f"尝试创建已存在的标点 openid: {biaodian.openid}, "
                        f"latitude: {biaodian.latitude}, longitude: {biaodian.longitude}, "
                        f"simi: {biaodian.simi}")
            raise ValueError("该标点已存在")

        # 创建新的标点对象
        db_biaodian = Biaodian(**biaodian.dict())
        db.add(db_biaodian)
        db.commit()
        db.refresh(db_biaodian)

        logger.info(f"成功创建标点: {db_biaodian.bd_id}")
        return {
            "bd_id": db_biaodian.bd_id,
            "latitude": db_biaodian.latitude,
            "longitude": db_biaodian.longitude,
            "beizhu": db_biaodian.beizhu,
            "weather": db_biaodian.weather,
            "zhuangbei": db_biaodian.zhuangbei,
            "type": db_biaodian.type,
            "yuhuo": db_biaodian.yuhuo,
            "tuijian": db_biaodian.tuijian,
            "userid": db_biaodian.userid,
            "simi": db_biaodian.simi,
            "city": db_biaodian.city,
            "province": db_biaodian.province,
            "openid": db_biaodian.openid,
            "biaoti": db_biaodian.biaoti
        }

    except ValueError:
        # 重新抛出业务逻辑异常
        db.rollback()
        raise
    except IntegrityError:
        # 处理数据库完整性约束错误
        db.rollback()
        logger.error(f"创建标点违反数据库约束: {biaodian.openid}")
        raise
    except SQLAlchemyError:
        # 处理其他数据库错误
        db.rollback()
        logger.error(f"创建标点数据库操作失败: {biaodian.openid}")
        raise
    except Exception:
        # 处理其他未预期的错误
        db.rollback()
        logger.error(f"创建标点失败: {biaodian.openid}")
        raise

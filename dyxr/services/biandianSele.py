from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.biaodianModel import Biaodian
from typing import Optional,List, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_by_openid(db: Session, openid: str) -> Optional[List[Dict[str, Any]]]:
    try:
        biaodian_list = db.query(Biaodian).filter(Biaodian.openid == openid, Biaodian.simi == 0).all()
        result = []
        if biaodian_list:
            for bd in biaodian_list:
                result.append({
                    "bd_id": bd.bd_id,
                    "latitude": bd.latitude,
                    "longitude": bd.longitude,
                    "beizhu": bd.beizhu,
                    "weather": bd.weather,
                    "zhuangbei": bd.zhuangbei,
                    "type": bd.type,
                    "yuhuo": bd.yuhuo,
                    "tuijian": bd.tuijian,
                    "userid": bd.userid,
                    "simi": bd.simi,
                    "city": bd.city,
                    "province": bd.province,
                    "openid": bd.openid,
                    "biaoti": bd.biaoti
                })
            logger.info(f"根据用户openid找到 {len(biaodian_list)} 个私密标点")
            return result
        else:
            logger.info(f"根据用户openid未找到标点 {openid}")
            return None
    except SQLAlchemyError as e:
        logger.error(f"根据用户openid查询标点失败: {str(e)}")
        raise



def get_biaodian_by_simi_pub(db: Session) -> dict:
    """获取一个公开标点（simi=1）"""
    try:
        biaodian = db.query(Biaodian).filter(Biaodian.simi == 1).all()
        result = []
        if biaodian:
            for bd in biaodian:
                result.append({
                    "bd_id": bd.bd_id,
                    "latitude": bd.latitude,
                    "longitude": bd.longitude,
                    "beizhu": bd.beizhu,
                    "weather": bd.weather,
                    "zhuangbei": bd.zhuangbei,
                    "type": bd.type,
                    "yuhuo": bd.yuhuo,
                    "tuijian": bd.tuijian,
                    "userid": bd.userid,
                    "simi": bd.simi,
                    "city": bd.city,
                    "province": bd.province,
                    "openid": bd.openid,
                    "biaoti": bd.biaoti
                })
            logger.info(f"找到公开标点")
            return result
        else:
            logger.info(f"未找到公开的标点")
            return None
    except SQLAlchemyError as e:
        logger.error(f"查询公开标点失败: {str(e)}")
        raise

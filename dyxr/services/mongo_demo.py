# from pymongo import MongoClient
# from pymongo.errors import PyMongoError
# from typing import Dict, Any, List, Optional
# from database import get_mongo
# import logging
#
# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# def create_biaodian(data: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     创建标点信息
#
#     Args:
#         data: 标点信息数据
#
#     Returns:
#         dict: 创建的标点信息
#     """
#     try:
#         mongo_db = get_mongo()
#         result = mongo_db.biaodian.insert_one(data)
#         created_biaodian = mongo_db.biaodian.find_one({"_id": result.inserted_id})
#         logger.info(f"标点信息创建成功: {result.inserted_id}")
#         return created_biaodian
#     except PyMongoError as e:
#         logger.error(f"创建标点信息失败: {str(e)}")
#         raise
#
#
# def get_biaodian_by_id(bd_id: str) -> Optional[Dict[str, Any]]:
#     """
#     根据ID获取标点信息
#
#     Args:
#         bd_id: 标点ID
#
#     Returns:
#         dict: 标点信息，如果未找到返回None
#     """
#     try:
#         mongo_db = get_mongo()
#         biaodian = mongo_db.biaodian.find_one({"bd_id": bd_id})
#         if biaodian:
#             logger.info(f"找到标点信息: {bd_id}")
#         else:
#             logger.info(f"未找到ID为 {bd_id} 的标点信息")
#         return biaodian
#     except PyMongoError as e:
#         logger.error(f"查询标点信息失败: {str(e)}")
#         raise
#
#
# def get_biaodians_by_type(type_value: int, limit: int = 10) -> List[Dict[str, Any]]:
#     """
#     根据类型获取标点信息列表
#
#     Args:
#         type_value: 类型值
#         limit: 限制返回数量，默认10条
#
#     Returns:
#         list: 标点信息列表
#     """
#     try:
#         mongo_db = get_mongo()
#         biaodians = list(mongo_db.biaodian.find({"type": type_value}).limit(limit))
#         logger.info(f"找到 {len(biaodians)} 条类型为 {type_value} 的标点信息")
#         return biaodians
#     except PyMongoError as e:
#         logger.error(f"查询标点信息列表失败: {str(e)}")
#         raise
#
#
# def update_biaodian(bd_id: str, data: Dict[str, Any]) -> bool:
#     """
#     更新标点信息
#
#     Args:
#         bd_id: 标点ID
#         data: 要更新的数据
#
#     Returns:
#         bool: 更新成功返回True，否则返回False
#     """
#     try:
#         mongo_db = get_mongo()
#         result = mongo_db.biaodian.update_one(
#             {"bd_id": bd_id},
#             {"$set": data}
#         )
#         if result.matched_count > 0:
#             logger.info(f"标点信息更新成功: {bd_id}")
#             return True
#         else:
#             logger.info(f"未找到ID为 {bd_id} 的标点信息")
#             return False
#     except PyMongoError as e:
#         logger.error(f"更新标点信息失败: {str(e)}")
#         raise
#
#
# def delete_biaodian(bd_id: str) -> bool:
#     """
#     删除标点信息
#
#     Args:
#         bd_id: 标点ID
#
#     Returns:
#         bool: 删除成功返回True，否则返回False
#     """
#     try:
#         mongo_db = get_mongo()
#         result = mongo_db.biaodian.delete_one({"bd_id": bd_id})
#         if result.deleted_count > 0:
#             logger.info(f"标点信息删除成功: {bd_id}")
#             return True
#         else:
#             logger.info(f"未找到ID为 {bd_id} 的标点信息")
#             return False
#     except PyMongoError as e:
#         logger.error(f"删除标点信息失败: {str(e)}")
#         raise
# import redis
# import json
# import logging
# from database import get_redis
#
# # 配置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
#
#
# def set_user_cache(user_id: int, user_data: dict, expire: int = 3600):
#     """
#     设置用户缓存
#
#     Args:
#         user_id: 用户ID
#         user_data: 用户数据
#         expire: 过期时间（秒），默认1小时
#
#     Returns:
#         bool: 设置成功返回True，否则返回False
#     """
#     try:
#         redis_client = get_redis()
#         key = f"user:{user_id}"
#         value = json.dumps(user_data)
#         result = redis_client.setex(key, expire, value)
#         logger.info(f"用户缓存设置成功: {key}")
#         return result
#     except redis.RedisError as e:
#         logger.error(f"设置用户缓存失败: {str(e)}")
#         raise
#
#
# def get_user_cache(user_id: int):
#     """
#     获取用户缓存
#
#     Args:
#         user_id: 用户ID
#
#     Returns:
#         dict: 用户数据，如果未找到返回None
#     """
#     try:
#         redis_client = get_redis()
#         key = f"user:{user_id}"
#         value = redis_client.get(key)
#         if value:
#             user_data = json.loads(value)
#             logger.info(f"找到用户缓存: {key}")
#             return user_data
#         else:
#             logger.info(f"未找到用户缓存: {key}")
#             return None
#     except (redis.RedisError, json.JSONDecodeError) as e:
#         logger.error(f"获取用户缓存失败: {str(e)}")
#         raise
#
#
# def update_user_cache(user_id: int, user_data: dict, expire: int = 3600):
#     """
#     更新用户缓存
#
#     Args:
#         user_id: 用户ID
#         user_data: 用户数据
#         expire: 过期时间（秒），默认1小时
#
#     Returns:
#         bool: 更新成功返回True，否则返回False
#     """
#     try:
#         redis_client = get_redis()
#         key = f"user:{user_id}"
#         value = json.dumps(user_data)
#         result = redis_client.setex(key, expire, value)
#         logger.info(f"用户缓存更新成功: {key}")
#         return result
#     except (redis.RedisError, json.JSONDecodeError) as e:
#         logger.error(f"更新用户缓存失败: {str(e)}")
#         raise
#
#
# def delete_user_cache(user_id: int):
#     """
#     删除用户缓存
#
#     Args:
#         user_id: 用户ID
#
#     Returns:
#         int: 删除的键数量
#     """
#     try:
#         redis_client = get_redis()
#         key = f"user:{user_id}"
#         result = redis_client.delete(key)
#         logger.info(f"用户缓存删除成功: {key}")
#         return result
#     except redis.RedisError as e:
#         logger.error(f"删除用户缓存失败: {str(e)}")
#         raise
#
#
# def list_users_cache(pattern: str = "user:*"):
#     """
#     列出所有用户缓存
#
#     Args:
#         pattern: 匹配模式，默认"user:*"
#
#     Returns:
#         list: 匹配的键列表
#     """
#     try:
#         redis_client = get_redis()
#         keys = redis_client.keys(pattern)
#         logger.info(f"找到 {len(keys)} 个用户缓存")
#         return keys
#     except redis.RedisError as e:
#         logger.error(f"列出用户缓存失败: {str(e)}")
#         raise
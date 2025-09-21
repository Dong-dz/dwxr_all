from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils, douyin_users, biaodian
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# 抖音小程序相关路由
api_router.include_router(douyin_users.router)
api_router.include_router(biaodian.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)

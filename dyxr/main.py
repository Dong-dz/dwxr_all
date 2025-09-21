import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import userRoute, biaodianRoute, douyin_route
from config import settings
import time
import uuid

uvicorn_logger = logging.getLogger("uvicorn")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="基于FastAPI的抖音小程序登录后端服务，支持用户管理、会话管理和标点信息管理",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    request_id = str(uuid.uuid4())

    logger.error(
        f"Global exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown"
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "errCode": -1,
            "errMsg": "系统错误",
            "detail": "服务器内部错误，请稍后重试",
            "timestamp": time.time(),
            "request_id": request_id
        }
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # 记录请求开始
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time

    # 记录请求完成
    logger.info(
        f"Request completed: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": round(process_time, 3)
        }
    )

    # 添加响应头
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(round(process_time, 3))

    return response


# 健康检查接口
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": settings.app_version,
        "service": settings.app_name
    }


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用{settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# 注册路由
app.include_router(douyin_route.router)  # 抖音小程序登录路由
app.include_router(userRoute.router)     # 用户路由
app.include_router(biaodianRoute.router) # 标点路由

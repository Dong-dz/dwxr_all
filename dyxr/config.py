from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    debug: bool = False
    app_name: str = "抖音小程序登录后端"
    app_version: str = "1.0.0"

    # MySQL配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "douyin_miniapp"

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # MongoDB配置
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_database: str = "test"
    mongo_user: Optional[str] = None
    mongo_password: Optional[str] = None

    # 抖音小程序配置
    douyin_app_id: str = "your_douyin_app_id"
    douyin_app_secret: str = "your_douyin_app_secret"
    douyin_auth_url: str = "https://developer.toutiao.com/api/apps/v2/jscode2session"

    # JWT配置
    jwt_secret_key: str = "your_jwt_secret_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120  # 2小时
    
    # 会话配置
    session_expire_seconds: int = 7200  # 2小时
    user_active_expire_seconds: int = 1800  # 30分钟
    
    # 安全配置
    login_rate_limit: int = 10  # 每小时最大登录次数
    rate_limit_window: int = 3600  # 1小时

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
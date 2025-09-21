from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from redis import Redis
from pymongo import MongoClient
from config import settings
import logging
import urllib.parse

# MySQL配置
MYSQL_URL = f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
engine = create_engine(MYSQL_URL, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis配置
redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password,
    decode_responses=True
)

# MongoDB配置
if settings.mongo_user and settings.mongo_password:
    # 使用认证方式连接MongoDB
    encoded_user = urllib.parse.quote_plus(settings.mongo_user)
    encoded_password = urllib.parse.quote_plus(settings.mongo_password)
    MONGO_URL = f"mongodb://{encoded_user}:{encoded_password}@{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_database}"
else:
    # 无认证方式连接MongoDB
    MONGO_URL = f"mongodb://{settings.mongo_host}:{settings.mongo_port}/{settings.mongo_database}"

mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client[settings.mongo_database]


def get_db():
    """
    获取MySQL数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """
    获取Redis客户端
    """
    return redis_client


def get_mongo():
    """
    获取MongoDB数据库实例
    """
    return mongo_db
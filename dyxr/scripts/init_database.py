#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建数据库表结构和初始化基础数据
"""

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime

from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from database import engine, Base, SessionLocal
from models.userModel import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database():
    """
    创建数据库（如果不存在）
    """
    try:
        # 创建一个不指定数据库的连接
        db_url_without_db = (
            f"mysql+pymysql://{settings.mysql_user}:"
            f"{settings.mysql_password}@{settings.mysql_host}:"
            f"{settings.mysql_port}"
        )
        temp_engine = create_engine(db_url_without_db)

        with temp_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(
                text(
                    f"SELECT SCHEMA_NAME FROM "
                    f"INFORMATION_SCHEMA.SCHEMATA WHERE "
                    f"SCHEMA_NAME = '{settings.mysql_database}'"
                )
            )

            if not result.fetchone():
                # 创建数据库
                conn.execute(
                    text(
                        f"CREATE DATABASE {settings.mysql_database} "
                        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                )
                conn.commit()
                logger.info(
                    f"Database '{settings.mysql_database}' created successfully"
                )
            else:
                logger.info(
                    f"Database '{settings.mysql_database}' already exists"
                )

        temp_engine.dispose()

    except SQLAlchemyError as e:
        logger.error(f"Failed to create database: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error when creating database: {str(e)}")
        raise


def create_tables():
    """
    创建所有数据表
    """
    try:
        logger.info("Creating database tables...")

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        logger.info("Database tables created successfully")

        # 显示创建的表
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {', '.join(tables)}")

    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error when creating tables: {str(e)}")
        raise


def create_admin_user():
    """
    创建管理员用户
    """
    try:
        logger.info("Creating admin user...")

        db = SessionLocal()

        # 检查管理员用户是否已存在
        admin_openid = "admin_test_openid"
        existing_admin = (
            db.query(User).filter(User.openid == admin_openid).first()
        )

        if not existing_admin:
            # 创建管理员用户
            admin_user = User(
                openid=admin_openid,
                unionid="admin_test_unionid",
                name="系统管理员",
                type="admin",
                quanxian="admin",
                dengji="10",
                uuid=str(uuid.uuid4()),
                status=1,
                created_at=datetime.utcnow(),
                last_login_at=datetime.utcnow(),
            )

            db.add(admin_user)
            db.commit()

            logger.info(f"Admin user created: {admin_openid}")
        else:
            logger.info("Admin user already exists")

        db.close()

    except SQLAlchemyError as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        if "db" in locals():
            db.rollback()
            db.close()
        raise
    except Exception as e:
        logger.error(f"Unexpected error when creating admin user: {str(e)}")
        if "db" in locals():
            db.close()
        raise


def create_test_users():
    """
    创建测试用户
    """
    try:
        logger.info("Creating test users...")

        db = SessionLocal()

        test_users = [
            {
                "openid": "test_user_001",
                "unionid": "test_union_001",
                "name": "测试用户1",
                "type": "normal",
                "quanxian": "user",
                "dengji": "1",
            },
            {
                "openid": "test_user_002",
                "unionid": "test_union_002",
                "name": "测试用户2",
                "type": "vip",
                "quanxian": "user",
                "dengji": "3",
            },
        ]

        for user_data in test_users:
            # 检查用户是否已存在
            existing_user = (
                db.query(User)
                .filter(User.openid == user_data["openid"])
                .first()
            )

            if not existing_user:
                test_user = User(
                    openid=user_data["openid"],
                    unionid=user_data["unionid"],
                    name=user_data["name"],
                    type=user_data["type"],
                    quanxian=user_data["quanxian"],
                    dengji=user_data["dengji"],
                    uuid=str(uuid.uuid4()),
                    status=1,
                    created_at=datetime.utcnow(),
                )

                db.add(test_user)
                logger.info(f"Test user created: {user_data['openid']}")
            else:
                logger.info(f"Test user already exists: {user_data['openid']}")

        db.commit()
        db.close()

    except SQLAlchemyError as e:
        logger.error(f"Failed to create test users: {str(e)}")
        if "db" in locals():
            db.rollback()
            db.close()
        raise
    except Exception as e:
        logger.error(f"Unexpected error when creating test users: {str(e)}")
        if "db" in locals():
            db.close()
        raise


def show_database_info():
    """
    显示数据库信息
    """
    try:
        logger.info("Database information:")
        logger.info(f"Host: {settings.mysql_host}:{settings.mysql_port}")
        logger.info(f"Database: {settings.mysql_database}")
        logger.info(f"User: {settings.mysql_user}")

        with engine.connect() as conn:
            # 显示表信息
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Tables: {', '.join(tables)}")

            # 显示用户数量
            if "users" in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.fetchone()[0]
                logger.info(f"Total users: {user_count}")

            # 显示登录日志数量
            if "login_logs" in tables:
                result = conn.execute(text("SELECT COUNT(*) FROM login_logs"))
                log_count = result.fetchone()[0]
                logger.info(f"Total login logs: {log_count}")

    except Exception as e:
        logger.error(f"Failed to show database info: {str(e)}")


def drop_all_tables():
    """
    删除所有表（谨慎使用）
    """
    try:
        logger.warning("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")

    except SQLAlchemyError as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        description="Database initialization script"
    )
    parser.add_argument(
        "--create-db",
        action="store_true",
        help="Create database if not exists",
    )
    parser.add_argument(
        "--create-tables", action="store_true", help="Create all tables"
    )
    parser.add_argument(
        "--create-admin", action="store_true", help="Create admin user"
    )
    parser.add_argument(
        "--create-test-users",
        action="store_true",
        help="Create test users",
    )
    parser.add_argument(
        "--show-info",
        action="store_true",
        help="Show database information",
    )
    parser.add_argument(
        "--drop-tables",
        action="store_true",
        help="Drop all tables (DANGEROUS!)",
    )
    parser.add_argument(
        "--init-all", action="store_true", help="Initialize everything"
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        return

    try:
        if args.drop_tables:
            confirm = input(
                "Are you sure you want to drop all tables? "
                "This will delete all data! (yes/no): "
            )
            if confirm.lower() == "yes":
                drop_all_tables()
            else:
                logger.info("Operation cancelled")
                return

        if args.create_db or args.init_all:
            create_database()

        if args.create_tables or args.init_all:
            create_tables()

        if args.create_admin or args.init_all:
            create_admin_user()

        if args.create_test_users or args.init_all:
            create_test_users()

        if args.show_info or args.init_all:
            show_database_info()

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

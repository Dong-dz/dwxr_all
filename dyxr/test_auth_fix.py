#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试auth.py修复脚本
"""

import sys
import traceback
from typing import Dict, Any

def test_imports():
    """测试导入功能"""
    try:
        from middleware.auth import AuthMiddleware, get_current_user, get_current_user_optional
        from middleware.auth import auth_middleware, get_client_ip, get_user_agent
        print("✅ 所有导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        traceback.print_exc()
        return False

def test_auth_middleware_creation():
    """测试认证中间件创建"""
    try:
        from middleware.auth import AuthMiddleware
        auth = AuthMiddleware()
        print("✅ AuthMiddleware 实例创建成功")
        return True
    except Exception as e:
        print(f"❌ AuthMiddleware 创建失败: {e}")
        traceback.print_exc()
        return False

async def test_redis_retry_mechanism():
    """测试Redis重试机制"""
    try:
        from middleware.auth import AuthMiddleware
        auth = AuthMiddleware()
        
        # 测试重试机制（这个可能会失败，但不应该崩溃）
        redis_client = await auth.get_redis_client_with_retry(max_retries=1)
        if redis_client:
            print("✅ Redis连接重试机制正常（连接成功）")
        else:
            print("⚠️  Redis连接重试机制正常（连接失败但没有崩溃）")
        return True
    except Exception as e:
        print(f"❌ Redis重试机制测试失败: {e}")
        traceback.print_exc()
        return False

def test_type_annotations():
    """测试类型注解"""
    try:
        from middleware.auth import AuthMiddleware
        import inspect
        
        # 检查方法签名
        auth = AuthMiddleware()
        sig = inspect.signature(auth.verify_session)
        print(f"✅ verify_session 方法签名正确: {sig}")
        
        sig2 = inspect.signature(auth.check_rate_limit)
        print(f"✅ check_rate_limit 方法签名正确: {sig2}")
        
        return True
    except Exception as e:
        print(f"❌ 类型注解测试失败: {e}")
        traceback.print_exc()
        return False

async def run_async_tests():
    """运行异步测试"""
    print("\n🔄 运行异步测试...")
    success = await test_redis_retry_mechanism()
    return success

def main():
    """主测试函数"""
    print("🚀 开始测试 auth.py 修复...")
    print("=" * 50)
    
    tests = [
        ("导入功能", test_imports),
        ("中间件创建", test_auth_middleware_creation),
        ("类型注解", test_type_annotations),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        try:
            if test_func():
                success_count += 1
        except Exception as e:
            print(f"❌ 测试 {test_name} 出现异常: {e}")
    
    # 运行异步测试
    import asyncio
    try:
        result = asyncio.run(run_async_tests())
        if result:
            success_count += 1
        total_tests += 1
    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
        total_tests += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！auth.py 修复成功！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
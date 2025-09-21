#!/usr/bin/env python3
"""
模块导入验证脚本
用于验证修复后的模块导入是否正常工作
"""

def test_imports():
    """测试所有关键模块的导入"""
    import_results = []
    
    # 测试utils模块导入
    modules_to_test = [
        ('utils.jwt_utils', ['JWTManager', 'create_session_token', 'mask_sensitive_data']),
        ('utils.http_utils', []),
        ('services.douyin_login_service', []),
        ('routes.douyin_route', []),
        ('models.userModel', []),
        ('models.biaodianModel', []),
        ('schemas.userSche', []),
        ('schemas.biaodianSche', [])
    ]
    
    for module_name, classes in modules_to_test:
        try:
            module = __import__(module_name, fromlist=classes)
            
            # 测试特定类或函数的导入
            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"✓ {module_name}.{class_name} 导入成功")
                else:
                    print(f"⚠ {module_name}.{class_name} 不存在")
            
            if not classes:  # 如果没有指定特定的类，只测试模块本身
                print(f"✓ {module_name} 导入成功")
            
            import_results.append((module_name, True, None))
            
        except ImportError as e:
            print(f"✗ {module_name} 导入失败: {e}")
            import_results.append((module_name, False, str(e)))
        except Exception as e:
            print(f"⚠ {module_name} 导入时出现其他错误: {e}")
            import_results.append((module_name, False, str(e)))
    
    # 汇总结果
    print("\n=== 导入测试结果汇总 ===")
    success_count = sum(1 for _, success, _ in import_results if success)
    total_count = len(import_results)
    
    print(f"成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有模块导入测试通过！")
        return True
    else:
        print("❌ 部分模块导入失败，需要进一步检查")
        return False

if __name__ == "__main__":
    test_imports()
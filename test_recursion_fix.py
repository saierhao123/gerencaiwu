#!/usr/bin/env python3
"""
测试递归错误修复
"""

import sys
import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication
import traceback

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_filtering_without_recursion():
    """测试筛选功能是否还会出现递归错误"""
    print("=== 测试筛选功能递归错误修复 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '调整后分类': ['支出-餐饮', '收入-工资', '支出-交通'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功']
        }
        
        test_df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {test_df.shape}")
        
        # 设置数据
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试筛选方法
        print("测试筛选方法...")
        window.apply_filters_and_refresh()
        print("✓ 筛选方法执行成功，没有递归错误")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 筛选功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_copy_without_recursion():
    """测试数据复制是否还会出现递归错误"""
    print("\n=== 测试数据复制递归错误修复 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '调整后分类': ['支出-餐饮', '收入-工资', '支出-交通'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功']
        }
        
        test_df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {test_df.shape}")
        
        # 测试安全数据复制
        print("测试安全数据复制...")
        safe_data = window.create_safe_data_copy(test_df)
        print(f"✓ 安全数据复制成功，形状: {safe_data.shape}")
        
        # 测试手动重建
        print("测试手动重建...")
        rebuilt_df = window.manual_rebuild_dataframe(test_df)
        print(f"✓ 手动重建成功，形状: {rebuilt_df.shape}")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 数据复制测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试递归错误修复...")
    print("=" * 50)
    
    tests = [
        ("筛选功能递归错误修复", test_filtering_without_recursion),
        ("数据复制递归错误修复", test_data_copy_without_recursion)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            traceback.print_exc()
        
        print("-" * 30)
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！递归错误应该已经修复。")
        return True
    else:
        print("⚠️  部分测试失败，递归错误可能仍然存在。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

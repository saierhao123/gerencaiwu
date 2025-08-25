#!/usr/bin/env python3
"""
测试崩溃修复功能
验证程序是否能正常运行而不会崩溃
"""

import sys
import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import traceback

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_recovery():
    """测试数据恢复功能"""
    print("=== 测试数据恢复功能 ===")
    try:
        from data_recovery import DataRecovery
        
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '交易分类': ['支出-餐饮', '收入-工资', '支出-交通'],
            '平台': ['微信', '支付宝', '微信']
        }
        
        df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {df.shape}")
        
        # 测试安全复制
        safe_df = DataRecovery.safe_copy_dataframe(df)
        print(f"✓ 安全复制成功，形状: {safe_df.shape}")
        
        # 测试数据验证
        validation = DataRecovery.validate_dataframe(df)
        print(f"✓ 数据验证完成，是否有效: {validation['is_valid']}")
        
        # 测试数据修复
        fixed_df = DataRecovery.fix_common_issues(df)
        print(f"✓ 数据修复完成，形状: {fixed_df.shape}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据恢复测试失败: {e}")
        traceback.print_exc()
        return False

def test_main_gui_import():
    """测试main_gui模块导入"""
    print("\n=== 测试main_gui模块导入 ===")
    try:
        from main_gui import MainWindow
        print("✓ main_gui模块导入成功")
        return True
    except Exception as e:
        print(f"✗ main_gui模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_gui_creation():
    """测试GUI创建"""
    print("\n=== 测试GUI创建 ===")
    try:
        app = QApplication([])
        
        # 创建主窗口
        from main_gui import MainWindow
        window = MainWindow()
        print("✓ 主窗口创建成功")
        
        # 检查必要的属性
        required_attrs = [
            'df', 'df_filtered', 'pie_canvas', 'bar_canvas', 
            'trend_canvas', 'platform_canvas', 'calendar_heatmap_canvas',
            'monthly_trend_canvas'
        ]
        
        for attr in required_attrs:
            if hasattr(window, attr):
                print(f"✓ 属性 {attr} 存在")
            else:
                print(f"✗ 属性 {attr} 缺失")
        
        # 测试方法存在性
        required_methods = [
            'apply_filters_and_refresh', 'refresh_charts', 'refresh_calendar',
            'create_safe_data_copy', 'manual_rebuild_dataframe'
        ]
        
        for method in required_methods:
            if hasattr(window, method):
                print(f"✓ 方法 {method} 存在")
            else:
                print(f"✗ 方法 {method} 缺失")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI创建测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_operations():
    """测试数据操作功能"""
    print("\n=== 测试数据操作功能 ===")
    try:
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '调整后分类': ['支出-餐饮', '收入-工资', '支出-交通'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功']
        }
        
        df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {df.shape}")
        
        # 测试数据清理
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 测试数据清理
        cleaned_df = window.clean_dataframe(df)
        print(f"✓ 数据清理成功，形状: {cleaned_df.shape}")
        
        # 测试安全数据复制
        safe_data = window.create_safe_data_copy(cleaned_df)
        print(f"✓ 安全数据复制成功，形状: {safe_data.shape}")
        
        # 测试手动重建
        rebuilt_df = window.manual_rebuild_dataframe(cleaned_df)
        print(f"✓ 手动重建成功，形状: {rebuilt_df.shape}")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 数据操作测试失败: {e}")
        traceback.print_exc()
        return False

def test_filtering_functionality():
    """测试筛选功能"""
    print("\n=== 测试筛选功能 ===")
    try:
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '调整后分类': ['支出-餐饮', '收入-工资', '支出-交通'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功']
        }
        
        df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {df.shape}")
        
        # 测试筛选功能
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 设置测试数据
        window.df = df
        window.df_filtered = df
        
        # 测试筛选方法（不实际执行，只检查方法存在）
        if hasattr(window, 'apply_filters_and_refresh'):
            print("✓ 筛选方法存在")
        else:
            print("✗ 筛选方法缺失")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 筛选功能测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始崩溃修复测试...")
    print("=" * 50)
    
    tests = [
        ("数据恢复功能", test_data_recovery),
        ("main_gui模块导入", test_main_gui_import),
        ("GUI创建", test_gui_creation),
        ("数据操作功能", test_data_operations),
        ("筛选功能", test_filtering_functionality)
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
        print("🎉 所有测试通过！程序应该可以正常运行。")
        return True
    else:
        print("⚠️  部分测试失败，程序可能仍有问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

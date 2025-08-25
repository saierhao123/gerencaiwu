#!/usr/bin/env python3
"""
测试main_gui的稳定性
验证程序是否能稳定运行而不会崩溃
"""

import sys
import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import traceback
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_gui_startup():
    """测试GUI启动稳定性"""
    print("=== 测试GUI启动稳定性 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        
        # 创建主窗口
        window = MainWindow()
        print("✓ 主窗口创建成功")
        
        # 检查基本属性
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
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI启动测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_processing_stability():
    """测试数据处理稳定性"""
    print("\n=== 测试数据处理稳定性 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建测试数据
        test_data = {
            '交易时间': [
                '2025-01-01 10:00:00', '2025-01-01 12:00:00', '2025-01-01 18:00:00',
                '2025-01-02 09:00:00', '2025-01-02 12:00:00', '2025-01-02 19:00:00'
            ],
            '金额': [50, 100, 80, 200, 150, 90],
            '调整后分类': [
                '支出-餐饮', '支出-交通', '支出-购物',
                '收入-工资', '支出-娱乐', '支出-餐饮'
            ],
            '平台': ['微信', '支付宝', '微信', '银行', '微信', '支付宝'],
            '交易状态': ['成功'] * 6
        }
        
        test_df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {test_df.shape}")
        
        # 测试数据清理
        cleaned_df = window.clean_dataframe(test_df)
        print(f"✓ 数据清理成功，形状: {cleaned_df.shape}")
        
        # 设置数据
        window.df = cleaned_df
        window.df_filtered = cleaned_df
        
        # 测试筛选
        print("测试筛选功能...")
        window.apply_filters_and_refresh()
        print("✓ 筛选功能正常")
        
        # 测试图表刷新
        print("测试图表刷新...")
        window.refresh_charts()
        print("✓ 图表刷新正常")
        
        # 测试日历刷新
        print("测试日历刷新...")
        window.refresh_calendar()
        print("✓ 日历刷新正常")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 数据处理稳定性测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理能力"""
    print("\n=== 测试错误处理能力 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建有问题的数据
        problematic_data = {
            '交易时间': ['2025-01-01', 'invalid_date', '2025-01-03'],
            '金额': [100, 'invalid_amount', 300],
            '调整后分类': ['支出-餐饮', None, '支出-交通'],
            '平台': ['微信', '', '支付宝'],
            '交易状态': ['成功', '成功', '成功']
        }
        
        problematic_df = pd.DataFrame(problematic_data)
        print(f"✓ 问题测试数据创建成功，形状: {problematic_df.shape}")
        
        # 测试问题数据处理
        print("测试问题数据处理...")
        cleaned_problematic_df = window.clean_dataframe(problematic_df)
        print(f"✓ 问题数据清理成功，形状: {cleaned_problematic_df.shape}")
        
        # 设置问题数据
        window.df = cleaned_problematic_df
        window.df_filtered = cleaned_problematic_df
        
        # 测试筛选（应该能处理问题数据）
        print("测试问题数据筛选...")
        window.apply_filters_and_refresh()
        print("✓ 问题数据筛选正常")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        traceback.print_exc()
        return False

def test_large_data_handling():
    """测试大数据处理能力"""
    print("\n=== 测试大数据处理能力 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建大量测试数据
        large_data = []
        for i in range(500):  # 500行数据
            large_data.append({
                '交易时间': f'2025-01-{(i%30)+1:02d} 10:00:00',
                '金额': (i % 1000) + 1,
                '调整后分类': f'支出-类别{i%10}',
                '平台': ['微信', '支付宝', '银行'][i%3],
                '交易状态': '成功'
            })
        
        large_df = pd.DataFrame(large_data)
        print(f"✓ 大量测试数据创建成功，形状: {large_df.shape}")
        
        # 测试大数据处理
        print("测试大数据处理...")
        cleaned_large_df = window.clean_dataframe(large_df)
        print(f"✓ 大数据清理成功，形状: {cleaned_large_df.shape}")
        
        # 设置大数据
        window.df = cleaned_large_df
        window.df_filtered = cleaned_large_df
        
        # 测试大数据筛选
        print("测试大数据筛选...")
        window.apply_filters_and_refresh()
        print("✓ 大数据筛选正常")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 大数据处理测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试main_gui稳定性...")
    print("=" * 60)
    
    tests = [
        ("GUI启动稳定性", test_gui_startup),
        ("数据处理稳定性", test_data_processing_stability),
        ("错误处理能力", test_error_handling),
        ("大数据处理能力", test_large_data_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n开始测试: {test_name}")
            if test_func():
                passed += 1
                print(f"✓ {test_name} 测试通过")
            else:
                print(f"✗ {test_name} 测试失败")
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            traceback.print_exc()
        
        print("-" * 40)
        time.sleep(1)  # 给系统一些时间
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！main_gui应该可以稳定运行。")
        return True
    else:
        print("⚠️  部分测试失败，main_gui可能仍有稳定性问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

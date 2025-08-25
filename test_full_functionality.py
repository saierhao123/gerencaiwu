#!/usr/bin/env python3
"""
全面功能测试
测试程序的实际运行情况，包括数据处理、图表更新等
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

def create_test_data():
    """创建测试数据"""
    test_data = {
        '交易时间': [
            '2025-01-01 10:00:00', '2025-01-01 12:00:00', '2025-01-01 18:00:00',
            '2025-01-02 09:00:00', '2025-01-02 12:00:00', '2025-01-02 19:00:00',
            '2025-01-03 08:00:00', '2025-01-03 11:00:00', '2025-01-03 20:00:00'
        ],
        '金额': [50, 100, 80, 200, 150, 90, 120, 60, 180],
        '调整后分类': [
            '支出-餐饮', '支出-交通', '支出-购物',
            '收入-工资', '支出-娱乐', '支出-餐饮',
            '支出-交通', '支出-购物', '收入-奖金'
        ],
        '平台': ['微信', '支付宝', '微信', '银行', '微信', '支付宝', '支付宝', '微信', '银行'],
        '交易状态': ['成功'] * 9
    }
    
    return pd.DataFrame(test_data)

def test_data_processing():
    """测试数据处理功能"""
    print("=== 测试数据处理功能 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建测试数据
        test_df = create_test_data()
        print(f"✓ 测试数据创建成功，形状: {test_df.shape}")
        
        # 测试数据清理
        cleaned_df = window.clean_dataframe(test_df)
        print(f"✓ 数据清理成功，形状: {cleaned_df.shape}")
        
        # 设置数据
        window.df = cleaned_df
        window.df_filtered = cleaned_df
        
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
        print(f"✗ 数据处理测试失败: {e}")
        traceback.print_exc()
        return False

def test_filtering_system():
    """测试筛选系统"""
    print("\n=== 测试筛选系统 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 设置测试数据
        test_df = create_test_data()
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试筛选方法
        print("测试筛选方法...")
        window.apply_filters_and_refresh()
        print("✓ 筛选方法执行成功")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 筛选系统测试失败: {e}")
        traceback.print_exc()
        return False

def test_chart_system():
    """测试图表系统"""
    print("\n=== 测试图表系统 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 设置测试数据
        test_df = create_test_data()
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试图表刷新
        print("测试图表刷新...")
        window.refresh_charts()
        print("✓ 图表刷新成功")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 图表系统测试失败: {e}")
        traceback.print_exc()
        return False

def test_calendar_system():
    """测试日历系统"""
    print("\n=== 测试日历系统 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 设置测试数据
        test_df = create_test_data()
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试日历刷新
        print("测试日历刷新...")
        window.refresh_calendar()
        print("✓ 日历刷新成功")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 日历系统测试失败: {e}")
        traceback.print_exc()
        return False

def test_stress_conditions():
    """测试压力条件"""
    print("\n=== 测试压力条件 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建大量测试数据
        large_data = []
        for i in range(1000):
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
        
        # 测试大数据筛选
        window.df = cleaned_large_df
        window.df_filtered = cleaned_large_df
        
        print("测试大数据筛选...")
        window.apply_filters_and_refresh()
        print("✓ 大数据筛选成功")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 压力条件测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_recovery():
    """测试错误恢复"""
    print("\n=== 测试错误恢复 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建有问题的测试数据
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
        
        # 测试问题数据筛选
        window.df = cleaned_problematic_df
        window.df_filtered = cleaned_problematic_df
        
        print("测试问题数据筛选...")
        window.apply_filters_and_refresh()
        print("✓ 问题数据筛选成功")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 错误恢复测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始全面功能测试...")
    print("=" * 60)
    
    tests = [
        ("数据处理功能", test_data_processing),
        ("筛选系统", test_filtering_system),
        ("图表系统", test_chart_system),
        ("日历系统", test_calendar_system),
        ("压力条件", test_stress_conditions),
        ("错误恢复", test_error_recovery)
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
        print("🎉 所有测试通过！程序功能完整，应该可以正常运行。")
        return True
    else:
        print("⚠️  部分测试失败，程序可能仍有问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

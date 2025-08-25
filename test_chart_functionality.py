#!/usr/bin/env python3
"""
测试图表功能
验证main_gui.py的图表功能是否正常工作
"""

import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication

def test_chart_creation():
    """测试图表创建功能"""
    print("=== 测试图表创建功能 ===")
    try:
        from main_gui import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        
        # 检查图表画布是否创建成功
        assert hasattr(window, 'pie_canvas'), "缺少饼图画布"
        assert hasattr(window, 'bar_canvas'), "缺少柱状图画布"
        assert hasattr(window, 'trend_canvas'), "缺少时间趋势图画布"
        assert hasattr(window, 'platform_canvas'), "缺少平台对比图画布"
        assert hasattr(window, 'calendar_heatmap_canvas'), "缺少日历热力图画布"
        assert hasattr(window, 'monthly_trend_canvas'), "缺少月度趋势图画布"
        
        print("✓ 所有图表画布创建成功")
        
        # 检查图表标签页是否创建成功
        assert hasattr(window, 'chart_tab_widget'), "缺少图表标签页组件"
        assert hasattr(window, 'calendar_tab_widget'), "缺少日历标签页组件"
        
        print("✓ 图表标签页组件创建成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 图表创建功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chart_methods():
    """测试图表方法"""
    print("\n=== 测试图表方法 ===")
    try:
        from main_gui import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        
        # 检查图表方法是否存在
        assert hasattr(window, 'update_pie_chart'), "缺少update_pie_chart方法"
        assert hasattr(window, 'update_bar_chart'), "缺少update_bar_chart方法"
        assert hasattr(window, 'update_trend_chart'), "缺少update_trend_chart方法"
        assert hasattr(window, 'update_platform_chart'), "缺少update_platform_chart方法"
        assert hasattr(window, 'update_calendar_heatmap'), "缺少update_calendar_heatmap方法"
        assert hasattr(window, 'update_monthly_trend'), "缺少update_monthly_trend方法"
        
        print("✓ 所有图表更新方法存在")
        
        # 检查文字分析方法是否存在
        assert hasattr(window, 'generate_text_analysis'), "缺少generate_text_analysis方法"
        assert hasattr(window, 'generate_calendar_text_analysis'), "缺少generate_calendar_text_analysis方法"
        
        print("✓ 文字分析方法存在")
        
        return True
        
    except Exception as e:
        print(f"✗ 图表方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chart_data_handling():
    """测试图表数据处理"""
    print("\n=== 测试图表数据处理 ===")
    try:
        from main_gui import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
            '金额': [100, 200, 150, 300, 250],
            '交易分类': ['支出-餐饮', '收入-工资', '支出-购物', '收入-奖金', '支出-交通'],
            '平台': ['微信', '支付宝', '微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功', '成功', '成功'],
            '调整后分类': ['餐饮', '工资', '购物', '奖金', '交通']
        }
        
        df = pd.DataFrame(test_data)
        
        # 设置数据
        window.df = df
        window.df_filtered = df
        
        print("✓ 测试数据创建成功")
        
        # 测试图表更新（不检查实际显示，只检查方法调用）
        try:
            # 测试图表更新方法调用
            window.update_pie_chart(df)
            window.update_bar_chart(df)
            window.update_trend_chart(df)
            window.update_platform_chart(df)
            window.update_calendar_heatmap(df, 2025, 1)
            window.update_monthly_trend(df, 2025, 1)
            
            print("✓ 所有图表更新方法调用成功")
            
        except Exception as e:
            print(f"✗ 图表更新方法调用失败: {e}")
            return False
        
        # 测试文字分析生成
        try:
            window.generate_text_analysis(df)
            window.generate_calendar_text_analysis(df, 2025, 1)
            print("✓ 文字分析生成成功")
            
        except Exception as e:
            print(f"✗ 文字分析生成失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 图表数据处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chart_integration():
    """测试图表集成功能"""
    print("\n=== 测试图表集成功能 ===")
    try:
        from main_gui import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 150],
            '交易分类': ['支出-餐饮', '收入-工资', '支出-购物'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功'],
            '调整后分类': ['餐饮', '工资', '购物']
        }
        
        df = pd.DataFrame(test_data)
        
        # 设置数据
        window.df = df
        window.df_filtered = df
        
        # 测试图表刷新集成
        try:
            window.refresh_charts()
            print("✓ 图表刷新集成成功")
            
        except Exception as e:
            print(f"✗ 图表刷新集成失败: {e}")
            return False
        
        # 测试日历刷新集成
        try:
            window.refresh_calendar()
            print("✓ 日历刷新集成成功")
            
        except Exception as e:
            print(f"✗ 日历刷新集成失败: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 图表集成功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("图表功能测试")
    print("=" * 60)
    
    tests = [
        ("图表创建功能测试", test_chart_creation),
        ("图表方法测试", test_chart_methods),
        ("图表数据处理测试", test_chart_data_handling),
        ("图表集成功能测试", test_chart_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✓ {test_name} 通过")
        else:
            print(f"✗ {test_name} 失败")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    if passed == total:
        print("🎉 所有测试通过！图表功能正常工作。")
        print("✅ 新增功能包括：")
        print("   - 分类饼图")
        print("   - 分类柱状图")
        print("   - 时间趋势图")
        print("   - 平台对比图")
        print("   - 日历热力图")
        print("   - 月度趋势图")
        print("   - 文字分析报告")
    else:
        print("⚠️  部分测试失败，请检查相关代码。")
    print("=" * 60)

if __name__ == "__main__":
    main()

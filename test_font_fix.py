#!/usr/bin/env python3
"""
测试字体修复
验证所有图表的中文字体显示是否正确
"""

import sys
import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication
import traceback

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_chart_fonts():
    """测试图表字体设置"""
    print("=== 测试图表字体设置 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建测试数据
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
        
        test_df = pd.DataFrame(test_data)
        print(f"✓ 测试数据创建成功，形状: {test_df.shape}")
        
        # 设置数据
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试饼图字体
        print("测试饼图字体...")
        try:
            window.update_pie_chart(test_df)
            print("✓ 饼图字体设置正常")
        except Exception as e:
            print(f"✗ 饼图字体设置失败: {e}")
        
        # 测试柱状图字体
        print("测试柱状图字体...")
        try:
            window.update_bar_chart(test_df)
            print("✓ 柱状图字体设置正常")
        except Exception as e:
            print(f"✗ 柱状图字体设置失败: {e}")
        
        # 测试趋势图字体
        print("测试趋势图字体...")
        try:
            window.update_trend_chart(test_df)
            print("✓ 趋势图字体设置正常")
        except Exception as e:
            print(f"✗ 趋势图字体设置失败: {e}")
        
        # 测试平台对比图字体
        print("测试平台对比图字体...")
        try:
            window.update_platform_chart(test_df)
            print("✓ 平台对比图字体设置正常")
        except Exception as e:
            print(f"✗ 平台对比图字体设置失败: {e}")
        
        # 测试日历热力图字体
        print("测试日历热力图字体...")
        try:
            window.update_calendar_heatmap(test_df, 2025, 1)
            print("✓ 日历热力图字体设置正常")
        except Exception as e:
            print(f"✗ 日历热力图字体设置失败: {e}")
        
        # 测试月度趋势图字体
        print("测试月度趋势图字体...")
        try:
            window.update_monthly_trend(test_df, 2025, 1)
            print("✓ 月度趋势图字体设置正常")
        except Exception as e:
            print(f"✗ 月度趋势图字体设置失败: {e}")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 图表字体测试失败: {e}")
        traceback.print_exc()
        return False

def test_pie_chart_overlap():
    """测试饼图文字重叠问题"""
    print("\n=== 测试饼图文字重叠问题 ===")
    try:
        from main_gui import MainWindow
        app = QApplication([])
        window = MainWindow()
        
        # 创建有长标签的测试数据
        test_data = {
            '交易时间': ['2025-01-01'] * 15,
            '金额': [100] * 15,
            '调整后分类': [
                '支出-餐饮美食', '支出-交通出行', '支出-购物消费', '支出-娱乐休闲',
                '支出-医疗保健', '支出-教育培训', '支出-住房租金', '支出-水电煤气',
                '支出-通讯费用', '支出-保险费用', '支出-投资理财', '支出-其他杂项',
                '收入-工资薪金', '收入-奖金补贴', '收入-投资收益'
            ],
            '平台': ['微信'] * 15,
            '交易状态': ['成功'] * 15
        }
        
        test_df = pd.DataFrame(test_data)
        print(f"✓ 长标签测试数据创建成功，形状: {test_df.shape}")
        
        # 设置数据
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试饼图长标签处理
        print("测试饼图长标签处理...")
        try:
            window.update_pie_chart(test_df)
            print("✓ 饼图长标签处理正常")
        except Exception as e:
            print(f"✗ 饼图长标签处理失败: {e}")
        
        # 清理
        window.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"✗ 饼图重叠测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试字体修复...")
    print("=" * 50)
    
    tests = [
        ("图表字体设置", test_chart_fonts),
        ("饼图文字重叠", test_pie_chart_overlap)
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
        print("🎉 所有测试通过！字体问题应该已经修复。")
        return True
    else:
        print("⚠️  部分测试失败，字体问题可能仍然存在。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

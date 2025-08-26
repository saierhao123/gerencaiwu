#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试main_gui.py的新功能
"""

import sys
import os
import traceback

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_imports():
    """测试所有必要的模块导入"""
    try:
        from main_gui import MainWindow, ProcessingThread
        print("✓ 主窗口类导入成功")
        
        from bill_parser import BillParser
        print("✓ 账单解析器导入成功")
        
        from data_visualizer import DataVisualizer
        print("✓ 数据可视化器导入成功")
        
        from transaction_classifier import TransactionClassifier
        print("✓ 交易分类器导入成功")
        
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_data_visualizer():
    """测试数据可视化器的新功能"""
    try:
        from data_visualizer import DataVisualizer  # 修复未定义问题
        visualizer = DataVisualizer()
        print("✓ 数据可视化器初始化成功")
        
        # 测试柱状图方法是否存在
        if hasattr(visualizer, 'create_bar_chart'):
            print("✓ 柱状图方法存在")
        else:
            print("✗ 柱状图方法不存在")
            return False
        
        # 测试饼图方法是否支持category_column参数
        import inspect
        pie_sig = inspect.signature(visualizer.create_pie_chart)
        if 'category_column' in pie_sig.parameters:
            print("✓ 饼图方法支持category_column参数")
        else:
            print("✗ 饼图方法不支持category_column参数")
            return False
        
        # 测试日历热力图方法是否支持category_column参数
        cal_sig = inspect.signature(visualizer.create_calendar_heatmap)
        if 'category_column' in cal_sig.parameters:
            print("✓ 日历热力图方法支持category_column参数")
        else:
            print("✗ 日历热力图方法不支持category_column参数")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 测试数据可视化器失败: {e}")
        traceback.print_exc()
        return False

def test_bill_parser():
    """测试账单解析器的新功能"""
    try:
        from bill_parser import BillParser  # 修复未定义问题
        parser = BillParser()
        print("✓ 账单解析器初始化成功")
        
        # 检查是否有zhangdang文件夹
        zhangdang_path = "zhangdang"
        if os.path.exists(zhangdang_path):
            print(f"✓ 找到账单文件夹: {zhangdang_path}")
            
            # 尝试处理账单
            try:
                df = parser.process_all_bills(zhangdang_path)
                if df is not None and not df.empty:
                    print(f"✓ 成功解析账单，共 {len(df)} 条记录")
                    
                    # 检查新字段是否存在
                    required_fields = ['调整后分类', '调整后子分类']
                    for field in required_fields:
                        if field in df.columns:
                            print(f"✓ 字段 '{field}' 存在")
                        else:
                            print(f"✗ 字段 '{field}' 不存在")
                    
                    # 显示字段信息
                    print(f"✓ 数据字段: {list(df.columns)}")
                    return True
                else:
                    print("✗ 账单解析结果为空")
                    return False
            except Exception as e:
                print(f"✗ 账单解析失败: {e}")
                traceback.print_exc()
                return False
        else:
            print(f"✗ 账单文件夹不存在: {zhangdang_path}")
            return False
            
    except Exception as e:
        print(f"✗ 测试账单解析器失败: {e}")
        traceback.print_exc()
        return False

def test_stats_string_bug():
    """测试 stats 字段为字符串时的兼容性"""
    try:
        from transaction_classifier import TransactionClassifier
        from data_visualizer import DataVisualizer

        # 构造 stats 部分字段为字符串的情况
        stats = {
            '总收入': '168.0',
            '总支出': '308.29',
            '非收支总额': '613.9999999999999',
            '净收入': '-140.29000000000002',
            '分类统计': "{'数量': {'互转': 32, '非收支': 27, '签到提现': 23}, '金额': {'互转': 4163.15}}",
            '平台统计': "{'sum': {'微信': 1961.12, '支付宝': 10700.34}, 'count': {'微信': 35, '支付宝': 124}}"
        }
        print("\n--- 测试 stats 字段为字符串时的兼容性 ---")
        # 直接调用 DataVisualizer.create_summary_report
        visualizer = DataVisualizer()
        try:
            report = visualizer.create_summary_report(stats)
            print("✓ create_summary_report 正常返回")
            print(report[:200] + " ...")
        except Exception as e:
            print("✗ create_summary_report 崩溃")
            print(f"错误信息: {e}")
            traceback.print_exc()
            return False

        # 测试 TransactionClassifier.get_classification_statistics 的健壮性
        try:
            classifier = TransactionClassifier()
            # 构造一个空DataFrame
            import pandas as pd
            df = pd.DataFrame(columns=['交易时间', '金额', '分类'])
            result = classifier.get_classification_statistics(df)
            print("✓ get_classification_statistics 正常返回")
        except Exception as e:
            print("✗ get_classification_statistics 崩溃")
            print(f"错误信息: {e}")
            traceback.print_exc()
            return False

        return True
    except Exception as e:
        print(f"✗ 测试 stats 字段为字符串时的兼容性失败: {e}")
        traceback.print_exc()
        return False

def test_processing_finished_stats_nested_string():
    """测试 main_gui.MainWindow.processing_finished 对嵌套字符串 stats 的兼容性"""
    try:
        from main_gui import MainWindow
        import pandas as pd

        window = MainWindow()
        df = pd.DataFrame({'交易时间': [], '金额': [], '分类': []})
        stats = {
            '总收入': '168.0',
            '总支出': '308.29',
            '非收支总额': '613.9999999999999',
            '净收入': '-140.29000000000002',
            '分类统计': "{'数量': {'互转': 32, '非收支': 27}, '金额': \"{'互转': 4163.15}\"}",
            '平台统计': "{'sum': {'微信': 1961.12, '支付宝': 10700.34}, 'count': {'微信': 35, '支付宝': 124}}"
        }
        try:
            window.processing_finished(df, stats, "测试报告")
            print("✓ processing_finished 嵌套字符串 stats 正常返回")
            return True
        except Exception as e:
            print("✗ processing_finished 嵌套字符串 stats 崩溃")
            print(f"错误信息: {e}")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"✗ 测试 processing_finished 嵌套字符串 stats 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chart_text_generation():
    """测试 main_gui.py 的图表文字输出功能"""
    try:
        from main_gui import MainWindow
        import pandas as pd

        window = MainWindow()
        # 构造简单数据
        df = pd.DataFrame({
            '交易时间': ['2023-01-01', '2023-01-02'],
            '金额': [100, 200],
            '交易分类': ['支出-餐饮', '收入-工资'],
            '平台': ['微信', '支付宝']
        })
        window.df = df
        window.df_filtered = df  # 设置筛选后的数据
        
        # 测试图表文字输出
        window.refresh_charts()
        chart_text = window.chart_text_edit.toPlainText()
        assert "收入分类分析" in chart_text or "支出分类分析" in chart_text or "收支分类分析" in chart_text
        assert "分类统计" in chart_text
        assert "平台统计" in chart_text
        print("✓ 图表文字输出测试通过")
        
        # 测试日历文字输出
        window.refresh_calendar()
        calendar_text = window.calendar_text_edit.toPlainText()
        assert "日历分析" in calendar_text
        print("✓ 日历文字输出测试通过")
        
        return True
    except Exception as e:
        print(f"✗ 图表文字输出测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("测试main_gui.py的新功能")
    print("=" * 50)
    
    tests = [
        ("模块导入测试", test_imports),
        ("数据可视化器测试", test_data_visualizer),
        ("账单解析器测试", test_bill_parser),
        ("stats字符串兼容性测试", test_stats_string_bug),
        ("processing_finished 嵌套字符串 stats 测试", test_processing_finished_stats_nested_string),
        ("图表文字输出测试", test_chart_text_generation),
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
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    if passed == total:
        print("🎉 所有测试通过！main_gui.py的新功能正常工作。")
    else:
        print("⚠️  部分测试失败，请检查相关代码。")
    print("=" * 50)

if __name__ == "__main__":
    main()

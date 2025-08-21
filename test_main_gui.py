#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试main_gui.py的新功能
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_imports():
    """测试所有必要的模块导入"""
    try:
        from main_gui import MainWindow, ProcessingThread, ChartBridge
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
        return False

def test_bill_parser():
    """测试账单解析器的新功能"""
    try:
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
                return False
        else:
            print(f"✗ 账单文件夹不存在: {zhangdang_path}")
            return False
            
    except Exception as e:
        print(f"✗ 测试账单解析器失败: {e}")
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

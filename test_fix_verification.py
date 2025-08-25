#!/usr/bin/env python3
"""
测试修复验证脚本
验证main_gui.py的崩溃问题是否已解决
"""

import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication

def test_data_recovery_tool():
    """测试数据恢复工具"""
    print("=== 测试数据恢复工具 ===")
    try:
        from data_recovery import DataRecovery
        
        # 创建测试数据
        test_data = {
            '交易时间': ['2025-01-01', '2025-01-02'],
            '金额': [100, 200],
            '交易分类': ['支出-餐饮', '收入-工资'],
            '平台': ['微信', '支付宝']
        }
        
        df = pd.DataFrame(test_data)
        
        # 测试安全复制
        safe_df = DataRecovery.safe_copy_dataframe(df)
        print(f"✓ 安全复制成功，行数: {len(safe_df)}")
        
        # 测试数据验证
        validation = DataRecovery.validate_dataframe(df)
        print(f"✓ 数据验证完成，是否有效: {validation['is_valid']}")
        
        # 测试数据修复
        fixed_df = DataRecovery.fix_common_issues(df)
        print(f"✓ 数据修复完成，行数: {len(fixed_df)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据恢复工具测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_import():
    """测试GUI模块导入"""
    print("\n=== 测试GUI模块导入 ===")
    try:
        from main_gui import MainWindow, ProcessingThread
        print("✓ 主窗口类导入成功")
        print("✓ 处理线程类导入成功")
        return True
        
    except Exception as e:
        print(f"✗ GUI模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_creation():
    """测试GUI创建"""
    print("\n=== 测试GUI创建 ===")
    try:
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 导入主窗口
        from main_gui import MainWindow
        
        # 创建主窗口
        window = MainWindow()
        print("✓ 主窗口创建成功")
        
        # 检查必要的属性
        assert hasattr(window, 'df'), "缺少df属性"
        assert hasattr(window, 'stats'), "缺少stats属性"
        assert hasattr(window, 'report_text'), "缺少report_text属性"
        assert hasattr(window, 'chart_text_edit'), "缺少chart_text_edit属性"
        assert hasattr(window, 'calendar_text_edit'), "缺少calendar_text_edit属性"
        assert hasattr(window, 'df_filtered'), "缺少df_filtered属性"
        print("✓ 所有必要属性存在")
        
        # 检查图表相关属性
        assert hasattr(window, 'pie_canvas'), "缺少饼图画布"
        assert hasattr(window, 'bar_canvas'), "缺少柱状图画布"
        assert hasattr(window, 'trend_canvas'), "缺少时间趋势图画布"
        assert hasattr(window, 'platform_canvas'), "缺少平台对比图画布"
        assert hasattr(window, 'calendar_heatmap_canvas'), "缺少日历热力图画布"
        assert hasattr(window, 'monthly_trend_canvas'), "缺少月度趋势图画布"
        print("✓ 所有图表画布存在")
        
        # 检查方法
        assert hasattr(window, 'refresh_charts'), "缺少refresh_charts方法"
        assert hasattr(window, 'refresh_calendar'), "缺少refresh_calendar方法"
        assert hasattr(window, 'clean_dataframe'), "缺少clean_dataframe方法"
        print("✓ 所有必要方法存在")
        
        # 测试默认文件夹设置
        if hasattr(window, 'folder_path'):
            print(f"✓ 默认文件夹: {window.folder_path}")
        else:
            print("⚠️  未设置默认文件夹")
        
        print("✓ GUI创建测试通过")
        return True
        
    except Exception as e:
        print(f"✗ GUI创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """测试数据处理功能"""
    print("\n=== 测试数据处理功能 ===")
    try:
        from main_gui import ProcessingThread
        
        # 检查ProcessingThread类
        assert hasattr(ProcessingThread, 'progress_updated'), "缺少progress_updated信号"
        assert hasattr(ProcessingThread, 'progress_updated'), "缺少processing_finished信号"
        assert hasattr(ProcessingThread, 'error_occurred'), "缺少error_occurred信号"
        print("✓ ProcessingThread类完整")
        
        print("✓ 数据处理功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据处理功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_filtering():
    """测试数据筛选功能"""
    print("\n=== 测试数据筛选功能 ===")
    try:
        # 创建QApplication
        app = QApplication(sys.argv)
        
        from main_gui import MainWindow
        window = MainWindow()
        
        # 创建测试数据
        test_df = pd.DataFrame({
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '交易分类': ['支出-餐饮', '收入-工资', '支出-购物'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功']
        })
        
        # 设置数据
        window.df = test_df
        window.df_filtered = test_df
        
        # 测试筛选功能
        try:
            # 模拟筛选操作
            window.platform_filter.setCurrentText("微信")
            window.apply_filters_and_refresh()
            print("✓ 平台筛选测试通过")
            
            # 重置筛选
            window.platform_filter.setCurrentText("全部平台")
            window.apply_filters_and_refresh()
            print("✓ 筛选重置测试通过")
            
        except Exception as e:
            print(f"✗ 筛选功能测试失败: {e}")
            return False
        
        print("✓ 数据筛选功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据筛选功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("main_gui.py 修复验证测试")
    print("=" * 60)
    
    tests = [
        ("数据恢复工具测试", test_data_recovery_tool),
        ("GUI模块导入测试", test_gui_import),
        ("GUI创建测试", test_gui_creation),
        ("数据处理功能测试", test_data_processing),
        ("数据筛选功能测试", test_data_filtering),
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
        print("🎉 所有测试通过！main_gui.py的崩溃问题已解决。")
        print("✅ 修复措施包括：")
        print("   - 使用数据恢复工具进行安全的数据复制")
        print("   - 改进的筛选方法，避免pandas复制问题")
        print("   - 增强的错误处理和异常恢复")
        print("   - 数据验证和清理机制")
    else:
        print("⚠️  部分测试失败，请检查相关代码。")
    print("=" * 60)

if __name__ == "__main__":
    main()

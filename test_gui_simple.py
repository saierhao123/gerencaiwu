#!/usr/bin/env python3
"""
简单的GUI功能测试脚本
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_gui_basic():
    """测试GUI基本功能"""
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
        print("✓ 所有必要属性存在")
        
        # 检查方法
        assert hasattr(window, 'refresh_charts'), "缺少refresh_charts方法"
        assert hasattr(window, 'refresh_calendar'), "缺少refresh_calendar方法"
        print("✓ 所有必要方法存在")
        
        # 测试默认文件夹设置
        if hasattr(window, 'folder_path'):
            print(f"✓ 默认文件夹: {window.folder_path}")
        else:
            print("⚠️  未设置默认文件夹")
        
        print("✓ GUI基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ GUI基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_processing():
    """测试数据处理功能"""
    try:
        from main_gui import ProcessingThread
        
        # 检查ProcessingThread类
        assert hasattr(ProcessingThread, 'progress_updated'), "缺少progress_updated信号"
        assert hasattr(ProcessingThread, 'processing_finished'), "缺少processing_finished信号"
        assert hasattr(ProcessingThread, 'error_occurred'), "缺少error_occurred信号"
        print("✓ ProcessingThread类完整")
        
        print("✓ 数据处理功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据处理功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("GUI基本功能测试")
    print("=" * 50)
    
    tests = [
        ("GUI基本功能测试", test_gui_basic),
        ("数据处理功能测试", test_data_processing),
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
        print("🎉 所有测试通过！GUI基本功能正常。")
    else:
        print("⚠️  部分测试失败，请检查相关代码。")
    print("=" * 50)

if __name__ == "__main__":
    main()

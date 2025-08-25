#!/usr/bin/env python3
"""
测试强健的筛选功能
验证修复后的筛选方法是否能处理损坏的数据
"""

import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication

def test_corrupted_data_handling():
    """测试损坏数据处理"""
    print("=== 测试损坏数据处理 ===")
    try:
        from main_gui import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        
        # 创建包含损坏数据的测试DataFrame
        corrupted_data = {
            '交易时间': ['2025-01-01', '2025-01-02', '2025-01-03'],
            '金额': [100, 200, 300],
            '交易分类': ['支出-餐饮', '收入-工资', '支出-购物'],
            '平台': ['微信', '支付宝', '微信'],
            '交易状态': ['成功', '成功', '成功'],
            '调整后分类': [
                '餐饮',  # 正常数据
                '工资',  # 正常数据
                '购物'   # 正常数据
            ]
        }
        
        # 添加一些损坏的数据
        corrupted_data['调整后分类'][1] = '工资' + '\x00' * 1000  # 添加大量空字符
        corrupted_data['交易状态'][2] = '成功' + '\r\n' * 500     # 添加大量换行符
        
        df = pd.DataFrame(corrupted_data)
        
        # 设置数据
        window.df = df
        window.df_filtered = df
        
        print("✓ 测试数据创建成功")
        
        # 测试字段安全检查
        print("\n--- 测试字段安全检查 ---")
        safe_platform = window.is_field_safe(df, '平台')
        safe_category = window.is_field_safe(df, '调整后分类')
        safe_status = window.is_field_safe(df, '交易状态')
        
        print(f"平台字段安全: {safe_platform}")
        print(f"分类字段安全: {safe_category}")
        print(f"状态字段安全: {safe_status}")
        
        # 测试字符串清理
        print("\n--- 测试字符串清理 ---")
        test_string = "测试\x00\x00\x00\r\n\r\n\r\n" + "重复" * 1000
        cleaned = window.safe_string_clean(test_string)
        print(f"原始字符串长度: {len(test_string)}")
        print(f"清理后字符串长度: {len(cleaned)}")
        print(f"清理后字符串: {cleaned[:100]}...")
        
        # 测试筛选功能
        print("\n--- 测试筛选功能 ---")
        try:
            # 测试平台筛选
            window.platform_filter.setCurrentText("微信")
            window.apply_filters_and_refresh()
            print("✓ 平台筛选测试通过")
            
            # 测试分类筛选
            window.platform_filter.setCurrentText("全部平台")
            window.category_filter.setCurrentText("餐饮")
            window.apply_filters_and_refresh()
            print("✓ 分类筛选测试通过")
            
            # 重置筛选
            window.category_filter.setCurrentText("全部分类")
            window.apply_filters_and_refresh()
            print("✓ 筛选重置测试通过")
            
        except Exception as e:
            print(f"✗ 筛选功能测试失败: {e}")
            return False
        
        print("✓ 损坏数据处理测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 损坏数据处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extreme_corruption():
    """测试极端损坏数据"""
    print("\n=== 测试极端损坏数据 ===")
    try:
        from main_gui import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainWindow()
        
        # 创建极端损坏的数据
        extreme_data = {
            '交易时间': ['2025-01-01'],
            '金额': [100],
            '交易分类': ['支出-餐饮'],
            '平台': ['微信'],
            '交易状态': ['成功'],
            '调整后分类': ['餐饮' + '\x00' * 10000]  # 极长字符串
        }
        
        df = pd.DataFrame(extreme_data)
        
        # 设置数据
        window.df = df
        window.df_filtered = df
        
        print("✓ 极端损坏数据创建成功")
        
        # 测试数据清理
        print("\n--- 测试极端数据清理 ---")
        try:
            cleaned_df = window.clean_dataframe(df)
            print(f"原始数据行数: {len(df)}")
            print(f"清理后数据行数: {len(cleaned_df)}")
            print("✓ 极端数据清理测试通过")
        except Exception as e:
            print(f"✗ 极端数据清理失败: {e}")
            return False
        
        # 测试筛选
        print("\n--- 测试极端数据筛选 ---")
        try:
            window.platform_filter.setCurrentText("微信")
            window.apply_filters_and_refresh()
            print("✓ 极端数据筛选测试通过")
        except Exception as e:
            print(f"✗ 极端数据筛选失败: {e}")
            return False
        
        print("✓ 极端损坏数据测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 极端损坏数据测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("强健筛选功能测试")
    print("=" * 60)
    
    tests = [
        ("损坏数据处理测试", test_corrupted_data_handling),
        ("极端损坏数据测试", test_extreme_corruption),
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
        print("🎉 所有测试通过！强健筛选功能正常工作。")
        print("✅ 修复措施包括：")
        print("   - 字段安全检查机制")
        print("   - 深度字符串清理")
        print("   - 渐进式错误处理")
        print("   - 损坏数据自动跳过")
    else:
        print("⚠️  部分测试失败，请检查相关代码。")
    print("=" * 60)

if __name__ == "__main__":
    main()

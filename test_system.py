"""
测试脚本
用于验证个人记账管理系统的各个模块功能
"""

import pandas as pd
import json
from bill_parser import BillParser
from transaction_classifier import TransactionClassifier
from data_visualizer import DataVisualizer


def test_bill_parser():
    """测试账单解析功能"""
    print("=" * 50)
    print("测试账单解析功能")
    print("=" * 50)
    
    try:
        parser = BillParser()
        
        # 测试扫描账单文件
        bill_files = parser.scan_bill_files("zhangdang")
        print(f"找到账单文件: {bill_files}")
        
        # 测试解析所有账单
        df = parser.process_all_bills("zhangdang")
        print(f"成功解析 {len(df)} 条交易记录")
        print(f"数据列: {list(df.columns)}")
        print(f"前5条记录:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"账单解析测试失败: {str(e)}")
        return None


def test_transaction_classifier(df):
    """测试交易分类功能"""
    print("\n" + "=" * 50)
    print("测试交易分类功能")
    print("=" * 50)
    
    try:
        classifier = TransactionClassifier()
        
        # 测试分类所有交易
        classified_df = classifier.classify_all_transactions(df)
        print(f"分类完成，共 {len(classified_df)} 条记录")
        
        # 显示分类统计
        classification_counts = classified_df['分类'].value_counts()
        print("分类统计:")
        for category, count in classification_counts.items():
            print(f"  {category}: {count} 条")
        
        # 生成统计信息
        stats = classifier.get_classification_statistics(classified_df)
        print(f"\n基本统计:")
        print(f"  总收入: ¥{stats['总收入']:.2f}")
        print(f"  总支出: ¥{stats['总支出']:.2f}")
        print(f"  净收入: ¥{stats['净收入']:.2f}")
        print(f"  非收支总额: ¥{stats['非收支总额']:.2f}")
        
        return classified_df, stats
        
    except Exception as e:
        print(f"交易分类测试失败: {str(e)}")
        return None, None


def test_data_visualizer(classified_df, stats):
    """测试数据可视化功能"""
    print("\n" + "=" * 50)
    print("测试数据可视化功能")
    print("=" * 50)
    
    try:
        visualizer = DataVisualizer()
        
        # 生成统计报告
        report_text = visualizer.create_summary_report(stats)
        print("统计报告:")
        print(report_text)
        
        # 生成饼图
        expense_pie = visualizer.create_pie_chart(classified_df, 'expense')
        income_pie = visualizer.create_pie_chart(classified_df, 'income')
        
        print("饼图生成完成")
        
        return report_text
        
    except Exception as e:
        print(f"数据可视化测试失败: {str(e)}")
        return None


def main():
    """主测试函数"""
    print("个人记账管理系统 - 功能测试")
    print("=" * 60)
    
    # 测试账单解析
    df = test_bill_parser()
    if df is None:
        print("账单解析失败，终止测试")
        return
    
    # 测试交易分类
    classified_df, stats = test_transaction_classifier(df)
    if classified_df is None:
        print("交易分类失败，终止测试")
        return
    
    # 测试数据可视化
    report_text = test_data_visualizer(classified_df, stats)
    if report_text is None:
        print("数据可视化失败")
        return
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main() 
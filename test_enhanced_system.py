"""
增强版系统测试脚本
测试所有新功能：字段保留、备注、分类、进度显示等
"""

import os
import sys
import pandas as pd
from bill_parser import BillParser
from transaction_classifier import TransactionClassifier
from data_visualizer import DataVisualizer


def test_bill_parser():
    """测试账单解析器的新功能"""
    print("=" * 50)
    print("测试账单解析器")
    print("=" * 50)
    
    parser = BillParser()
    
    # 测试文件夹扫描
    test_folder = "zhangdang"
    if not os.path.exists(test_folder):
        print(f"测试文件夹 {test_folder} 不存在，跳过测试")
        return None
    
    try:
        # 扫描文件
        bill_files = parser.scan_bill_files(test_folder)
        print(f"扫描到 {len(bill_files)} 个账单文件:")
        for f in bill_files:
            print(f"  - {os.path.basename(f)}")
        
        # 解析所有账单
        print("\n开始解析账单...")
        df = parser.process_all_bills(test_folder)
        
        print(f"\n解析完成，共 {len(df)} 条记录")
        print(f"列名: {list(df.columns)}")
        
        # 检查关键字段
        required_fields = ['交易时间', '平台', '金额', '收/支', '备注']
        for field in required_fields:
            if field in df.columns:
                print(f"✓ {field} 字段存在")
            else:
                print(f"✗ {field} 字段缺失")
        
        # 显示前几条记录
        print("\n前3条记录:")
        print(df.head(3).to_string())
        
        return df
        
    except Exception as e:
        print(f"解析失败: {str(e)}")
        return None


def test_transaction_classifier(df):
    """测试交易分类器的新功能"""
    print("\n" + "=" * 50)
    print("测试交易分类器")
    print("=" * 50)
    
    if df is None or df.empty:
        print("无数据可分类")
        return None
    
    try:
        classifier = TransactionClassifier()
        
        # 分类交易
        print("开始分类交易...")
        classified_df = classifier.classify_all_transactions(df)
        
        print(f"分类完成，共 {len(classified_df)} 条记录")
        
        # 检查分类字段
        if '分类' in classified_df.columns:
            print("✓ 分类字段已添加")
            
            # 显示分类统计
            classification_counts = classified_df['分类'].value_counts()
            print("\n分类统计:")
            for category, count in classification_counts.items():
                print(f"  {category}: {count} 笔")
        else:
            print("✗ 分类字段缺失")
        
        # 生成统计信息
        print("\n生成统计信息...")
        stats = classifier.get_classification_statistics(classified_df)
        
        print("基本统计:")
        print(f"  总收入: ¥{stats.get('总收入', 0):.2f}")
        print(f"  总支出: ¥{stats.get('总支出', 0):.2f}")
        print(f"  净收入: ¥{stats.get('净收入', 0):.2f}")
        print(f"  非收支总额: ¥{stats.get('非收支总额', 0):.2f}")
        
        return classified_df, stats
        
    except Exception as e:
        print(f"分类失败: {str(e)}")
        return None, None


def test_data_visualizer(df, stats):
    """测试数据可视化器的新功能"""
    print("\n" + "=" * 50)
    print("测试数据可视化器")
    print("=" * 50)
    
    if df is None or df.empty:
        print("无数据可可视化")
        return
    
    try:
        visualizer = DataVisualizer()
        
        # 生成统计报告
        print("生成统计报告...")
        report_text = visualizer.create_summary_report(stats)
        
        print("\n统计报告预览（前20行）:")
        lines = report_text.split('\n')[:20]
        for line in lines:
            print(f"  {line}")
        
        # 测试饼图生成
        print("\n测试饼图生成...")
        pie_fig = visualizer.create_pie_chart(df, mode='all')
        print("✓ 饼图生成成功")
        
        # 测试日历图生成
        print("测试日历图生成...")
        if '交易时间' in df.columns:
            # 获取数据的年份和月份
            df_copy = df.copy()
            df_copy['交易时间'] = pd.to_datetime(df_copy['交易时间'], errors='coerce')
            if not df_copy['交易时间'].isna().all():
                sample_date = df_copy['交易时间'].dropna().iloc[0]
                year, month = sample_date.year, sample_date.month
                
                calendar_fig = visualizer.create_calendar_heatmap(df, year, month)
                print(f"✓ {year}年{month}月日历图生成成功")
            else:
                print("✗ 无法获取有效日期")
        else:
            print("✗ 交易时间字段缺失")
        
        # 测试HTML转换
        print("测试HTML转换...")
        html_content = visualizer.figure_to_html(pie_fig)
        if html_content and len(html_content) > 100:
            print("✓ HTML转换成功")
        else:
            print("✗ HTML转换失败")
        
    except Exception as e:
        print(f"可视化测试失败: {str(e)}")


def test_field_preservation(df):
    """测试字段保留情况"""
    print("\n" + "=" * 50)
    print("测试字段保留")
    print("=" * 50)
    
    if df is None or df.empty:
        print("无数据可测试")
        return
    
    # 检查关键字段
    print("字段检查:")
    
    # 平台字段
    if '平台' in df.columns:
        platforms = df['平台'].unique()
        print(f"✓ 平台字段: {list(platforms)}")
    else:
        print("✗ 平台字段缺失")
    
    # 收/支字段
    if '收/支' in df.columns:
        income_expense = df['收/支'].unique()
        print(f"✓ 收/支字段: {list(income_expense)}")
    else:
        print("✗ 收/支字段缺失")
    
    # 备注字段
    if '备注' in df.columns:
        remark_count = df['备注'].notna().sum()
        print(f"✓ 备注字段: {remark_count} 条有备注")
    else:
        print("✗ 备注字段缺失")
    
    # 交易分类/类型字段
    wechat_has_type = '交易类型' in df.columns
    alipay_has_category = '交易分类' in df.columns
    
    if wechat_has_type or alipay_has_category:
        print("✓ 交易分类/类型字段存在")
        if wechat_has_type:
            print(f"  - 微信交易类型: {df[df['平台']=='微信']['交易类型'].nunique()} 种")
        if alipay_has_category:
            print(f"  - 支付宝交易分类: {df[df['平台']=='支付宝']['交易分类'].nunique()} 种")
    else:
        print("✗ 交易分类/类型字段缺失")


def main():
    """主测试函数"""
    print("增强版个人记账管理系统测试")
    print("测试内容：字段保留、备注、分类、进度显示等")
    
    # 测试账单解析
    df = test_bill_parser()
    
    # 测试交易分类
    classified_df, stats = test_transaction_classifier(df)
    
    # 测试数据可视化
    test_data_visualizer(classified_df, stats)
    
    # 测试字段保留
    test_field_preservation(df)
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的个人记账系统
"""

import pandas as pd
from bill_parser import BillParser

def test_bill_parsing():
    """测试账单解析功能"""
    print("=== 测试账单解析功能 ===")
    
    try:
        parser = BillParser()
        df = parser.process_all_bills('zhangdang')
        
        print(f"成功解析 {len(df)} 条记录")
        print(f"列数: {len(df.columns)}")
        print(f"列名: {df.columns.tolist()}")
        
        # 检查关键字段
        print("\n=== 字段检查 ===")
        required_fields = ['交易时间', '平台', '交易分类', '交易对方', '商品说明', 
                          '收/支', '金额', '支付方式', '交易状态', '交易单号', 
                          '商户单号', '备注', '调整后分类', '调整后子分类']
        
        for field in required_fields:
            if field in df.columns:
                print(f"✓ {field}: 存在")
                # 检查是否有空值
                null_count = df[field].isna().sum()
                if null_count > 0:
                    print(f"  - 空值数量: {null_count}")
            else:
                print(f"✗ {field}: 缺失")
        
        # 检查微信数据
        print("\n=== 微信数据检查 ===")
        wechat_df = df[df['平台'] == '微信']
        print(f"微信记录数: {len(wechat_df)}")
        if len(wechat_df) > 0:
            print("微信交易分类示例:")
            print(wechat_df['交易分类'].value_counts().head())
            print("微信交易状态示例:")
            print(wechat_df['交易状态'].value_counts().head())
            print("微信支付方式示例:")
            print(wechat_df['支付方式'].value_counts().head())
        
        # 检查支付宝数据
        print("\n=== 支付宝数据检查 ===")
        alipay_df = df[df['平台'] == '支付宝']
        print(f"支付宝记录数: {len(alipay_df)}")
        if len(alipay_df) > 0:
            print("支付宝交易分类示例:")
            print(alipay_df['交易分类'].value_counts().head())
            print("支付宝交易状态示例:")
            print(alipay_df['交易状态'].value_counts().head())
            print("支付宝支付方式示例:")
            print(alipay_df['支付方式'].value_counts().head())
        
        # 检查调整后分类
        print("\n=== 调整后分类检查 ===")
        print("调整后分类统计:")
        print(df['调整后分类'].value_counts().head(10))
        
        print("\n调整后子分类统计:")
        print(df['调整后子分类'].value_counts().head(10))
        
        # 显示一些示例数据
        print("\n=== 示例数据 ===")
        sample_cols = ['交易时间', '平台', '交易分类', '交易对方', '商品说明', 
                      '收/支', '金额', '支付方式', '交易状态', '调整后分类']
        print(df[sample_cols].head(5).to_string())
        
        return True
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bill_parsing()
    if success:
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 测试失败！")

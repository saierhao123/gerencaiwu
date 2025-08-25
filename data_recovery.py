#!/usr/bin/env python3
"""
数据恢复和验证工具
用于处理pandas DataFrame中损坏的数据，防止递归错误
"""

import pandas as pd
import numpy as np
import json
from typing import Any, Dict, List, Union
import sys

class DataRecovery:
    """数据恢复和验证工具"""
    
    @staticmethod
    def safe_copy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """安全地复制DataFrame，避免递归错误"""
        try:
            # 首先检查是否有递归风险
            if DataRecovery._has_recursion_risk(df):
                print("检测到递归风险，使用安全复制方法")
                return DataRecovery.rebuild_dataframe(df)
            
            # 尝试浅拷贝
            return df.copy(deep=False)
        except Exception as e:
            print(f"浅拷贝失败: {e}")
            try:
                # 尝试深拷贝
                return df.copy(deep=True)
            except Exception as e2:
                print(f"深拷贝也失败: {e2}")
                # 如果都失败，尝试重建DataFrame
                return DataRecovery.rebuild_dataframe(df)
    
    @staticmethod
    def _has_recursion_risk(df: pd.DataFrame) -> bool:
        """检查DataFrame是否有递归风险"""
        try:
            # 检查数据大小
            if len(df) > 10000:  # 如果数据行数过多，可能有风险
                return True
            
            # 检查字符串列的长度
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        # 检查是否有异常长的字符串
                        max_len = df[col].astype(str).str.len().max()
                        if pd.notna(max_len) and max_len > 10000:
                            return True
                    except:
                        return True
            
            # 检查内存使用
            try:
                memory_usage = df.memory_usage(deep=True).sum()
                if memory_usage > 100 * 1024 * 1024:  # 100MB
                    return True
            except:
                return True
                
            return False
            
        except Exception:
            return True
    
    @staticmethod
    def rebuild_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """重建DataFrame，移除损坏的数据"""
        try:
            print("开始重建DataFrame...")
            
            # 获取列名
            columns = list(df.columns)
            
            # 逐列重建数据
            new_data = {}
            for col in columns:
                try:
                    # 尝试安全地获取列数据
                    col_data = df[col].values
                    # 清理数据
                    cleaned_data = DataRecovery.clean_column_data(col_data)
                    new_data[col] = cleaned_data
                except Exception as e:
                    print(f"列 {col} 重建失败: {e}")
                    # 如果列重建失败，创建空列
                    new_data[col] = [""] * len(df)
            
            # 创建新的DataFrame
            new_df = pd.DataFrame(new_data)
            print(f"DataFrame重建完成，新数据形状: {new_df.shape}")
            return new_df
            
        except Exception as e:
            print(f"DataFrame重建失败: {e}")
            # 返回空的DataFrame
            return pd.DataFrame()
    
    @staticmethod
    def clean_column_data(col_data: np.ndarray) -> List[Any]:
        """清理列数据，移除损坏的值"""
        cleaned = []
        for item in col_data:
            try:
                cleaned_item = DataRecovery.clean_value(item)
                cleaned.append(cleaned_item)
            except Exception:
                cleaned.append("")
        return cleaned
    
    @staticmethod
    def clean_value(value: Any) -> Any:
        """清理单个值"""
        try:
            if pd.isna(value):
                return ""
            
            if isinstance(value, str):
                # 清理字符串
                cleaned = str(value)
                # 移除可能导致问题的字符
                cleaned = cleaned.replace('\x00', '')
                cleaned = cleaned.replace('\r', '')
                cleaned = cleaned.replace('\n', ' ')
                
                # 限制长度，防止递归
                if len(cleaned) > 1000:
                    cleaned = cleaned[:1000] + "..."
                
                return cleaned
            
            elif isinstance(value, (int, float)):
                # 数值类型直接返回
                return value
            
            elif isinstance(value, (list, dict)):
                # 复杂类型转换为字符串
                try:
                    return json.dumps(value, ensure_ascii=False, default=str)
                except Exception:
                    return str(value)
            
            else:
                # 其他类型转换为字符串
                return str(value)
                
        except Exception:
            return ""
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """验证DataFrame的完整性"""
        validation_result = {
            'is_valid': True,
            'total_rows': 0,
            'total_columns': 0,
            'null_counts': {},
            'data_types': {},
            'memory_usage': 0,
            'issues': []
        }
        
        try:
            validation_result['total_rows'] = len(df)
            validation_result['total_columns'] = len(df.columns)
            
            # 检查内存使用
            try:
                validation_result['memory_usage'] = df.memory_usage(deep=True).sum()
            except:
                validation_result['memory_usage'] = 0
            
            # 检查空值
            for col in df.columns:
                try:
                    null_count = df[col].isnull().sum()
                    validation_result['null_counts'][col] = int(null_count)
                    
                    if null_count == len(df):
                        validation_result['issues'].append(f"列 {col} 全为空")
                except:
                    validation_result['issues'].append(f"列 {col} 检查失败")
            
            # 检查数据类型
            for col in df.columns:
                try:
                    validation_result['data_types'][col] = str(df[col].dtype)
                except:
                    validation_result['data_types'][col] = "unknown"
            
            # 检查是否有循环引用
            try:
                df_copy = df.copy(deep=False)
                validation_result['is_valid'] = True
            except Exception as e:
                validation_result['is_valid'] = False
                validation_result['issues'].append(f"数据复制失败: {str(e)}")
                
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"验证过程出错: {str(e)}")
        
        return validation_result
    
    @staticmethod
    def fix_common_issues(df: pd.DataFrame) -> pd.DataFrame:
        """修复常见的数据问题"""
        try:
            print("开始修复数据问题...")
            
            # 创建新的DataFrame而不是修改原数据
            fixed_df = df.copy(deep=False)
            
            # 修复字符串列中的问题
            for col in fixed_df.columns:
                if fixed_df[col].dtype == 'object':
                    try:
                        fixed_df[col] = fixed_df[col].astype(str).apply(
                            lambda x: DataRecovery.clean_value(x) if pd.notna(x) else ""
                        )
                    except Exception as e:
                        print(f"列 {col} 字符串修复失败: {e}")
                        # 如果修复失败，将该列设为空字符串
                        fixed_df[col] = ""
            
            # 修复金额列
            if '金额' in fixed_df.columns:
                try:
                    fixed_df['金额'] = pd.to_numeric(fixed_df['金额'], errors='coerce').fillna(0.0)
                except Exception as e:
                    print(f"金额列修复失败: {e}")
            
            # 修复时间列
            if '交易时间' in fixed_df.columns:
                try:
                    fixed_df['交易时间'] = pd.to_datetime(fixed_df['交易时间'], errors='coerce')
                except Exception as e:
                    print(f"时间列修复失败: {e}")
            
            print("数据问题修复完成")
            return fixed_df
            
        except Exception as e:
            print(f"修复数据问题失败: {e}")
            return df
    
    @staticmethod
    def emergency_recovery(df: pd.DataFrame) -> pd.DataFrame:
        """紧急数据恢复，使用最保守的方法"""
        try:
            print("开始紧急数据恢复...")
            
            # 获取列名
            columns = list(df.columns)
            
            # 创建最小化的数据
            new_data = {}
            for col in columns:
                new_data[col] = [""] * len(df)
            
            # 创建新的DataFrame
            emergency_df = pd.DataFrame(new_data)
            print("紧急数据恢复完成")
            return emergency_df
            
        except Exception as e:
            print(f"紧急数据恢复失败: {e}")
            return pd.DataFrame()

def test_data_recovery():
    """测试数据恢复功能"""
    print("测试数据恢复功能...")
    
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
    
    print("数据恢复功能测试完成！")

if __name__ == "__main__":
    test_data_recovery()

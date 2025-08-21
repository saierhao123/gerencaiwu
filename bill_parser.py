"""
账单解析模块
负责解析微信和支付宝账单文件，统一数据格式
"""

import pandas as pd
import os
from typing import List
import json


class BillParser:
    """账单解析器"""
    
    def __init__(self, config_file: str = "config.json"):
        """初始化解析器，加载配置（分类规则等预留使用）"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def parse_wechat_bill(self, file_path: str) -> pd.DataFrame:
        """解析微信账单文件
        - 跳过前16行元数据
        - 保留原有字段结构，统一字段名映射
        - 确保备注字段存在
        """
        try:
            df = pd.read_excel(file_path, skiprows=16)
            
            # 列名映射，保留原有字段结构
            column_mapping = {
                '交易时间': '交易时间',
                '交易类型': '交易分类',  # 微信的交易类型映射为交易分类
                '交易对方': '交易对方',
                '商品': '商品说明',
                '收/支': '收/支',  # 保留原有的收/支字段
                '金额(元)': '金额',
                '支付方式': '支付方式',
                '当前状态': '交易状态',  # 微信的当前状态映射为交易状态
                '交易单号': '交易单号',
                '商户单号': '商户单号',
                '备注': '备注'
            }
            
            # 只重命名存在的列
            existing_columns = {col: col for col in df.columns}
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    existing_columns[old_name] = new_name
            
            df = df.rename(columns=existing_columns)
            df['平台'] = '微信'
            
            # 确保所有必要字段都存在
            required_fields = ['交易时间', '交易分类', '交易对方', '商品说明', '收/支', '金额', '支付方式', '交易状态', '交易单号', '商户单号', '备注']
            for field in required_fields:
                if field not in df.columns:
                    df[field] = ''
            
            # 金额标准化
            if '金额' in df.columns:
                df['金额'] = (
                    df['金额'].astype(str)
                    .str.replace('¥', '', regex=False)
                    .str.replace(',', '', regex=False)
                )
                df['金额'] = pd.to_numeric(df['金额'], errors='coerce')
            
            # 时间标准化
            if '交易时间' in df.columns:
                df['交易时间'] = pd.to_datetime(df['交易时间'], errors='coerce')
            
            # 基础清洗
            df = df.fillna('')
            
            # 过滤无效行（时间或金额无效）
            if '交易时间' in df.columns and '金额' in df.columns:
                df = df[(~df['交易时间'].isna()) & (~df['金额'].isna())]
            
            return df
        except Exception as e:
            raise ValueError(f"解析微信账单失败: {str(e)}")
    
    def _read_alipay_csv(self, file_path: str, skiprows: int) -> pd.DataFrame:
        """尝试多种常见编码读取支付宝CSV。
        依次尝试: utf-8, utf-8-sig, gb18030
        """
        encodings = ['utf-8', 'utf-8-sig', 'gb18030']
        last_err = None
        for enc in encodings:
            try:
                return pd.read_csv(file_path, skiprows=skiprows, encoding=enc)
            except Exception as e:
                last_err = e
                continue
        # 若全部失败，抛出最后一次错误
        raise last_err if last_err else ValueError('未知编码读取失败')
    
    def parse_alipay_bill(self, file_path: str) -> pd.DataFrame:
        """解析支付宝账单文件
        - 跳过前25行元数据
        - 编码容错（utf-8/utf-8-sig/gb18030）
        - 保留原有字段结构，统一字段名映射
        - 确保备注字段存在
        """
        try:
            # 有些导出前言行数可能略有出入，做容错
            for skip in [25, 24, 26, 23]:
                try:
                    df = self._read_alipay_csv(file_path, skiprows=skip)
                    # 简单校验是否包含核心列
                    if {'交易时间', '金额'}.issubset(set(df.columns)):
                        break
                except Exception:
                    df = None
            
            if df is None:
                raise ValueError('无法解析支付宝CSV，请检查导出格式是否为标准交易明细')

            # 列名映射，保留原有字段结构
            column_mapping = {
                '交易时间': '交易时间',
                '交易分类': '交易分类',  # 保留支付宝的交易分类
                '交易对方': '交易对方',
                '商品说明': '商品说明',
                '收/支': '收/支',  # 保留原有的收/支字段
                '金额': '金额',
                '收/付款方式': '支付方式',  # 支付宝的收/付款方式映射为支付方式
                '交易状态': '交易状态',
                '交易订单号': '交易单号',
                '商家订单号': '商户单号',
                '备注': '备注'
            }
            
            # 只重命名存在的列
            existing_columns = {col: col for col in df.columns}
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    existing_columns[old_name] = new_name
            
            df = df.rename(columns=existing_columns)
            df['平台'] = '支付宝'
            
            # 确保所有必要字段都存在
            required_fields = ['交易时间', '交易分类', '交易对方', '商品说明', '收/支', '金额', '支付方式', '交易状态', '交易单号', '商户单号', '备注']
            for field in required_fields:
                if field not in df.columns:
                    df[field] = ''
            
            # 金额标准化
            if '金额' in df.columns:
                df['金额'] = (
                    df['金额'].astype(str)
                    .str.replace('¥', '', regex=False)
                    .str.replace(',', '', regex=False)
                )
                df['金额'] = pd.to_numeric(df['金额'], errors='coerce')
            
            # 时间标准化
            if '交易时间' in df.columns:
                df['交易时间'] = pd.to_datetime(df['交易时间'], errors='coerce')
            
            # 基础清洗
            df = df.fillna('')
            
            # 过滤无效行（时间或金额无效）
            if '交易时间' in df.columns and '金额' in df.columns:
                df = df[(~df['交易时间'].isna()) & (~df['金额'].isna())]
            
            return df
        except Exception as e:
            raise ValueError(f"解析支付宝账单失败: {str(e)}")
    
    def identify_bill_type(self, file_path: str) -> str:
        """识别账单类型：优先文件名关键词，其次按扩展名"""
        filename = os.path.basename(file_path).lower()
        if ('微信' in filename) or ('wechat' in filename):
            return 'wechat'
        if ('支付宝' in filename) or ('alipay' in filename):
            return 'alipay'
        if file_path.endswith('.xlsx'):
            return 'wechat'
        if file_path.endswith('.csv'):
            return 'alipay'
        raise ValueError(f"无法识别账单类型: {file_path}")
    
    def parse_bill_file(self, file_path: str) -> pd.DataFrame:
        """解析单个账单文件（自动识别类型）"""
        bill_type = self.identify_bill_type(file_path)
        if bill_type == 'wechat':
            return self.parse_wechat_bill(file_path)
        if bill_type == 'alipay':
            return self.parse_alipay_bill(file_path)
        raise ValueError(f"不支持的账单类型: {bill_type}")

    def scan_bill_files(self, folder_path: str) -> List[str]:
        """扫描账单文件：用try-except彻底拦截空路径，避免stat错误"""
        bill_files: List[str] = []
        # 第一层防护：强制确保folder_path是字符串（不是None）
        if not isinstance(folder_path, str):
            if folder_path is None:
                raise ValueError("文件夹路径不能为空（None）")
            else:
                raise ValueError(f"文件夹路径必须是字符串，当前是：{type(folder_path)}")

        # 第二层防护：检查文件夹是否存在且是目录
        try:
            if not os.path.exists(folder_path):
                raise ValueError(f"文件夹不存在: {folder_path}")
            if not os.path.isdir(folder_path):
                raise ValueError(f"{folder_path} 不是有效文件夹（是文件）")
        except Exception as e:
            raise ValueError(f"检查文件夹失败: {str(e)}")

        # 第三层防护：遍历文件时，用try-except拦截所有路径错误
        keywords = ['微信', '支付宝', 'wechat', 'alipay', '账单', '流水', '明细']
        try:
            # 先获取文件夹下所有文件，过滤空文件名
            filenames = [f for f in os.listdir(folder_path) if f and f.strip() != ""]
            for filename in filenames:
                # 过滤隐藏文件
                if filename.startswith('.'):
                    continue

                # 拼接路径后，立即检查是否为None
                file_path = os.path.join(folder_path, filename)
                if file_path is None:
                    print(f"跳过空路径文件：{filename}")
                    continue

                # 用try-except包裹所有os操作，避免stat错误
                try:
                    # 检查路径是否存在、是否是文件
                    if not os.path.exists(file_path):
                        print(f"跳过不存在的文件：{file_path}")
                        continue
                    if not os.path.isfile(file_path):
                        print(f"跳过非文件（子文件夹）：{file_path}")
                        continue

                    # 检查文件格式和关键词
                    lower_filename = filename.lower()
                    if lower_filename.endswith(('.xlsx', '.csv')) and any(k in lower_filename for k in keywords):
                        bill_files.append(file_path)
                except Exception as e:
                    print(f"处理文件 {filename} 时出错（已跳过）：{str(e)}")
                    continue
        except Exception as e:
            raise ValueError(f"遍历文件夹时出错: {str(e)}")

        return bill_files

    def process_all_bills(self, folder_path: str) -> pd.DataFrame:
        """批量解析账单：确保folder_path不是None"""
        # 强制检查：folder_path必须是字符串，不能是None
        if folder_path is None:
            raise ValueError("调用process_all_bills时，folder_path不能为None")
        if not isinstance(folder_path, str):
            raise ValueError(f"folder_path必须是字符串，当前是：{type(folder_path)}")

        # 扫描账单文件
        bill_files = self.scan_bill_files(folder_path)
        if not bill_files:
            raise ValueError(
                f"文件夹 {folder_path} 中未找到有效账单文件！\n"
                "要求：\n"
                "1. 微信账单：.xlsx格式，文件名含「微信」或「账单」\n"
                "2. 支付宝账单：.csv格式，文件名含「支付宝」或「账单」"
            )

        all_data = []
        for file_path in bill_files:
            try:
                df = self.parse_bill_file(file_path)
                all_data.append(df)
                print(f"成功解析: {os.path.basename(file_path)} ({len(df)} 条记录)")
            except Exception as e:
                print(f"解析失败 {os.path.basename(file_path)}: {str(e)}")

        if not all_data:
            raise ValueError("没有成功解析任何账单文件，请检查文件是否损坏")

        # 合并数据（原逻辑保留）
        combined_df = pd.concat(all_data, ignore_index=True)
        required_fields = ['交易时间', '平台', '交易分类', '交易对方', '商品说明', '收/支', '金额', '支付方式',
                           '交易状态', '交易单号', '商户单号', '备注']
        for field in required_fields:
            if field not in combined_df.columns:
                combined_df[field] = ''

        combined_df['调整后分类'] = ''
        combined_df['调整后子分类'] = ''
        combined_df = self._apply_classification_rules(combined_df)

        # 去重和排序（原逻辑保留）
        subset_cols = [c for c in ['交易时间', '金额', '交易对方', '商品说明'] if c in combined_df.columns]
        if subset_cols:
            combined_df = combined_df.drop_duplicates(subset=subset_cols, keep='first')
        if '交易时间' in combined_df.columns:
            combined_df = combined_df.sort_values('交易时间', ascending=False)

        return combined_df

    def _apply_classification_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """根据配置文件对交易进行分类调整（确保分类字段有值）"""
        try:
            classification_rules = self.config.get('分类规则', {})

            for idx, row in df.iterrows():
                description = str(row.get('商品说明', '')).lower()
                party = str(row.get('交易对方', '')).lower()
                income_expense = str(row.get('收/支', ''))

                # 根据收/支选择规则（修复：默认用“非收支”规则）
                if income_expense in ['支出', '支']:
                    rules = classification_rules.get('支出', {})
                    default_main = '支出-其他'  # 支出默认分类
                elif income_expense in ['收入', '收']:
                    rules = classification_rules.get('收入', {})
                    default_main = '收入-其他'  # 收入默认分类
                else:
                    rules = classification_rules.get('非收支', {})
                    default_main = '非收支'  # 非收支默认分类

                main_category = ''
                sub_category = ''
                for category, keywords in rules.items():
                    for keyword in keywords:
                        if keyword.lower() in description or keyword.lower() in party:
                            main_category = category
                            sub_category = keyword
                            break
                    if main_category:
                        break

                # 修复：若没匹配到规则，用默认分类（不再用空值）
                if not main_category:
                    main_category = default_main  # 用上面定义的默认分类
                    sub_category = str(row.get('商品说明', ''))[:20] if row.get('商品说明') else '无说明'

                # 更新分类字段（确保有值）
                df.at[idx, '调整后分类'] = main_category
                df.at[idx, '调整后子分类'] = sub_category

            return df

        except Exception as e:
            print(f"应用分类规则时出错: {str(e)}")
            # 出错时，给分类字段赋默认值（避免空字段）
            df['调整后分类'] = df.apply(
                lambda x: '支出-其他' if x.get('收/支') in ['支出', '支']
                else ('收入-其他' if x.get('收/支') in ['收入', '收']
                      else '非收支'), axis=1
            )
            df['调整后子分类'] = df.get('商品说明', '').astype(str).str[:20]
            return df

    def process_and_print_bills(self, folder_path: str) -> pd.DataFrame:
        """批量解析账单 + 自动输出到控制台（新增错误捕获）"""
        try:
            # 1. 原有解析逻辑（保留）
            print("【调试】开始解析账单...")
            combined_df = self.process_all_bills(folder_path)
            print(f"【调试】解析完成，共 {len(combined_df)} 条记录")

            # 2. 分类统计（关键：加try-except捕获分类错误）
            print("【调试】开始生成分类统计...")
            from transaction_classifier import TransactionClassifier
            classifier = TransactionClassifier()

            # 先检查combined_df是否有“分类”或“调整后分类”字段
            if '调整后分类' not in combined_df.columns:
                print("【调试】缺少'调整后分类'字段，自动添加空字段")
                combined_df['调整后分类'] = ''

            # 生成统计数据（捕获这里的错误）
            try:
                stats = classifier.get_classification_statistics(combined_df)
                print("【调试】分类统计生成成功")
            except Exception as e:
                print(f"【调试】生成分类统计出错：{str(e)}")
                # 若统计出错，用简化统计避免程序崩溃
                stats = {
                    '总收入': 0, '总支出': 0, '净收入': 0,
                    '分类统计': {'数量': {}, '金额': {}},
                    '平台统计': {'sum': {}, 'count': {}}
                }

            # 3. 控制台输出（捕获输出错误）
            print("【调试】开始输出到控制台...")
            from console_printer import ConsolePrinter
            console_printer = ConsolePrinter()

            print("\n" + "=" * 60)
            print("                账单解析结果 - 控制台输出                ")
            print("=" * 60)

            # 输出时加try-except，避免输出格式错误导致崩溃
            try:
                console_printer.print_parsed_data_summary(combined_df)
                console_printer.print_transaction_details(combined_df)
                console_printer.print_classification_stats(stats)
            except Exception as e:
                print(f"【调试】控制台输出出错：{str(e)}")
                print("【调试】输出简化版数据：")
                print(f"总记录数：{len(combined_df)} 条")
                print(f"微信记录：{len(combined_df[combined_df['平台'] == '微信'])} 条")
                print(f"支付宝记录：{len(combined_df[combined_df['平台'] == '支付宝'])} 条")

            print("=" * 60 + "\n")
            return combined_df

        # 捕获所有错误，打印详细信息（关键：定位错误原因）
        except Exception as e:
            # 打印错误类型和详细信息，方便定位
            import traceback
            error_detail = traceback.format_exc()
            print(f"【调试】process_and_print_bills 整体出错：{str(e)}")
            print(f"【调试】错误详情：\n{error_detail}")
            # 抛出错误让弹窗显示（便于你看到具体问题）
            raise ValueError(f"处理失败: 分类环节出错 - {str(e)}")
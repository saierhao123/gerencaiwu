"""
交易分类模块
负责对交易记录进行自动分类和手动分类管理
"""

import pandas as pd
import json
from typing import Dict, Optional
import os
import re


class TransactionClassifier:
    """交易分类器"""
    
    def __init__(self, config_file: str = "config.json", user_rules_file: str = "user_rules.json"):
        """初始化分类器，加载分类规则与用户手动分类缓存
        - user_rules.json 用于保存用户记忆的分类规则（可选持久化）
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.classification_rules = self.config.get('分类规则', {})
        self.user_rules_file = user_rules_file
        self.user_classifications: Dict[str, str] = self._load_user_rules()
    
    def _load_user_rules(self) -> Dict[str, str]:
        if os.path.exists(self.user_rules_file):
            try:
                with open(self.user_rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def save_user_rules(self):
        try:
            # 只有内容有变化时才保存，减少磁盘写入和控制台输出
            if os.path.exists(self.user_rules_file):
                with open(self.user_rules_file, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                if old_data == self.user_classifications:
                    return  # 无变化则不保存
            dir_path = os.path.dirname(self.user_rules_file)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            with open(self.user_rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_classifications, f, ensure_ascii=False, indent=2)
            # 控制台输出只保留一次
            print(f"用户规则已保存到 {self.user_rules_file}，共 {len(self.user_classifications)} 条")
        except Exception as e:
            print(f"保存用户规则失败：{str(e)}")
    
    def _text(self, value) -> str:
        return str(value or '').lower()

    def classify_transaction(self, row: pd.Series) -> tuple:
        # 新增：失败状态直接返回特殊分类
        fail_status_keywords = ['对方已退还', '已全额退款', '还款失败', '失败', '退款', '退还']
        status = str(row.get('交易状态', '') or '').strip()
        if any(kw in status for kw in fail_status_keywords):
            return '未达到分类要求', 'status_filter'
        try:
            amount = float(row.get('金额', 0) or 0)
            party = str(row.get('交易对方', '') or '').strip()
            desc = str(row.get('商品说明', '') or '').strip()
            # 生成金额区间
            fuzzy_config = self.config.get('系统设置', {}).get('金额模糊化', {})
            enable_fuzzy = fuzzy_config.get('启用', True)
            ignore_amount = fuzzy_config.get('忽略金额', False)
            intervals = fuzzy_config.get('区间设置', [0, 10, 20, 50, 100, 300, 500])
            max_label = fuzzy_config.get('超出最大区间的标识', '500+')
            amount_part = ""
            if not ignore_amount:
                amount_abs = abs(amount)
                amount_label = max_label
                if amount_abs == 0:
                    amount_label = "0"
                else:
                    for i in range(len(intervals) - 1):
                        min_amt = intervals[i]
                        max_amt = intervals[i + 1]
                        if min_amt <= amount_abs < max_amt:
                            amount_label = f"{min_amt}-{max_amt}"
                            break
                amount_part = f"{amount_label}"
            # 指纹key
            key = f"{amount_part}_{party}"
            # 1. user_rules.json优先，商品说明正则匹配
            rules = self.user_classifications.get(key, [])
            for rule in rules:
                try:
                    pattern = rule.get("desc_regex", "")
                    if pattern and re.search(pattern, desc):
                        print(f"【调试】user_rules命中: {key} | {pattern} -> {rule.get('category')}")
                        return rule.get("category"), "user_rules"
                except Exception as e:
                    print(f"【调试】user_rules正则异常: {e}")
            # 2. user_rules模糊匹配（只用金额区间+对方，无商品说明）
            if rules:
                print(f"【调试】user_rules模糊命中: {key}（无商品说明）-> {rules[0].get('category')}")
                return rules[0].get('category'), "user_rules"
            # 3. 未命中，输出未匹配指纹
            print(f"【调试】user_rules未命中: {key}_{desc}")
        except Exception as e:
            print(f"【调试】user_rules匹配异常: {e}")

        # 1) 跨平台转账优先
        if bool(row.get('跨平台转账', False)):
            return '非收支', "config"
        # 2) config规则
        t_type = self._text(row.get('交易分类', ''))
        desc = self._text(row.get('商品说明', ''))
        party = self._text(row.get('交易对方', ''))
        income_expense = self._text(row.get('收/支', ''))  # 使用收/支字段
        haystack = f"{t_type} {desc} {party}"
        # 2) 非收支关键词
        for kw in self.classification_rules.get('非收支', []):
            if self._text(kw) in haystack:
                return '非收支', "config"
        # 3) 支出 / 收入
        if '支出' in income_expense:
            for cate, kws in self.classification_rules.get('支出', {}).items():
                for kw in kws:
                    if self._text(kw) in haystack:
                        return f'支出-{cate}', "config"
            return '支出-其他', "config"
        if '收入' in income_expense:
            for cate, kws in self.classification_rules.get('收入', {}).items():
                for kw in kws:
                    if self._text(kw) in haystack:
                        return f'收入-{cate}', "config"
            return '收入-其他', "config"
        return '未分类', "config"

    def _fingerprint(self, row: pd.Series) -> str:
        """指纹=金额区间_交易对方_商品说明，全部去除多余空格"""
        party = str(row.get('交易对方', '') or '').strip()
        desc = str(row.get('商品说明', '') or '').strip()

        # 2. 从config读取“金额模糊化”配置
        fuzzy_config = self.config.get('系统设置', {}).get('金额模糊化', {})
        enable_fuzzy = fuzzy_config.get('启用', True)
        ignore_amount = fuzzy_config.get('忽略金额', False)  # 读取“忽略金额”开关
        intervals = fuzzy_config.get('区间设置', [0, 5, 20, 50, 100])
        max_label = fuzzy_config.get('超出最大区间的标识', '100+')

        # 3. 处理金额部分（根据开关决定是否包含金额）
        amount_part = ""  # 金额部分的字符串（空=忽略金额）
        if not ignore_amount:
            # 不忽略金额：按之前的区间逻辑生成金额标识
            amount = row.get('金额', 0)
            try:
                amount_val = float(amount)
            except Exception:
                amount_val = 0.0
            amount_abs = abs(amount_val)

            if enable_fuzzy:
                # 金额区间匹配
                amount_label = max_label
                if amount_abs == 0:
                    amount_label = "0"
                else:
                    for i in range(len(intervals) - 1):
                        min_amt = intervals[i]
                        max_amt = intervals[i + 1]
                        if min_amt <= amount_abs < max_amt:
                            amount_label = f"{min_amt}-{max_amt}"
                            break
                amount_part = f"{amount_label}_"  # 加“_”分隔，方便后续拆分
            else:
                # 不启用模糊化：保留整数位金额
                amount_part = f"{amount_val:.0f}_"

        # 4. 生成最终指纹（忽略金额时：交易对方_商品说明；不忽略时：金额标识_交易对方_商品说明）
        return f"{amount_part}{party}_{desc}".strip()

    def _fingerprint_with_custom_desc(self, row: pd.Series, desc: str) -> str:
        party = str(row.get('交易对方', '') or '').strip()
        # 金额区间部分同原逻辑
        fuzzy_config = self.config.get('系统设置', {}).get('金额模糊化', {})
        enable_fuzzy = fuzzy_config.get('启用', True)
        ignore_amount = fuzzy_config.get('忽略金额', False)
        intervals = fuzzy_config.get('区间设置', [0, 5, 20, 50, 100])
        max_label = fuzzy_config.get('超出最大区间的标识', '100+')
        amount_part = ""
        if not ignore_amount:
            amount = row.get('金额', 0)
            try:
                amount_val = float(amount)
            except Exception:
                amount_val = 0.0
            amount_abs = abs(amount_val)
            if enable_fuzzy:
                amount_label = max_label
                if amount_abs == 0:
                    amount_label = "0"
                else:
                    for i in range(len(intervals) - 1):
                        min_amt = intervals[i]
                        max_amt = intervals[i + 1]
                        if min_amt <= amount_abs < max_amt:
                            amount_label = f"{min_amt}-{max_amt}"
                            break
                amount_part = f"{amount_label}_"
            else:
                amount_part = f"{amount_val:.0f}_"
        return f"{amount_part}{party}_{desc}".strip()

    def classify_all_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """分类所有交易记录，优先应用user_rules"""
        if '分类' in df.columns and '分类来源' in df.columns:
            return df  # 如果已经分类，直接返回，避免重复计算
        df_copy = df.copy()
        # 添加分类字段和分类来源字段
        results = df_copy.apply(self.classify_transaction, axis=1)
        df_copy['分类'] = results.apply(lambda x: x[0])
        df_copy['分类来源'] = results.apply(lambda x: x[1])
        return df_copy

    def add_user_classification(self, row: pd.Series, classification: str, persist: bool = True):
        self.user_classifications[self._fingerprint(row)] = classification
        if persist:
            self.save_user_rules()

    def get_classification_statistics(self, df: pd.DataFrame) -> Dict:
        print("【调试】进入 get_classification_statistics，数据行数：", len(df))
        stats: Dict = {}
        try:
            # 检查关键字段
            print("【调试】字段列表：", df.columns.tolist())
            # 关键：先检查“分类”或“调整后分类”字段是否存在，不存在则用默认字段
            if '调整后分类' in df.columns and not df['调整后分类'].empty:
                category_field = '调整后分类'
            elif '分类' in df.columns and not df['分类'].empty:
                category_field = '分类'
            else:
                # 若都没有，临时添加“分类”字段（避免报错）
                df['分类'] = '未分类'
                category_field = '分类'

            # 金额字段类型转换
            df_copy = df.copy()
            df_copy['金额'] = pd.to_numeric(df_copy['金额'], errors='coerce').fillna(0)

            # 统计前输出部分数据
            print("【调试】分类字段样例：", df_copy[category_field].head(5).tolist())
            print("【调试】金额字段样例：", df_copy['金额'].head(5).tolist())

            # 计算总收入/总支出
            stats['总收入'] = df_copy[df_copy[category_field].str.startswith('收入', na=False)]['金额'].sum()
            stats['总支出'] = df_copy[df_copy[category_field].str.startswith('支出', na=False)]['金额'].sum()
            stats['非收支总额'] = df_copy[df_copy[category_field] == '非收支']['金额'].sum()
            stats['净收入'] = stats['总收入'] - stats['总支出']

            # 分类统计
            stats['分类统计'] = {
                '数量': df_copy[category_field].value_counts(dropna=False).to_dict(),
                '金额': df_copy.groupby(category_field, dropna=False)['金额'].sum().to_dict()
            }

            # 平台统计
            if '平台' in df_copy.columns:
                platform_agg = df_copy.groupby('平台', dropna=False)['金额'].agg(['sum', 'count']).round(2)
                stats['平台统计'] = platform_agg.to_dict()
            else:
                stats['平台统计'] = {'sum': {}, 'count': {}}

            print("【调试】统计结果预览：", {k: str(v)[:200] for k, v in stats.items()})
            return stats
        except Exception as e:
            import traceback
            print("【调试】get_classification_statistics异常：", str(e))
            print(traceback.format_exc())
            # 返回空统计，避免程序崩溃
            return {
                '总收入': 0, '总支出': 0, '净收入': 0,
                '分类统计': {'数量': {}, '金额': {}},
                '平台统计': {'sum': {}, 'count': {}}
            }

    def get_daily_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        df_copy = df.copy()
        df_copy['日期'] = pd.to_datetime(df_copy['交易时间'], errors='coerce').dt.date
        daily = df_copy.groupby('日期', dropna=True).apply(
            lambda g: pd.Series({
                '收入': g[g['分类'].str.startswith('收入', na=False)]['金额'].sum(),
                '支出': g[g['分类'].str.startswith('支出', na=False)]['金额'].sum()
            })
        ).reset_index()
        if not daily.empty:
            daily['净额'] = daily['收入'] - daily['支出']
        return daily
    
    def get_special_statistics(self, df: pd.DataFrame, keyword: str = '馒头') -> Dict:
        kw = self._text(keyword)
        g = df[(df['分类'].str.startswith('支出', na=False)) & (
            df['商品说明'].astype(str).str.lower().str.contains(kw, na=False) |
            df['交易对方'].astype(str).str.lower().str.contains(kw, na=False)
        )]
        return {
            '金额': float(g['金额'].sum() if not g.empty else 0),
            '笔数': int(len(g))
        }
    
    def get_finance_refund_statistics(self, df: pd.DataFrame) -> Dict:
        finance_kws = ['理财', '基金', '余额宝']
        refund_kw = '退款'
        hay = (df['交易分类'].astype(str).str.lower() + ' ' + df['商品说明'].astype(str).str.lower())
        mask = hay.str.contains(refund_kw.lower(), na=False)
        for k in finance_kws:
            mask = mask | hay.str.contains(k.lower(), na=False)
        g = df[mask]
        return {
            '金额': float(g['金额'].sum() if not g.empty else 0),
            '笔数': int(len(g))
        }

"""
交易分类模块
负责对交易记录进行自动分类和手动分类管理
"""

import pandas as pd
import json
from typing import Dict, Optional
import os


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
            # 确保文件夹存在
            if not os.path.exists(os.path.dirname(self.user_rules_file)):
                os.makedirs(os.path.dirname(self.user_rules_file), exist_ok=True)

            with open(self.user_rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_classifications, f, ensure_ascii=False, indent=2)

            # 验证保存结果
            if os.path.exists(self.user_rules_file):
                print(f"用户规则已保存到 {self.user_rules_file}，共 {len(self.user_classifications)} 条")
            else:
                print(f"警告：用户规则保存路径不存在 {self.user_rules_file}")
        except Exception as e:
            print(f"保存用户规则失败：{str(e)}")
    
    def _text(self, value) -> str:
        return str(value or '').lower()

    def classify_transaction(self, row: pd.Series) -> str:
        """分类优先级：
        1) 跨平台转账标记 True → 非收支
        2) 关键词 非收支
        3) 按收/支 分别匹配关键词
        4) 未分类
        """
        # 1) 跨平台转账优先
        if bool(row.get('跨平台转账', False)):
            return '非收支'
        
        t_type = self._text(row.get('交易分类', ''))
        desc = self._text(row.get('商品说明', ''))
        party = self._text(row.get('交易对方', ''))
        income_expense = self._text(row.get('收/支', ''))  # 使用收/支字段
        haystack = f"{t_type} {desc} {party}"
        
        # 2) 非收支关键词
        for kw in self.classification_rules.get('非收支', []):
            if self._text(kw) in haystack:
                return '非收支'
        
        # 3) 支出 / 收入
        if '支出' in income_expense:
            for cate, kws in self.classification_rules.get('支出', {}).items():
                for kw in kws:
                    if self._text(kw) in haystack:
                        return f'支出-{cate}'
            return '支出-其他'
        if '收入' in income_expense:
            for cate, kws in self.classification_rules.get('收入', {}).items():
                for kw in kws:
                    if self._text(kw) in haystack:
                        return f'收入-{cate}'
            return '收入-其他'
        return '未分类'

    def _fingerprint(self, row: pd.Series) -> str:
        """优化后：支持配置“是否忽略金额”，指纹=（金额相关_）交易对方_商品说明"""
        # 1. 提取交易核心信息（交易对方、商品说明，去空格避免差异）
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
        return f"{amount_part}{party}_{desc}"
    
    def classify_all_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """分类所有交易记录"""
        df_copy = df.copy()
        
        # 添加分类字段
        df_copy['分类'] = df_copy.apply(self.classify_transaction, axis=1)
        
        # 应用用户记忆
        for idx, row in df_copy.iterrows():
            fp = self._fingerprint(row)
            if fp in self.user_classifications:
                df_copy.at[idx, '分类'] = self.user_classifications[fp]
        
        return df_copy
    
    def add_user_classification(self, row: pd.Series, classification: str, persist: bool = True):
        self.user_classifications[self._fingerprint(row)] = classification
        if persist:
            self.save_user_rules()

    def get_classification_statistics(self, df: pd.DataFrame) -> Dict:
        stats: Dict = {}
        # 关键：先检查“分类”或“调整后分类”字段是否存在，不存在则用默认字段
        if '调整后分类' in df.columns and not df['调整后分类'].empty:
            category_field = '调整后分类'  # 优先用BillParser生成的“调整后分类”
        elif '分类' in df.columns and not df['分类'].empty:
            category_field = '分类'
        else:
            # 若都没有，临时添加“分类”字段（避免报错）
            df['分类'] = '未分类'
            category_field = '分类'

        # 修复：统计时先过滤无效金额（确保金额是数值型）
        df_copy = df.copy()
        df_copy['金额'] = pd.to_numeric(df_copy['金额'], errors='coerce').fillna(0)

        # 计算总收入/总支出（用category_field，避免硬编码“分类”）
        stats['总收入'] = df_copy[df_copy[category_field].str.startswith('收入', na=False)]['金额'].sum()
        stats['总支出'] = df_copy[df_copy[category_field].str.startswith('支出', na=False)]['金额'].sum()
        stats['非收支总额'] = df_copy[df_copy[category_field] == '非收支']['金额'].sum()
        stats['净收入'] = stats['总收入'] - stats['总支出']

        # 分类统计（同样用category_field）
        stats['分类统计'] = {
            '数量': df_copy[category_field].value_counts(dropna=False).to_dict(),
            '金额': df_copy.groupby(category_field, dropna=False)['金额'].sum().to_dict()
        }

        # 平台统计（检查“平台”字段是否存在）
        if '平台' in df_copy.columns:
            platform_agg = df_copy.groupby('平台', dropna=False)['金额'].agg(['sum', 'count']).round(2)
            stats['平台统计'] = platform_agg.to_dict()
        else:
            stats['平台统计'] = {'sum': {}, 'count': {}}  # 无平台字段时返回空

        return stats
    
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
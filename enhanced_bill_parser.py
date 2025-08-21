import json
import re
import pandas as pd
from collections import defaultdict

class TransactionClassifier:
    def __init__(self, rules_path='classification_rules.json'):
        self.rules = self._load_rules(rules_path)
        self.custom_rules = []
        self.reset_stats()

    def reset_stats(self):
        self.stats = defaultdict(lambda: defaultdict(float))

    def _load_rules(self, path):
        """加载JSON分类规则"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                # 验证必要结构
                assert '分类规则' in rules and '支出' in rules['分类规则']
                return rules
        except Exception as e:
            print(f"无法加载分类规则: {str(e)}，使用默认规则")
            return {
                "分类规则": {
                    "支出": {"其他": {"keywords": []}},
                    "收入": {"其他": {"keywords": []}},
                    "非收支": {"其他": {"keywords": []}}
                },
                "系统设置": {}
            }

    def add_custom_rule(self, main_cat, sub_cat, keywords=None, regex=None, 
                       amount_range=None, exclude=None, priority=1):
        """添加自定义分类规则"""
        self.custom_rules.append({
            "main_category": main_cat,
            "sub_category": sub_cat,
            "keywords": keywords or [],
            "regex": regex or [],
            "amount_range": amount_range or [0, float('inf')],
            "exclude": exclude or [],
            "priority": priority
        })

    def _match_rule(self, text, amount, rule):
        """检查单条规则是否匹配"""
        # 排除关键词检查
        for kw in rule.get('exclude', []):
            if kw.lower() in text.lower():
                return False

        # 金额范围检查
        min_amt, max_amt = rule.get('amount_range', [0, float('inf')])
        if not (min_amt <= abs(amount) <= max_amt):
            return False

        # 关键词匹配
        for kw in rule.get('keywords', []):
            if kw.lower() in text.lower():
                return True

        # 正则匹配
        for pattern in rule.get('regex', []):
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def classify_transaction(self, transaction):
        """分类单笔交易"""
        text = f"{transaction.get('交易对方', '')} {transaction.get('商品说明', '')}"
        amount = float(transaction.get('金额', 0))
        
        # 确定主分类
        main_cat = transaction.get('收/支', '').strip()
        if not main_cat:
            main_cat = '收入' if amount > 0 else '支出' if amount < 0 else '非收支'

        # 查找最佳匹配
        best_match = {
            'sub_cat': self.rules['系统设置'].get('默认分类', {}).get(main_cat, '其他'),
            'priority': -1
        }

        # 检查内置规则
        if main_cat in self.rules['分类规则']:
            for sub_cat, rule in self.rules['分类规则'][main_cat].items():
                if self._match_rule(text, amount, rule):
                    priority = rule.get('priority', 0)
                    if priority > best_match['priority']:
                        best_match = {'sub_cat': sub_cat, 'priority': priority}

        # 检查自定义规则
        for rule in self.custom_rules:
            if rule['main_category'] == main_cat and self._match_rule(text, amount, rule):
                if rule['priority'] > best_match['priority']:
                    best_match = {'sub_cat': rule['sub_category'], 'priority': rule['priority']}

        # 记录统计
        self.stats[main_cat][best_match['sub_cat']] += abs(amount)
        return main_cat, best_match['sub_cat']

    def classify_all_transactions(self, df):
        """批量分类交易数据"""
        self.reset_stats()
        df['调整后分类'] = ''
        df['调整后子分类'] = ''

        for idx, row in df.iterrows():
            main_cat, sub_cat = self.classify_transaction(row)
            df.at[idx, '调整后分类'] = main_cat
            df.at[idx, '调整后子分类'] = sub_cat

        return df

    def get_classification_statistics(self, df):
        """获取分类统计信息"""
        # 确保已经分类
        if '调整后分类' not in df.columns:
            df = self.classify_all_transactions(df)
        
        # 准备统计数据
        stats = {
            '总记录数': len(df),
            '总金额': df['金额'].sum(),
            '收入总额': df[df['调整后分类'] == '收入']['金额'].sum(),
            '支出总额': df[df['调整后分类'] == '支出']['金额'].sum(),
            '非收支总额': df[df['调整后分类'] == '非收支']['金额'].sum(),
            '分类统计': {}
        }
        
        # 按主分类和子分类统计
        for main_cat, sub_cats in self.stats.items():
            stats['分类统计'][main_cat] = {
                '总额': sum(sub_cats.values()),
                '子分类': dict(sub_cats)
            }
        
        return stats
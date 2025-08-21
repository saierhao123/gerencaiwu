import sys
import json
import re
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QDialog, QLineEdit, QTextEdit, QComboBox,
                             QDialogButtonBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor
from collections import defaultdict


class EnhancedTransactionClassifier:
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
            print(f"无法加载分类规则: {str(e)}")
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
        for sub_cat, rule in self.rules['分类规则'].get(main_cat, {}).items():
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

    def get_statistics(self):
        """获取分类统计结果"""
        return dict(self.stats)


class ProcessingThread(QThread):
    progress_updated = pyqtSignal(str)
    processing_finished = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path, classifier):
        super().__init__()
        self.file_path = file_path
        self.classifier = classifier

    def run(self):
        try:
            self.progress_updated.emit("正在加载数据...")
            df = pd.read_csv(self.file_path, encoding='utf-8')

            self.progress_updated.emit("正在分类交易...")
            classified_df = self.classifier.classify_all_transactions(df)

            self.progress_updated.emit("正在生成统计...")
            stats = self.classifier.get_statistics()

            self.processing_finished.emit({
                'dataframe': classified_df,
                'statistics': stats
            })
        except Exception as e:
            self.error_occurred.emit(f"处理失败: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.classifier = EnhancedTransactionClassifier()
        self.init_ui()
        self.load_sample_rules()

    def init_ui(self):
        self.setWindowTitle("增强版记账分类系统")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 控制区域
        control_layout = QHBoxLayout()
        self.btn_load = QPushButton("加载CSV文件")
        self.btn_load.clicked.connect(self.load_csv)
        control_layout.addWidget(self.btn_load)

        self.btn_classify = QPushButton("开始分类")
        self.btn_classify.clicked.connect(self.start_classification)
        self.btn_classify.setEnabled(False)
        control_layout.addWidget(self.btn_classify)

        self.btn_add_rule = QPushButton("添加规则")
        self.btn_add_rule.clicked.connect(self.show_add_rule_dialog)
        control_layout.addWidget(self.btn_add_rule)
        layout.addLayout(control_layout)

        # 数据显示区域
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "交易时间", "交易对方", "商品说明", "金额", "主分类", "子分类"
        ])

        # 修正的列宽设置代码
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # 状态栏
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

    def load_sample_rules(self):
        """加载示例自定义规则"""
        self.classifier.add_custom_rule(
            main_cat="支出",
            sub_cat="X_健身运动",
            keywords=["健身房", "私教课", "瑜伽"],
            amount_range=[100, 5000],
            priority=2
        )
        self.classifier.add_custom_rule(
            main_cat="支出",
            sub_cat="Y_数码产品",
            regex=["iPhone.*", "MacBook.*", "耳机$"],
            amount_range=[500, 20000],
            priority=2
        )

    def load_csv(self):
        """加载CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开CSV文件", "", "CSV文件 (*.csv)")
        if file_path:
            self.current_file = file_path
            self.btn_classify.setEnabled(True)
            self.status_label.setText(f"已加载文件: {file_path}")

    def start_classification(self):
        """开始分类处理"""
        if not hasattr(self, 'current_file'):
            QMessageBox.warning(self, "警告", "请先加载CSV文件")
            return

        self.thread = ProcessingThread(self.current_file, self.classifier)
        self.thread.progress_updated.connect(self.update_status)
        self.thread.processing_finished.connect(self.show_results)
        self.thread.error_occurred.connect(self.show_error)
        self.thread.start()

        self.btn_classify.setEnabled(False)
        self.status_label.setText("正在处理...")

    def update_status(self, message):
        """更新状态信息"""
        self.status_label.setText(message)

    def show_results(self, result):
        """显示分类结果"""
        df = result['dataframe']
        stats = result['statistics']

        # 显示在表格中
        self.table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('交易时间', ''))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('交易对方', ''))))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get('商品说明', ''))))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥{float(row['金额']):.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(row['调整后分类']))
            self.table.setItem(i, 5, QTableWidgetItem(row['调整后子分类']))

        # 显示统计信息
        stat_msg = "分类统计:\n"
        for main_cat, sub_cats in stats.items():
            stat_msg += f"{main_cat}:\n"
            for sub_cat, amount in sub_cats.items():
                stat_msg += f"  {sub_cat}: ¥{amount:.2f}\n"

        QMessageBox.information(self, "分类完成", stat_msg)
        self.btn_classify.setEnabled(True)
        self.status_label.setText("分类完成")

    def show_error(self, message):
        """显示错误信息"""
        QMessageBox.critical(self, "错误", message)
        self.btn_classify.setEnabled(True)
        self.status_label.setText("就绪")

    def show_add_rule_dialog(self):
        """显示添加规则对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加自定义规则")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # 主分类选择
        layout.addWidget(QLabel("主分类:"))
        main_cat_combo = QComboBox()
        main_cat_combo.addItems(["支出", "收入", "非收支"])
        layout.addWidget(main_cat_combo)

        # 子分类名称
        layout.addWidget(QLabel("子分类名称:"))
        sub_cat_edit = QLineEdit()
        layout.addWidget(sub_cat_edit)

        # 关键词
        layout.addWidget(QLabel("关键词(逗号分隔):"))
        keywords_edit = QLineEdit()
        layout.addWidget(keywords_edit)

        # 正则表达式
        layout.addWidget(QLabel("正则表达式(每行一个):"))
        regex_edit = QTextEdit()
        regex_edit.setMaximumHeight(80)
        layout.addWidget(regex_edit)

        # 金额范围
        layout.addWidget(QLabel("金额范围:"))
        amount_layout = QHBoxLayout()
        min_amt_edit = QLineEdit()
        min_amt_edit.setPlaceholderText("最小值")
        max_amt_edit = QLineEdit()
        max_amt_edit.setPlaceholderText("最大值")
        amount_layout.addWidget(min_amt_edit)
        amount_layout.addWidget(QLabel("到"))
        amount_layout.addWidget(max_amt_edit)
        layout.addLayout(amount_layout)

        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 收集规则数据
            main_cat = main_cat_combo.currentText()
            sub_cat = sub_cat_edit.text().strip()
            keywords = [kw.strip() for kw in keywords_edit.text().split(',') if kw.strip()]
            regex = [line.strip() for line in regex_edit.toPlainText().split('\n') if line.strip()]

            try:
                min_amt = float(min_amt_edit.text()) if min_amt_edit.text() else 0
                max_amt = float(max_amt_edit.text()) if max_amt_edit.text() else float('inf')
            except ValueError:
                QMessageBox.warning(self, "输入错误", "金额必须是数字")
                return

            # 添加规则
            self.classifier.add_custom_rule(
                main_cat=main_cat,
                sub_cat=sub_cat,
                keywords=keywords,
                regex=regex,
                amount_range=[min_amt, max_amt],
                priority=2
            )
            QMessageBox.information(self, "成功", "自定义规则已添加")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
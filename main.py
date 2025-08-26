"""
个人记账管理系统主程序
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QComboBox, QMessageBox, QHeaderView
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor  # 补充导入
import pandas as pd
from console_printer import ConsolePrinter
from bill_parser import BillParser
from transaction_classifier import TransactionClassifier

# 日志配置
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

class ProcessingThread(QThread):
    progress_updated = pyqtSignal(str, int)
    processing_finished = pyqtSignal(object, object, object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
    
    def run(self):
        try:
            self.progress_updated.emit("开始解析账单文件夹...", 10)
            parser = BillParser()
            df = parser.process_all_bills(self.folder_path)
            self.progress_updated.emit(f"成功解析 {len(df)} 条交易记录", 30)

            self.progress_updated.emit("开始分类交易...", 50)
            classifier = TransactionClassifier()
            classified_df = classifier.classify_all_transactions(df)
            self.progress_updated.emit("交易分类完成", 70)

            self.progress_updated.emit("生成统计信息...", 85)
            try:
                stats = classifier.get_classification_statistics(classified_df)
            except Exception as e:
                stats = {}
            self.progress_updated.emit("统计信息生成完成", 100)
            self.processing_finished.emit(classified_df, stats, None)
        except Exception as e:
            logging.exception("ProcessingThread.run异常")
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.stats = None
        self.current_folder = None
        self.row_to_original_index = {}
        self.init_ui()
    
    def init_ui(self):
        try:
            self.setWindowTitle("个人记账管理系统")
            self.setGeometry(100, 100, 1400, 900)
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            control_layout = QHBoxLayout()
            self.folder_label = QLabel("📁 当前账单文件夹: 未选择")
            self.folder_label.setWordWrap(True)
            self.folder_label.setStyleSheet("font-size: 12px; color: #555;")
            control_layout.addWidget(self.folder_label, stretch=1)
            btn_layout = QHBoxLayout()
            select_folder_btn = QPushButton("📂 选择账单文件夹")
            select_folder_btn.setStyleSheet("padding: 8px; font-size: 12px;")
            btn_layout.addWidget(select_folder_btn)
            self.process_btn = QPushButton("▶️ 开始处理账单")
            self.process_btn.setStyleSheet("padding: 8px; font-size: 12px; background-color: #4CAF50; color: white;")
            btn_layout.addWidget(self.process_btn)
            self.refresh_btn = QPushButton("🔄 刷新数据")
            self.refresh_btn.setStyleSheet("padding: 8px; font-size: 12px;")
            btn_layout.addWidget(self.refresh_btn)
            control_layout.addLayout(btn_layout)
            main_layout.addLayout(control_layout)
            select_folder_btn.clicked.connect(self.select_folder)
            self.process_btn.clicked.connect(self.start_processing)
            self.refresh_btn.clicked.connect(self.refresh_data)
            progress_layout = QHBoxLayout()
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setVisible(False)
            self.progress_label = QLabel("准备就绪")
            self.progress_label.setStyleSheet("color: #0066cc; font-weight: bold;")
            progress_layout.addWidget(self.progress_label)
            progress_layout.addWidget(self.progress_bar, 1)
            main_layout.addLayout(progress_layout)
            self.tab_widget = QTabWidget()
            main_layout.addWidget(self.tab_widget)
            self.create_transaction_tab()
            self.set_default_folder()
        except Exception as e:
            logging.exception("MainWindow.init_ui异常")
            QMessageBox.critical(self, "错误", f"界面初始化失败: {e}")

    def create_transaction_tab(self):
        try:
            transaction_widget = QWidget()
            transaction_layout = QVBoxLayout(transaction_widget)
            filter_layout = QHBoxLayout()
            filter_layout.addWidget(QLabel("平台筛选:"))
            self.platform_filter = QComboBox()
            self.platform_filter.addItem("全部")
            self.platform_filter.setFixedWidth(150)
            self.platform_filter.currentTextChanged.connect(self.filter_transactions)
            filter_layout.addWidget(self.platform_filter)
            filter_layout.addWidget(QLabel("分类筛选:"))
            self.category_filter = QComboBox()
            self.category_filter.addItem("全部")
            self.category_filter.setFixedWidth(300)
            self.category_filter.currentTextChanged.connect(self.filter_transactions)
            filter_layout.addWidget(self.category_filter)
            # 新增交易状态筛选
            filter_layout.addWidget(QLabel("交易状态筛选:"))
            self.status_filter = QComboBox()
            self.status_filter.addItems(["全部", "成功", "失败"])
            self.status_filter.setFixedWidth(150)
            self.status_filter.currentTextChanged.connect(self.filter_transactions)
            filter_layout.addWidget(self.status_filter)
            filter_layout.addStretch()
            transaction_layout.addLayout(filter_layout)
            self.transaction_table = QTableWidget()
            self.transaction_table.setColumnCount(12)
            self.transaction_table.setHorizontalHeaderLabels([
                "交易时间", "平台", "交易分类", "交易对方", "商品说明",
                "收/支", "金额", "支付方式", "交易状态", "调整后分类", "调整后子分类", "分类来源"
            ])
            self.transaction_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # 禁止编辑
            header = self.transaction_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(12, QHeaderView.ResizeMode.Fixed)
            self.transaction_table.setColumnWidth(1, 80)
            self.transaction_table.setColumnWidth(2, 100)
            self.transaction_table.setColumnWidth(8, 100)
            self.transaction_table.setColumnWidth(9, 150)
            self.transaction_table.setColumnWidth(10, 100)
            self.transaction_table.setColumnWidth(11, 120)
            self.transaction_table.setColumnWidth(12, 100)
            transaction_layout.addWidget(self.transaction_table)
            self.tab_widget.addTab(transaction_widget, "交易明细")
        except Exception as e:
            logging.exception("MainWindow.create_transaction_tab异常")
            QMessageBox.critical(self, "错误", f"交易明细标签页初始化失败: {e}")

    def processing_finished(self, df: pd.DataFrame, stats: dict, report_text: str):
        logging.info("【调试】进入processing_finished")
        try:
            self.df = df
            self.stats = stats if stats is not None else {}
            logging.info("【调试】准备刷新表格")
            self.update_transaction_table()
            logging.info("【调试】刷新表格完成")
            logging.info("【调试】准备刷新筛选")
            self.update_filter_options()
            logging.info("【调试】刷新筛选完成")
        except Exception as e:
            logging.exception("MainWindow.processing_finished UI刷新异常")
            QMessageBox.critical(self, "错误", f"刷新界面时出错: {e}")
        try:
            self.progress_bar.setVisible(False)
            self.progress_label.setVisible(False)
            self.process_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
        except Exception as e:
            logging.exception("MainWindow.processing_finished 控件状态异常")
        try:
            logging.info("=== 开始执行控制台输出 ===")
            console_printer = ConsolePrinter()
            console_printer.print_all(df, stats)
            logging.info("=== 控制台输出执行完成 ===")
        except Exception as e:
            logging.exception("MainWindow.processing_finished 控制台输出异常")
        try:
            QMessageBox.information(self, "完成", "账单处理完成！")
        except Exception as e:
            logging.exception("MainWindow.processing_finished QMessageBox异常")

    def update_transaction_table(self):
        try:
            if self.df is None or self.df.empty:
                self.transaction_table.setRowCount(0)
                return

            # 移除可能影响背景色的样式表
            self.transaction_table.setStyleSheet("")

            self.transaction_table.setRowCount(len(self.df))
            self.row_to_original_index = {}

            fail_status_keywords = ['对方已退还', '已全额退款', '还款失败', '失败', '退款', '退还']

            for row_idx, (original_index, row_data) in enumerate(self.df.iterrows()):
                self.row_to_original_index[row_idx] = original_index
                time_str = str(row_data.get('交易时间', ''))
                if time_str and time_str != 'NaT':
                    try:
                        time_obj = pd.to_datetime(time_str)
                        time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass

                status_str = str(row_data.get('交易状态', ''))
                is_fail = any(kw in status_str for kw in fail_status_keywords)

                try:
                    amount_val = float(row_data.get('金额', 0) or 0)
                except Exception:
                    amount_val = 0.0

                # 确定行的背景色
                if is_fail:
                    row_color = QColor(255, 200, 200)  # 失败交易使用淡红色
                elif row_idx % 2 == 0:
                    row_color = QColor(230, 240, 188)  # 偶数行
                else:
                    row_color = QColor(255, 255, 255)  # 奇数行

                items = [
                    QTableWidgetItem(time_str),
                    QTableWidgetItem(str(row_data.get('平台', ''))),
                    QTableWidgetItem(str(row_data.get('交易分类', ''))),
                    QTableWidgetItem(str(row_data.get('交易对方', ''))),
                    QTableWidgetItem(str(row_data.get('商品说明', ''))),
                    QTableWidgetItem(str(row_data.get('收/支', ''))),
                    QTableWidgetItem(f"¥{amount_val:.2f}" if row_data.get('金额', 0) != '' else ''),
                    QTableWidgetItem(str(row_data.get('支付方式', '') or row_data.get('收/付款方式', ''))),
                    QTableWidgetItem(status_str),
                    QTableWidgetItem("未达到分类" if is_fail else str(row_data.get('调整后分类', ''))),
                    QTableWidgetItem("未达到分类" if is_fail else str(row_data.get('调整后子分类', ''))),
                    QTableWidgetItem(str(row_data.get('分类来源', '')))
                ]

                # 设置所有单元格的背景色
                for item in items:
                    item.setBackground(row_color)
                    # 确保背景色不会被样式覆盖
                    item.setData(Qt.ItemDataRole.BackgroundRole, row_color)

                for col, item in enumerate(items):
                    self.transaction_table.setItem(row_idx, col, item)

        except Exception as e:
            logging.exception("MainWindow.update_transaction_table异常")
            QMessageBox.critical(self, "错误", f"刷新表格时出错: {e}")

    def update_filter_options(self):
        try:
            if self.df is None or self.df.empty:
                return
            platforms = ['全部'] + sorted(self.df['平台'].unique().tolist())
            self.platform_filter.clear()
            self.platform_filter.addItems(platforms)
            categories = ['全部'] + sorted(self.df['调整后分类'].unique().tolist())
            self.category_filter.clear()
            self.category_filter.addItems(categories)
        except Exception as e:
            logging.exception("MainWindow.update_filter_options异常")
            QMessageBox.critical(self, "错误", f"刷新筛选选项时出错: {e}")

    def filter_transactions(self):
        try:
            if self.df is None or self.df.empty:
                self.transaction_table.setRowCount(0)
                return

            # 移除可能影响背景色的样式表
            self.transaction_table.setStyleSheet("")

            platform_filter = self.platform_filter.currentText()
            category_filter = self.category_filter.currentText()
            status_filter = self.status_filter.currentText()

            filtered_df = self.df.copy()
            if platform_filter != "全部":
                filtered_df = filtered_df[filtered_df['平台'] == platform_filter]
            if category_filter != "全部":
                filtered_df = filtered_df[filtered_df['调整后分类'] == category_filter]

            fail_status_keywords = ['对方已退还', '已全额退款', '还款失败', '失败', '退款', '退还']
            if status_filter == "成功":
                filtered_df = filtered_df[~filtered_df['交易状态'].astype(str).apply(
                    lambda x: any(kw in x for kw in fail_status_keywords))]
            elif status_filter == "失败":
                filtered_df = filtered_df[filtered_df['交易状态'].astype(str).apply(
                    lambda x: any(kw in x for kw in fail_status_keywords))]

            self.transaction_table.setRowCount(len(filtered_df))
            self.row_to_original_index = {}

            for row_idx, (original_index, row_data) in enumerate(filtered_df.iterrows()):
                self.row_to_original_index[row_idx] = original_index
                time_str = str(row_data.get('交易时间', ''))
                if time_str and time_str != 'NaT':
                    try:
                        time_obj = pd.to_datetime(time_str)
                        time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass

                status_str = str(row_data.get('交易状态', ''))
                is_fail = any(kw in status_str for kw in fail_status_keywords)

                # 确定行的背景色
                if is_fail:
                    row_color = QColor(255, 200, 200)  # 失败交易使用淡红色
                elif row_idx % 2 == 0:
                    row_color = QColor(230, 240, 188)  # 偶数行
                else:
                    row_color = QColor(255, 255, 255)  # 奇数行

                items = [
                    QTableWidgetItem(time_str),
                    QTableWidgetItem(str(row_data.get('平台', ''))),
                    QTableWidgetItem(str(row_data.get('交易分类', ''))),
                    QTableWidgetItem(str(row_data.get('交易对方', ''))),
                    QTableWidgetItem(str(row_data.get('商品说明', ''))),
                    QTableWidgetItem(str(row_data.get('收/支', ''))),
                    QTableWidgetItem(
                        f"¥{float(row_data.get('金额', 0) or 0):.2f}" if row_data.get('金额', 0) != '' else ''),
                    QTableWidgetItem(str(row_data.get('支付方式', '') or row_data.get('收/付款方式', ''))),
                    QTableWidgetItem(status_str),
                    QTableWidgetItem("未达到分类" if is_fail else str(row_data.get('调整后分类', ''))),
                    QTableWidgetItem("未达到分类" if is_fail else str(row_data.get('调整后子分类', ''))),
                    QTableWidgetItem(str(row_data.get('分类来源', '')))
                ]

                # 设置所有单元格的背景色
                for item in items:
                    item.setBackground(row_color)
                    # 确保背景色不会被样式覆盖
                    item.setData(Qt.ItemDataRole.BackgroundRole, row_color)

                for col, item in enumerate(items):
                    self.transaction_table.setItem(row_idx, col, item)

        except Exception as e:
            logging.exception("MainWindow.filter_transactions异常")
            QMessageBox.critical(self, "错误", f"筛选交易时出错: {e}")

    def select_folder(self):
        try:
            folder_path = QFileDialog.getExistingDirectory(self, "选择账单文件夹")
            if folder_path:
                self.current_folder = folder_path
                self.folder_label.setText(f"📁 当前账单文件夹: {folder_path}")
        except Exception as e:
            logging.exception("MainWindow.select_folder异常")
            QMessageBox.critical(self, "错误", f"选择文件夹时出错: {e}")

    def refresh_data(self):
        try:
            self.start_processing()
        except Exception as e:
            logging.exception("MainWindow.refresh_data异常")
            QMessageBox.critical(self, "错误", f"刷新数据时出错: {e}")

    def set_default_folder(self):
        try:
            default_folder = "zhangdang"
            if os.path.exists(default_folder):
                self.current_folder = default_folder
                self.folder_label.setText(f"📁 当前账单文件夹: {default_folder}")
        except Exception as e:
            logging.exception("MainWindow.set_default_folder异常")

    def start_processing(self):
        try:
            if not self.current_folder:
                QMessageBox.warning(self, "警告", "请先选择账单文件夹")
                return
            self.process_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_label.setText("正在处理账单...")
            self.processing_thread = ProcessingThread(self.current_folder)
            self.processing_thread.progress_updated.connect(self.on_progress_update)
            self.processing_thread.processing_finished.connect(self.processing_finished)
            self.processing_thread.error_occurred.connect(lambda msg: QMessageBox.critical(self, "错误", msg))
            self.processing_thread.start()
        except Exception as e:
            logging.exception("MainWindow.start_processing异常")
            QMessageBox.critical(self, "错误", f"开始处理账单时出错: {e}")

    def on_progress_update(self, message, value):
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        QApplication.processEvents()  # 强制刷新UI

def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.exception("main异常")
        QMessageBox.critical(None, "致命错误", f"程序启动失败: {e}")

if __name__ == "__main__":
    main()

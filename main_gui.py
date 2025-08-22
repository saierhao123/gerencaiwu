"""
主GUI界面
使用PyQt6实现用户友好的图形界面
"""

import sys
import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pandas as pd

from bill_parser import BillParser
from transaction_classifier import TransactionClassifier
from data_visualizer import DataVisualizer

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
except Exception:
    QWebEngineView = None
    QWebChannel = None


class ChartBridge(QObject):
    """桥接JS与PyQt：用于接收plotly点击事件payload"""
    chartClicked = pyqtSignal(str)

    @pyqtSlot(str)
    def onChartClick(self, payload_json: str):
        self.chartClicked.emit(payload_json)


class ProcessingThread(QThread):
    """在后台线程解析+分类+统计，避免阻塞UI线程"""
    progress_updated = pyqtSignal(str, int)  # 增加进度值
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
            # 专项统计
            try:
                special = {
                    '"馒头"支出统计': classifier.get_special_statistics(classified_df, '馒头'),
                    '理财退款统计': classifier.get_finance_refund_statistics(classified_df)
                }
            except Exception:
                special = {}
            self.progress_updated.emit("统计信息生成完成", 95)

            self.progress_updated.emit("生成可视化/报告...", 98)
            try:
                visualizer = DataVisualizer()
                report_text = visualizer.create_summary_report(stats, special)
            except Exception:
                report_text = ""
            self.progress_updated.emit("完成", 100)

            self.processing_finished.emit(classified_df, stats, report_text)
        except Exception as e:
            import traceback
            self.error_occurred.emit(f"{str(e)}\n{traceback.format_exc()}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.stats = None
        self.report_text = None
        self.visualizer = DataVisualizer()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("个人记账管理系统")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部控制区域
        control_layout = QHBoxLayout()
        self.folder_label = QLabel("账单文件夹: 未选择")
        self.folder_label.setMinimumWidth(300)
        control_layout.addWidget(self.folder_label)

        select_folder_btn = QPushButton("选择文件夹")
        select_folder_btn.clicked.connect(self.select_folder)
        control_layout.addWidget(select_folder_btn)

        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        control_layout.addWidget(self.process_btn)

        export_btn = QPushButton("导出结果CSV")
        export_btn.clicked.connect(self.export_csv)
        control_layout.addWidget(export_btn)

        main_layout.addLayout(control_layout)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        main_layout.addWidget(self.progress_label)

        # 标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.create_transaction_tab()
        self.create_statistics_tab()
        self.create_chart_tab()
        self.create_calendar_tab()

        self.set_default_folder()

    def create_transaction_tab(self):
        transaction_widget = QWidget()
        layout = QVBoxLayout(transaction_widget)

        # 筛选控件
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选:"))
        self.platform_filter = QComboBox()
        self.platform_filter.addItems(["全部平台", "微信", "支付宝"])
        self.platform_filter.currentTextChanged.connect(self.apply_filters_and_refresh)
        filter_layout.addWidget(self.platform_filter)
        self.category_filter = QComboBox()
        self.category_filter.addItems(["全部分类", "收入", "支出", "非收支"])
        self.category_filter.currentTextChanged.connect(self.apply_filters_and_refresh)
        filter_layout.addWidget(self.category_filter)
        # 新增交易状态筛选
        filter_layout.addWidget(QLabel("交易状态筛选:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "成功", "失败"])
        self.status_filter.currentTextChanged.connect(self.apply_filters_and_refresh)
        filter_layout.addWidget(self.status_filter)
        layout.addLayout(filter_layout)

        # 交易表
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(13)
        self.transaction_table.setHorizontalHeaderLabels([
            "交易时间", "平台", "交易对方", "商品说明", "金额", "分类", "收/付款方式", "交易状态",
            "交易单号", "调整后分类", "调整后子分类", "备注", "分类来源"
        ])
        self.transaction_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.transaction_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.transaction_table)

        self.tab_widget.addTab(transaction_widget, "交易明细")

    def create_statistics_tab(self):
        statistics_widget = QWidget()
        layout = QVBoxLayout(statistics_widget)

        # 重新加载按钮
        reload_layout = QHBoxLayout()
        reload_btn = QPushButton("重新加载统计")
        reload_btn.clicked.connect(self.reload_statistics)
        reload_layout.addWidget(reload_btn)
        reload_layout.addStretch()
        layout.addLayout(reload_layout)

        self.report_text_edit = QTextEdit()
        self.report_text_edit.setReadOnly(True)
        layout.addWidget(self.report_text_edit)
        self.tab_widget.addTab(statistics_widget, "统计报告")

    def create_chart_tab(self):
        chart_widget = QWidget()
        layout = QVBoxLayout(chart_widget)

        # 控制区域
        control_layout = QHBoxLayout()

        # 视图切换（全部/收入/支出）
        control_layout.addWidget(QLabel("视图:"))
        self.view_mode = QComboBox()
        self.view_mode.addItems(["全部", "仅收入", "仅支出"])
        self.view_mode.currentTextChanged.connect(self.refresh_charts)
        control_layout.addWidget(self.view_mode)

        # 分类标准选择
        control_layout.addWidget(QLabel("分类标准:"))
        self.classification_standard = QComboBox()
        self.classification_standard.addItems(["官方分类标准", "自定义分类标准"])
        self.classification_standard.currentTextChanged.connect(self.refresh_charts)
        control_layout.addWidget(self.classification_standard)

        # 重新加载按钮
        reload_charts_btn = QPushButton("重新加载图表")
        reload_charts_btn.clicked.connect(self.refresh_charts)
        control_layout.addWidget(reload_charts_btn)

        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 图表类型选择
        chart_type_layout = QHBoxLayout()
        chart_type_layout.addWidget(QLabel("图表类型:"))
        self.chart_type = QComboBox()
        self.chart_type.addItems(["饼图", "柱状图"])
        self.chart_type.currentTextChanged.connect(self.refresh_charts)
        chart_type_layout.addWidget(self.chart_type)
        chart_type_layout.addStretch()
        layout.addLayout(chart_type_layout)

        # 嵌入 Plotly HTML（需要 QWebEngineView）
        if QWebEngineView is not None:
            self.chart_view = QWebEngineView()
            layout.addWidget(self.chart_view, 1)
            # JS桥接
            self.chart_bridge = ChartBridge()
            self.chart_bridge.chartClicked.connect(self.on_chart_clicked)
            self.chart_channel = QWebChannel()
            self.chart_channel.registerObject('pybridge', self.chart_bridge)
        else:
            self.chart_view = QLabel("缺少 QWebEngineView，无法展示交互式图表。请安装 PyQt6-WebEngine。")
            self.chart_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.chart_view, 1)

        self.tab_widget.addTab(chart_widget, "图表分析")

    def create_calendar_tab(self):
        cal_widget = QWidget()
        layout = QVBoxLayout(cal_widget)

        # 控制区域
        controls = QHBoxLayout()
        controls.addWidget(QLabel("年份:"))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(QDate.currentDate().year())
        self.year_spin.valueChanged.connect(self.refresh_calendar)
        controls.addWidget(self.year_spin)
        controls.addWidget(QLabel("月份:"))
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setValue(QDate.currentDate().month())
        self.month_spin.valueChanged.connect(self.refresh_calendar)
        controls.addWidget(self.month_spin)

        # 分类标准选择
        controls.addWidget(QLabel("分类标准:"))
        self.calendar_classification = QComboBox()
        self.calendar_classification.addItems(["官方分类标准", "自定义分类标准"])
        self.calendar_classification.currentTextChanged.connect(self.refresh_calendar)
        controls.addWidget(self.calendar_classification)

        # 重新加载按钮
        reload_calendar_btn = QPushButton("重新加载日历")
        reload_calendar_btn.clicked.connect(self.refresh_calendar)
        controls.addWidget(reload_calendar_btn)

        controls.addStretch()
        layout.addLayout(controls)

        if QWebEngineView is not None:
            self.calendar_view = QWebEngineView()
            layout.addWidget(self.calendar_view, 1)
            self.calendar_bridge = ChartBridge()
            self.calendar_bridge.chartClicked.connect(self.on_calendar_clicked)
            self.calendar_channel = QWebChannel()
            self.calendar_channel.registerObject('pybridge', self.calendar_bridge)
        else:
            self.calendar_view = QLabel("缺少 QWebEngineView，无法展示交互式日历图。请安装 PyQt6-WebEngine。")
            self.calendar_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.calendar_view, 1)

        self.tab_widget.addTab(cal_widget, "日历图")

    def set_default_folder(self):
        default_folder = "zhangdang"
        if os.path.exists(default_folder):
            self.folder_path = default_folder
            self.folder_label.setText(f"账单文件夹: {default_folder}")
            self.process_btn.setEnabled(True)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择账单文件夹")
        if folder_path:
            self.folder_path = folder_path
            self.folder_label.setText(f"账单文件夹: {folder_path}")
            self.process_btn.setEnabled(True)

    def start_processing(self):
        if not hasattr(self, 'folder_path'):
            QMessageBox.warning(self, "警告", "请先选择账单文件夹")
            return
        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_label.setText("正在处理...")
        self.setEnabled(False)
        self.processing_thread = ProcessingThread(self.folder_path)
        self.processing_thread.progress_updated.connect(self.on_progress_update)
        self.processing_thread.processing_finished.connect(self.processing_finished)
        self.processing_thread.error_occurred.connect(self.processing_error)
        self.processing_thread.finished.connect(lambda: self.setEnabled(True))
        self.processing_thread.start()

    def on_progress_update(self, message, value):
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        QApplication.processEvents()  # 强制刷新UI

    def update_progress(self, message: str):
        cur = self.progress_bar.value()
        self.progress_bar.setValue(min(cur + 15, 95))
        self.progress_label.setText(message)
        QApplication.processEvents()  # 强制刷新UI，防止进度条卡住

    def processing_finished(self, df: pd.DataFrame, stats: dict, report_text: str):
        try:
            self.df = df
            self.stats = stats if stats is not None else {}
            self.report_text = report_text if report_text is not None else ""
            self.update_transaction_table()
            self.update_statistics_tab()
            self.refresh_charts()
            self.refresh_calendar()
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "错误", f"刷新界面时出错: {e}\n{traceback.format_exc()}")
        self.progress_bar.setValue(100)
        self.progress_label.setText("完成")
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.process_btn.setEnabled(True)
        self.setEnabled(True)
        QMessageBox.information(self, "完成", "账单处理完成！")

    def processing_error(self, error_message: str):
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(True)
        self.setEnabled(True)
        QMessageBox.critical(self, "错误", f"处理失败: {error_message}")

    def update_transaction_table(self):
        if self.df is None or self.df.empty:
            self.transaction_table.setRowCount(0)
            return

        # 更新筛选选项
        self.update_filter_options()

        self.transaction_table.setRowCount(len(self.df))
        # 设置表格线加粗
        self.transaction_table.setStyleSheet("""
            QTableWidget::item {
                border-bottom: 2.5px solid #3399FF;
                border-right: 2.5px solid #3399FF;
            }
        """)
        fail_status_keywords = ['对方已退还', '已全额退款', '还款失败', '失败', '退款', '退还']
        for i, (_, row) in enumerate(self.df.iterrows()):
            status_str = str(row.get('交易状态', ''))
            is_fail = any(kw in status_str for kw in fail_status_keywords)
            # 保证所有字段都存在，防止KeyError
            def safe_get(key):
                return row[key] if key in row else ""
            try:
                amount_val = float(row.get('金额', 0) or 0)
            except Exception:
                amount_val = 0.0
            items = [
                QTableWidgetItem(str(row.get('交易时间', ''))),
                QTableWidgetItem(str(row.get('平台', ''))),
                QTableWidgetItem(str(row.get('交易对方', ''))),
                QTableWidgetItem(str(row.get('商品说明', ''))),
                QTableWidgetItem(f"¥{amount_val:.2f}"),
                QTableWidgetItem(str(row.get('交易分类', ''))),  # 保持原始平台分类
                QTableWidgetItem(str(row.get('支付方式', ''))),
                QTableWidgetItem(status_str),
                QTableWidgetItem(str(row.get('交易单号', ''))),
                QTableWidgetItem("未达到分类" if is_fail else str(row.get('调整后分类', ''))),
                QTableWidgetItem("未达到分类" if is_fail else str(row.get('调整后子分类', ''))),
                QTableWidgetItem(str(row.get('备注', ''))),
                QTableWidgetItem(str(row.get('分类来源', '')))
            ]
            for col, item in enumerate(items):
                if i % 2 == 0:
                    item.setBackground(QColor(220, 240, 255))
                self.transaction_table.setItem(i, col, item)
        # 设置列宽
        self.transaction_table.setColumnWidth(0, 150)
        self.transaction_table.setColumnWidth(1, 80)
        self.transaction_table.setColumnWidth(2, 120)
        self.transaction_table.setColumnWidth(3, 200)
        self.transaction_table.setColumnWidth(4, 100)
        self.transaction_table.setColumnWidth(5, 100)
        self.transaction_table.setColumnWidth(6, 100)
        self.transaction_table.setColumnWidth(7, 100)
        self.transaction_table.setColumnWidth(8, 150)
        self.transaction_table.setColumnWidth(9, 120)
        self.transaction_table.setColumnWidth(10, 120)
        self.transaction_table.setColumnWidth(11, 150)
        self.transaction_table.setColumnWidth(12, 100)

    def update_filter_options(self):
        """更新筛选选项"""
        if self.df is None or self.df.empty:
            return

        # 更新分类筛选选项
        if '调整后分类' in self.df.columns:
            categories = ['全部分类'] + sorted(self.df['调整后分类'].dropna().unique().tolist())
            current_category = self.category_filter.currentText()
            self.category_filter.clear()
            self.category_filter.addItems(categories)
            if current_category in categories:
                self.category_filter.setCurrentText(current_category)

    def update_statistics_tab(self):
        self.report_text_edit.setPlainText(self.report_text or "")

    def reload_statistics(self):
        """重新加载统计信息"""
        if self.df is not None and not self.df.empty:
            try:
                classifier = TransactionClassifier()
                stats = classifier.get_classification_statistics(self.df)
                special = {
                    '"馒头"支出统计': classifier.get_special_statistics(self.df, '馒头'),
                    '理财退款统计': classifier.get_finance_refund_statistics(self.df)
                }
                visualizer = DataVisualizer()
                self.report_text = visualizer.create_summary_report(stats, special)
                self.update_statistics_tab()
                QMessageBox.information(self, "成功", "统计信息已重新加载！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重新加载统计失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "暂无数据可重新加载")

    def apply_filters_and_refresh(self):
        # 刷新表格
        if self.df is not None and not self.df.empty:
            platform_filter = self.platform_filter.currentText()
            category_filter = self.category_filter.currentText()
            status_filter = self.status_filter.currentText()
            filtered_df = self.df.copy()
            if platform_filter != "全部平台":
                filtered_df = filtered_df[filtered_df['平台'] == platform_filter]
            if category_filter != "全部分类":
                if '调整后分类' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['调整后分类'] == category_filter]
                else:
                    if category_filter == "收入":
                        filtered_df = filtered_df[filtered_df['交易分类'].str.startswith('收入', na=False)]
                    elif category_filter == "支出":
                        filtered_df = filtered_df[filtered_df['交易分类'].str.startswith('支出', na=False)]
                    elif category_filter == "非收支":
                        filtered_df = filtered_df[filtered_df['交易分类'] == '非收支']
            # 新增：交易状态筛选
            fail_status_keywords = ['对方已退还', '已全额退款', '还款失败', '失败', '退款', '退还']
            if status_filter == "成功":
                filtered_df = filtered_df[~filtered_df['交易状态'].astype(str).apply(lambda x: any(kw in x for kw in fail_status_keywords))]
            elif status_filter == "失败":
                filtered_df = filtered_df[filtered_df['交易状态'].astype(str).apply(lambda x: any(kw in x for kw in fail_status_keywords))]
            self.df_filtered = filtered_df
            self.update_transaction_table()
            # 刷新图像
            self.refresh_charts()
            self.refresh_calendar()

    def refresh_charts(self):
        """刷新图表"""
        if QWebEngineView is None:
            return

        data = getattr(self, 'df_filtered', self.df)
        if data is None or data.empty:
            html = "<html><body><h3 style='text-align:center; font-family: Arial, sans-serif; font-size: 18px;'>暂无数据</h3></body></html>"
            self.chart_view.setHtml(html)
            return

        mode_map = {
            '全部': 'all',
            '仅收入': 'income',
            '仅支出': 'expense'
        }
        mode = mode_map.get(self.view_mode.currentText(), 'all')

        # 根据分类标准选择数据列
        if self.classification_standard.currentText() == "自定义分类标准" and '调整后分类' in data.columns:
            category_column = '调整后分类'
        else:
            category_column = '交易分类'

        chart_type = self.chart_type.currentText()
        if chart_type == "饼图":
            fig = self.visualizer.create_pie_chart(data, mode=mode, category_column=category_column)
        else:  # 柱状图
            fig = self.visualizer.create_bar_chart(data, mode=mode, category_column=category_column)

        html = self.visualizer.figure_to_html(fig, bridge_object_name='pybridge', enable_click=True)
        self.chart_view.setHtml(html)
        # 绑定channel
        if self.chart_view.page() and QWebChannel is not None:
            self.chart_view.page().setWebChannel(self.chart_channel)

    def refresh_calendar(self):
        """刷新日历"""
        if QWebEngineView is None:
            return

        data = getattr(self, 'df_filtered', self.df)
        if data is None or data.empty:
            html = "<html><body><h3 style='text-align:center; font-family: Arial, sans-serif; font-size: 18px;'>暂无数据</h3></html>"
            self.calendar_view.setHtml(html)
            return

        year = self.year_spin.value()
        month = self.month_spin.value()

        # 根据分类标准选择数据列
        if self.calendar_classification.currentText() == "自定义分类标准" and '调整后分类' in data.columns:
            category_column = '调整后分类'
        else:
            category_column = '交易分类'

        fig = self.visualizer.create_calendar_heatmap(data, year, month, category_column=category_column)
        html = self.visualizer.figure_to_html(fig, bridge_object_name='pybridge', enable_click=True)
        self.calendar_view.setHtml(html)
        if self.calendar_view.page() and QWebChannel is not None:
            self.calendar_view.page().setWebChannel(self.calendar_channel)

    def on_chart_clicked(self, payload_json: str):
        # 点击图表分类后，弹窗该分类明细
        try:
            import json
            payload = json.loads(payload_json)
            if not payload.get('points'):
                return
            label = payload['points'][0].get('label')
            if not label:
                return
            data = getattr(self, 'df_filtered', self.df)
            if data is None:
                return

            # 根据分类标准选择数据列
            if self.classification_standard.currentText() == "自定义分类标准" and '调整后分类' in data.columns:
                category_column = '调整后分类'
            else:
                category_column = '交易分类'

            details = data[data[category_column] == label]
            self.show_details_dialog(f"分类明细 - {label}", details)
        except Exception:
            pass

    def on_calendar_clicked(self, payload_json: str):
        # 点击某日热力格后，弹窗展示该日明细
        try:
            import json
            payload = json.loads(payload_json)
            if not payload.get('points'):
                return
            custom_date = payload['points'][0].get('customdata')
            # customdata 可能为空或为''（补位格），需过滤
            if not custom_date:
                return
            # customdata 可能是二维矩阵中的单元格值
            if isinstance(custom_date, list):
                custom_date = custom_date[0]
            data = getattr(self, 'df_filtered', self.df)
            if data is None:
                return
            details = data[pd.to_datetime(data['交易时间'], errors='coerce').dt.strftime('%Y-%m-%d') == custom_date]
            self.show_details_dialog(f"日期明细 - {custom_date}", details)
        except Exception:
            pass

    def show_details_dialog(self, title: str, df: pd.DataFrame):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(1000, 700)
        v = QVBoxLayout(dlg)
        table = QTableWidget()
        cols = ["交易时间", "平台", "交易对方", "商品说明", "金额", "分类", "支付方式", "交易状态", "交易单号", "调整后分类", "调整后子分类", "备注", "分类来源"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        if df is None or df.empty:
            table.setRowCount(0)
        else:
            table.setRowCount(len(df))
            for i, (_, row) in enumerate(df.iterrows()):
                table.setItem(i, 0, QTableWidgetItem(str(row.get('交易时间', ''))))
                table.setItem(i, 1, QTableWidgetItem(str(row.get('平台', ''))))
                table.setItem(i, 2, QTableWidgetItem(str(row.get('交易对方', ''))))
                table.setItem(i, 3, QTableWidgetItem(str(row.get('商品说明', ''))))
                amount = row.get('金额', 0) or 0
                try:
                    amount = float(amount)
                except Exception:
                    amount = 0.0
                table.setItem(i, 4, QTableWidgetItem(f"¥{amount:.2f}"))
                table.setItem(i, 5, QTableWidgetItem(str(row.get('交易分类', ''))))
                table.setItem(i, 6, QTableWidgetItem(str(row.get('支付方式', ''))))
                table.setItem(i, 7, QTableWidgetItem(str(row.get('交易状态', ''))))
                table.setItem(i, 8, QTableWidgetItem(str(row.get('交易单号', ''))))
                table.setItem(i, 9, QTableWidgetItem(str(row.get('调整后分类', ''))))
                table.setItem(i, 10, QTableWidgetItem(str(row.get('调整后子分类', ''))))
                table.setItem(i, 11, QTableWidgetItem(str(row.get('备注', ''))))
                # 新增分类来源
                table.setItem(i, 12, QTableWidgetItem(str(row.get('分类来源', ''))))
        table.resizeColumnsToContents()
        v.addWidget(table)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)
        dlg.exec()

    def export_csv(self):
        if self.df is None or self.df.empty:
            QMessageBox.information(self, "提示", "暂无数据可导出，请先处理账单。")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "分类结果.csv", "CSV Files (*.csv)")
        if not file_path:
            return
        try:
            self.df.to_csv(file_path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "成功", f"已导出到: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

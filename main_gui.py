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
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

from bill_parser import BillParser
from transaction_classifier import TransactionClassifier
from data_visualizer import DataVisualizer

# 导入数据恢复工具
try:
    from data_recovery import DataRecovery
except ImportError:
    # 如果导入失败，创建一个简单的替代类
    class DataRecovery:
        @staticmethod
        def safe_copy_dataframe(df):
            try:
                return df.copy(deep=False)
            except Exception:
                return df
        @staticmethod
        def validate_dataframe(df):
            return {'is_valid': True, 'issues': []}
        @staticmethod
        def fix_common_issues(df):
            return df


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
        self.df_filtered = None  # 初始化筛选数据
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
        control_layout.addWidget(QLabel("视图:"))
        self.view_mode = QComboBox()
        self.view_mode.addItems(["全部", "仅收入", "仅支出"])
        self.view_mode.currentTextChanged.connect(self.refresh_charts)
        control_layout.addWidget(self.view_mode)
        control_layout.addWidget(QLabel("分类标准:"))
        self.classification_standard = QComboBox()
        self.classification_standard.addItems(["官方分类标准", "自定义分类标准"])
        self.classification_standard.currentTextChanged.connect(self.refresh_charts)
        control_layout.addWidget(self.classification_standard)
        reload_charts_btn = QPushButton("重新加载图表")
        reload_charts_btn.clicked.connect(self.refresh_charts)
        control_layout.addWidget(reload_charts_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 创建图表显示区域
        self.chart_tab_widget = QTabWidget()
        layout.addWidget(self.chart_tab_widget)

        # 饼图标签页
        self.pie_chart_widget = QWidget()
        self.pie_chart_layout = QVBoxLayout(self.pie_chart_widget)
        self.pie_canvas = self.create_pie_chart()
        self.pie_chart_layout.addWidget(self.pie_canvas)
        self.chart_tab_widget.addTab(self.pie_chart_widget, "分类饼图")

        # 柱状图标签页
        self.bar_chart_widget = QWidget()
        self.bar_chart_layout = QVBoxLayout(self.bar_chart_widget)
        self.bar_canvas = self.create_bar_chart()
        self.bar_chart_layout.addWidget(self.bar_canvas)
        self.chart_tab_widget.addTab(self.bar_chart_widget, "分类柱状图")

        # 时间趋势图标签页
        self.trend_chart_widget = QWidget()
        self.trend_chart_layout = QVBoxLayout(self.trend_chart_widget)
        self.trend_canvas = self.create_trend_chart()
        self.trend_chart_layout.addWidget(self.trend_canvas)
        self.chart_tab_widget.addTab(self.trend_chart_widget, "时间趋势图")

        # 平台对比图标签页
        self.platform_chart_widget = QWidget()
        self.platform_chart_layout = QVBoxLayout(self.platform_chart_widget)
        self.platform_canvas = self.create_platform_chart()
        self.platform_chart_layout.addWidget(self.platform_canvas)
        self.chart_tab_widget.addTab(self.platform_chart_widget, "平台对比图")

        # 文字分析结果标签页
        self.text_analysis_widget = QWidget()
        self.text_analysis_layout = QVBoxLayout(self.text_analysis_widget)
        self.chart_text_edit = QTextEdit()
        self.chart_text_edit.setReadOnly(True)
        self.chart_text_edit.setPlaceholderText("图表分析结果将在这里显示...")
        self.text_analysis_layout.addWidget(self.chart_text_edit)
        self.chart_tab_widget.addTab(self.text_analysis_widget, "文字分析")

        self.tab_widget.addTab(chart_widget, "图表分析")

    def create_calendar_tab(self):
        cal_widget = QWidget()
        layout = QVBoxLayout(cal_widget)

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
        controls.addWidget(QLabel("分类标准:"))
        self.calendar_classification = QComboBox()
        self.calendar_classification.addItems(["官方分类标准", "自定义分类标准"])
        self.calendar_classification.currentTextChanged.connect(self.refresh_calendar)
        controls.addWidget(self.calendar_classification)
        reload_calendar_btn = QPushButton("重新加载日历")
        reload_calendar_btn.clicked.connect(self.refresh_calendar)
        controls.addWidget(reload_calendar_btn)
        controls.addStretch()
        layout.addLayout(controls)

        # 创建日历图表显示区域
        self.calendar_tab_widget = QTabWidget()
        layout.addWidget(self.calendar_tab_widget)

        # 日历热力图标签页
        self.calendar_heatmap_widget = QWidget()
        self.calendar_heatmap_layout = QVBoxLayout(self.calendar_heatmap_widget)
        self.calendar_heatmap_canvas = self.create_calendar_heatmap()
        self.calendar_heatmap_layout.addWidget(self.calendar_heatmap_canvas)
        self.calendar_tab_widget.addTab(self.calendar_heatmap_widget, "日历热力图")

        # 月度趋势图标签页
        self.monthly_trend_widget = QWidget()
        self.monthly_trend_layout = QVBoxLayout(self.monthly_trend_widget)
        self.monthly_trend_canvas = self.create_monthly_trend()
        self.monthly_trend_layout.addWidget(self.monthly_trend_canvas)
        self.calendar_tab_widget.addTab(self.monthly_trend_widget, "月度趋势图")

        # 文字分析结果标签页
        self.calendar_text_widget = QWidget()
        self.calendar_text_layout = QVBoxLayout(self.calendar_text_widget)
        self.calendar_text_edit = QTextEdit()
        self.calendar_text_edit.setReadOnly(True)
        self.calendar_text_edit.setPlaceholderText("日历分析结果将在这里显示...")
        self.calendar_text_layout.addWidget(self.calendar_text_edit)
        self.calendar_tab_widget.addTab(self.calendar_text_widget, "文字分析")

        self.tab_widget.addTab(cal_widget, "日历表")

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
            import json
            # 递归修正stats所有dict和金额字段类型
            def safe_json_load(val):
                if isinstance(val, str):
                    try:
                        return json.loads(val.replace("'", '"'))
                    except Exception:
                        return val
                return val

            def safe_float(val):
                try:
                    return float(val)
                except Exception:
                    return 0.0

            def fix_stats(stats):
                if not isinstance(stats, dict):
                    return stats
                for k in list(stats.keys()):
                    v = stats[k]
                    if isinstance(v, str):
                        v2 = safe_json_load(v)
                        stats[k] = v2
                        v = v2
                    if isinstance(v, dict):
                        stats[k] = fix_stats(v)
                # 金额相关字段转float
                for key in ['总收入', '总支出', '净收入', '非收支总额']:
                    if key in stats:
                        stats[key] = safe_float(stats[key])
                return stats

            if stats is not None:
                stats = fix_stats(stats)

            # 清理和验证数据
            self.df = self.clean_dataframe(df)
            self.stats = stats if stats is not None else {}
            self.report_text = report_text if report_text is not None else ""
            
            # 初始化筛选数据
            self.df_filtered = self.df
            
            self.update_transaction_table()
            self.update_statistics_tab()
            self.refresh_charts()
            self.refresh_calendar()
        except Exception as e:
            import traceback
            print(f"✗ processing_finished 出错: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新界面时出错: {e}\n{traceback.format_exc()}")
        self.progress_bar.setValue(100)
        self.progress_label.setText("完成")
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.process_btn.setEnabled(True)
        self.setEnabled(True)
        QMessageBox.information(self, "完成", "账单处理完成！")

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理和验证DataFrame，防止数据损坏"""
        try:
            if df is None or df.empty:
                return df
            
            # 使用数据恢复工具进行安全复制
            cleaned_df = DataRecovery.safe_copy_dataframe(df)
            
            # 验证数据完整性
            validation = DataRecovery.validate_dataframe(cleaned_df)
            if not validation['is_valid']:
                print(f"数据验证发现问题: {validation['issues']}")
                # 尝试修复数据
                cleaned_df = DataRecovery.fix_common_issues(cleaned_df)
            
            # 使用数据恢复工具修复常见问题
            cleaned_df = DataRecovery.fix_common_issues(cleaned_df)
            
            # 额外清理：处理可能损坏的字符串字段
            cleaned_df = self.deep_clean_strings(cleaned_df)
            
            # 验证修复后的数据
            if cleaned_df.isnull().all().all():
                print("警告：清理后的数据全为空，返回原始数据")
                return df
            
            return cleaned_df
            
        except Exception as e:
            print(f"数据清理失败: {e}")
            # 如果清理失败，返回原始数据
            return df
    
    def deep_clean_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        """深度清理字符串字段，移除损坏的数据"""
        try:
            for col in df.columns:
                if df[col].dtype == 'object':
                    # 安全地清理字符串列
                    try:
                        df[col] = df[col].fillna('').astype(str).apply(self.safe_string_clean)
                    except Exception as e:
                        print(f"列 {col} 字符串清理失败: {e}")
                        # 如果清理失败，将该列设为空字符串
                        df[col] = ''
            return df
        except Exception as e:
            print(f"深度字符串清理失败: {e}")
            return df
    
    def is_field_safe(self, df: pd.DataFrame, field_name: str) -> bool:
        """检查字段是否安全可用"""
        try:
            if field_name not in df.columns:
                return False
            
            # 尝试访问字段数据
            sample_data = df[field_name].head(10)
            # 尝试转换为字符串
            str_data = sample_data.astype(str)
            # 尝试应用字符串清理
            cleaned_data = str_data.apply(self.safe_string_clean)
            
            return True
        except Exception as e:
            print(f"字段 {field_name} 不安全: {e}")
            return False
    
    def safe_string_clean(self, text: str) -> str:
        """安全地清理字符串，避免递归问题"""
        try:
            if not isinstance(text, str):
                return str(text)
            
            # 移除可能导致问题的字符
            cleaned = text.replace('\x00', '')  # 移除空字符
            cleaned = cleaned.replace('\r', '')  # 移除回车符
            cleaned = cleaned.replace('\n', ' ')  # 将换行符替换为空格
            
            # 移除其他可能导致问题的字符
            cleaned = cleaned.replace('\t', ' ')  # 移除制表符
            cleaned = cleaned.replace('\b', '')   # 移除退格符
            cleaned = cleaned.replace('\f', ' ')  # 移除换页符
            
            # 处理可能的循环引用字符串
            if '...' in cleaned and len(cleaned) > 100:
                # 如果字符串过长且包含省略号，可能是循环引用
                cleaned = cleaned[:100] + "..."
            
            # 限制字符串长度，避免过长字符串导致问题
            if len(cleaned) > 500:  # 减少最大长度
                cleaned = cleaned[:500] + "..."
            
            # 确保字符串是有效的
            if not cleaned or cleaned.isspace():
                return "空数据"
            
            return cleaned
        except Exception:
            return "数据错误"
    
    def create_pie_chart(self):
        """创建饼图画布"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        return canvas
    
    def create_bar_chart(self):
        """创建柱状图画布"""
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        return canvas
    
    def create_trend_chart(self):
        """创建时间趋势图画布"""
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        return canvas
    
    def create_platform_chart(self):
        """创建平台对比图画布"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        return canvas
    
    def update_pie_chart(self, data):
        """更新饼图"""
        try:
            if data is None or data.empty:
                return
            
            # 获取分类数据
            category_column = '调整后分类' if '调整后分类' in data.columns else '交易分类'
            
            # 根据视图模式筛选数据
            view_mode = self.view_mode.currentText()
            if view_mode == "仅收入":
                filtered_data = data[data[category_column].astype(str).str.startswith('收入', na=False)]
            elif view_mode == "仅支出":
                filtered_data = data[data[category_column].astype(str).str.startswith('支出', na=False)]
            else:
                filtered_data = data[data[category_column] != '非收支']
            
            if filtered_data.empty:
                return
            
            # 计算分类统计
            category_stats = filtered_data.groupby(category_column)['金额'].sum().sort_values(ascending=False)
            
            # 只显示前10个分类，其他归为"其他"
            if len(category_stats) > 10:
                top_categories = category_stats.head(9)
                other_amount = category_stats.iloc[9:].sum()
                category_stats = pd.concat([top_categories, pd.Series({'其他': other_amount})])
            
            # 清除旧图
            self.pie_canvas.figure.clear()
            ax = self.pie_canvas.figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 绘制饼图，调整标签位置避免重叠
            colors = plt.cm.Set3(np.linspace(0, 1, len(category_stats)))
            
            # 计算标签位置，避免重叠
            wedges, texts, autotexts = ax.pie(category_stats.values, 
                                             labels=category_stats.index, 
                                             autopct='%1.1f%%',
                                             colors=colors,
                                             startangle=90,
                                             pctdistance=0.85,  # 百分比标签距离
                                             labeldistance=1.1)  # 标签距离
            
            # 设置标题和字体
            title = f"{view_mode}分类分布" if view_mode != "全部" else "收支分类分布"
            ax.set_title(title, fontsize=14, fontweight='bold', fontfamily='SimHei')
            
            # 调整标签字体大小和位置
            for text in texts:
                text.set_fontsize(10)
                text.set_fontfamily('SimHei')
                # 如果标签太长，进行换行处理
                if len(text.get_text()) > 8:
                    text.set_text(text.get_text()[:8] + '\n' + text.get_text()[8:])
            
            # 调整百分比标签字体
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_fontweight('bold')
                autotext.set_color('white')
            
            # 刷新画布
            self.pie_canvas.draw()
            
        except Exception as e:
            print(f"更新饼图失败: {e}")
    
    def update_bar_chart(self, data):
        """更新柱状图"""
        try:
            if data is None or data.empty:
                return
            
            # 获取分类数据
            category_column = '调整后分类' if '调整后分类' in data.columns else '交易分类'
            
            # 根据视图模式筛选数据
            view_mode = self.view_mode.currentText()
            if view_mode == "仅收入":
                filtered_data = data[data[category_column].astype(str).str.startswith('收入', na=False)]
            elif view_mode == "仅支出":
                filtered_data = data[data[category_column].astype(str).str.startswith('支出', na=False)]
            else:
                filtered_data = data[data[category_column] != '非收支']
            
            if filtered_data.empty:
                return
            
            # 计算分类统计
            category_stats = filtered_data.groupby(category_column)['金额'].agg(['sum', 'count']).sort_values('sum', ascending=False)
            
            # 只显示前15个分类
            category_stats = category_stats.head(15)
            
            # 清除旧图
            self.bar_canvas.figure.clear()
            ax = self.bar_canvas.figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 创建双轴图
            x = range(len(category_stats))
            width = 0.35
            
            # 绘制金额柱状图
            ax.bar([i - width/2 for i in x], category_stats['sum'], width, 
                   label='金额', color='skyblue', alpha=0.8)
            
            # 创建第二个y轴用于显示笔数
            ax2 = ax.twinx()
            ax2.bar([i + width/2 for i in x], category_stats['count'], width, 
                    label='笔数', color='lightcoral', alpha=0.8)
            
            # 设置x轴标签
            ax.set_xticks(x)
            ax.set_xticklabels(category_stats.index, rotation=45, ha='right', fontsize=9, fontfamily='SimHei')
            
            # 设置标签和标题
            ax.set_ylabel('金额 (元)', fontsize=12, fontfamily='SimHei')
            ax2.set_ylabel('笔数', fontsize=12, fontfamily='SimHei')
            title = f"{view_mode}分类统计" if view_mode != "全部" else "收支分类统计"
            ax.set_title(title, fontsize=14, fontweight='bold', fontfamily='SimHei')
            
            # 添加图例
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', prop={'family': 'SimHei'})
            
            # 调整布局
            self.bar_canvas.figure.tight_layout()
            
            # 刷新画布
            self.bar_canvas.draw()
            
        except Exception as e:
            print(f"更新柱状图失败: {e}")
    
    def update_trend_chart(self, data):
        """更新时间趋势图"""
        try:
            if data is None or data.empty:
                return
            
            # 清除旧图
            self.trend_canvas.figure.clear()
            ax = self.trend_canvas.figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 处理时间数据
            data_copy = data.copy()
            data_copy['交易时间'] = pd.to_datetime(data_copy['交易时间'], errors='coerce')
            data_copy = data_copy.dropna(subset=['交易时间'])
            
            if data_copy.empty:
                return
            
            # 按日期分组统计
            daily_stats = data_copy.groupby(data_copy['交易时间'].dt.date)['金额'].agg(['sum', 'count'])
            daily_stats = daily_stats.sort_index()
            
            # 转换为datetime用于绘图
            dates = [datetime.combine(date, datetime.min.time()) for date in daily_stats.index]
            
            # 绘制双轴图
            ax.plot(dates, daily_stats['sum'], 'b-', linewidth=2, label='日交易金额', marker='o')
            ax.set_ylabel('金额 (元)', color='b', fontsize=12, fontfamily='SimHei')
            ax.tick_params(axis='y', labelcolor='b')
            
            # 创建第二个y轴用于显示笔数
            ax2 = ax.twinx()
            ax2.bar(dates, daily_stats['count'], alpha=0.3, color='orange', label='日交易笔数')
            ax2.set_ylabel('笔数', color='orange', fontsize=12, fontfamily='SimHei')
            ax2.tick_params(axis='y', labelcolor='orange')
            
            # 设置x轴格式
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
            
            # 设置标题和标签
            ax.set_title('交易时间趋势分析', fontsize=14, fontweight='bold', fontfamily='SimHei')
            ax.set_xlabel('日期', fontsize=12, fontfamily='SimHei')
            
            # 添加图例
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', prop={'family': 'SimHei'})
            
            # 调整布局
            self.trend_canvas.figure.tight_layout()
            
            # 刷新画布
            self.trend_canvas.draw()
            
        except Exception as e:
            print(f"更新时间趋势图失败: {e}")
    
    def update_platform_chart(self, data):
        """更新平台对比图"""
        try:
            if data is None or data.empty:
                return
            
            # 清除旧图
            self.platform_canvas.figure.clear()
            ax = self.platform_canvas.figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 计算平台统计
            platform_stats = data.groupby('平台')['金额'].agg(['sum', 'count']).sort_values('sum', ascending=False)
            
            if platform_stats.empty:
                return
            
            # 创建双轴图
            x = range(len(platform_stats))
            width = 0.35
            
            # 绘制金额柱状图
            ax.bar([i - width/2 for i in x], platform_stats['sum'], width, 
                   label='金额', color='lightgreen', alpha=0.8)
            
            # 创建第二个y轴用于显示笔数
            ax2 = ax.twinx()
            ax2.bar([i + width/2 for i in x], platform_stats['count'], width, 
                    label='笔数', color='lightblue', alpha=0.8)
            
            # 设置x轴标签
            ax.set_xticks(x)
            ax.set_xticklabels(platform_stats.index, fontsize=10, fontfamily='SimHei')
            
            # 设置标签和标题
            ax.set_ylabel('金额 (元)', fontsize=12, fontfamily='SimHei')
            ax2.set_ylabel('笔数', fontsize=12, fontfamily='SimHei')
            ax.set_title('平台对比分析', fontsize=14, fontweight='bold', fontfamily='SimHei')
            
            # 添加图例
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right', prop={'family': 'SimHei'})
            
            # 调整布局
            self.platform_canvas.figure.tight_layout()
            
            # 刷新画布
            self.platform_canvas.draw()
            
        except Exception as e:
            print(f"更新平台对比图失败: {e}")
    
    def create_calendar_heatmap(self):
        """创建日历热力图画布"""
        fig = Figure(figsize=(10, 8))
        canvas = FigureCanvas(fig)
        return canvas
    
    def create_monthly_trend(self):
        """创建月度趋势图画布"""
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        return canvas
    
    def update_calendar_heatmap(self, data, year, month):
        """更新日历热力图"""
        try:
            if data is None or data.empty:
                return
            
            # 清除旧图
            self.calendar_heatmap_canvas.figure.clear()
            ax = self.calendar_heatmap_canvas.figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 处理时间数据
            data_copy = data.copy()
            data_copy['交易时间'] = pd.to_datetime(data_copy['交易时间'], errors='coerce')
            data_copy = data_copy.dropna(subset=['交易时间'])
            
            # 过滤当月数据
            monthly_data = data_copy[(data_copy['交易时间'].dt.year == year) & 
                                   (data_copy['交易时间'].dt.month == month)]
            
            if monthly_data.empty:
                ax.text(0.5, 0.5, f"{year}年{month}月暂无交易数据", 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14, fontfamily='SimHei')
                self.calendar_heatmap_canvas.draw()
                return
            
            # 按日期分组统计
            daily_stats = monthly_data.groupby(monthly_data['交易时间'].dt.date)['金额'].sum()
            
            # 创建日历网格
            first_day = datetime(year, month, 1)
            last_day = (first_day.replace(month=first_day.month + 1) - timedelta(days=1))
            start_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
            
            # 创建日历矩阵
            calendar_matrix = np.zeros((6, 7))
            calendar_matrix.fill(np.nan)
            
            # 填充数据
            current_day = first_day
            week_idx = 0
            day_idx = start_weekday
            
            while current_day <= last_day:
                if current_day.date() in daily_stats.index:
                    calendar_matrix[week_idx, day_idx] = daily_stats[current_day.date()]
                
                day_idx += 1
                if day_idx >= 7:
                    day_idx = 0
                    week_idx += 1
                
                current_day += timedelta(days=1)
            
            # 绘制热力图
            im = ax.imshow(calendar_matrix, cmap='YlOrRd', aspect='auto')
            
            # 设置坐标轴
            ax.set_xticks(range(7))
            ax.set_xticklabels(['周一', '周二', '周三', '周四', '周五', '周六', '周日'], 
                              fontsize=10, fontfamily='SimHei')
            ax.set_yticks(range(6))
            ax.set_yticklabels(['第1周', '第2周', '第3周', '第4周', '第5周', '第6周'], 
                              fontsize=10, fontfamily='SimHei')
            
            # 添加日期标签
            current_day = first_day
            week_idx = 0
            day_idx = start_weekday
            
            while current_day <= last_day:
                if not np.isnan(calendar_matrix[week_idx, day_idx]):
                    ax.text(day_idx, week_idx, f"{current_day.day}\n¥{calendar_matrix[week_idx, day_idx]:.0f}", 
                           ha='center', va='center', fontsize=8, fontweight='bold', fontfamily='SimHei')
                else:
                    ax.text(day_idx, week_idx, str(current_day.day), 
                           ha='center', va='center', fontsize=8, color='gray', fontfamily='SimHei')
                
                day_idx += 1
                if day_idx >= 7:
                    day_idx = 0
                    week_idx += 1
                
                current_day += timedelta(days=1)
            
            # 设置标题和颜色条
            ax.set_title(f'{year}年{month}月 交易金额热力图', fontsize=14, fontweight='bold', fontfamily='SimHei')
            cbar = self.calendar_heatmap_canvas.figure.colorbar(im, ax=ax)
            cbar.set_label('交易金额 (元)', fontsize=12, fontfamily='SimHei')
            
            # 调整布局
            self.calendar_heatmap_canvas.figure.tight_layout()
            
            # 刷新画布
            self.calendar_heatmap_canvas.draw()
            
        except Exception as e:
            print(f"更新日历热力图失败: {e}")
    
    def update_monthly_trend(self, data, year, month):
        """更新月度趋势图"""
        try:
            if data is None or data.empty:
                return
            
            # 清除旧图
            self.monthly_trend_canvas.figure.clear()
            ax = self.monthly_trend_canvas.figure.add_subplot(111)
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 处理时间数据
            data_copy = data.copy()
            data_copy['交易时间'] = pd.to_datetime(data_copy['交易时间'], errors='coerce')
            data_copy = data_copy.dropna(subset=['交易时间'])
            
            # 过滤当月数据
            monthly_data = data_copy[(data_copy['交易时间'].dt.year == year) & 
                                   (data_copy['交易时间'].dt.month == month)]
            
            if monthly_data.empty:
                ax.text(0.5, 0.5, f"{year}年{month}月暂无交易数据", 
                       ha='center', va='center', transform=ax.transAxes, fontsize=14, fontfamily='SimHei')
                self.monthly_trend_canvas.draw()
                return
            
            # 根据分类标准选择数据列
            if self.calendar_classification.currentText() == "自定义分类标准" and '调整后分类' in monthly_data.columns:
                category_column = '调整后分类'
            else:
                category_column = '交易分类'
            
            # 按日期分组统计
            daily_stats = []
            for date, group in monthly_data.groupby(monthly_data['交易时间'].dt.date):
                income = group[group[category_column].astype(str).str.startswith('收入', na=False)]['金额'].sum()
                expense = group[group[category_column].astype(str).str.startswith('支出', na=False)]['金额'].sum()
                net = income - expense
                daily_stats.append((date, income, expense, net))
            
            daily_stats.sort(key=lambda x: x[0])
            
            if not daily_stats:
                return
            
            # 提取数据
            dates = [day[0] for day in daily_stats]
            incomes = [day[1] for day in daily_stats]
            expenses = [day[2] for day in daily_stats]
            nets = [day[3] for day in daily_stats]
            
            # 转换为datetime用于绘图
            plot_dates = [datetime.combine(date, datetime.min.time()) for date in dates]
            
            # 绘制堆叠柱状图
            x = range(len(plot_dates))
            width = 0.8
            
            # 收入柱状图（正值）
            ax.bar(x, incomes, width, label='收入', color='lightgreen', alpha=0.8)
            
            # 支出柱状图（负值）
            ax.bar(x, [-exp for exp in expenses], width, label='支出', color='lightcoral', alpha=0.8)
            
            # 净额线图
            ax.plot(x, nets, 'b-', linewidth=2, label='净额', marker='o', markersize=6)
            
            # 设置x轴
            ax.set_xticks(x)
            ax.set_xticklabels([f"{date.day}日" for date in dates], rotation=45, ha='right', fontsize=10, fontfamily='SimHei')
            
            # 设置y轴
            ax.set_ylabel('金额 (元)', fontsize=12, fontfamily='SimHei')
            ax.set_title(f'{year}年{month}月 收支趋势分析', fontsize=14, fontweight='bold', fontfamily='SimHei')
            
            # 添加图例
            ax.legend(loc='upper right', prop={'family': 'SimHei'})
            
            # 添加网格
            ax.grid(True, alpha=0.3)
            
            # 调整布局
            self.monthly_trend_canvas.figure.tight_layout()
            
            # 刷新画布
            self.monthly_trend_canvas.draw()
            
        except Exception as e:
            print(f"更新月度趋势图失败: {e}")
 
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
                import json
                def safe_json_load(val):
                    if isinstance(val, str):
                        try:
                            return json.loads(val.replace("'", '"'))
                        except Exception:
                            return val
                    return val
                def safe_float(val):
                    try:
                        return float(val)
                    except Exception:
                        return 0.0
                def fix_stats(stats):
                    if not isinstance(stats, dict):
                        return stats
                    for k in list(stats.keys()):
                        v = stats[k]
                        if isinstance(v, str):
                            v2 = safe_json_load(v)
                            stats[k] = v2
                            v = v2
                        if isinstance(v, dict):
                            stats[k] = fix_stats(v)
                    for key in ['总收入', '总支出', '净收入', '非收支总额']:
                        if key in stats:
                            stats[key] = safe_float(stats[key])
                    return stats
                stats = fix_stats(stats)

                special = {
                    '"馒头"支出统计': classifier.get_special_statistics(self.df, '馒头'),
                    '理财退款统计': classifier.get_finance_refund_statistics(self.df)
                }
                visualizer = DataVisualizer()
                self.report_text = visualizer.create_summary_report(stats, special)
                self.update_statistics_tab()
                QMessageBox.information(self, "成功", "统计信息已重新加载！")
            except Exception as e:
                import traceback
                print(f"✗ reload_statistics 出错: {e}")
                print(traceback.format_exc())
                QMessageBox.critical(self, "错误", f"重新加载统计失败: {str(e)}\n{traceback.format_exc()}")
        else:
            QMessageBox.warning(self, "警告", "暂无数据可重新加载")

    def apply_filters_and_refresh(self):
        """应用筛选条件并刷新显示"""
        # 刷新表格
        if self.df is None or self.df.empty:
            return

        try:
            platform_filter = self.platform_filter.currentText()
            category_filter = self.category_filter.currentText()
            status_filter = self.status_filter.currentText()
            
            # 如果筛选条件都是默认值，直接显示所有数据
            if (platform_filter == "全部平台" and 
                category_filter == "全部分类" and 
                status_filter == "全部"):
                self.df_filtered = self.df
                self.update_transaction_table()
                self.refresh_charts()
                self.refresh_calendar()
                return
            
            # 使用numpy数组和手动循环来避免pandas递归错误
            print("使用安全筛选方法...")
            
            # 安全地获取列名
            try:
                columns = self.get_safe_columns()
                if not columns:
                    print("无法获取安全的列名，显示所有数据")
                    self.df_filtered = self.df
                    self.update_transaction_table()
                    self.refresh_charts()
                    self.refresh_calendar()
                    return
            except Exception as e:
                print(f"获取列名失败: {e}")
                self.df_filtered = self.df
                self.update_transaction_table()
                self.refresh_charts()
                self.refresh_calendar()
                return
            
            # 获取列索引
            try:
                platform_col_idx = columns.index('平台') if '平台' in columns else -1
                category_col_idx = columns.index('调整后分类') if '调整后分类' in columns else -1
                if category_col_idx == -1:
                    category_col_idx = columns.index('交易分类') if '交易分类' in columns else -1
                status_col_idx = columns.index('交易状态') if '交易状态' in columns else -1
            except Exception as e:
                print(f"获取列索引失败: {e}")
                # 如果获取列索引失败，显示所有数据
                self.df_filtered = self.df
                self.update_transaction_table()
                self.refresh_charts()
                self.refresh_calendar()
                return
            
            # 手动筛选数据
            filtered_indices = []
            try:
                df_values = self.df.values
            except Exception as e:
                print(f"获取DataFrame值失败: {e}")
                self.df_filtered = self.df
                self.update_transaction_table()
                self.refresh_charts()
                self.refresh_calendar()
                return
            
            for i in range(len(df_values)):
                include_row = True
                
                # 检查平台筛选
                if platform_filter != "全部平台" and platform_col_idx >= 0:
                    try:
                        row_platform = str(df_values[i, platform_col_idx])
                        if row_platform != platform_filter:
                            include_row = False
                    except:
                        pass
                
                # 检查分类筛选
                if category_filter != "全部分类" and category_col_idx >= 0:
                    try:
                        row_category = str(df_values[i, category_col_idx])
                        if row_category != category_filter:
                            include_row = False
                    except:
                        pass
                
                # 检查状态筛选
                if status_filter != "全部" and status_col_idx >= 0:
                    try:
                        row_status = str(df_values[i, status_col_idx])
                        if row_status != status_filter:
                            include_row = False
                    except:
                        pass
                
                if include_row:
                    filtered_indices.append(i)
            
            # 使用筛选后的索引创建新的DataFrame
            if filtered_indices:
                try:
                    # 使用iloc安全地获取筛选后的数据
                    self.df_filtered = self.df.iloc[filtered_indices].copy()
                except Exception as e:
                    print(f"创建筛选DataFrame失败: {e}")
                    # 如果失败，手动重建
                    self.df_filtered = self.manual_rebuild_filtered_df(df_values, filtered_indices, columns)
            else:
                # 如果没有匹配的数据，创建空的DataFrame
                try:
                    self.df_filtered = self.create_empty_dataframe(columns)
                except Exception as e:
                    print(f"创建空DataFrame失败: {e}")
                    # 如果创建失败，使用原始数据
                    self.df_filtered = self.df
            
            # 刷新显示
            self.update_transaction_table()
            self.refresh_charts()
            self.refresh_calendar()
            
        except Exception as e:
            print(f"✗ apply_filters_and_refresh 出错: {e}")
            # 如果筛选失败，显示原始数据
            self.df_filtered = self.df
            QMessageBox.warning(self, "筛选警告", f"筛选过程中出现错误，将显示所有数据。\n错误信息: {str(e)}")
    
    def get_safe_columns(self):
        """安全地获取列名，避免递归错误"""
        try:
            # 尝试直接获取列名
            columns = list(self.df.columns)
            # 验证列名是否安全
            safe_columns = []
            for col in columns:
                try:
                    # 检查列名是否为字符串且可哈希
                    if isinstance(col, str) and len(col) < 1000:
                        safe_columns.append(col)
                    else:
                        safe_columns.append(f"列_{len(safe_columns)}")
                except:
                    safe_columns.append(f"列_{len(safe_columns)}")
            return safe_columns
        except Exception as e:
            print(f"获取列名失败: {e}")
            # 返回默认列名
            return ['交易时间', '金额', '交易分类', '平台', '交易状态']
    
    def create_empty_dataframe(self, columns):
        """安全地创建空的DataFrame"""
        try:
            # 使用字典方式创建，避免列名问题
            empty_data = {col: [] for col in columns}
            return pd.DataFrame(empty_data)
        except Exception as e:
            print(f"创建空DataFrame失败: {e}")
            # 如果失败，尝试使用默认列名
            try:
                default_columns = ['交易时间', '金额', '交易分类', '平台', '交易状态']
                empty_data = {col: [] for col in default_columns}
                return pd.DataFrame(empty_data)
            except:
                # 最后尝试创建最简单的DataFrame
                return pd.DataFrame()
    
    def manual_rebuild_filtered_df(self, df_values, filtered_indices, columns):
        """手动重建筛选后的DataFrame"""
        try:
            # 创建新的数据字典
            new_data = {col: [] for col in columns}
            
            # 手动填充数据
            for idx in filtered_indices:
                for col_idx, col_name in enumerate(columns):
                    try:
                        if col_idx < len(df_values[idx]):
                            value = df_values[idx, col_idx]
                            # 安全地处理值
                            if pd.isna(value):
                                new_data[col_name].append("")
                            else:
                                new_data[col_name].append(str(value))
                        else:
                            new_data[col_name].append("")
                    except Exception:
                        new_data[col_name].append("")
            
            # 创建新的DataFrame
            return pd.DataFrame(new_data)
            
        except Exception as e:
            print(f"手动重建DataFrame失败: {e}")
            # 返回空的DataFrame
            return self.create_empty_dataframe(columns)

    def refresh_charts(self):
        """刷新所有图表和文字分析"""
        try:
            if not hasattr(self, 'df_filtered') or self.df_filtered is None:
                data = self.df
            else:
                data = self.df_filtered
                
            if data is None or data.empty:
                self.chart_text_edit.setPlainText("暂无数据可分析")
                return

            # 使用更安全的数据处理方式
            safe_data = self.create_safe_data_copy(data)

            # 逐个更新图表，每个都有独立的错误处理
            chart_update_success = True
            
            # 更新饼图
            try:
                self.update_pie_chart(safe_data)
                print("✓ 饼图更新成功")
            except Exception as e:
                print(f"✗ 饼图更新失败: {e}")
                chart_update_success = False

            # 更新柱状图
            try:
                self.update_bar_chart(safe_data)
                print("✓ 柱状图更新成功")
            except Exception as e:
                print(f"✗ 柱状图更新失败: {e}")
                chart_update_success = False

            # 更新趋势图
            try:
                self.update_trend_chart(safe_data)
                print("✓ 趋势图更新成功")
            except Exception as e:
                print(f"✗ 趋势图更新失败: {e}")
                chart_update_success = False

            # 更新平台对比图
            try:
                self.update_platform_chart(safe_data)
                print("✓ 平台对比图更新成功")
            except Exception as e:
                print(f"✗ 平台对比图更新失败: {e}")
                chart_update_success = False

            # 生成文字分析报告
            try:
                self.generate_text_analysis(safe_data)
                print("✓ 文字分析生成成功")
            except Exception as e:
                print(f"✗ 文字分析生成失败: {e}")
                self.chart_text_edit.setPlainText(f"文字分析生成失败: {str(e)}")
            
            if not chart_update_success:
                self.chart_text_edit.append("\n\n注意：部分图表更新失败，但程序仍在运行。")
            
        except Exception as e:
            import traceback
            error_msg = f"图表分析失败: {str(e)}\n{traceback.format_exc()}"
            self.chart_text_edit.setPlainText(error_msg)
            print(f"✗ refresh_charts 出错: {e}")
            print(traceback.format_exc())
    
    def create_safe_data_copy(self, data):
        """创建安全的数据副本，避免递归错误"""
        try:
            # 首先检查数据是否安全
            if data is None or data.empty:
                return data
            
            # 检查数据大小，如果过大可能有递归风险
            if len(data) > 10000:
                print("数据过大，使用安全复制方法")
                return self.manual_rebuild_dataframe(data)
            
            # 首先尝试使用数据恢复工具
            return DataRecovery.safe_copy_dataframe(data)
        except Exception as e:
            print(f"数据恢复工具失败: {e}")
            try:
                # 如果失败，尝试简单的复制
                return data.copy(deep=False)
            except Exception as e2:
                print(f"简单复制也失败: {e2}")
                # 最后尝试手动重建
                return self.manual_rebuild_dataframe(data)
    
    def manual_rebuild_dataframe(self, data):
        """手动重建DataFrame，完全避免pandas操作"""
        try:
            if data is None or data.empty:
                return pd.DataFrame()
            
            # 安全地获取列名
            try:
                columns = self.get_safe_columns_from_data(data)
            except:
                columns = ['交易时间', '金额', '交易分类', '平台', '交易状态']
            
            # 创建新的数据字典
            new_data = {col: [] for col in columns}
            
            # 手动填充数据，限制行数避免递归
            max_rows = min(len(data), 1000)  # 限制最大行数
            
            for idx in range(max_rows):
                try:
                    row = data.iloc[idx]
                    for col_name in columns:
                        try:
                            if col_name in row:
                                value = row[col_name]
                                # 安全地处理值
                                if pd.isna(value):
                                    new_data[col_name].append("")
                                else:
                                    # 限制字符串长度
                                    str_value = str(value)
                                    if len(str_value) > 1000:
                                        str_value = str_value[:1000] + "..."
                                    new_data[col_name].append(str_value)
                            else:
                                new_data[col_name].append("")
                        except Exception:
                            new_data[col_name].append("")
                except Exception:
                    # 如果某行处理失败，添加空行
                    for col_name in columns:
                        new_data[col_name].append("")
            
            # 创建新的DataFrame
            return pd.DataFrame(new_data)
            
        except Exception as e:
            print(f"手动重建DataFrame失败: {e}")
            # 返回空的DataFrame
            return pd.DataFrame()
    
    def get_safe_columns_from_data(self, data):
        """从数据中安全地获取列名"""
        try:
            columns = list(data.columns)
            safe_columns = []
            for col in columns:
                try:
                    if isinstance(col, str) and len(col) < 1000:
                        safe_columns.append(col)
                    else:
                        safe_columns.append(f"列_{len(safe_columns)}")
                except:
                    safe_columns.append(f"列_{len(safe_columns)}")
            return safe_columns if safe_columns else ['交易时间', '金额', '交易分类', '平台', '交易状态']
        except Exception:
            return ['交易时间', '金额', '交易分类', '平台', '交易状态']

    def generate_text_analysis(self, data):
        """生成文字分析报告"""
        try:
            # 根据分类标准选择数据列
            if self.classification_standard.currentText() == "自定义分类标准" and '调整后分类' in data.columns:
                category_column = '调整后分类'
            else:
                category_column = '交易分类'

            # 根据视图模式筛选数据
            view_mode = self.view_mode.currentText()
            try:
                if view_mode == "仅收入":
                    filtered_data = data[data[category_column].astype(str).str.startswith('收入', na=False)]
                    title = "收入分类分析"
                elif view_mode == "仅支出":
                    filtered_data = data[data[category_column].astype(str).str.startswith('支出', na=False)]
                    title = "支出分类分析"
                else:
                    filtered_data = data[data[category_column] != '非收支']
                    title = "收支分类分析"
            except Exception as e:
                print(f"数据筛选失败: {e}")
                filtered_data = data
                title = "收支分类分析"

            if filtered_data.empty:
                self.chart_text_edit.setPlainText(f"{title}（无数据）")
                return

            # 生成分类统计
            try:
                category_stats = filtered_data.groupby(category_column)['金额'].agg(['sum', 'count']).sort_values('sum', ascending=False)
            except Exception as e:
                print(f"分类统计失败: {e}")
                category_stats = pd.DataFrame({'sum': [0], 'count': [0]}, index=['无数据'])
            
            # 生成平台统计
            try:
                platform_stats = filtered_data.groupby('平台')['金额'].agg(['sum', 'count']).sort_values('sum', ascending=False)
            except Exception as e:
                print(f"平台统计失败: {e}")
                platform_stats = pd.DataFrame({'sum': [0], 'count': [0]}, index=['无数据'])

            # 格式化输出
            output = f"=== {title} ===\n\n"
            
            # 分类统计
            output += "【分类统计】\n"
            output += f"{'分类':<20} {'金额':<15} {'笔数':<10} {'占比':<10}\n"
            output += "-" * 60 + "\n"
            try:
                total_amount = category_stats['sum'].sum()
                for category, row in category_stats.iterrows():
                    amount = row['sum']
                    count = row['count']
                    percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                    output += f"{str(category):<20} ¥{amount:<14.2f} {count:<10} {percentage:<9.1f}%\n"
                
                output += f"\n总计: ¥{total_amount:.2f} ({category_stats['count'].sum()}笔)\n\n"
            except Exception as e:
                output += f"分类统计计算失败: {str(e)}\n\n"
            
            # 平台统计
            output += "【平台统计】\n"
            output += f"{'平台':<15} {'金额':<15} {'笔数':<10} {'占比':<10}\n"
            output += "-" * 55 + "\n"
            try:
                for platform, row in platform_stats.iterrows():
                    amount = row['sum']
                    count = row['count']
                    percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                    output += f"{str(platform):<15} ¥{amount:<14.2f} {count:<10} {percentage:<9.1f}%\n"
            except Exception as e:
                output += f"平台统计计算失败: {str(e)}\n"
            
            # 时间趋势分析
            output += f"\n【时间趋势分析】\n"
            try:
                safe_data_copy = data.copy()
                safe_data_copy['交易时间'] = pd.to_datetime(safe_data_copy['交易时间'], errors='coerce')
                safe_data_copy['日期'] = safe_data_copy['交易时间'].dt.date
                daily_stats = safe_data_copy.groupby('日期')['金额'].agg(['sum', 'count'])
                daily_stats = daily_stats.sort_index()
                
                output += f"分析期间: {daily_stats.index.min()} 至 {daily_stats.index.max()}\n"
                output += f"总天数: {len(daily_stats)} 天\n"
                output += f"日均交易: {daily_stats['count'].mean():.1f} 笔\n"
                output += f"日均金额: ¥{daily_stats['sum'].mean():.2f}\n"
                
                # 最高和最低交易日
                max_day = daily_stats.loc[daily_stats['sum'].idxmax()]
                min_day = daily_stats.loc[daily_stats['sum'].idxmin()]
                output += f"最高交易日: {daily_stats['sum'].idxmax()} (¥{max_day['sum']:.2f}, {max_day['count']}笔)\n"
                output += f"最低交易日: {daily_stats['sum'].idxmin()} (¥{min_day['sum']:.2f}, {min_day['count']}笔)\n"
                
            except Exception as e:
                output += f"时间趋势分析失败: {str(e)}\n"

            self.chart_text_edit.setPlainText(output)
            
        except Exception as e:
            print(f"生成文字分析失败: {e}")
            self.chart_text_edit.setPlainText(f"文字分析生成失败: {str(e)}")

    def refresh_calendar(self):
        """刷新日历视图"""
        try:
            if not hasattr(self, 'df_filtered') or self.df_filtered is None:
                data = self.df
            else:
                data = self.df_filtered
                
            if data is None or data.empty:
                self.calendar_text_edit.setPlainText("暂无数据可分析")
                return

            # 使用安全的数据副本
            safe_data = self.create_safe_data_copy(data)

            # 获取当前选择的年月
            year = self.year_spin.value()
            month = self.month_spin.value()

            # 逐个更新日历图表，每个都有独立的错误处理
            calendar_update_success = True
            
            # 更新日历热力图
            try:
                self.update_calendar_heatmap(safe_data, year, month)
                print("✓ 日历热力图更新成功")
            except Exception as e:
                print(f"✗ 日历热力图更新失败: {e}")
                calendar_update_success = False

            # 更新月度趋势图
            try:
                self.update_monthly_trend(safe_data, year, month)
                print("✓ 月度趋势图更新成功")
            except Exception as e:
                print(f"✗ 月度趋势图更新失败: {e}")
                calendar_update_success = False

            # 生成文字分析报告
            try:
                self.generate_calendar_text_analysis(safe_data, year, month)
                print("✓ 日历文字分析生成成功")
            except Exception as e:
                print(f"✗ 日历文字分析生成失败: {e}")
                self.calendar_text_edit.setPlainText(f"日历文字分析生成失败: {str(e)}")
            
            if not calendar_update_success:
                self.calendar_text_edit.append("\n\n注意：部分日历图表更新失败，但程序仍在运行。")
            
        except Exception as e:
            import traceback
            error_msg = f"日历分析失败: {str(e)}\n{traceback.format_exc()}"
            self.calendar_text_edit.setPlainText(error_msg)
            print(f"✗ refresh_calendar 出错: {e}")
            print(traceback.format_exc())

    def generate_calendar_text_analysis(self, data, year, month):
        """生成日历文字分析报告"""
        try:
            # 根据分类标准选择数据列
            if self.calendar_classification.currentText() == "自定义分类标准" and '调整后分类' in data.columns:
                category_column = '调整后分类'
            else:
                category_column = '交易分类'

            # 过滤当月数据
            data_copy = data.copy()
            data_copy['交易时间'] = pd.to_datetime(data_copy['交易时间'], errors='coerce')
            data_copy['日期'] = data_copy['交易时间'].dt.date
            monthly_data = data_copy[(data_copy['交易时间'].dt.year == year) & (data_copy['交易时间'].dt.month == month)]
            
            if monthly_data.empty:
                self.calendar_text_edit.setPlainText(f"{year}年{month}月暂无交易数据")
                return

            # 按日期分组统计
            daily_stats = []
            for date, group in monthly_data.groupby('日期'):
                income = group[group[category_column].astype(str).str.startswith('收入', na=False)]['金额'].sum()
                expense = group[group[category_column].astype(str).str.startswith('支出', na=False)]['金额'].sum()
                net = income - expense
                daily_stats.append((date, income, expense, net))
            
            daily_stats.sort(key=lambda x: x[0])
            
            # 格式化输出
            output = f"=== {year}年{month}月 日历分析 ===\n\n"
            
            # 月度汇总
            total_income = sum(day[1] for day in daily_stats)
            total_expense = sum(day[2] for day in daily_stats)
            total_net = total_income - total_expense
            total_days = len(daily_stats)
            
            output += f"【月度汇总】\n"
            output += f"总天数: {total_days} 天\n"
            output += f"总收入: ¥{total_income:.2f}\n"
            output += f"总支出: ¥{total_expense:.2f}\n"
            output += f"净收入: ¥{total_net:.2f}\n"
            output += f"日均收入: ¥{total_income/total_days:.2f}\n" if total_days > 0 else "日均收入: ¥0.00\n"
            output += f"日均支出: ¥{total_expense/total_days:.2f}\n" if total_days > 0 else "日均支出: ¥0.00\n"
            output += f"日均净收入: ¥{total_net/total_days:.2f}\n" if total_days > 0 else "日均净收入: ¥0.00\n\n"
            
            # 每日明细
            output += "【每日明细】\n"
            output += f"{'日期':<12} {'收入':<12} {'支出':<12} {'净额':<12} {'状态':<10}\n"
            output += "-" * 65 + "\n"
            
            for date, income, expense, net in daily_stats:
                status = "盈余" if net > 0 else "赤字" if net < 0 else "平衡"
                output += f"{str(date):<12} ¥{income:<11.2f} ¥{expense:<11.2f} ¥{net:<11.2f} {status:<10}\n"
            
            # 统计信息
            output += f"\n【统计信息】\n"
            positive_days = len([day for day in daily_stats if day[3] > 0])
            negative_days = len([day for day in daily_stats if day[3] < 0])
            balance_days = len([day for day in daily_stats if day[3] == 0])
            
            output += f"盈余天数: {positive_days} 天 ({positive_days/total_days*100:.1f}%)\n" if total_days > 0 else "盈余天数: 0 天 (0.0%)\n"
            output += f"赤字天数: {negative_days} 天 ({negative_days/total_days*100:.1f}%)\n" if total_days > 0 else "赤字天数: 0 天 (0.0%)\n"
            output += f"平衡天数: {balance_days} 天 ({balance_days/total_days*100:.1f}%)\n" if total_days > 0 else "平衡天数: 0 天 (0.0%)\n"
            
            # 最高和最低交易日
            if daily_stats:
                max_income_day = max(daily_stats, key=lambda x: x[1])
                max_expense_day = max(daily_stats, key=lambda x: x[2])
                max_net_day = max(daily_stats, key=lambda x: x[3])
                min_net_day = min(daily_stats, key=lambda x: x[3])
                
                output += f"\n【峰值记录】\n"
                output += f"最高收入日: {max_income_day[0]} (¥{max_income_day[1]:.2f})\n"
                output += f"最高支出日: {max_expense_day[0]} (¥{max_expense_day[2]:.2f})\n"
                output += f"最高净收入日: {max_net_day[0]} (¥{max_net_day[3]:.2f})\n"
                output += f"最高净支出日: {min_net_day[0]} (¥{min_net_day[3]:.2f})\n"

            self.calendar_text_edit.setPlainText(output)
            
        except Exception as e:
            print(f"生成日历文字分析失败: {e}")
            self.calendar_text_edit.setPlainText(f"日历文字分析生成失败: {str(e)}")

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

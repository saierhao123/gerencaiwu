"""
个人记账管理系统主程序
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QComboBox, QMessageBox, QHeaderView
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pandas as pd
# 新增：导入控制台输出工具类
from console_printer import ConsolePrinter  # 这行是新增的
from bill_parser import BillParser
from transaction_classifier import TransactionClassifier
from data_visualizer import DataVisualizer


class ProcessingThread(QThread):
    progress_updated = pyqtSignal(str)
    processing_finished = pyqtSignal(object, object, object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, folder_path: str):
        super().__init__()
        self.folder_path = folder_path
    
    def run(self):
        try:
            self.progress_updated.emit("开始解析账单文件...")
            
            parser = BillParser()
            df = parser.process_all_bills(self.folder_path)
            self.progress_updated.emit(f"成功解析 {len(df)} 条交易记录")
            
            self.progress_updated.emit("开始分类交易...")
            classifier = TransactionClassifier()
            classified_df = classifier.classify_all_transactions(df)
            self.progress_updated.emit("交易分类完成")
            
            self.progress_updated.emit("生成统计信息...")
            stats = classifier.get_classification_statistics(classified_df)
            self.progress_updated.emit("统计信息生成完成")
            
            self.progress_updated.emit("生成可视化图表...")
            visualizer = DataVisualizer()
            visualizer.plot_category_pie(stats)
            report_text = visualizer.create_summary_report(stats)
            self.progress_updated.emit("可视化图表生成完成")
            print("【调试】准备触发processing_finished信号")
            self.processing_finished.emit(classified_df, stats, report_text)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.stats = None
        self.report_text = None
        self.current_folder = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("个人记账管理系统")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)

        # 顶部控制区域 - 更清晰的布局
        control_layout = QHBoxLayout()

        # 左侧：文件夹显示
        self.folder_label = QLabel("📁 当前账单文件夹: 未选择")
        self.folder_label.setWordWrap(True)  # 自动换行
        self.folder_label.setStyleSheet("font-size: 12px; color: #555;")
        control_layout.addWidget(self.folder_label, stretch=1)

        # 右侧：按钮组
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
        # === 事件绑定 ===
        select_folder_btn.clicked.connect(self.select_folder)
        self.process_btn.clicked.connect(self.start_processing)
        self.refresh_btn.clicked.connect(self.refresh_data)
        # 进度容器
        progress_layout = QHBoxLayout()

        # 进度条（水平）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)

        # 进度说明标签
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setStyleSheet("color: #0066cc; font-weight: bold;")

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, 1)  # 进度条占更多空间

        main_layout.addLayout(progress_layout)

        
        # 标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建标签页
        self.create_transaction_tab()
        self.create_statistics_tab()
        
        # 设置默认文件夹
        self.set_default_folder()
    
    def create_transaction_tab(self):
        """创建交易明细标签页"""
        transaction_widget = QWidget()
        transaction_layout = QVBoxLayout(transaction_widget)
        
        # 筛选控制区域
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("平台筛选:"))
        self.platform_filter = QComboBox()
        self.platform_filter.addItem("全部")
        self.platform_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(self.platform_filter)
        
        filter_layout.addWidget(QLabel("分类筛选:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("全部")
        self.category_filter.currentTextChanged.connect(self.filter_transactions)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        
        transaction_layout.addLayout(filter_layout)
        
        # 交易明细表格
        self.transaction_table = QTableWidget()
        self.transaction_table.setColumnCount(12)
        self.transaction_table.setHorizontalHeaderLabels([
            "交易时间", "平台", "交易分类", "交易对方", "商品说明", 
            "收/支", "金额", "支付方式", "交易状态", "交易单号", "调整后分类", "调整后子分类"
        ])
        # 让“调整后分类”和“调整后子分类”可编辑
        self.transaction_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)

        # 设置表格属性
        header = self.transaction_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # 平台列固定宽度
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # 交易分类列固定宽度
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # 交易状态列固定宽度
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)  # 交易单号列固定宽度
        header.setSectionResizeMode(10, QHeaderView.ResizeMode.Fixed)  # 调整后分类列固定宽度
        header.setSectionResizeMode(11, QHeaderView.ResizeMode.Fixed)  # 调整后子分类列固定宽度
        
        self.transaction_table.setColumnWidth(1, 80)   # 平台
        self.transaction_table.setColumnWidth(2, 100)  # 交易分类
        self.transaction_table.setColumnWidth(8, 100)  # 交易状态
        self.transaction_table.setColumnWidth(9, 150)  # 交易单号
        self.transaction_table.setColumnWidth(10, 100)  # 调整后分类
        self.transaction_table.setColumnWidth(11, 120)  # 调整后子分类
        
        transaction_layout.addWidget(self.transaction_table)
        
        self.tab_widget.addTab(transaction_widget, "交易明细")

        # 监听单元格修改
        self.transaction_table.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, column):
        """用户修改分类时，基于原始数据生成指纹"""
        if self.df is None or row not in self.row_to_original_index:
            return

        # 只处理“调整后分类”和“调整后子分类”
        if column not in [10, 11]:
            return

        item = self.transaction_table.item(row, column)
        if not item:
            return
        new_value = item.text().strip()

        # 关键：获取原始交易数据（不含用户修改的分类）
        original_index = self.row_to_original_index[row]
        row_data = self.df.loc[original_index].copy()  # 复制原始数据
        # 清除可能影响指纹的字段（确保与解析时一致）
        for field in ['调整后分类', '调整后子分类', '分类']:
            if field in row_data:
                del row_data[field]

        # 生成指纹并保存
        try:
            from transaction_classifier import TransactionClassifier
            classifier = TransactionClassifier()
            classifier.add_user_classification(row_data, new_value, persist=True)

            # 更新内存中的df
            if column == 10:
                self.df.at[original_index, '调整后分类'] = new_value
            else:
                self.df.at[original_index, '调整后子分类'] = new_value

            QMessageBox.information(self, "成功", f"已保存分类：{new_value}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存分类失败：{str(e)}")

    def create_statistics_tab(self):
        """创建统计结果标签页"""
        statistics_widget = QWidget()
        statistics_layout = QVBoxLayout(statistics_widget)

        # 图表显示区域
        self.chart_label = QLabel("📊 图表将在这里显示")
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_label.setStyleSheet("color: #888; font-size: 14px;")
        self.chart_label.setMinimumHeight(400)
        statistics_layout.addWidget(self.chart_label)

        # 文本报告
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        self.statistics_text.setMaximumHeight(200)
        statistics_layout.addWidget(self.statistics_text)

        self.tab_widget.addTab(statistics_widget, "📊 统计与图表")

    def set_default_folder(self):
        """设置默认文件夹：确保路径不为None"""
        default_folder = "zhangdang"
        # 检查默认文件夹是否存在且是有效文件夹
        if os.path.exists(default_folder) and os.path.isdir(default_folder):
            self.current_folder = default_folder
            self.folder_label.setText(f"账单文件夹: {default_folder}")
            self.process_btn.setEnabled(True)
        else:
            # 默认文件夹不存在时，设为空字符串，不是None
            self.current_folder = ""
            self.folder_label.setText("账单文件夹: 未选择（默认文件夹zhangdang不存在）")
            self.process_btn.setEnabled(False)

    def select_folder(self):
        """选择账单文件夹：确保只保存有效路径"""
        # 打开文件夹选择对话框，用户取消时返回空字符串
        folder = QFileDialog.getExistingDirectory(self, "选择账单文件夹")
        # 只有用户选择了有效文件夹（不是空字符串），才更新current_folder
        if folder and folder.strip():
            self.current_folder = folder
            self.folder_label.setText(f"账单文件夹: {folder}")
            self.process_btn.setEnabled(True)
        else:
            # 用户取消选择时，保持原状态，不设为None
            self.folder_label.setText("账单文件夹: 未选择")
            self.current_folder = ""  # 设为空字符串，不是None
            self.process_btn.setEnabled(False)
    
    def refresh_data(self):
        """刷新数据（重新处理当前文件夹）"""
        if self.current_folder:
            self.start_processing()
    
    def start_processing(self):
        """开始处理账单文件"""
        """开始处理账单文件：添加最终防护"""
        # 新增：最终防护，确保current_folder不是None且是字符串
        if self.current_folder is None or not isinstance(self.current_folder, str):
            QMessageBox.warning(self, "警告", "文件夹路径无效（为空或不是字符串），请重新选择文件夹")
            return

        if not self.current_folder:
            QMessageBox.warning(self, "警告", "请先选择账单文件夹")
            return
        
        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # # 启动处理线程
        # self.processing_thread = ProcessingThread(self.current_folder)
        # self.processing_thread.progress_updated.connect(self.update_progress)
        # self.processing_thread.processing_finished.connect(self.processing_finished)
        # self.processing_thread.error_occurred.connect(self.processing_error)
        # self.processing_thread.start()

        # try:
        #     self.update_progress("开始解析账单文件...")
        #     parser = BillParser()
        #     df, parse_errors = parser.parse_folder(self.current_folder)
        #     self.update_progress(f"成功解析 {len(df)} 条交易记录")
        #
        #     self.update_progress("开始分类交易...")
        #     if parse_errors:
        #         print("=== 解析过程中的提示 ===")
        #         for err in parse_errors:
        #             print(f"提示：{err}")
        #
        #     self.progress_label.setText("正在分类交易记录...")
        #     classifier = TransactionClassifier()
        #     classified_df = classifier.classify_all_transactions(df)
        #     self.update_progress("交易分类完成")
        #
        #     self.update_progress("生成统计信息...")
        #     stats = classifier.get_classification_statistics(classified_df)
        #     self.update_progress("统计信息生成完成")
        #
        #     self.update_progress("生成可视化图表...")
        #     visualizer = DataVisualizer()
        #     report_text = visualizer.create_summary_report(stats)
        #     self.update_progress("可视化图表生成完成")
        #
        #     # 直接调用处理完成的逻辑
        #     self.processing_finished(df, stats, report_text)
        # except Exception as e:
        #     self.processing_error(str(e))
        class ProcessingThread(QThread):
            progress_updated = pyqtSignal(str)
            processing_finished = pyqtSignal(pd.DataFrame, dict, str)
            error_occurred = pyqtSignal(str)

            def __init__(self, folder_path: str):
                super().__init__()
                self.folder_path = folder_path

            def run(self):
                try:
                    self.progress_updated.emit("开始解析账单文件...")
                    # 关键：调用BillParser新增的process_and_print_bills方法（会自动输出到控制台）
                    from bill_parser import BillParser
                    parser = BillParser()
                    # 这里调用新增的方法，解析完成后会自动打印到控制台
                    combined_df = parser.process_and_print_bills(self.folder_path)

                    self.progress_updated.emit("生成统计信息...")
                    from transaction_classifier import TransactionClassifier
                    classifier = TransactionClassifier()
                    stats = classifier.get_classification_statistics(combined_df)

                    self.progress_updated.emit("生成可视化图表...")
                    from data_visualizer import DataVisualizer
                    visualizer = DataVisualizer()
                    visualizer.plot_category_pie(stats, "temp_chart.png")
                    report_text = visualizer.create_summary_report(stats)
                    report_text = f"解析完成：共{len(combined_df)}条记录，饼图已保存"

                    self.progress_updated.emit("处理完成！")
                    self.processing_finished.emit(combined_df, stats, report_text)
                except Exception as e:
                    self.error_occurred.emit(str(e))

        # 启动线程（你的原有逻辑，完全保留）
        self.processing_thread = ProcessingThread(self.current_folder)
        # 进度更新：主线程更新标签（安全）
        self.processing_thread.progress_updated.connect(self.progress_label.setText)
        # 处理完成：主线程更新GUI（安全）
        self.processing_thread.processing_finished.connect(self.processing_finished)
        # 错误处理：主线程弹出弹窗（安全）
        self.processing_thread.error_occurred.connect(lambda msg: QMessageBox.critical(self, "错误", msg))
        self.processing_thread.start()
    def update_progress(self, message: str):
        self.progress_label.setText(f"📌 {message}")
        # 可以加一些进度值（可选）
        if "解析" in message:
            self.progress_bar.setValue(25)
        elif "分类" in message:
            self.progress_bar.setValue(50)
        elif "统计" in message:
            self.progress_bar.setValue(75)
        elif "完成" in message:
            self.progress_bar.setValue(100)
    
    def processing_finished(self, df: pd.DataFrame, stats: dict, report_text: str):
        """处理完成"""
        self.df = df
        self.stats = stats
        self.report_text = report_text
        
        # 更新界面
        self.update_transaction_table()
        self.update_statistics_tab()
        
        # 更新筛选选项
        self.update_filter_options()
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # 启用按钮
        self.process_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        print("=== 开始执行控制台输出 ===")  # 新增测试打印
        try:
            # 初始化控制台打印机
            console_printer = ConsolePrinter()
            # 打印所有解析后的数据（汇总+明细+统计）
            console_printer.print_all(df, stats)
            print("=== 控制台输出执行完成 ===")  # 新增测试打印
        except Exception as e:
            # 即使控制台输出出错，也不影响主程序运行
            print(f"控制台输出时出错：{str(e)}")
        QMessageBox.information(self, "完成", "账单处理完成！")
    
    def processing_error(self, error_message: str):
        """处理出错"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.process_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"处理失败: {error_message}")
    
    def update_transaction_table(self):
        """更新交易明细表格"""
        if self.df is None or self.df.empty:
            return
        
        # 设置行数
        self.transaction_table.setRowCount(len(self.df))
        
        # 填充数据
        for row_idx, (_, row_data) in enumerate(self.df.iterrows()):
            # 交易时间
            time_str = str(row_data.get('交易时间', ''))
            if time_str and time_str != 'NaT':
                try:
                    time_obj = pd.to_datetime(time_str)
                    time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            time_item = QTableWidgetItem(time_str)
            self.transaction_table.setItem(row_idx, 0, time_item)
            
            # 平台
            platform_item = QTableWidgetItem(str(row_data.get('平台', '')))
            self.transaction_table.setItem(row_idx, 1, platform_item)
            
            # 交易分类（微信）或交易类型（支付宝）
            category_value = row_data.get('交易分类', '') or row_data.get('交易类型', '')
            category_item = QTableWidgetItem(str(category_value))
            self.transaction_table.setItem(row_idx, 2, category_item)
            
            # 交易对方
            party_item = QTableWidgetItem(str(row_data.get('交易对方', '')))
            self.transaction_table.setItem(row_idx, 3, party_item)
            
            # 商品说明
            desc_item = QTableWidgetItem(str(row_data.get('商品说明', '')))
            self.transaction_table.setItem(row_idx, 4, desc_item)
            
            # 收/支
            income_expense_item = QTableWidgetItem(str(row_data.get('收/支', '')))
            self.transaction_table.setItem(row_idx, 5, income_expense_item)
            
            # 金额
            amount_value = row_data.get('金额', 0)
            try:
                amount_str = f"¥{float(amount_value):.2f}"
            except:
                amount_str = str(amount_value)
            amount_item = QTableWidgetItem(amount_str)
            self.transaction_table.setItem(row_idx, 6, amount_item)
            
            # 支付方式
            payment_value = row_data.get('支付方式', '') or row_data.get('收/付款方式', '')
            payment_item = QTableWidgetItem(str(payment_value))
            self.transaction_table.setItem(row_idx, 7, payment_item)
            
            # 交易状态
            status_item = QTableWidgetItem(str(row_data.get('交易状态', '')))
            self.transaction_table.setItem(row_idx, 8, status_item)
            
            # 交易单号
            trade_no_item = QTableWidgetItem(str(row_data.get('交易单号', '')))
            self.transaction_table.setItem(row_idx, 9, trade_no_item)
            
            # 调整后分类
            adjusted_category_item = QTableWidgetItem(str(row_data.get('调整后分类', '')))
            self.transaction_table.setItem(row_idx, 10, adjusted_category_item)
            
            # 调整后子分类
            adjusted_sub_category_item = QTableWidgetItem(str(row_data.get('调整后子分类', '')))
            self.transaction_table.setItem(row_idx, 11, adjusted_sub_category_item)

    def update_statistics_tab(self):
        """更新统计标签页（安全加载图片）"""
        if self.report_text:
            self.statistics_text.setText(self.report_text)

        if self.stats:
            from data_visualizer import DataVisualizer
            visualizer = DataVisualizer()
            chart_path = visualizer.plot_category_pie(self.stats, "temp_chart.png")

            # 关键：检查图片路径有效性，避免加载失败
            if chart_path and os.path.exists(chart_path):
                from PyQt6.QtGui import QPixmap
                # 用QPixmap加载时，先确保文件未被占用
                try:
                    pixmap = QPixmap(chart_path)
                    if not pixmap.isNull():  # 验证图片有效性
                        self.chart_label.setPixmap(pixmap.scaled(
                            self.chart_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        ))
                    else:
                        self.chart_label.setText("⚠️ 图表加载失败：图片损坏")
                except Exception as e:
                    self.chart_label.setText(f"⚠️ 图表加载错误：{str(e)}")
            else:
                self.chart_label.setText("⚠️ 未生成有效图表")
    
    def update_filter_options(self):
        """更新筛选选项"""
        if self.df is None or self.df.empty:
            return
        
        # 更新平台筛选
        platforms = ['全部'] + sorted(self.df['平台'].unique().tolist())
        self.platform_filter.clear()
        self.platform_filter.addItems(platforms)
        
        # 更新分类筛选 - 使用调整后分类
        categories = ['全部'] + sorted(self.df['调整后分类'].unique().tolist())
        self.category_filter.clear()
        self.category_filter.addItems(categories)
    
    def filter_transactions(self):
        """筛选交易记录"""
        if self.df is None or self.df.empty:
            return
        
        platform_filter = self.platform_filter.currentText()
        category_filter = self.category_filter.currentText()
        
        # 应用筛选
        filtered_df = self.df.copy()
        
        if platform_filter != "全部":
            filtered_df = filtered_df[filtered_df['平台'] == platform_filter]
        
        if category_filter != "全部":
            filtered_df = filtered_df[filtered_df['调整后分类'] == category_filter]
        
        # 更新表格显示
        self.transaction_table.setRowCount(len(filtered_df))
        
        for row_idx, (_, row_data) in enumerate(filtered_df.iterrows()):
            # 交易时间
            time_str = str(row_data.get('交易时间', ''))
            if time_str and time_str != 'NaT':
                try:
                    time_obj = pd.to_datetime(time_str)
                    time_str = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            time_item = QTableWidgetItem(time_str)
            self.transaction_table.setItem(row_idx, 0, time_item)
            
            # 平台
            platform_item = QTableWidgetItem(str(row_data.get('平台', '')))
            self.transaction_table.setItem(row_idx, 1, platform_item)
            
            # 交易分类（微信）或交易类型（支付宝）
            category_value = row_data.get('交易分类', '') or row_data.get('交易类型', '')
            category_item = QTableWidgetItem(str(category_value))
            self.transaction_table.setItem(row_idx, 2, category_item)
            
            # 交易对方
            party_item = QTableWidgetItem(str(row_data.get('交易对方', '')))
            self.transaction_table.setItem(row_idx, 3, party_item)
            
            # 商品说明
            desc_item = QTableWidgetItem(str(row_data.get('商品说明', '')))
            self.transaction_table.setItem(row_idx, 4, desc_item)
            
            # 收/支
            income_expense_item = QTableWidgetItem(str(row_data.get('收/支', '')))
            self.transaction_table.setItem(row_idx, 5, income_expense_item)
            
            # 金额
            amount_value = row_data.get('金额', 0)
            try:
                amount_str = f"¥{float(amount_value):.2f}"
            except:
                amount_str = str(amount_value)
            amount_item = QTableWidgetItem(amount_str)
            self.transaction_table.setItem(row_idx, 6, amount_item)
            
            # 支付方式
            payment_value = row_data.get('支付方式', '') or row_data.get('收/付款方式', '')
            payment_item = QTableWidgetItem(str(payment_value))
            self.transaction_table.setItem(row_idx, 7, payment_item)
            
            # 交易状态
            status_item = QTableWidgetItem(str(row_data.get('交易状态', '')))
            self.transaction_table.setItem(row_idx, 8, status_item)
            
            # 交易单号
            trade_no_item = QTableWidgetItem(str(row_data.get('交易单号', '')))
            self.transaction_table.setItem(row_idx, 9, trade_no_item)
            
            # 调整后分类
            adjusted_category_item = QTableWidgetItem(str(row_data.get('调整后分类', '')))
            self.transaction_table.setItem(row_idx, 10, adjusted_category_item)
            
            # 调整后子分类
            adjusted_sub_category_item = QTableWidgetItem(str(row_data.get('调整后子分类', '')))
            self.transaction_table.setItem(row_idx, 11, adjusted_sub_category_item)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 
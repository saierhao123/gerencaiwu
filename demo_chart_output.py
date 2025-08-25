#!/usr/bin/env python3
"""
演示图表分析文字输出功能
"""

import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QHBoxLayout, QComboBox, QLabel
from PyQt6.QtCore import Qt

class ChartDemoWindow(QMainWindow):
    """图表分析演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.create_sample_data()
        
    def init_ui(self):
        self.setWindowTitle("图表分析文字输出演示")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
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
        
        refresh_btn = QPushButton("刷新图表")
        refresh_btn.clicked.connect(self.refresh_charts)
        control_layout.addWidget(refresh_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 图表分析结果文字显示区域
        self.chart_text_edit = QTextEdit()
        self.chart_text_edit.setReadOnly(True)
        self.chart_text_edit.setPlaceholderText("图表分析结果将在这里显示...")
        layout.addWidget(self.chart_text_edit)
        
        # 初始显示
        self.refresh_charts()
        
    def create_sample_data(self):
        """创建示例数据"""
        self.df = pd.DataFrame({
            '交易时间': [
                '2025-01-01 12:00:00', '2025-01-01 18:00:00', '2025-01-02 09:00:00',
                '2025-01-02 12:00:00', '2025-01-03 10:00:00', '2025-01-03 15:00:00',
                '2025-01-04 08:00:00', '2025-01-04 20:00:00', '2025-01-05 11:00:00',
                '2025-01-05 19:00:00', '2025-01-06 14:00:00', '2025-01-06 21:00:00'
            ],
            '金额': [25.5, 68.0, 1200.0, 35.8, 89.9, 156.7, 45.2, 78.3, 299.9, 12.5, 67.8, 234.5],
            '交易分类': [
                '支出-餐饮', '支出-购物', '收入-工资', '支出-餐饮', '支出-交通', '支出-购物',
                '支出-餐饮', '支出-娱乐', '支出-购物', '支出-餐饮', '支出-交通', '支出-购物'
            ],
            '平台': ['微信', '支付宝', '银行', '微信', '支付宝', '微信', '支付宝', '微信', '支付宝', '微信', '支付宝', '微信']
        })
        
        # 添加调整后分类字段
        self.df['调整后分类'] = self.df['交易分类']
        
    def refresh_charts(self):
        """刷新图表分析结果"""
        if self.df is None or self.df.empty:
            self.chart_text_edit.setPlainText("暂无数据可分析")
            return

        try:
            # 根据分类标准选择数据列
            if self.classification_standard.currentText() == "自定义分类标准" and '调整后分类' in self.df.columns:
                category_column = '调整后分类'
            else:
                category_column = '交易分类'

            # 根据视图模式筛选数据
            view_mode = self.view_mode.currentText()
            if view_mode == "仅收入":
                filtered_data = self.df[self.df[category_column].astype(str).str.startswith('收入', na=False)]
                title = "收入分类分析"
            elif view_mode == "仅支出":
                filtered_data = self.df[self.df[category_column].astype(str).str.startswith('支出', na=False)]
                title = "支出分类分析"
            else:
                filtered_data = self.df[self.df[category_column] != '非收支']
                title = "收支分类分析"

            if filtered_data.empty:
                self.chart_text_edit.setPlainText(f"{title}（无数据）")
                return

            # 生成分类统计
            category_stats = filtered_data.groupby(category_column)['金额'].agg(['sum', 'count']).sort_values('sum', ascending=False)
            
            # 生成平台统计
            platform_stats = filtered_data.groupby('平台')['金额'].agg(['sum', 'count']).sort_values('sum', ascending=False)

            # 格式化输出
            output = f"=== {title} ===\n\n"
            
            # 分类统计
            output += "【分类统计】\n"
            output += f"{'分类':<20} {'金额':<15} {'笔数':<10} {'占比':<10}\n"
            output += "-" * 60 + "\n"
            total_amount = category_stats['sum'].sum()
            for category, row in category_stats.iterrows():
                amount = row['sum']
                count = row['count']
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                output += f"{str(category):<20} ¥{amount:<14.2f} {count:<10} {percentage:<9.1f}%\n"
            
            output += f"\n总计: ¥{total_amount:.2f} ({category_stats['count'].sum()}笔)\n\n"
            
            # 平台统计
            output += "【平台统计】\n"
            output += f"{'平台':<15} {'金额':<15} {'笔数':<10} {'占比':<10}\n"
            output += "-" * 55 + "\n"
            for platform, row in platform_stats.iterrows():
                amount = row['sum']
                count = row['count']
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                output += f"{str(platform):<15} ¥{amount:<14.2f} {count:<10} {percentage:<9.1f}%\n"
            
            # 时间趋势分析
            output += f"\n【时间趋势分析】\n"
            try:
                self.df['交易时间'] = pd.to_datetime(self.df['交易时间'], errors='coerce')
                self.df['日期'] = self.df['交易时间'].dt.date
                daily_stats = self.df.groupby('日期')['金额'].agg(['sum', 'count'])
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
            import traceback
            error_msg = f"图表分析失败: {str(e)}\n{traceback.format_exc()}"
            self.chart_text_edit.setPlainText(error_msg)
            print(f"✗ refresh_charts 出错: {e}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ChartDemoWindow()
    window.show()
    
    print("图表分析演示程序已启动")
    print("您可以切换视图模式和分类标准来查看不同的分析结果")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

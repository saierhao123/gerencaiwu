"""
数据可视化模块
负责生成各种图表和可视化展示
"""

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
import plotly.io as pio
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
plt.switch_backend('Agg')  # 用Agg后端（仅生成图片文件，不启动GUI）
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 解决中文显示问题
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class DataVisualizer:
    """数据可视化器"""
    
    def __init__(self, config_file: str = "config.json"):
        """初始化可视化器
        - 设置中文字体为 SimHei（黑体），避免中文乱码
        - 读取颜色/字号配置
        """
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # matplotlib 中文支持（备用）
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.colors = self.config['系统设置']['图表设置']['饼图颜色']
        font_cfg = self.config['系统设置']['图表设置']['字体设置']
        self.font_family = font_cfg.get('中文字体', 'SimHei')
        self.font_size = int(font_cfg.get('字体大小', 12))
        self.text_color = font_cfg.get('颜色', '#222222')
    
    def _title(self, text: str) -> Dict:
        return dict(text=text, font=dict(size=self.font_size + 4, family=self.font_family, color=self.text_color), x=0.5)
    
    def _axis(self, title: str) -> Dict:
        return dict(title=title,
                    titlefont=dict(size=self.font_size, family=self.font_family, color=self.text_color),
                    tickfont=dict(size=self.font_size - 2, family=self.font_family, color=self.text_color))
    
    def _legend(self) -> Dict:
        return dict(font=dict(size=self.font_size - 2, family=self.font_family, color=self.text_color))
    
    def _hoverlabel(self) -> Dict:
        return dict(font=dict(size=self.font_size, family=self.font_family, color=self.text_color), bgcolor='rgba(255,255,255,0.9)')
    
    def _empty_figure(self, title: str) -> go.Figure:
        fig = go.Figure()
        fig.update_layout(title=self._title(title), hoverlabel=self._hoverlabel())
        return fig
    
    def create_pie_chart(self, df: pd.DataFrame, mode: str = 'all', category_column: str = '分类') -> go.Figure:
        """创建交互式饼图
        - mode: 'all' 全部（排除非收支）；'income' 仅收入；'expense' 仅支出
        - category_column: 用于分类的列名，支持 '分类' 或 '调整后分类'
        """
        if df is None or df.empty:
            return self._empty_figure('无数据')
        if mode == 'expense':
            data = df[df[category_column].str.startswith('支出', na=False)]
            title = '支出分类占比'
        elif mode == 'income':
            data = df[df[category_column].str.startswith('收入', na=False)]
            title = '收入分类占比'
        else:
            data = df[df[category_column] != '非收支']
            title = '收支分类占比'
        if data.empty:
            return self._empty_figure(f'{title}（无数据）')
        
        category_stats = data.groupby(category_column)['金额'].sum().sort_values(ascending=False)
        category_stats = category_stats[category_stats > 0]
        if category_stats.empty:
            return self._empty_figure(f'{title}（金额为0）')
        
        fig = go.Figure(data=[go.Pie(
            labels=category_stats.index,
            values=category_stats.values,
            hole=0.3,
            textinfo='label+percent+value',
            textfont=dict(size=self.font_size, family=self.font_family, color=self.text_color),
            marker=dict(colors=self.colors[:len(category_stats)]),
            hovertemplate='<b>%{label}</b><br>金额：¥%{value:.2f}<br>占比：%{percent}<extra></extra>'
        )])
        fig.update_layout(
            title=self._title(title),
            showlegend=True,
            legend=self._legend(),
            hoverlabel=self._hoverlabel()
        )
        return fig
    
    def _month_date_range(self, year: int, month: int) -> Tuple[datetime, datetime, pd.DatetimeIndex]:
        start_date = datetime(year, month, 1)
        end_date = (datetime(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1))
        return start_date, end_date, pd.date_range(start_date, end_date, freq='D')

    def plot_category_pie(self, stats: Dict, save_path: str = "temp_chart.png"):
        """生成分类饼图（修复线程冲突，用无GUI模式）"""
        try:
            # 1. 提取分类统计数据（确保数据有效）
            category_amount = stats.get("分类统计", {}).get("金额", {})
            if not category_amount:
                raise ValueError("无分类统计数据，无法生成饼图")

            # 2. 过滤无效数据（金额为0或空的分类）
            valid_data = {cat: amt for cat, amt in category_amount.items() if amt != 0 and str(cat).strip()}
            if not valid_data:
                raise ValueError("有效分类数据为空，无法生成饼图")

            # 3. 准备饼图数据
            labels = list(valid_data.keys())
            sizes = list(valid_data.values())
            # 设置颜色（用你config.json中的颜色，或默认颜色）
            colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"]

            # 4. 生成饼图（无GUI模式，直接保存文件）
            fig, ax = plt.subplots(figsize=(8, 8))  # 创建画布（无GUI渲染）
            # 绘制饼图（添加百分比标签，避免文字重叠）
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors[:len(labels)],
                autopct='%1.1f%%', startangle=90, pctdistance=0.85
            )

            # 美化文字（可选，不影响稳定性）
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
            for text in texts:
                text.set_fontsize(11)

            if os.path.exists(save_path):
                try:
                    os.remove(save_path)  # 删除旧图，避免文件锁定
                except Exception as e:
                    print(f"删除旧饼图失败：{str(e)}")

            # 5. 保存图片（直接保存，不显示窗口）
            plt.tight_layout()  # 调整布局，避免标签被截断
            plt.savefig(save_path, dpi=150, bbox_inches='tight')  # 保存为文件
            plt.close(fig)  # 强制关闭画布，释放内存（关键：避免内存泄漏）

            if os.path.exists(save_path):
                print(f"分类饼图已保存到：{save_path}")
                return save_path
            else:
                raise FileNotFoundError(f"饼图保存失败，文件不存在：{save_path}")
        except Exception as e:
            print(f"生成饼图失败：{str(e)}")
        return None  # 失败返回None
            # 若失败，不抛出错误（避免导致GUI闪退）
    def create_calendar_heatmap(self, df: pd.DataFrame, year: int, month: int, category_column: str = '分类') -> go.Figure:
        """创建真正的日历热力图
        - 使用plotly的日历图格式
        - 上：收入（红色）
        - 下：支出（绿色）
        - 悬停显示：日期 + 金额
        - 点击：通过 plotly_click 事件（由外部HTML/JS桥接到PyQt）
        - category_column: 用于分类的列名，支持 '分类' 或 '调整后分类'
        """
        if df is None or df.empty:
            return self._empty_figure('无数据')
        
        df_copy = df.copy()
        df_copy['日期'] = pd.to_datetime(df_copy['交易时间'], errors='coerce')
        if df_copy['日期'].isna().all():
            return self._empty_figure('日期无效')
        
        start_date, end_date, date_range = self._month_date_range(year, month)
        month_data = df_copy[(df_copy['日期'] >= start_date) & (df_copy['日期'] <= end_date)]
        if month_data.empty:
            return self._empty_figure(f'{year}年{month}月无数据')
        
        # 准备日历数据
        calendar_data = []
        for d in date_range:
            day_income = float(month_data[(month_data['日期'].dt.date == d.date()) & 
                                        (month_data[category_column].str.startswith('收入', na=False))]['金额'].sum())
            day_expense = float(month_data[(month_data['日期'].dt.date == d.date()) & 
                                         (month_data[category_column].str.startswith('支出', na=False))]['金额'].sum())
            
            if day_income > 0:
                calendar_data.append({
                    'date': d.strftime('%Y-%m-%d'),
                    'value': day_income,
                    'type': '收入',
                    'color': 'red'
                })
            if day_expense > 0:
                calendar_data.append({
                    'date': d.strftime('%Y-%m-%d'),
                    'value': day_expense,
                    'type': '支出',
                    'color': 'green'
                })
        
        if not calendar_data:
            return self._empty_figure(f'{year}年{month}月无收支数据')
        
        # 创建日历图
        fig = go.Figure()
        
        # 收入数据（红色）
        income_data = [d for d in calendar_data if d['type'] == '收入']
        if income_data:
            fig.add_trace(go.Scatter(
                x=[d['date'] for d in income_data],
                y=[d['value'] for d in income_data],
                mode='markers',
                name='收入',
                marker=dict(
                    size=20,
                    color='red',
                    symbol='circle'
                ),
                text=[f"收入: ¥{d['value']:.2f}" for d in income_data],
                hovertemplate='<b>%{text}</b><br>日期: %{x}<extra></extra>',
                hoverlabel=self._hoverlabel()
            ))
        
        # 支出数据（绿色）
        expense_data = [d for d in calendar_data if d['type'] == '支出']
        if expense_data:
            fig.add_trace(go.Scatter(
                x=[d['date'] for d in expense_data],
                y=[d['value'] for d in expense_data],
                mode='markers',
                name='支出',
                marker=dict(
                    size=20,
                    color='green',
                    symbol='square'
                ),
                text=[f"支出: ¥{d['value']:.2f}" for d in expense_data],
                hovertemplate='<b>%{text}</b><br>日期: %{x}<extra></extra>',
                hoverlabel=self._hoverlabel()
            ))
        
        # 设置布局
        fig.update_layout(
            title=self._title(f'{year}年{month}月每日收支日历'),
            xaxis=self._axis('日期'),
            yaxis=self._axis('金额 (元)'),
            legend=self._legend(),
            hoverlabel=self._hoverlabel(),
            xaxis_rangeslider_visible=False,
            height=400
        )
        
        # 设置x轴为日期格式
        fig.update_xaxes(
            type='date',
            tickformat='%m-%d',
            tickmode='array',
            tickvals=date_range,
            ticktext=[d.strftime('%m-%d') for d in date_range]
        )
        
        return fig
    
    def create_bar_chart(self, df: pd.DataFrame, mode: str = 'all', category_column: str = '分类') -> go.Figure:
        """创建交互式柱状图
        - mode: 'all' 全部（排除非收支）；'income' 仅收入；'expense' 仅支出
        - category_column: 用于分类的列名，支持 '分类' 或 '调整后分类'
        """
        if df is None or df.empty:
            return self._empty_figure('无数据')
        
        if mode == 'expense':
            data = df[df[category_column].str.startswith('支出', na=False)]
            title = '支出分类柱状图'
        elif mode == 'income':
            data = df[df[category_column].str.startswith('收入', na=False)]
            title = '收入分类柱状图'
        else:
            data = df[df[category_column] != '非收支']
            title = '收支分类柱状图'
        
        if data.empty:
            return self._empty_figure(f'{title}（无数据）')
        
        category_stats = data.groupby(category_column)['金额'].sum().sort_values(ascending=False)
        category_stats = category_stats[category_stats > 0]
        if category_stats.empty:
            return self._empty_figure(f'{title}（金额为0）')
        
        fig = go.Figure(data=[go.Bar(
            x=category_stats.index,
            y=category_stats.values,
            marker=dict(
                color=self.colors[:len(category_stats)],
                line=dict(color='#333333', width=1)
            ),
            text=[f'¥{v:.2f}' for v in category_stats.values],
            textposition='auto',
            textfont=dict(size=self.font_size - 1, family=self.font_family, color=self.text_color),
            hovertemplate='<b>%{x}</b><br>金额：¥%{y:.2f}<extra></extra>'
        )])
        
        fig.update_layout(
            title=self._title(title),
            xaxis=self._axis('分类'),
            yaxis=self._axis('金额 (元)'),
            showlegend=False,
            hoverlabel=self._hoverlabel(),
            height=500,
            bargap=0.2
        )
        
        # 设置x轴标签旋转，避免重叠
        fig.update_xaxes(tickangle=45)
        
        return fig
    
    def figure_to_html(self, fig: go.Figure, bridge_object_name: str = 'pybridge', enable_click: bool = True) -> str:
        base = pio.to_html(fig, include_plotlyjs='cdn', full_html=True)
        script = f"""
<script>
  function bindPlotlyEvents() {{
    var gd = document.querySelector('div.js-plotly-plot');
    if (!gd) return;
    gd.on('plotly_click', function(data) {{
      try {{
        var payload = {{points: data.points}};
        if (window.{bridge_object_name} && window.{bridge_object_name}.onChartClick) {{
          window.{bridge_object_name}.onChartClick(JSON.stringify(payload));
        }}
      }} catch (e) {{ console.error(e); }}
    }});
  }}
  if (document.readyState !== 'loading') {{ bindPlotlyEvents(); }}
  else {{ document.addEventListener('DOMContentLoaded', bindPlotlyEvents); }}
</script>
"""
        if not enable_click:
            script = ''
        return base.replace('</body>', script + '\n</body>')
    
    def create_summary_report(self, stats: Dict, special: Optional[Dict] = None) -> str:
        report = []
        report.append("=" * 50)
        report.append("个人记账管理系统 - 月度统计报告")
        report.append("=" * 50)
        report.append("")
        report.append("【基本统计】")
        report.append(f"总收入: ¥{stats.get('总收入', 0):.2f}")
        report.append(f"总支出: ¥{stats.get('总支出', 0):.2f}")
        report.append(f"净收入: ¥{stats.get('净收入', 0):.2f}")
        report.append(f"非收支总额: ¥{stats.get('非收支总额', 0):.2f}")
        report.append("")
        report.append("【分类统计】")
        classification_amounts = (stats.get('分类统计', {}) or {}).get('金额', {})
        for category, amount in sorted(classification_amounts.items(), key=lambda x: x[1], reverse=True):
            if amount > 0:
                report.append(f"{category}: ¥{amount:.2f}")
        report.append("")
        report.append("【平台统计】")
        platform_stats = stats.get('平台统计', {})
        for platform, data in platform_stats.items():
            if isinstance(data, dict) and 'sum' in data and 'count' in data:
                report.append(f"{platform}: ¥{float(data['sum']):.2f} ({int(data['count'])}笔)")
        if special:
            report.append("")
            report.append("【专项统计】")
            for k, v in special.items():
                if isinstance(v, dict):
                    amount = v.get('金额', 0)
                    count = v.get('笔数', 0)
                    report.append(f"{k}: ¥{amount:.2f}（{count} 笔）")
                else:
                    report.append(f"{k}: {v}")
        
        # 添加分类数量统计
        classification_counts = (stats.get('分类统计', {}) or {}).get('数量', {})
        if classification_counts:
            report.append("")
            report.append("【分类数量统计】")
            for category, count in sorted(classification_counts.items(), key=lambda x: x[1], reverse=True):
                report.append(f"{category}: {count} 笔")
        
        return "\n".join(report) 
import pandas as pd
from typing import Dict, Optional
import colorama  # 用于控制台输出颜色（让结果更易读）

# 初始化颜色库（支持Windows/Linux/Mac）
colorama.init(autoreset=True)


class ConsolePrinter:
    """控制台输出工具类：负责格式化打印解析后的交易数据和统计结果"""

    def __init__(self):
        # 定义颜色常量（方便复用）
        self.COLOR_TITLE = colorama.Fore.CYAN + colorama.Style.BRIGHT  # 标题色（亮青色）
        self.COLOR_SUCCESS = colorama.Fore.GREEN  # 成功/正向数据色（绿色）
        self.COLOR_WARNING = colorama.Fore.YELLOW  # 警告/中性数据色（黄色）
        self.COLOR_ERROR = colorama.Fore.RED  # 错误色（红色）
        self.COLOR_RESET = colorama.Style.RESET_ALL  # 重置颜色

    def print_separator(self, char: str = "-", length: int = 80):
        """打印分隔线（用于区分不同模块输出）"""
        print(f"\n{self.COLOR_WARNING}{char * length}{self.COLOR_RESET}")

    def print_title(self, title: str):
        """打印模块标题（如“解析完成的交易数据”）"""
        self.print_separator()
        print(f"{self.COLOR_TITLE}{title.center(80)}{self.COLOR_RESET}")
        self.print_separator()

    def print_parsed_data_summary(self, df: pd.DataFrame):
        """打印解析后的交易数据汇总（总条数、平台分布、时间范围）"""
        self.print_title("📊 交易数据解析汇总")

        # 确认核心字段存在
        required_fields = ["交易时间", "交易对方", "商品说明", "收/支", "金额", "平台"]
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            print(f"{self.COLOR_WARNING}⚠️  缺少必要字段：{missing_fields}，可能解析不完整{self.COLOR_RESET}")
            return

        if df.empty:
            print(f"{self.COLOR_WARNING}⚠️  未解析到任何交易数据{self.COLOR_RESET}")
            return

        # 1. 总条数和时间范围
        total_count = len(df)
        # 处理交易时间（转为datetime确保正确排序）
        df["交易时间"] = pd.to_datetime(df["交易时间"], errors="coerce")
        start_time = df["交易时间"].min()
        end_time = df["交易时间"].max()
        print(f"1. 总交易条数：{self.COLOR_SUCCESS}{total_count} 条{self.COLOR_RESET}")
        print(
            f"2. 时间范围：{self.COLOR_SUCCESS}{start_time.strftime('%Y-%m-%d')} 至 {end_time.strftime('%Y-%m-%d')}{self.COLOR_RESET}")

        # 2. 平台分布
        platform_dist = df["平台"].value_counts()
        print(f"\n3. 平台分布：")
        for platform, count in platform_dist.items():
            percentage = (count / total_count) * 100
            print(f"   - {platform}：{self.COLOR_SUCCESS}{count} 条（{percentage:.1f}%）{self.COLOR_RESET}")

    def print_transaction_details(self, df: pd.DataFrame, max_rows: int = 20):
        """打印交易明细（默认显示前20条，避免输出过长）"""
        self.print_title(f"📋 交易明细（前{max_rows}条）")

        if df.empty:
            print(f"{self.COLOR_WARNING}⚠️  无交易明细可显示{self.COLOR_RESET}")
            return

        # 确保交易时间格式化
        df["交易时间"] = pd.to_datetime(df["交易时间"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")

        # 显示的字段（使用统一后的字段名）
        display_columns = [
            "交易时间", "平台", "交易对方", "商品说明",
            "收/支", "金额", "支付方式"
        ]
        valid_columns = [col for col in display_columns if col in df.columns]
        display_df = df[valid_columns].head(max_rows).copy()

        # 格式化金额
        display_df["金额"] = display_df["金额"].apply(lambda x: f"¥{float(x):.2f}")

        # 打印明细
        print(display_df.to_string(index=False, max_colwidth=20))
        if len(df) > max_rows:
            print(f"\n{self.COLOR_WARNING}⚠️  已省略后续 {len(df) - max_rows} 条记录{self.COLOR_RESET}")

    def print_classification_stats(self, stats: Dict):
        """打印分类统计结果（总收入、总支出、各分类占比等）"""
        self.print_title("💰 分类统计汇总")

        if not stats:
            print(f"{self.COLOR_WARNING}⚠️  无统计数据可显示{self.COLOR_RESET}")
            return

        # 1. 核心财务指标
        print("1. 核心财务概览：")
        print(f"   - 总收入：{self.COLOR_SUCCESS}¥{stats.get('总收入', 0):.2f}{self.COLOR_RESET}")
        print(f"   - 总支出：{self.COLOR_ERROR}¥{stats.get('总支出', 0):.2f}{self.COLOR_RESET}")
        print(f"   - 非收支总额：{self.COLOR_WARNING}¥{stats.get('非收支总额', 0):.2f}{self.COLOR_RESET}")
        print(
            f"   - 净收入：{self.COLOR_SUCCESS if stats.get('净收入', 0) >= 0 else self.COLOR_ERROR}¥{stats.get('净收入', 0):.2f}{self.COLOR_RESET}")

        # 2. 分类金额统计
        category_amount = stats.get("分类统计", {}).get("金额", {})
        if category_amount:
            print(f"\n2. 各分类金额分布：")
            for category, amount in sorted(category_amount.items(), key=lambda x: abs(x[1]), reverse=True):
                # 根据分类类型设置颜色（收入绿色、支出红色、非收支黄色）
                if category.startswith("收入"):
                    color = self.COLOR_SUCCESS
                elif category.startswith("支出"):
                    color = self.COLOR_ERROR
                else:
                    color = self.COLOR_WARNING
                print(f"   - {category}：{color}¥{amount:.2f}{self.COLOR_RESET}")

        # 3. 平台统计
        platform_stats = stats.get("平台统计", {})
        if platform_stats and "sum" in platform_stats:
            print(f"\n3. 平台金额统计：")
            for platform, amount in platform_stats["sum"].items():
                print(f"   - {platform}：{self.COLOR_SUCCESS}¥{amount:.2f}{self.COLOR_RESET}")

    def print_all(self, df: pd.DataFrame, stats: Optional[Dict] = None):
        """一键打印所有数据（汇总+明细+统计）"""
        self.print_parsed_data_summary(df)  # 打印汇总
        self.print_transaction_details(df)  # 打印明细
        if stats:
            self.print_classification_stats(stats)  # 打印统计
        self.print_separator(char="=", length=80)

"""
工具类模块
提供通用功能和错误处理
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import traceback


class Logger:
    """日志管理器"""
    
    def __init__(self, log_file: str = "app.log"):
        self.logger = logging.getLogger("PersonalFinanceManager")
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.get_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.get_default_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "分类规则": {
                "支出": {
                    "餐饮": ["餐厅", "外卖", "咖啡", "奶茶", "胡辣汤", "果源", "馒头", "炒货", "便利店", "超市", "百货", "售水站"],
                    "交通": ["打车", "公交", "地铁", "共享单车", "加油"],
                    "购物": ["淘宝", "天猫", "拼多多", "京东", "购物"],
                    "教育": ["教育", "培训", "学习"],
                    "医疗": ["医院", "药店", "诊所"],
                    "娱乐": ["电影", "游戏", "KTV", "旅游"],
                    "宠物": ["宠物医院", "狗粮", "猫粮"],
                    "日常": ["日用", "生活", "超市", "便利店"]
                },
                "收入": {
                    "工资": ["工资", "薪水", "薪资"],
                    "红包": ["红包", "奖励", "提现", "签到"],
                    "投资": ["理财收益", "基金分红", "利息"],
                    "其他": ["转账", "退款"]
                },
                "非收支": ["转账", "理财", "退款", "余额宝", "基金", "投资", "零钱通", "花呗", "借呗", "充值", "提现"]
            },
            "系统设置": {
                "默认文件夹": "zhangdang",
                "图表设置": {
                    "饼图颜色": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F"],
                    "字体设置": {
                        "中文字体": "SimHei",
                        "字体大小": 12
                    }
                },
                "数据处理": {
                    "跨平台转账时间差": 30,
                    "金额误差范围": 0.01
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_amount(amount: Any) -> bool:
        """验证金额格式"""
        try:
            if isinstance(amount, (int, float)):
                return True
            if isinstance(amount, str):
                # 移除货币符号和逗号
                cleaned = amount.replace('¥', '').replace(',', '').strip()
                float(cleaned)
                return True
            return False
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """验证日期格式"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return True
        except ValueError:
            try:
                datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')
                return True
            except ValueError:
                return False
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """验证文件路径"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    @staticmethod
    def validate_folder_path(folder_path: str) -> bool:
        """验证文件夹路径"""
        return os.path.exists(folder_path) and os.path.isdir(folder_path)


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def handle_exception(self, e: Exception, context: str = "") -> str:
        """处理异常"""
        error_msg = f"{context}: {str(e)}"
        self.logger.error(error_msg)
        self.logger.debug(traceback.format_exc())
        return error_msg
    
    def safe_execute(self, func, *args, **kwargs):
        """安全执行函数"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_exception(e, f"执行函数 {func.__name__} 时出错")
            return None


class FileManager:
    """文件管理器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def ensure_directory(self, directory: str) -> bool:
        """确保目录存在"""
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"创建目录: {directory}")
            return True
        except Exception as e:
            self.logger.error(f"创建目录失败 {directory}: {e}")
            return False
    
    def backup_file(self, file_path: str, backup_dir: str = "backup") -> bool:
        """备份文件"""
        try:
            if not os.path.exists(file_path):
                return False
            
            self.ensure_directory(backup_dir)
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
            
            import shutil
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"文件备份成功: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"文件备份失败: {e}")
            return False
    
    def get_file_size(self, file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"


class DataProcessor:
    """数据处理器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def clean_amount(self, amount: Any) -> float:
        """清理金额数据"""
        try:
            if isinstance(amount, (int, float)):
                return float(amount)
            if isinstance(amount, str):
                # 移除货币符号、逗号和空格
                cleaned = amount.replace('¥', '').replace(',', '').replace(' ', '')
                return float(cleaned)
            return 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"无法解析金额: {amount}")
            return 0.0
    
    def clean_date(self, date_str: str) -> Optional[datetime]:
        """清理日期数据"""
        try:
            # 尝试多种日期格式
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y/%m/%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            self.logger.warning(f"无法解析日期: {date_str}")
            return None
        except Exception as e:
            self.logger.error(f"日期解析错误: {e}")
            return None
    
    def normalize_text(self, text: str) -> str:
        """标准化文本"""
        if not text:
            return ""
        
        # 移除多余空格
        text = ' '.join(text.split())
        # 转换为小写用于比较
        return text.strip()
    
    def detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except ImportError:
            return 'utf-8'
        except Exception:
            return 'utf-8'


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, name: str):
        """开始计时"""
        self.start_times[name] = datetime.now()
    
    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时（秒）"""
        if name in self.start_times:
            elapsed = datetime.now() - self.start_times[name]
            seconds = elapsed.total_seconds()
            self.logger.info(f"{name} 耗时: {seconds:.2f}秒")
            del self.start_times[name]
            return seconds
        return 0.0
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss": memory_info.rss,  # 物理内存
                "vms": memory_info.vms,  # 虚拟内存
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)} 
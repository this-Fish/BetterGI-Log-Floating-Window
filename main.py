# ### 1.4.6
#   - **適配**
#   - 適配BGI_0.63.0日志格式


__author__ = "蜜柑魚"
        
# 在頂部導入
import os
import sys
import re
import time
import logging
import shutil
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

# tkinter 相關
import tkinter as tk
import tkinter.font as tkfont

# Windows API
import ctypes

# 鍵盤全局快捷鍵
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
    KEYBOARD_MODULE = keyboard  # 新增：保存模組引用
except ImportError:
    KEYBOARD_AVAILABLE = False
    KEYBOARD_MODULE = None  # 新增：設置為 None
    logging.warning("keyboard 庫未安裝，全局快捷鍵不可用")
    # 創建虛擬的 KeyboardEvent 類以避免 NameError
    class KeyboardEvent:
        pass

def get_base_path():
    """获取程序运行的基础路径"""
    try:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 确保路径存在
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
            
        return base_path
    except Exception as e:
        logging.error(f"获取基础路径失败: {str(e)}")
        return os.getcwd()  # 回退到当前工作目录

# 配置日志系统 - 只保留控制台输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

class ConfigLoader:
        # 內嵌完整設定檔模板（基於用戶提供的 config.txt，log_path 保持註解狀態）
    DEFAULT_CONFIG_TEMPLATE = '''# BetterGI日志悬浮窗配置文件
# =============================================
# 基本设置段 - 程序运行必需的核心参数
# =============================================

# 日志文件目录路径（必须设置）
# 请修改为您的BetterGI日志实际目录路径
# 示例：log_path=C:\\Program Files\\BetterGI\\log
# log_path=D:\\BetterGI\\BetterGI_060\\log

# 日志文件名前缀（通常不需要修改）
log_filename_prefix=better-genshin-impact

# 窗口预设位置X坐标
initial_x=0

# 窗口预设位置Y坐标
initial_y=0

# 是否跳过调试日志 (true-跳过, false-显示)
skip_debug_log=false

# 自适应高度
dynamic_height=true

# 备份配置
# -----------------
# 备份目录路径（留空则不备份，设置路径会自动启用备份功能）
# backup_path=X:\\我的雲端硬碟\\BGI_log
# backup_path=
# 备份间隔（分钟），默认30
backup_interval=30
# 保留最近多少天的备份文件，默认7
backup_keep_days=6
# 调试开关：启动时立即备份一次
backup_debug=false
# 是否启用准点备份（true-按整点分钟对齐，false-相对时间模式）
backup_align_to_clock=true

# =============================================
# 主样式段 - 用户自定义设置
# =============================================
# 窗口透明度 (0.1-1.0，1.0为完全不透明)
window_alpha=0.7

# 窗口背景颜色（十六进制颜色代码）
bg_color=#000000

# 正常状态文字颜色
normal_color=#00FF00

# 超时警告文字颜色（60秒无更新时显示）
stale_color=#FF0000

# 高频切换警告文字颜色
high_freq_color=#FFA500

# 备份临时消息文字颜色
backup_msg_color=#FFD700

# DBG级别日志文字颜色
debug_color=#808080

# ERR级别日志文字颜色
error_color=#FF6B6B

# WRN级别日志文字颜色
warning_color=#FFD700

# 状态行标题颜色（配置组行）
status_header_color=#87CEFA

# 任务行标题颜色
task_header_color=#87CEFA

# 字体名称（请确保系统中已安装该字体）
font_name=Consolas

# 字体大小
font_size=12

# 字体粗细 (normal-正常, bold-粗体)
font_weight=bold

# 窗口最大宽度（像素）
max_width=768

# 窗口最大高度（像素）
max_height=288

# 日志记录显示行数
display_lines=13

# 窗口刷新间隔（毫秒）
refresh_interval=1000

# 是否啟用自動換行
auto_wrap=true

# =============================================
# 第二样式配置段 - 使用Alt+K切换到此样式
# =============================================
# 第二样式窗口透明度
style2_window_alpha=0.7

# 第二样式窗口背景颜色
style2_bg_color=#000000

# 第二样式正常状态文字颜色
style2_normal_color=#FFFFFF

# 第二样式超时警告文字颜色
style2_stale_color=#FFFFFF

# 第二样式高频警告文字颜色
style2_high_freq_color=#FFFFFF

# 备份临时消息文字颜色（第二样式）
style2_backup_msg_color=#FFD700

# 第二样式DBG级别日志文字颜色
style2_debug_color=#808080

# 第二样式ERR级别日志文字颜色
style2_error_color=#FF6B6B

# 第二样式WRN级别日志文字颜色
style2_warning_color=#FFD700

# 第二样式状态行标题颜色
style2_status_header_color=#00FF00

# 第二样式任务行标题颜色
style2_task_header_color=#00FFFF

# 第二样式字体名称
style2_font_name=Consolas

# 第二样式字体大小
style2_font_size=9

# 第二样式字体粗细
style2_font_weight=bold

# 第二样式窗口最大宽度
style2_max_width=460

# 第二样式窗口最大高度
style2_max_height=220

# 第二样式日志记录显示行数
style2_display_lines=12

# 第二样式窗口刷新间隔
style2_refresh_interval=500

# 第二样式是否啟用自動換行
style2_auto_wrap=true

# =============================================
[程序自动管理配置段]
# 注意：以下配置由程序自动管理，请勿手动修改
# =============================================

# 透明背景模式状态 (true-开启, false-关闭)
# 程序根据Alt+I快捷键自动更新
transparent_mode=false

# 不可选中模式状态 (true-开启, false-关闭)
# 程序根据Alt+N快捷键自动更新
click_through=false

# 第二样式启用状态 (true-开启, false-关闭)
# 程序根据Alt+K快捷键自动更新
author_style2=false

# 窗口记忆位置X坐标
# 程序自动保存窗口关闭时的位置
window_x=

# 窗口记忆位置Y坐标
# 程序自动保存窗口关闭时的位置
window_y=
'''

    def __init__(self, config_file="config.txt"):
        """配置文件加载器 - 从config.txt读取用户设置"""
        script_dir = get_base_path()
        self.config_file = Path(script_dir) / config_file
        
        # 默认配置值
        self.default_config = {
            "log_path": "",  # 原神日志文件目录路径
            "log_filename_prefix": "better-genshin-impact",  # 日志文件名前缀
            "skip_debug_log": False,  # 是否跳过调试日志
            "backup_path": "",              # 备份目录路径，为空则不备份
            "backup_interval": 60,          # 备份间隔（分钟）
            "backup_debug": False,          # 调试开关：初始备份一次
            "backup_align_to_clock": False,   # 是否启用准点备份
            "backup_enabled": False,        # 备份功能总开关（根据backup_path是否为空自动设置）
            "backup_keep_days": 10,         # 保留最近多少天的备份文件
            "window_alpha": 0.7,      # 窗口透明度
            "bg_color": "#000000",    # 背景颜色
            "normal_color": "#00FF00",# 正常状态文字颜色
            "stale_color": "#FF0000", # 超时警告颜色
            "high_freq_color": "#FFA500", # 高频切换警告颜色
            "debug_color": "#808080",  # DBG级别日志颜色（灰色）
            "error_color": "#FF6B6B",  # ERR级别日志颜色（浅红色）
            "warning_color": "#FFD700", # WRN级别日志颜色（浅黄色）
            "status_header_color": "#87CEFA",  # 状态行标题颜色（配置组行）
            "task_header_color": "#87CEFA",    # 任务行标题颜色
            "backup_msg_color": "#FFD700",     # 备份临时消息颜色（黄色）
            "font_name": "Consolas",  # 字体名称
            "font_size": 11,          # 字体大小
            "font_weight": "bold",    # 字体粗细
            "max_height": 220,        # 窗口最大高度
            "max_width": 460,         # 窗口最大宽度
            "initial_x": 0,           # 窗口预设位置X坐标
            "initial_y": 0,           # 窗口预设位置Y坐标
            "display_lines": 11,      # 显示行数
            "refresh_interval": 1000, # 刷新间隔(毫秒)
            "auto_wrap": False,         # 是否启用自动换行 - 主样式默认
            "transparent_mode": False, # 透明背景模式默认状态
            "click_through": False,   # 不可选中模式默认状态
            "author_style2": False,   # 仿BGI日志窗口样式默认状态
            "window_x": None,         # 窗口X坐标
            "window_y": None,          # 窗口Y坐标
            "dynamic_height": False   # 动态调整窗口高度
        }
        
        # 第二样式配置
        self.second_style_config = {
            "window_alpha": 0.7,
            "bg_color": "#000000",
            "normal_color": "#FFFFFF",
            "stale_color": "#FFFFFF",
            "high_freq_color": "#FFFFFF",
            "debug_color": "#808080",  # DBG级别日志颜色（灰色）
            "error_color": "#FF6B6B",  # ERR级别日志颜色（浅红色）
            "warning_color": "#FFD700", # WRN级别日志颜色（浅黄色）
            "status_header_color": "#00FF00",  # 第二样式的状态行颜色
            "task_header_color": "#00FFFF",   # 第二样式的任务行颜色
            "backup_msg_color": "#FFD700",    # 第二样式备份消息颜色
            "font_name": "Consolas",
            "font_size": 9,
            "font_weight": "bold",
            "max_width": 460,
            "max_height": 220,
            "display_lines": 12,
            "refresh_interval": 500,
            "auto_wrap": True  # 第二样式默认启用换行
        }
        
        self.config = self.default_config.copy()
        self.user_config = self.default_config.copy()  # 保存用户自定义配置
        self.log_path_configured = False  # 标记log_path是否已正确配置
        
        # 保存初始的日志路径配置（只在程序开始时加载一次）
        self.initial_log_path = ""
        self.initial_log_filename_prefix = "better-genshin-impact"
        self.initial_log_path_configured = False
        
        # 確保設定檔完整（自動補全缺失項目）
        self._ensure_config_complete()
        
        # 加载所有配置
        self.load_all_settings()
        
        # 保存初始的日志路径配置
        self.initial_log_path = self.config.get("log_path", "")
        self.initial_log_filename_prefix = self.config.get("log_filename_prefix", "better-genshin-impact")
        self.initial_log_path_configured = self.log_path_configured
        
        # 如果配置中启用了第二样式，则应用
        if self.config.get("author_style2", False):
            self.apply_second_style()
            
    def _ensure_config_complete(self):
        """確保 config.txt 完整：若不存在則寫入模板，若存在則補全缺失的配置項（排除 log_path 和 backup_enabled）"""
        if not self.config_file.exists():
            # 檔案不存在，直接寫入完整模板
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    f.write(self.DEFAULT_CONFIG_TEMPLATE)
                logging.info(f"已建立完整設定檔: {self.config_file}")
            except Exception as e:
                logging.error(f"建立設定檔失敗: {str(e)}")
            return

        # 檔案存在，需要補全缺失的項目
        # 步驟1：讀取現有檔案中所有有效的 key=value（跳過註解行、空行）
        existing_keys = set()
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key = line.split('=', 1)[0].strip()
                        existing_keys.add(key)
        except Exception as e:
            logging.error(f"讀取設定檔失敗: {str(e)}")
            return

        # 步驟2：定義所有應該存在的配置項（排除 log_path 和 backup_enabled）
        all_expected_keys = set()
        # 加入主樣式 default_config 中的所有 key（排除 log_path 和 backup_enabled）
        for key in self.default_config:
            if key not in ("log_path", "backup_enabled"):
                all_expected_keys.add(key)
        # 加入第二樣式中的所有 key（因為它們在模板中是以 style2_ 前綴存在）
        for key in self.second_style_config:
            all_expected_keys.add(f"style2_{key}")
        # 確保 backup_msg_color 和 style2_backup_msg_color 存在（已包含在上面的邏輯中）
        # 額外確保 window_x, window_y 等程式自動管理的項目也納入補全（它們在 default_config 中）
        # 但注意：backup_enabled 已經被排除

        # 找出缺失的 keys
        missing_keys = all_expected_keys - existing_keys
        if not missing_keys:
            logging.debug("設定檔完整，無需補全")
            return

        logging.info(f"發現缺失的配置項: {missing_keys}，將自動補全")

        # 步驟3：備份原檔案
        backup_file = self.config_file.with_suffix('.txt.bak')
        try:
            shutil.copy2(self.config_file, backup_file)
            logging.info(f"已備份原設定檔至: {backup_file}")
        except Exception as e:
            logging.warning(f"備份設定檔失敗: {str(e)}")

        # 步驟4：將缺失的項目追加到檔案末尾
        try:
            with open(self.config_file, 'a', encoding='utf-8') as f:
                f.write("\n\n# ===== 以下為程式自動補全的配置項 =====\n")
                for key in sorted(missing_keys):
                    # 取得預設值
                    if key.startswith("style2_"):
                        # 第二樣式 key，去掉前綴後從 second_style_config 取值
                        inner_key = key[7:]  # 移除 "style2_"
                        default_value = self.second_style_config.get(inner_key, "")
                    else:
                        # 主樣式 key
                        default_value = self.default_config.get(key, "")
                    # 寫入 key=預設值
                    f.write(f"{key}={default_value}\n")
            logging.info(f"已自動補全 {len(missing_keys)} 個配置項")
        except Exception as e:
            logging.error(f"補全設定檔失敗: {str(e)}")

    def load_all_settings(self):
        """加载所有配置 - 直接根据配置项名称读取，不依赖段落标记"""
        if not self.config_file.exists():
            logging.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过注释行和空行
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析配置行
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 处理第二样式配置（以style2_开头的配置项）
                        if key.startswith('style2_'):
                            self._process_second_style_config(key, value, line_num)
                        else:
                            # 处理普通配置
                            self._process_config_value(key, value, line_num)
            
            logging.info("所有配置加载成功")
            
        except Exception as e:
            logging.error(f"配置文件读取失败: {str(e)}")

    def _process_second_style_config(self, key, value, line_num):
        """处理第二样式配置"""
        # 移除style2_前缀
        clean_key = key[7:]  # 移除"style2_"前缀
        
        # 只处理第二样式配置中存在的键
        if clean_key in self.second_style_config:
            try:
                # 根据数据类型转换
                if clean_key in ["window_alpha"]:
                    self.second_style_config[clean_key] = float(value)
                elif clean_key in ["font_size", "max_width", "max_height", 
                                 "display_lines", "refresh_interval"]:
                    self.second_style_config[clean_key] = int(value)
                elif clean_key in ["auto_wrap"]:
                    self.second_style_config[clean_key] = value.lower() in ('true', '1', 'yes', 'on')
                else:
                    self.second_style_config[clean_key] = value
            except (ValueError, TypeError) as e:
                logging.warning(f"第二样式配置第{line_num}行: {clean_key} 配置值无效: {value} - {str(e)}")

    def _process_config_value(self, key, value, line_num):
        """处理配置值转换"""
        try:
            # 特殊处理log_path
            if key == "log_path":
                self._handle_log_path_config(value)
                return

            if key in ["window_x", "window_y"]:
                try:
                    if value and value.strip():
                        self.config[key] = int(value)
                        self.user_config[key] = int(value)
                    else:
                        self.config[key] = None
                        self.user_config[key] = None
                except (ValueError, TypeError):
                    self.config[key] = None
                    self.user_config[key] = None
                    logging.warning(f"第{line_num}行: {key} 轉換為整數失敗，設為 None")
                    
            elif key == "window_alpha":
                self.config[key] = float(value)
                self.user_config[key] = float(value)
                
            elif key in ["font_size", "max_width", "max_height", 
                    "initial_x", "initial_y", "display_lines", "refresh_interval"]:
                self.config[key] = int(value)
                self.user_config[key] = int(value)
                
            elif key in ["transparent_mode", "click_through", "author_style2", "skip_debug_log", "dynamic_height", "auto_wrap"]:
                self.config[key] = value.lower() in ('true', '1', 'yes', 'on')
                self.user_config[key] = value.lower() in ('true', '1', 'yes', 'on')
                
            elif key in ["backup_interval", "backup_keep_days", "backup_align_to_clock"]:
                if key == "backup_align_to_clock":
                    self.config[key] = value.lower() in ('true', '1', 'yes', 'on')
                    self.user_config[key] = self.config[key]
                else:
                    self.config[key] = int(value)
                    self.user_config[key] = int(value)
            
            elif key in ["backup_debug", "backup_enabled"]:
                self.config[key] = value.lower() in ('true', '1', 'yes', 'on')
                self.user_config[key] = value.lower() in ('true', '1', 'yes', 'on')
                
            elif key == "backup_path":
                # 處理備份路徑
                value_stripped = value.strip() if value else ""
                self.config[key] = value_stripped
                self.user_config[key] = value_stripped
                
                # 如果備份路徑不為空，則自動啟用備份功能
                if value_stripped:
                    self.config["backup_enabled"] = True
                    self.user_config["backup_enabled"] = True
                else:
                    self.config["backup_enabled"] = False
                    self.user_config["backup_enabled"] = False
            elif key == "backup_msg_color":
                self.config[key] = value
                self.user_config[key] = value
            else:
                self.config[key] = value
                self.user_config[key] = value
                
        except (ValueError, TypeError) as e:
            logging.warning(f"第{line_num}行: {key} 配置值无效: {value} - {str(e)}")
            # 使用默认值
            if key in self.default_config:
                self.config[key] = self.default_config[key]
                self.user_config[key] = self.default_config[key]

    def _handle_log_path_config(self, value):
        """处理log_path配置"""
        if value:  # 只有非空值才视为有效配置
            self.log_path_configured = True
            self.config["log_path"] = value
            self.user_config["log_path"] = value
            logging.info(f"找到log_path配置: {value}")
        else:
            self.log_path_configured = False
            logging.warning("log_path配置为空")

    def apply_second_style(self):
        """应用第二样式"""
        # 保存当前的log_filename_prefix、窗口位置和skip_debug_log
        current_log_prefix = self.config.get("log_filename_prefix", "better-genshin-impact")
        current_window_x = self.config.get("window_x", 0)
        current_window_y = self.config.get("window_y", 0)
        current_skip_debug_log = self.config.get("skip_debug_log", False)
        
        # 应用第二样式配置
        self.config.update(self.second_style_config)
        
        # 恢复log_filename_prefix、窗口位置和skip_debug_log
        self.config["log_filename_prefix"] = current_log_prefix
        self.config["window_x"] = current_window_x
        self.config["window_y"] = current_window_y
        self.config["log_path"] = self.user_config["log_path"]
        self.config["skip_debug_log"] = current_skip_debug_log
        
        # 设置第二样式状态
        self.config["author_style2"] = True
        
        logging.info("应用第二样式")
        
        
    
    def restore_user_style(self):
        """恢复用户自定义样式"""
        # 保存当前的窗口位置、功能状态和skip_debug_log
        current_window_x = self.config.get("window_x", 0)
        current_window_y = self.config.get("window_y", 0)
        current_transparent_mode = self.config.get("transparent_mode", False)
        current_click_through = self.config.get("click_through", False)
        current_skip_debug_log = self.config.get("skip_debug_log", False)
        
        # 使用 update 方法更新配置，而不是完全替换对象
        self.config.update(self.user_config)
        
        # 恢复窗口位置和功能状态（这些应该在切换样式时保持不变）
        self.config["window_x"] = current_window_x
        self.config["window_y"] = current_window_y
        self.config["transparent_mode"] = current_transparent_mode
        self.config["click_through"] = current_click_through
        self.config["skip_debug_log"] = current_skip_debug_log
        self.config["author_style2"] = False  # 明确设置为False
        
        # 同时更新user_config中的这些项，确保一致性
        self.user_config["window_x"] = current_window_x
        self.user_config["window_y"] = current_window_y
        self.user_config["transparent_mode"] = current_transparent_mode
        self.user_config["click_through"] = current_click_through
        self.user_config["skip_debug_log"] = current_skip_debug_log
        self.user_config["author_style2"] = False
        
        logging.info("恢复用户自定义样式 - 已应用用户config.txt配置")

    def save_window_state(self, x, y, transparent_mode=False, click_through=False, author_style2=False):
        """保存窗口位置和状态到config.txt"""
        try:
            # 读取现有配置文件内容
            config_lines = []
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_lines = f.readlines()
            
            # 要更新的配置项
            updates = {
                "window_x": str(x),
                "window_y": str(y),
                "transparent_mode": str(transparent_mode).lower(),
                "click_through": str(click_through).lower(),
                "author_style2": str(author_style2).lower()
            }
            
            # 构建新的配置内容
            new_lines = []
            found_keys = set()
            
            for line in config_lines:
                stripped_line = line.strip()
                
                # 处理注释行和空行
                if not stripped_line or stripped_line.startswith('#'):
                    new_lines.append(line)
                    continue
                
                # 解析配置行
                if '=' in stripped_line:
                    key, original_value = stripped_line.split('=', 1)
                    key = key.strip()
                    
                    if key in updates:
                        # 找到原始行中的注释部分
                        line_without_newline = line.rstrip('\n')
                        if '#' in line_without_newline:
                            # 找到注释开始位置（在等号之后）
                            hash_index = line_without_newline.find('#', equal_index)
                            equal_index = line_without_newline.find('=')
                            if hash_index > equal_index:
                                # 注释在等号后面，保留注释
                                new_line = line_without_newline[:equal_index+1] + updates[key] + line_without_newline[hash_index:] + '\n'
                            else:
                                # 注释在等号前面，不应该发生
                                new_line = line_without_newline[:equal_index+1] + updates[key] + '\n'
                        else:
                            # 没有注释
                            equal_index = line_without_newline.find('=')
                            new_line = line_without_newline[:equal_index+1] + updates[key] + '\n'
                        
                        new_lines.append(new_line)
                        found_keys.add(key)
                    else:
                        # 保留其他配置项
                        new_lines.append(line)
                else:
                    # 保留无法解析的行
                    new_lines.append(line)
            
            # 添加未找到的配置项（放在文件末尾）
            for key, value in updates.items():
                if key not in found_keys:
                    new_lines.append(f"{key}={value}\n")
            
            # 写回配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # 更新内存中的配置
            self.config["window_x"] = x
            self.config["window_y"] = y
            self.config["transparent_mode"] = transparent_mode
            self.config["click_through"] = click_through
            self.config["author_style2"] = author_style2
            
            logging.info(f"保存窗口位置到config.txt: ({x}, {y}), 透明模式: {transparent_mode}, 不可选中模式: {click_through}, 仿BGI日志窗口样式: {author_style2}")
            
        except Exception as e:
            logging.error(f"保存窗口位置到config.txt失败: {str(e)}")
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def is_log_path_configured(self):
        """检查log_path是否已正确配置"""
        return self.log_path_configured
    
    def get_initial_log_config(self):
        """获取初始的日志配置（只在程序开始时加载一次）"""
        return {
            "log_path": self.initial_log_path,
            "log_filename_prefix": self.initial_log_filename_prefix,
            "log_path_configured": self.initial_log_path_configured
        }

class GlobalShortcutManager:
    """全局快捷键管理器"""
    
    def __init__(self, root_window):
        self.root = root_window
        self.event_queue = queue.Queue()
        self.listening = False
        self.thread = None
        self.hotkeys_registered = False
        self.last_health_check = time.time()
        self.health_check_interval = 30  # 每30秒检查一次健康状态
        self._lock = threading.Lock()  # 新增
        # 使用全局的 keyboard 模組
        self.keyboard_module = KEYBOARD_MODULE
        
    def start_listening(self):
        """启动全局快捷键监听"""
        with self._lock:
            if self.listening:  # 防止重複啟動
                return
            
        if not KEYBOARD_AVAILABLE:
            logging.warning("keyboard 库不可用，跳过全局快捷键初始化")
            return
            
        try:
            # 确保先清理可能的热键
            self._safe_unhook_all()
            
            self.listening = True
            self.thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.thread.start()
            
            # 在主线程中处理事件
            self.root.after(100, self._process_events)
            # 新增健康检查定时器
            self.root.after(30000, self._health_check)  # 30秒后开始健康检查
            logging.info("全局快捷键监听已启动")
        except Exception as e:
            logging.error(f"启动全局快捷键监听失败: {str(e)}")
            
    def _health_check(self):
        """健康检查 - 定期检查快捷键是否正常工作"""
        if not self.listening:
            return
            
        try:
            current_time = time.time()
            # 每30秒检查一次
            if current_time - self.last_health_check >= self.health_check_interval:
                if not self.hotkeys_registered:
                    logging.warning("健康检查: 热键未注册，尝试重新注册")
                    self._safe_register_hotkeys()
                else:
                    logging.debug("健康检查: 快捷键状态正常")
                
                self.last_health_check = current_time
            
            # 继续健康检查
            if self.listening:
                self.root.after(30000, self._health_check)
                
        except Exception as e:
            logging.error(f"健康检查失败: {str(e)}")
            if self.listening:
                self.root.after(30000, self._health_check)
    
    def _safe_unhook_all(self):
        """安全地清理所有热键"""
        if not KEYBOARD_AVAILABLE or self.keyboard_module is None:
            return
        try:
            self.keyboard_module.unhook_all()
            self.hotkeys_registered = False
            time.sleep(0.1)  # 短暂延迟确保清理完成
        except Exception as e:
            logging.warning(f"清理热键时出现警告: {str(e)}")
            
    def _safe_register_hotkeys(self):
        """安全注册热键 - 增强错误处理"""
        if not KEYBOARD_AVAILABLE:
            return False
            
        try:
            # 先清理可能冲突的热键
            self._safe_unhook_all()
            
            # 短暂延迟确保系统稳定
            time.sleep(0.2)
            
            # 尝试注册全局快捷键
            try:
                keyboard.add_hotkey('alt+p', self._create_event_callback('close'), suppress=True)
                keyboard.add_hotkey('alt+u', self._create_event_callback('reset_position'), suppress=True)
                keyboard.add_hotkey('alt+i', self._create_event_callback('toggle_transparent'), suppress=True)
                keyboard.add_hotkey('alt+n', self._create_event_callback('toggle_click_through'), suppress=True)
                keyboard.add_hotkey('alt+k', self._create_event_callback('toggle_second_style'), suppress=True)
                keyboard.add_hotkey('alt+b', self._create_event_callback('backup'), suppress=True)  # 新增 Alt+B 立即备份
                
                self.hotkeys_registered = True
                logging.info("全局快捷键注册完成: Alt+P(关闭), Alt+U(重置位置), Alt+I(透明模式), Alt+N(不可选中), Alt+K(第二样式), Alt+B(立即备份), P(隐藏/显示)")
                return True
                
            except Exception as register_error:
                logging.warning(f"全局快捷键注册失败（可能是安全软件阻止），回退到窗口内快捷键: {str(register_error)}")
                # 回退到窗口内快捷键
                self._fallback_to_window_hotkeys()
                return False
            
        except Exception as e:
            logging.error(f"注册全局快捷键失败: {str(e)}")
            self.hotkeys_registered = False
            # 即使失败也尝试回退
            self._fallback_to_window_hotkeys()
            return False
    
    def _fallback_to_window_hotkeys(self):
        """回退到窗口内快捷键"""
        logging.info("使用窗口内快捷键替代全局快捷键")
        # 这里实际上不需要做太多，因为FloatingLogViewer会自己设置窗口内快捷键
        # 主要是在状态日志中表明正在使用备用方案
        self.hotkeys_registered = False  # 标记为未注册成功
    
    def _create_event_callback(self, event_type):
        """创建事件回调函数 - 避免lambda函数的内存问题"""
        def callback():
            self._queue_event(event_type)
        return callback
    
    def _listen_loop(self):
        """后台监听循环 - 增强稳定性"""
        retry_count = 0
        max_retries = 5  # 增加最大重试次数
        base_retry_delay = 2
        last_success_time = time.time()
        
        while self.listening and retry_count < max_retries:
            try:
                # 注册热键
                success = self._safe_register_hotkeys()
                
                if not success:
                    logging.error(f"无法注册热键，重试 {retry_count + 1}/{max_retries}")
                    retry_count += 1
                    # 指数退避策略
                    delay = base_retry_delay * (2 ** (retry_count - 1))
                    time.sleep(min(delay, 30))  # 最大延迟30秒
                    continue
                
                # 重置重试计数和计时
                retry_count = 0
                last_success_time = time.time()
                
                # 保持线程运行，定期检查状态
                while self.listening:
                    # 检查热键是否仍然有效
                    if not self.hotkeys_registered:
                        logging.warning("热键可能已失效，尝试重新注册")
                        break
                    
                    # 检查是否长时间没有成功事件（可能表示热键失效）
                    if time.time() - last_success_time > 120:  # 2分钟没有成功事件
                        logging.warning("长时间没有检测到快捷键事件，可能已失效")
                        break
                        
                    time.sleep(1)  # 减少CPU使用
                    
            except Exception as e:
                logging.error(f"全局快捷键监听循环异常: {str(e)}")
                retry_count += 1
                delay = base_retry_delay * (2 ** (retry_count - 1))
                time.sleep(min(delay, 30))
        
        if retry_count >= max_retries:
            logging.error("全局快捷键监听达到最大重试次数，已停止")
            # 尝试最后一次恢复
            self._attempt_recovery()
        else:
            logging.info("全局快捷键监听正常退出")
            
    def _attempt_recovery(self):
        """尝试恢复快捷键功能"""
        logging.info("尝试恢复快捷键功能...")
        try:
            self._safe_unhook_all()
            time.sleep(1)
            success = self._safe_register_hotkeys()
            if success:
                logging.info("快捷键功能恢复成功")
                # 重置重试计数
                self.listening = True
                # 重新启动监听线程
                self.thread = threading.Thread(target=self._listen_loop, daemon=True)
                self.thread.start()
            else:
                logging.error("快捷键功能恢复失败")
        except Exception as e:
            logging.error(f"恢复快捷键功能时发生错误: {str(e)}")
    
    def _queue_event(self, event_type):
        """将事件放入队列 - 增强版本"""
        try:
            current_time = time.time()
            # 限制事件频率 - 防止过快连续触发
            if hasattr(self, '_last_event_time'):
                time_since_last = current_time - self._last_event_time
                if time_since_last < 0.1:  # 最少100毫秒间隔
                    return
            
            self._last_event_time = current_time
            
            if self.event_queue.qsize() < 20:  # 增加队列容量
                self.event_queue.put(event_type)
                logging.debug(f"事件已加入队列: {event_type}")
            else:
                logging.warning("事件队列已满，丢弃事件")
        except Exception as e:
            logging.error(f"事件队列操作失败: {str(e)}")
    
    def _process_events(self):
        """在主线程中处理快捷键事件 - 增强错误处理"""
        try:
            processed_count = 0
            max_events_per_cycle = 10  # 增加每次处理的事件数量
            
            while processed_count < max_events_per_cycle:
                try:
                    event = self.event_queue.get_nowait()
                    self._handle_event(event)
                    processed_count += 1
                except queue.Empty:
                    break
                    
        except Exception as e:
            logging.error(f"处理事件队列时发生错误: {str(e)}")
            # 不退出，继续处理
        
        # 继续检查事件
        if self.listening:
            self.root.after(50, self._process_events)
    
    def _handle_event(self, event):
        """处理具体的事件 - 增强错误处理"""
        try:
            logging.info(f"处理快捷键事件: {event}")
            
            # 检查主窗口是否仍然有效
            if not self.root or not hasattr(self.root, 'winfo_exists') or not self.root.winfo_exists():
                logging.warning("主窗口已销毁，停止处理事件")
                self.stop_listening()
                return
            
            if event == 'close':
                self.root._on_close_shortcut()
            elif event == 'reset_position':
                self.root._on_reset_position_shortcut()
            elif event == 'toggle_transparent':
                self.root._on_transparent_toggle_shortcut()
            elif event == 'toggle_click_through':
                self.root._on_click_through_toggle_shortcut()
            elif event == 'toggle_second_style':
                self.root._on_second_style_toggle_shortcut()
            elif event == 'toggle_visibility':  # 新增：处理隐藏/显示事件
                self.root._on_toggle_visibility_shortcut()
            elif event == 'backup':  # 新增：处理立即备份事件
                self.root._on_backup_shortcut()
                
        except Exception as e:
            logging.error(f"处理快捷键事件失败: {str(e)}")
            # 不重新抛出异常，防止事件处理循环中断
    
    def stop_listening(self):
        """停止监听 - 增强版本"""
        with self._lock:
            if not self.listening:
                return
        self.listening = False
        self._safe_unhook_all()
        logging.info("全局快捷键监听已停止")

class SmartLogReader:
    def __init__(self, log_dir, log_filename_prefix, log_path_configured, display_lines=11, 
                 skip_debug_log=False, dynamic_height=False, auto_wrap=False, 
                 max_width=460, font_config=None, backup_path="", backup_interval=60, 
                 backup_debug=False, backup_enabled=False, backup_keep_days=10,
                 backup_align_to_clock=False):
        """智能日志读取器 - 负责读取和解析原神日志文件"""
        # 在初始化时验证log_dir的有效性
        if not log_path_configured:
            self.log_dir = None
            self.log_path_valid = False
        elif not log_dir or not log_dir.strip():
            self.log_dir = None
            self.log_path_valid = False
        else:
            self.log_dir = Path(log_dir)
            self.log_path_valid = self._check_log_path()
        
        self.log_filename_prefix = log_filename_prefix
        self.log_path_configured = log_path_configured  # 接收配置狀態
        self.skip_debug_log = skip_debug_log  # 是否跳过调试日志
        
        # 备份配置
        self.backup_enabled = backup_enabled and backup_path and backup_path.strip()
        self.backup_path = Path(backup_path.strip()) if (backup_path and backup_path.strip()) else None
        self.backup_interval = backup_interval  # 分鐘
        self.backup_debug = backup_debug
        self.backup_keep_days = backup_keep_days  # 保留天數
        self.backup_align_to_clock = backup_align_to_clock  # 保存
        
        
        # 备份状态跟踪
        self.last_backup_time = 0
        self.last_backup_date = None
        self.backup_timer = None
        self.backup_thread = None
        
        # 新增：换行相关配置
        self.auto_wrap = auto_wrap
        self.max_width = max_width
        self.font_config = font_config  # 字体配置
        
        # 字体缓存用于宽度计算
        self._font_cache = None
        self._last_font_config = None
        
        # 新增：讀取行數（display_lines*2(其中1行為空格)行用於分析）
        # 优化：当跳过调试日志时，需要读取更多行以确保有足够的非调试日志显示
        self.read_lines = max(display_lines * 2, 100) if skip_debug_log else display_lines * 3
        self.display_lines = display_lines  # 保存顯示行數
        self.dynamic_height=dynamic_height
        
        self.current_date = datetime.now().date()  # 当前日志文件日期
        self._position = 0  # 文件读取位置
        
        self._last_valid_content = deque(maxlen=100)  # 内容缓存，限制100行
        self._current_file = None     # 当前日志文件路径
        self._current_file_mtime = 0  # 当前文件修改时间
        
        # 状态信息
        self.current_task = "无当前任务"
        self.current_config = "无激活配置组"
        
        # 任務進度信息 - 分開處理
        self.current_progress = "0/0"  # 任務進度
        self.current_config_progress = "0/0"  # 配置組進度 - 新增
        self.task_progress = {}  # 任務進度緩存
        
        # 任务切换频率监测
        self.task_switch_times = deque(maxlen=10)  # 存储最近10次任务切换时间
        self.high_frequency_warning = False  # 高频切换警告状态
        self.high_frequency_start = None     # 高频状态开始时间

        # 任务检测正则表达式 - 匹配不同类型的任务
        self.task_patterns = {
            # "JS脚本": re.compile(r'→ 开始执行JS脚本: "(.+?)"'),
            "JS脚本": re.compile(r'→ 开始执行JS脚本: "([^"]+)"'),
            "配置文件": re.compile(r'assets/(.+?\.json)'),
            # "地图任务": re.compile(r'→ 开始执行(?:地图|路径)追踪任务: "(.+?)"'),
            "地图任务": re.compile(r'→ 开始执行(?:地图|路径)追踪任务: "([^"]+)"'),
            "键鼠脚本": re.compile(r'→ 开始执行键鼠脚本: "([^"]+)"'),
        }
        
        # 配置组正则表达式
        self.config_pattern = re.compile(
            r'配置组\s*"(.+?)"\s*(?:加载完成|执行结束|开始执行|共\d+个脚本)'
        )
        
        # 日志格式处理正则表达式 - 提取时间戳、级别和消息
        self.log_format_pattern = re.compile(
            r'^(\[\d{2}:\d{2}:\d{2}\.\d{3}\])\s+\[(\w+)\]\s+[\w\.]+\s*(.*)$'
        )
        
        # 进度信息正则表达式
        self.progress_patterns = {
            "任务开始进度": re.compile(r'\[(\d+)/(\d+)\][^"]*"([^"]+)":\s*开始执行'),
            "当前进度": re.compile(r'当前进度：\s*(\d+)/(\d+)\s*\([^)]+\)'),
            "購買进度": re.compile(r'当前进度：\s*(\d+)/(\d+)'),
            # "采集CD进度": re.compile(r'当前进度：路径组[^为]*为第\s*(\d+)/(\d+)\s*个'),
            # 采集CD进度(2.10.0)
            # "采集CD进度": re.compile(r'当前进度：.*?第\s*(\d+)/(\d+)\s*个'),
            # 采集CD进度(3.0.2)
            "采集CD进度": re.compile(r'(?:当前进度：)?执行路线.*?第\s*(\d+)/(\d+)\s*个'),
            
            "组任务进度": re.compile(r'开始处理第\s*(\d+)\s*组第\s*(\d+)/(\d+)\s*个([^\.]+\.json)'),
            "垂钓点进度": re.compile(r'当前垂钓点:[^(]+\(进度:\s*(\d+)/(\d+)\)'),  # 垂钓点进度
            "产出进度": re.compile(r'当前产出(?:（.*?）)?：\s*(\d+)(?:/(\d+))?\s*个'),
            "运行时间进度": re.compile(r'当前运行时间：([\d.]+)/(\d+)分钟'),  # 保持不变，只匹配有总时间的情况
            # 新增：循环执行进度格式 - 匹配 "正在执行 夏栎木 第 9/56 次循环"
            "循环执行进度": re.compile(r'正在执行\s+([^\s]+)\s+第\s*(\d+)/(\d+)\s*次循环'),
            "F2": re.compile(r'当前进度：\s*=+\s*第\s*(\d+)/(\d+)\s*轮\s*=+'),
            "配置组任务执行进度": re.compile(r'(?:配置组任务执行|一条龙任务执行)[：:]\s*(\d+)/(\d+)'),
            # 新增狗粮进度
            "狗粮进度": re.compile(r'(?:当前进度：)?.*?为.+?第\s*(\d+)/(\d+)\s*个'),
        }

        # 如果启用了备份且备份路径有效，初始化备份功能
        if self.backup_path:
            self._init_backup()
        self._update_log_file()  # 初始化日志文件

    def _check_log_path(self):
        """检查日志路径是否存在且有效"""
        if not self.log_dir:
            return False
            
        try:
            # 检查路径存在性
            if not self.log_dir.exists():
                logging.warning(f"日志目录不存在: {self.log_dir}")
                # 尝试创建目录
                try:
                    self.log_dir.mkdir(parents=True, exist_ok=True)
                    logging.info(f"已创建日志目录: {self.log_dir}")
                except (PermissionError, OSError) as e:
                    logging.error(f"创建日志目录失败: {str(e)}")
                    return False
                except Exception as e:
                    logging.error(f"创建日志目录时发生未知错误: {str(e)}")
                    return False

            # 检查是否是目录（不是文件）
            if not self.log_dir.is_dir():
                logging.warning(f"日志路径不是目录: {self.log_dir}")
                return False
                
            # 检查目录可读性
            if not os.access(str(self.log_dir), os.R_OK):
                logging.warning(f"没有读取日志目录的权限: {self.log_dir}")
                return False

            return True

        except PermissionError as e:
            logging.error(f"权限错误: {str(e)}")
            return False
        except OSError as e:
            logging.error(f"操作系统错误: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"检查日志路径时发生未知错误: {str(e)}")
            return False

    def _generate_log_patterns(self, date=None):
        """生成所有可能的日志文件模式 - 支持带序号的文件"""
        target_date = date or self.current_date
        date_str = target_date.strftime('%Y%m%d')
        
        patterns = [
            # 基础模式: better-genshin-impactYYYYMMDD.log
            self.log_dir / f"{self.log_filename_prefix}{date_str}.log",
            # 带序号模式: better-genshin-impactYYYYMMDD_00N.log
            self.log_dir / f"{self.log_filename_prefix}{date_str}_*.log"
        ]
        
        return patterns

    def _find_active_log_file(self):
        """查找当前活跃的日志文件（最近被修改的）"""
        if not self.log_path_valid:
            return None
            
        patterns = self._generate_log_patterns()
        candidate_files = []
        
        # 收集所有匹配的日志文件
        for pattern in patterns:
            if '*' in str(pattern):
                # 使用通配符匹配带序号的文件
                import glob
                matches = glob.glob(str(pattern))
                candidate_files.extend([Path(match) for match in matches])
            else:
                # 处理固定文件名
                if pattern.exists():
                    candidate_files.append(pattern)
        
        if not candidate_files:
            return None
            
        # 优先选择当前日期的文件，然后按修改时间排序
        current_date_str = self.current_date.strftime('%Y%m%d')
        current_date_files = [f for f in candidate_files if current_date_str in f.name]
        
        if current_date_files:
            # 在当前日期文件中选择最新的
            return max(current_date_files, key=lambda f: f.stat().st_mtime)
        else:
            # 如果没有当前日期的，选择所有文件中最新的
            return max(candidate_files, key=lambda f: f.stat().st_mtime)
        
    def _update_log_file(self):
        """安全更新日志文件 - 处理日期切换和文件轮换"""
        if not self.log_path_valid:
            return
            
        new_file = self._find_active_log_file()
        
        # 如果没有找到日志文件，创建默认的
        if new_file is None:
            default_patterns = self._generate_log_patterns()
            new_file = default_patterns[0]
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                new_file.touch()  # 创建空文件
                logging.info(f"创建新日志文件: {new_file}")
            except Exception as e:
                logging.error(f"文件创建失败: {str(e)}")
        
        # 检查是否需要切换文件
        if new_file == self._current_file:
            # 检查当前文件是否已被更新
            if self._current_file.exists():
                current_mtime = self._current_file.stat().st_mtime
                if current_mtime == self._current_file_mtime:
                    return  # 文件未更新，无需处理
                else:
                    self._current_file_mtime = current_mtime
            return
        
        # 切换到新文件，重置状态
        self._current_file = new_file
        self._position = 0
        self._last_valid_content.clear()
        
        if self._current_file.exists():
            self._current_file_mtime = self._current_file.stat().st_mtime

        logging.info(f"切换到日志文件: {new_file}")

    def _detect_date_change(self):
        """精确检测日期变更 - 处理跨天的日志文件切换"""
        today = datetime.now().date()
        date_changed = False
        
        if today != self.current_date:
            logging.info(f"检测到日期变更 {self.current_date} → {today}")
            
            try:
                # 备份前一天的文件
                self._check_and_backup_previous_day()
            except Exception as e:
                logging.error(f"备份前一天文件失败，但继续处理日期变更: {str(e)}")
            
            # 更新当前日期
            self.current_date = today
            self._update_log_file()
            date_changed = True
            
        return date_changed

    def _merge_log_lines(self, lines):
        """合并跨行的日志条目 - 处理异常堆栈等多行日志"""
        merged_lines = []
        current_entry = None
        
        for line in lines:
            # 检测是否是新的日志条目开头（以时间戳开头）
            if self._is_log_start(line):
                # 保存前一个条目
                if current_entry is not None:
                    merged_lines.append(current_entry)
                # 开始新条目
                current_entry = line
            else:
                # 追加到当前条目（异常信息等）
                if current_entry is not None:
                    current_entry += " " + line.strip()
        
        # 添加最后一个条目
        if current_entry is not None:
            merged_lines.append(current_entry)
            
        return merged_lines

    def _is_log_start(self, line):
        """检测行是否以时间戳开头 - 判断是否为新的日志条目"""
        return bool(re.match(r'\[\d{2}:\d{2}:\d{2}\.\d{3}\]', line))

    def _tail_lines(self, lines=50):
        """高效获取文件尾部内容 - 确保读取完整的行"""
        if not self.log_path_valid or not self._current_file or not self._current_file.exists():
            return None

        try:
            with open(self._current_file, 'rb') as f:
                f.seek(0, 2)  # 移动到文件末尾
                file_size = f.tell()
                block_size = 1024
                buffer = b''
                lines_found = 0
                
                # 从文件末尾向前读取，直到收集到足够的行
                while lines_found < lines and file_size > 0:
                    # 计算要读取的位置和大小
                    read_size = min(block_size, file_size)
                    file_size -= read_size
                    f.seek(file_size)
                    
                    # 读取数据并添加到缓冲区前面
                    chunk = f.read(read_size)
                    buffer = chunk + buffer
                    
                    # 计算缓冲区中的行数
                    lines_found = buffer.count(b'\n')
                    
                    # 如果缓冲区太长，丢弃最早的部分
                    if lines_found > lines * 2:  # 保留一些额外行作为缓冲
                        # 找到第N个换行符之后的位置
                        lines_to_keep = lines * 2
                        pos = 0
                        for _ in range(lines_to_keep):
                            pos = buffer.find(b'\n', pos) + 1
                            if pos == 0:  # 没找到
                                break
                        if pos > 0:
                            buffer = buffer[pos:]

                # 解码并分割为行
                text = buffer.decode('utf-8', 'ignore')
                all_lines = text.splitlines()
                
                # 返回最后lines行，如果不足则返回全部
                return all_lines[-min(lines, len(all_lines)):]
                
        except Exception as e:
            logging.error(f"文件读取错误: {str(e)}")
            return None

    def _filter_debug_logs(self, lines):
        """过滤调试日志 - 跳过包含DBG]的行"""
        if not self.skip_debug_log:
            return lines
            
        filtered_lines = []
        for line in lines:
            # 跳过包含DBG]的调试日志行
            if 'DBG]' not in line:
                filtered_lines.append(line)
        
        return filtered_lines

    def _detect_task_switching(self, new_task):
        """检测任务切换频率 - 只在实际任务名称变化时记录（修复版本）"""
        now = time.time()
        
        # 获取任务名称的基础部分（去除进度信息）
        def get_base_task_name(task_str):
            """从任务字符串中提取基础任务名称（去除进度部分）"""
            if "无当前任务" in task_str:
                return "无当前任务"
            
            # 如果任务字符串包含进度格式，提取前面的部分
            progress_patterns = [
                r'(.+?) \[\d+/\d+\]',
                r'(.+?) \(\d+/\d+\)',
                r'(.+?) \d+/\d+个',
                r'(.+?) 第 \d+/\d+ 次循环'
            ]
            
            for pattern in progress_patterns:
                match = re.match(pattern, task_str)
                if match:
                    return match.group(1).strip()
            
            return task_str
        
        # 只在任务实际变化时记录（排除进度更新）
        new_base_task = get_base_task_name(new_task)
        current_base_task = get_base_task_name(self.current_task)
            
        # 新增：忽略从"无当前任务"到实际任务的切换（这是正常开始）
        # 也忽略从实际任务到"无当前任务"的切换（这是正常结束）
        should_record = False
        if (new_base_task != current_base_task and 
            new_base_task != "无当前任务" and 
            current_base_task != "无当前任务"):
            # 只有从一个实际任务切换到另一个实际任务才记录
            should_record = True
            switch_type = "任务切换"
        elif new_base_task == "无当前任务" and current_base_task != "无当前任务":
            # 任务正常结束，不记录为切换
            switch_type = "任务结束"
            logging.debug(f"任务正常结束: {current_base_task} -> 无当前任务 (不计入切换)")
        elif new_base_task != "无当前任务" and current_base_task == "无当前任务":
            # 任务正常开始，不记录为切换
            switch_type = "任务开始"
            logging.debug(f"任务正常开始: 无当前任务 -> {new_base_task} (不计入切换)")
        else:
            # 其他情况（如进度更新）
            switch_type = "进度更新"
        
        # 只在应该记录时才记录切换
        if should_record:
            # 记录详细的任务切换信息
            task_switch_info = f"{switch_type}: {current_base_task} -> {new_base_task}"
            
            # 如果有进度信息，也一并记录
            if new_task != new_base_task:
                task_switch_info += f" (进度: {new_task})"
            
            logging.info(task_switch_info)
            self.task_switch_times.append(now)
            
            # 清理超过1分钟的记录
            while self.task_switch_times and (now - self.task_switch_times[0] > 60):
                removed_time = self.task_switch_times.popleft()
                logging.debug(f"移除过期切换记录: {removed_time}")
            
            current_switches = len(self.task_switch_times)
            # 记录当前切换统计
            if current_switches > 0:
                logging.debug(f"切换统计: 当前{current_switches}次/分钟")
            
            # 检查1分钟内是否超过5次切换
            if current_switches >= 5:
                if not self.high_frequency_warning:
                    self.high_frequency_warning = True
                    self.high_frequency_start = now
                    logging.warning(f"⚠️ 任务切换过于频繁！检测到 {current_switches} 次任务切换/分钟")
                    # 输出详细的切换记录
                    switch_details = []
                    for i, switch_time in enumerate(self.task_switch_times):
                        switch_details.append(f"{i+1}. {datetime.fromtimestamp(switch_time).strftime('%H:%M:%S')}")
                    logging.debug(f"详细切换记录:\n" + "\n".join(switch_details))
                else:
                    # 如果已经处于高频警告状态，只记录增加次数
                    logging.debug(f"继续高频切换，当前 {current_switches} 次/分钟")
            else:
                # 只有当切换次数真正减少时才取消警告
                if self.high_frequency_warning and current_switches < 4:
                    self.high_frequency_warning = False
                    logging.info("✅ 高频任务切换状态结束")
                    
            # 输出当前切换队列状态
            logging.debug(f"切换队列状态: {current_switches} 次记录")
        # 检查高频状态是否已结束（超过90秒无新警告）
        if self.high_frequency_warning and (now - self.high_frequency_start > 90):
            self.high_frequency_warning = False
            logging.info("⏰ 高频任务切换状态超时自动结束")
            
        # 记录基础任务名称用于调试
        logging.debug(f"任务基础名称: 当前='{current_base_task}', 新='{new_base_task}', 类型={switch_type}")
    
    #  兼容BGI_0.63.0版本新日志格式
    def _format_log_line(self, line):
        """兼容新旧日志格式，统一显示为 [HH:MM:SS 级别] 消息"""
        if not isinstance(line, str):
            try:
                line = str(line)
            except Exception as e:
                logging.warning(f"无法格式化非字符串日志行: {type(line)}，错误: {str(e)}")
                return str(line)

        # 新格式：时间 级别 [额外标识] 类名 消息
        new_pattern = re.compile(
            r'^(\[\d{2}:\d{2}:\d{2}\.\d{3}\])\s+\[(\w+)\]\s+\[[^\]]+\]\s+[\w.]+\s+(.*)$'
        )
        # 旧格式：时间 级别 类名 消息
        old_pattern = re.compile(
            r'^(\[\d{2}:\d{2}:\d{2}\.\d{3}\])\s+\[(\w+)\]\s+[\w.]+\s+(.*)$'
        )

        # 依次尝试匹配
        match = new_pattern.match(line)
        if not match:
            match = old_pattern.match(line)

        if match:
            timestamp = match.group(1)   # 如 [01:34:32.678]
            level = match.group(2)       # 如 INF 或 DBG
            message = match.group(3)  or ""  # 确保消息不为None

            # 去掉毫秒，只保留 HH:MM:SS
            time_part = timestamp[:9]  # 截取 [HH:MM:SS
            return f"{time_part} {level}] {message}"
        else:
            # 无法匹配时原样返回（如续行或非标准行）
            return line
    
    def _extract_progress_info(self, line):
        """从日志行中提取进度信息 - 分開處理配置組進度和任務進度"""
        # 優先匹配配置組進度
        config_progress_pattern = re.compile(r'(?:一条龙任务执行|配置组任务执行)[：:]\s*(\d+)/(\d+)')
        config_match = config_progress_pattern.search(line)
        
        if config_match:
            # 這是配置組進度
            current, total = config_match.groups()
            return {
                "type": "config",  # 標記為配置組進度
                "value": f"{current}/{total}"
            }
        
        # 然後匹配其他任務進度
        for progress_type, pattern in self.progress_patterns.items():
            # 跳過配置组任务执行进度，因為已經在上面處理過了
            if progress_type == "配置组任务执行进度":
                continue
                
            match = pattern.search(line)
            if match:
                groups = match.groups()
                try:
                    if progress_type == "任务开始进度" and len(groups) >= 3:
                        current, total, task_name = groups[:3]
                        # 缓存这个任务的进度信息
                        self.task_progress[task_name] = f"{current}/{total}"
                        return {
                            "type": "task",  # 標記為任務進度
                            "value": f"{current}/{total}"
                        }
                    elif progress_type == "当前进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                    elif progress_type == "購買进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                    elif progress_type == "采集CD进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                    elif progress_type == "组任务进度" and len(groups) >= 4:
                        group_num, current, total, task_name = groups[:4]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                    #垂钓点进度格式
                    elif progress_type == "垂钓点进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                    # 新增：循环执行进度格式
                    elif progress_type == "循环执行进度" and len(groups) >= 3:
                        item_name, current, total = groups[:3]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                    # 修改：产出进度格式 - 处理无目标值的情况
                    elif progress_type == "产出进度":
                        if len(groups) >= 2:
                            current, total = groups[:2]
                            if total is not None:  # 有目标值
                                value = f"{current}/{total}个"
                            else:  # 無目標值
                                value = f"{current}/∞个"
                            return {
                                "type": "task",
                                "value": value
                            }
                        elif len(groups) >= 1 and groups[0] is not None:
                            # 只有当前值，无目标值
                            return {
                                "type": "task",
                                "value": f"{groups[0]}/∞个"
                            }
                    # 修改：運行時間進度格式 - 確保正確處理
                    elif progress_type == "运行时间进度" and len(groups) >= 2:
                        current_time, total_time = groups[:2]
                        # 將小數分鐘轉換為分鐘:秒格式（秒數四捨五入）
                        try:
                            current_minutes = float(current_time)
                            minutes = int(current_minutes)
                            seconds = round((current_minutes - minutes) * 60)  # 四捨五入到整數秒
                            
                            # 處理四捨五入後可能出現60秒的情況
                            if seconds == 60:
                                minutes += 1
                                seconds = 0
                                
                            # 格式化為 分鐘.秒 (秒數顯示兩位數)
                            formatted_time = f"{minutes}.{seconds:02d}"
                            value = f"{formatted_time}/{total_time}分钟"
                        except (ValueError, TypeError):
                            # 如果轉換失敗，返回原始格式
                            value = f"{current_time}/{total_time}分钟"
                        
                        return {
                            "type": "task",
                            "value": value
                        }
                    # 在 _extract_progress_info 方法中更新 F2 的处理逻辑
                    elif progress_type == "F2" and len(groups) >= 2:
                        current, total = groups[:2]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}轮"
                        }
                    elif progress_type == "狗粮进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return {
                            "type": "task",
                            "value": f"{current}/{total}"
                        }
                except (ValueError, IndexError) as e:
                    logging.warning(f"进度信息解析失败: {line}, 错误: {e}")
        return None

    def get_content(self):
    
        """安全获取日志内容 - 主入口方法"""
        # 如果日志路径无效，返回错误信息
        if not self.log_path_valid:
            return ["⚠️ 日志路径配置错误 ⚠️", "", "无法找到有效的日志文件，请：", 
                    "1. 打开 config.txt 文件", "2. 找到 log_path 配置项", 
                    "3. 取消注释并设置正确的路径", "4. 保存配置文件后重启程序", "",
                    "详细说明请查看 README.md", "", "按 Alt+P 关闭程序"]
        
        """獲取日誌內容時增加延遲，避免讀取部分寫入的內容"""
        time.sleep(0.05)  # 50ms 延遲，確保日誌寫入完成
        
        # 检查日期变更和文件更新
        self._detect_date_change()
        self._update_log_file()
        
        # 动态调整读取行数：当跳过调试日志时，需要读取更多行
        if self.skip_debug_log:
            # 增加读取行数以确保有足够的非调试日志
            actual_read_lines = max(self.read_lines * 2, 400)  # 增加到400行
        else:
            actual_read_lines = max(self.read_lines, 150)  # 最少150行
        
        # 获取日志内容，失败时使用缓存
        full_content = self._tail_lines(actual_read_lines) or list(self._last_valid_content)

        # 合并跨行日志条目
        merged_content = self._merge_log_lines(full_content)

        # 过滤调试日志（如果启用）
        if self.skip_debug_log:
            merged_content = self._filter_debug_logs(merged_content)

        # 二次过滤确保无空行
        filtered_content = [line for line in merged_content if line.strip()]

        # 处理文件空内容情况 & 处理全空情况
        if not filtered_content:
            if self._current_file.exists() and self._current_file.stat().st_size == 0:
                filtered_content = ["-- 新日志文件已创建 --"]
            else:
                filtered_content = ["-- 日志内容为空 --"]

        # 保存当前任务状态用于切换检测
        previous_task = self.current_task

        # 使用临时变量存储最新状态
        latest_config = self.current_config
        latest_task = self.current_task
        latest_progress = self.current_progress  # 任務進度
        latest_config_progress = self.current_config_progress  # 配置組進度

        # 优先搜索进度信息，然后才是任务和配置信息
        progress_found = False
        task_found = False
        config_found = False
        config_progress_found = False
        
        # 逆向搜索日誌內容 - 從最新日誌開始搜索
        for line in reversed(full_content):
            # 1. 優先搜索進度信息（最重要）
            if not progress_found:
                progress_info = self._extract_progress_info(line)
                if progress_info:
                    progress_type = progress_info.get("type")
                    progress_value = progress_info.get("value")
                    
                    if progress_type == "config":
                        # 這是配置組進度
                        latest_config_progress = progress_value
                        # 配置組進度刷新時，歸零當前任務進度
                        latest_progress = "0/0"
                        config_progress_found = True
                        progress_found = True
                    elif progress_type == "task":
                        # 這是任務進度，只有在沒有找到配置組進度時才記錄
                        if not config_progress_found:
                            latest_progress = progress_value
                            progress_found = True
        
            # 2. 然後搜索配置信息
            if not config_found:
                if config_match := self.config_pattern.search(line):
                    config_name = config_match.group(1)
                    # 只更新"加載完成"或"開始執行"的配置組
                    if "加载完成" in line or "开始执行" in line:
                        latest_config = config_name
                        config_found = True
            
            # 3. 最後搜索任務信息
            if not task_found:
                for task_type, pattern in self.task_patterns.items():
                    if match := pattern.search(line):
                        task_name = match.group(1).strip()
                        
                        # 特殊處理：對於釣魚點任務，保持完整的任務名稱
                        if task_type == "垂钓点":
                            # 釣魚點任務名稱保持原樣，不進行路徑和擴展名處理
                            latest_task = f"{task_type}: {task_name}"
                        else:
                            # 常見擴展名列表（可根據需要增減）
                            known_extensions = ['.json', '.js']
                            
                            # 其他任務類型：提取純文件名（不含路徑和擴展名）
                            if '/' in task_name or '\\' in task_name:
                                base_name = os.path.basename(task_name)
                                # 檢查是否有已知擴展名
                                for ext in known_extensions:
                                    if base_name.endswith(ext):
                                        task_name = base_name[:-len(ext)]
                                        break
                                else:
                                    task_name = base_name  # 無已知擴展名，保留原文件名
                            else:
                                # 如果只有文件名且包含已知擴展名，移除擴展名；否則保留原樣
                                for ext in known_extensions:
                                    if task_name.endswith(ext):
                                        task_name = task_name[:-len(ext)]
                                        break
                                # 若無匹配的已知擴展名，則保留原 task_name（包括其中的點號）
                            
                            latest_task = f"{task_type}: {task_name}"
                        task_found = True
                        break  # 一行通常只匹配一個任務類型
            
            # 如果所有信息都已找到，提前退出循环
            if progress_found and task_found and config_found:
                break

        # 最终更新状态
        self.current_config = latest_config
        self.current_task = latest_task
        self.current_progress = latest_progress
        self.current_config_progress = latest_config_progress  # 更新配置組進度

        # 检测任务切换频率
        self._detect_task_switching(previous_task)

        # 格式化日志行（只对要显示的内容进行格式化）
        display_content = filtered_content[-self.display_lines:] if len(filtered_content) > self.display_lines else filtered_content
        
        # 新增：如果启用自动换行，处理换行
        if self.auto_wrap:
            formatted_content = []
            for line in display_content:
                formatted_line = self._format_log_line(line)  # 这里会调用我们修改的方法
                wrapped_lines = self._wrap_text_line(formatted_line)  # 这里会调用我们修改的方法
                formatted_content.extend(wrapped_lines)

            # 重要：换行后可能行数超过 display_lines，需要再次限制
            if len(formatted_content) > self.display_lines:
                formatted_content = formatted_content[-self.display_lines:]
        else:
            formatted_content = [self._format_log_line(line) for line in display_content]

        # 更新缓存为格式化后的内容
        if formatted_content:
            self._last_valid_content = deque(formatted_content, maxlen=100)
        return formatted_content

    def _get_font(self):
        """获取字体对象用于宽度测量"""
        if self._font_cache is None and self.font_config:
            try:
                import tkinter.font as tkfont
                # 根据字体配置创建字体对象
                font_name = self.font_config.get("font_name", "Consolas")
                font_size = self.font_config.get("font_size", 11)
                font_weight = self.font_config.get("font_weight", "normal")
                
                self._font_cache = tkfont.Font(
                    family=font_name,
                    size=font_size,
                    weight=font_weight
                )
            except Exception as e:
                logging.warning(f"创建字体对象失败: {str(e)}，使用默认字体")
                # 回退到默认字体
                self._font_cache = tkfont.Font(family="Consolas", size=11, weight="normal")
        
        return self._font_cache
    
    def _wrap_text_line(self, line):
        """对单行文本进行换行处理"""
        if not self.auto_wrap:
            return [line]
        
        # 确保 line 是字符串
        if not isinstance(line, str):
            try:
                line = str(line)
            except Exception as e:
                logging.warning(f"无法将行转换为字符串: {type(line)}，错误: {str(e)}，返回原始行")
                return [line]
        
        if not line.strip():
            return [line]
            
        font = self._get_font()
        if not font:
            return [line]  # 无法获取字体时返回原行
            
        try:
            # 计算缩进宽度（两个全角空格）
            indent = "　　"
            indent_width = font.measure(indent)
            # 计算可用宽度（减去边距）
            available_width = self.max_width - indent_width - 2  # 8像素边距
            
            # 如果整行宽度不超过可用宽度，直接返回
            if font.measure(line) <= available_width:
                return [line]
                
            # 需要换行处理
            wrapped_lines = []
            current_line = ""
            is_first_line = True
            
            # 按单词分割（优先在空格处换行）
            words = line.split(' ')
            
            for word in words:
                if not word:  # 跳过空单词
                    continue
                    
                # 测试添加单词后的宽度
                test_line = current_line + " " + word if current_line else word
                if font.measure(test_line) <= available_width:
                    current_line = test_line
                else:
                    # 当前行已满，开始新行
                    if current_line:
                        if is_first_line:
                            wrapped_lines.append(current_line)
                            is_first_line = False
                        else:
                            wrapped_lines.append(indent + current_line)
                    
                    # 如果单个单词就超宽，需要强制分割
                    if font.measure(word) > available_width:
                        # 对超长单词进行字符级分割
                        self._wrap_long_word(word, wrapped_lines, font, available_width, indent, is_first_line)
                        current_line = ""
                        is_first_line = False
                    else:
                        current_line = word
                        
            # 添加最后一行
            if current_line:
                if is_first_line:
                    wrapped_lines.append(current_line)
                else:
                    wrapped_lines.append(indent + current_line)
                
            return wrapped_lines if wrapped_lines else [line]
            
        except Exception as e:
            logging.warning(f"换行处理失败: {str(e)}，返回原始行")
            return [line]
    
    def _wrap_long_word(self, word, wrapped_lines, font, available_width, indent, is_first_line):
        """处理超长单词的字符级分割"""
        # 确保 word 是字符串
        if not isinstance(word, str):
            try:
                word = str(word)
            except Exception as e:
                logging.warning(f"无法将单词转换为字符串: {type(word)}，错误: {str(e)}，跳过分割")
                if is_first_line:
                    wrapped_lines.append(str(word))
                else:
                    wrapped_lines.append(indent + str(word))
                return
        
        current_chunk = ""
        for char in word:
            test_chunk = current_chunk + char
            if font.measure(test_chunk) <= available_width:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    if is_first_line:
                        wrapped_lines.append(current_chunk)
                        is_first_line = False
                    else:
                        wrapped_lines.append(indent + current_chunk)
                current_chunk = char
                
        if current_chunk:
            if is_first_line:
                wrapped_lines.append(current_chunk)
            else:
                wrapped_lines.append(indent + current_chunk)
    
    def _init_backup(self):
        """初始化备份功能"""
        # 檢查是否啟用備份功能
        if not self.backup_path:
            logging.info("備份路徑未設置，跳過備份初始化")
            return
        
        try:
            # 確保備份目錄存在
            self.backup_path.mkdir(parents=True, exist_ok=True)
            
            # 確認目錄是否創建成功
            if not self.backup_path.exists():
                logging.error(f"無法創建備份目錄: {self.backup_path}")
                self.backup_enabled = False
                return
                
            logging.info(f"備份目錄已準備: {self.backup_path}")
            
            # 如果調試模式開啟，立即執行一次備份
            if self.backup_debug and self._current_file:
                self._backup_log_file(debug_mode=True)
                
            # 啟動備份定時器
            self._start_backup_timer()
            
            # 初始清理
            self._cleanup_old_backups()
            
            # 確認備份功能已啟用
            self.backup_enabled = True
        except Exception as e:
            logging.error(f"初始化備份功能失敗: {str(e)}")
            self.backup_enabled = False
    
    def _start_backup_timer(self):
        """启动备份定时器（支持对齐模式）"""
        if not self.backup_path or not self.backup_interval:
            return
            
        # 取消现有的定时器
        if self.backup_timer:
            self.backup_timer.cancel()
        
        # 计算下次备份延迟（秒）
        if self.backup_align_to_clock:
            delay = self._calculate_next_aligned_time()
        else:
            delay = self.backup_interval * 60
        
        # 创建新的定时器
        self.backup_timer = threading.Timer(delay, self._on_backup_timer)
        self.backup_timer.daemon = True
        self.backup_timer.start()
        mode = "对齐模式" if self.backup_align_to_clock else "相对模式"
        logging.info(f"备份定时器已启动，{mode}，间隔: {self.backup_interval}分钟，延迟: {delay:.0f}秒")
    
    def _on_backup_timer(self):
        """备份定时器回调函数"""
        try:
            # 备份当前日志文件
            if self._current_file and self._current_file.exists():
                self._backup_log_file()
                
        except Exception as e:
            logging.error(f"定时备份失败: {str(e)}")
            
        finally:
            # 重新启动定时器
            self._start_backup_timer()
    
    def backup_now(self, manual=False):
        """手動立即備份，返回是否成功"""
        if not self.backup_enabled:
            return False
        if not self._current_file or not self._current_file.exists():
            return False
        return self._backup_log_file(manual=manual)
    
    def _backup_log_file(self, debug_mode=False, manual=False):
        """备份日志文件
        :param debug_mode: 是否為調試模式備份（不影響定時器）
        :param manual: 是否為手動觸發
        """
        if not self.backup_path or not self._current_file:
            return False

        try:
            current_time = time.time()
            # 检查是否需要备份（距离上次备份时间超过5秒，避免频繁备份）
            if not debug_mode and (current_time - self.last_backup_time < 5):
                return False

            source_file = self._current_file
            if not source_file or not source_file.exists():
                return False

            # 获取文件名（不包含时间戳）
            file_name = source_file.name
            # 处理带序号的文件名：better-genshin-impactYYYYMMDD_001.log
            # 处理不带序号的文件名：better-genshin-impactYYYYMMDD.log
            target_file = self.backup_path / file_name

            # 复制文件
            shutil.copy2(source_file, target_file)

            self.last_backup_time = current_time
            log_msg = f"日志文件已备份: {source_file.name} -> {target_file}"
            if debug_mode:
                log_msg = "[调试] " + log_msg
            logging.info(log_msg)

            # 手動備份且為相對模式（非調試）時重置定時器
            if manual and not debug_mode and not self.backup_align_to_clock:
                self._start_backup_timer()
                logging.info("手動備份後已重置相對模式定時器")

            # 备份完成后清理旧文件
            self._cleanup_old_backups()
            return True

        except Exception as e:
            logging.error(f"备份日志文件失败: {str(e)}")
            return False
    
    def _calculate_next_aligned_time(self):
        if not self.backup_align_to_clock:
            return self.backup_interval * 60
        
        interval = self.backup_interval
        if 60 % interval != 0:
            logging.warning(f"备份间隔 {interval} 分钟不是60的约数，无法使用对齐模式，已自动切换为相对模式")
            self.backup_align_to_clock = False
            return interval * 60
        
        now = datetime.now()
        current_minute = now.minute
        # 计算下一个对齐的分钟数（0, interval, 2*interval, ..., 60）
        next_multiple = ((current_minute // interval) + 1) * interval
        if next_multiple == 60:
            # 下一小时的整点
            next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            # 当前小时的某个分钟
            next_time = now.replace(minute=next_multiple, second=0, microsecond=0)
        # 如果计算出的时间已经过去（极少情况），加一个间隔
        if next_time <= now:
            next_time += timedelta(minutes=interval)
        delta = (next_time - now).total_seconds()
        logging.info(f"下次对齐备份时间: {next_time.strftime('%Y-%m-%d %H:%M:%S')}, 间隔 {delta:.0f} 秒")
        return max(delta, 1)
    
    def _check_and_backup_previous_day(self):
        """检查并备份前一天的文件（在检测到日期变更时调用）"""
        if not self.backup_enabled:
            return
            
        try:
            # 获取前一天的日期
            yesterday = datetime.now().date() - timedelta(days=1)
            
            # 查找前一天的文件
            patterns = self._generate_log_patterns(yesterday)
            yesterday_file = None
            
            for pattern in patterns:
                if '*' in str(pattern):
                    # 使用通配符匹配带序号的文件
                    import glob
                    matches = glob.glob(str(pattern))
                    if matches:
                        # 找到修改时间最新的文件
                        matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                        yesterday_file = Path(matches[0])
                        break
                else:
                    if pattern.exists():
                        yesterday_file = pattern
                        break
            
            # 如果找到前一天的文件，备份它
            if yesterday_file and yesterday_file.exists():
                # 获取文件名（不包含时间戳）
                file_name = yesterday_file.name
                if "_" in file_name and file_name.endswith(".log"):
                    base_name = file_name.split("_")[0] + ".log"
                else:
                    base_name = file_name
                    
                target_file = self.backup_path / base_name
                
                # 复制文件
                shutil.copy2(yesterday_file, target_file)
                logging.info(f"前一天日志文件已备份: {yesterday_file.name} -> {target_file}")
                
                # 清理旧文件
                self._cleanup_old_backups()
                
        except Exception as e:
            logging.error(f"备份前一天文件失败: {str(e)}")
    
    def _cleanup_old_backups(self):
        """清理超过指定天数的旧备份文件"""
        if not self.backup_enabled or not self.backup_path:
            logging.debug("備份功能未啟用或備份路徑為空，跳過清理")
            return
            
        try:
            logging.debug(f"開始清理舊備份文件，備份路徑: {self.backup_path}")
            current_date = datetime.now().date()
            logging.debug(f"當前日期: {current_date}")
            
            file_count = 0
            deleted_count = 0
            
            for file_path in self.backup_path.glob("*.log"):
                file_count += 1
                # 尝试从文件名中提取日期
                date_str = self._extract_date_from_filename(file_path.name)
                
                if date_str:
                    try:
                        file_date = datetime.strptime(date_str, "%Y%m%d").date()
                        
                        # 计算文件日期与当前日期的天数差
                        days_diff = (current_date - file_date).days
                        
                        # 如果超过配置的天数，删除文件
                        if days_diff > self.backup_keep_days:
                            file_path.unlink()
                            deleted_count += 1
                            logging.info(f"删除旧备份文件: {file_path.name} (创建于 {days_diff} 天前)")
                    except ValueError:
                        # 日期格式不正确，跳过
                        continue
                else:
                    # 无法从文件名提取日期，尝试使用文件修改时间
                    try:
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime).date()
                        days_diff = (current_date - file_mtime).days
                        
                        if days_diff > self.backup_keep_days:
                            file_path.unlink()
                            deleted_count += 1
                            logging.info(f"删除旧备份文件(按修改时间): {file_path.name} (修改于 {days_diff} 天前)")
                    except Exception:
                        # 无法获取修改时间，跳过
                        continue
            logging.debug(f"備份清理完成: 檢查了 {file_count} 個文件，刪除了 {deleted_count} 個文件")
                        
        except Exception as e:
            logging.error(f"清理舊備份文件失敗: {str(e)}", exc_info=True)  # 添加 exc_info 獲取堆棧信息
    
    def _extract_date_from_filename(self, filename):
        """从文件名中提取日期字符串 (YYYYMMDD 格式)"""
        # 尝试匹配以下格式：
        # 1. better-genshin-impact20231201.log
        # 2. better-genshin-impact20231201_001.log
        
        # 匹配8位数字日期
        match = re.search(r'(\d{8})', filename)
        if match:
            return match.group(1)
        return None
    
    def stop_backup(self):
        """停止备份功能"""
        if self.backup_timer:
            self.backup_timer.cancel()
            self.backup_timer = None
            
        if self.backup_thread:
            self.backup_thread = None
            
        self.backup_enabled = False
        logging.info("备份功能已停止")
    

class FloatingLogViewer(tk.Tk):
    def __init__(self, config):
        """悬浮日志查看器主窗口 - 基于tkinter的透明悬浮窗口"""
        super().__init__()
        self.config = config
        
        # 获取初始的日志配置（只在程序开始时加载一次）
        initial_log_config = config.get_initial_log_config()
        log_dir = initial_log_config["log_path"]
        log_filename_prefix = initial_log_config["log_filename_prefix"]
        log_path_configured = initial_log_config["log_path_configured"]
        display_lines = config.get("display_lines", 11)
        skip_debug_log = config.get("skip_debug_log", False)
        auto_wrap = config.get("auto_wrap", False)  # 新增
        dynamic_height = config.get("dynamic_height", False)
        max_width = config.get("max_width", 460)
        
        # 从配置中获取备份设置
        backup_path = config.get("backup_path", "")
        backup_interval = config.get("backup_interval", 60)
        backup_debug = config.get("backup_debug", False)
        backup_enabled = config.get("backup_enabled", False)  # 從配置讀取啟用狀態
        backup_keep_days = config.get("backup_keep_days", 10)
        
        # 准备字体配置传递给 SmartLogReader
        font_config = {
            "font_name": config.get("font_name", "Consolas"),
            "font_size": config.get("font_size", 11),
            "font_weight": config.get("font_weight", "bold")
        }
        
        # 初始化日志读取器 - 添加新参数
        self.reader = SmartLogReader(
            log_dir, 
            log_filename_prefix, 
            log_path_configured, 
            display_lines, 
            skip_debug_log,
            dynamic_height,
            auto_wrap,
            max_width,
            font_config,
            backup_path,          # 新增
            backup_interval,      # 新增
            backup_debug,         # 新增
            backup_enabled,        # 新增
            backup_keep_days,      # 新增
            backup_align_to_clock=config.get("backup_align_to_clock", False)  # 新增
        )
        self._prev_content = []  # 上一次显示的内容
        self.last_change_time = datetime.now()  # 最后内容变更时间
        
        # 颜色配置
        self.normal_color = config.get("normal_color", "#00FF00")
        self.stale_color = config.get("stale_color", "#FF0000")
        self.high_freq_color = config.get("high_freq_color", "#FFA500")
        self.debug_color = config.get("debug_color", "#808080")  # 新增
        self.error_color = config.get("error_color", "#FF6B6B")  # 新增
        self.warning_color = config.get("warning_color", "#FFD700")  # 新增
        self.backup_msg_color = config.get("backup_msg_color", "#FFD700")  # 备份临时消息颜色
        
        # 性能优化：字体缓存
        self._font_cache = None
        self._last_font_config = None
        
        # 窗口状态
        self.monitor_running = True
        self.drag_start_pos = None  # 拖动状态变量
        self.current_width = config.get("max_width", 460)  # 使用max_width作为当前宽度
        
        # 功能状态
        self.transparent_mode = config.get("transparent_mode", False)  # 从配置读取透明模式状态
        self.click_through = config.get("click_through", False)  # 从配置读取不可选中模式状态
        self.author_style2_active = config.get("author_style2", False)  # 从配置读取仿BGI日志窗口样式状态
        
        # 新增：窗口隐藏状态
        self.is_hidden = False  # 窗口是否隐藏
        self.hidden_message = "日志悬浮窗 - 停用中"  # 隐藏时显示的文字

        # 新增：临时消息（类似警告行）
        self.temp_message = None          # 当前临时消息文字
        self.temp_message_expiry = 0      # 过期时间戳（time.time()）
        self.temp_message_color = self.backup_msg_color  # 使用配置的颜色
        
        # 窗口配置 - 使用保存的位置，如果 window_x/window_y 为 None 则使用 initial_x/initial_y
        self.preset_x = config.get("initial_x", 0)
        self.preset_y = config.get("initial_y", 0)
        
        # 获取 window_x 和 window_y，如果为 None 则使用预设值
        window_x = config.get("window_x")
        window_y = config.get("window_y")
        
        # 确保 current_x 和 current_y 不会是 None
        self.current_x = window_x if window_x is not None else self.preset_x
        self.current_y = window_y if window_y is not None else self.preset_y
        
        # 最终安全检查（防御性编程）
        if self.current_x is None:
            self.current_x = 0
            logging.warning("current_x 为 None，使用默认值 0")
        if self.current_y is None:
            self.current_y = 0
            logging.warning("current_y 为 None，使用默认值 0")
        
        # 记录使用的配置
        if window_x is None:
            logging.info(f"window_x 为空，使用预设位置: {self.preset_x}")
        if window_y is None:
            logging.info(f"window_y 为空，使用预设位置: {self.preset_y}")

        self.max_width = config.get("max_width", 460)
        self.max_height = config.get("max_height", 220)
        self.display_lines = config.get("display_lines", 11)
        self.refresh_interval = config.get("refresh_interval", 1000)
        self.dynamic_height=self.config.get("dynamic_height", False)

        # 初始化界面
        self._setup_window()
        self._setup_ui()
        self._setup_keyboard_shortcuts()  # 新增：设置键盘快捷键
        self._start_auto_refresh()
        
        # 确保清理可能残留的全局快捷键
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
                logging.info("清理可能残留的全局快捷键")
            except Exception as e:
                logging.warning(f"清理全局快捷键时出现警告: {str(e)}")
        
        # 初始化全局快捷键管理器
        self.shortcut_manager = GlobalShortcutManager(self)
        self.shortcut_manager.start_listening()
        
        # 新增：延迟检查快捷键状态，确保备用方案生效
        self.after(2000, self._check_shortcut_status)  # 2秒后检查
    
    def _check_shortcut_status(self):
        """检查快捷键状态，确保有可用的快捷键方案"""
        if KEYBOARD_AVAILABLE and not self.shortcut_manager.hotkeys_registered:
            logging.warning("全局快捷键注册可能被安全软件阻止，强制启用窗口内快捷键")
            self._setup_keyboard_shortcuts()  # 强制启用窗口内快捷键
        elif not KEYBOARD_AVAILABLE:
            logging.info("keyboard库不可用，使用窗口内快捷键")
            self._setup_keyboard_shortcuts()

    def _setup_window(self):
        """窗口视觉配置 - 设置透明、置顶等属性"""
        # 设置窗口标题，让系统识别
        self.title("BetterGI日志悬浮窗")
        
        # 根据透明模式状态设置窗口属性
        if self.transparent_mode:
            bg_color = self.config.get("bg_color", "#000000")
            self.configure(bg=bg_color)
            self.attributes('-alpha', 1.0)
            self.attributes('-transparentcolor', bg_color)
            
            logging.info("启动时启用透明背景模式 - 背景透明，文字正常显示")
        else:
            self.configure(bg=self.config.get("bg_color", "#000000"))
            self.attributes('-alpha', self.config.get("window_alpha", 0.7))
        
        self.attributes('-topmost', True)  # 窗口置顶
        
        # 确保坐标有效
        if self.current_x is None:
            self.current_x = self.preset_x if self.preset_x is not None else 0
        if self.current_y is None:
            self.current_y = self.preset_y if self.preset_y is not None else 0

        # 设置窗口尺寸和位置
        geometry_string = f"{self.max_width}x{self.max_height}+{self.current_x}+{self.current_y}"
        self.geometry(geometry_string)
        
        # 强制更新窗口以确保设置生效
        self.update_idletasks()
        
        # 延迟移除边框，确保系统已识别窗口
        self.after(100, self._make_window_floating)
        
        # 设置窗口关闭协议
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        logging.info(f"窗口初始化完成 - 位置: ({self.current_x}, {self.current_y})")

    def _make_window_floating(self):
        """将窗口变为悬浮样式"""
        self.overrideredirect(True)
        self.update_idletasks()
        
        # 设置任务栏图标（Windows系统）
        if os.name == 'nt':
            self._setup_taskbar_icon()
        
        # 延迟设置鼠标穿透，确保窗口已完全创建
        self.after(200, self._apply_initial_click_through)
        
    def _apply_initial_click_through(self):
        """应用初始的鼠标穿透设置"""
        if self.click_through:
            # 启用鼠标穿透（仅在全局快捷键可用时）
            success = self._set_window_click_through(True)
            if success:
                logging.info("启动时启用不可选中模式 - 鼠标穿透已启用")
            else:
                logging.warning("启动时启用不可选中模式失败")
            
    def _setup_taskbar_icon(self):
        """设置任务栏图标 - 使用Windows API"""
        try:
            # 定义Windows API常量
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            
            # 获取窗口句柄
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            
            # 获取当前扩展样式
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # 移除工具窗口样式，添加应用窗口样式
            ex_style = (ex_style & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
            
            # 设置新的扩展样式
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)
            
            logging.info("已设置任务栏图标")
        except Exception as e:
            logging.error(f"设置任务栏图标失败: {str(e)}")
        
    def _setup_ui(self):
        """界面元素初始化 - 创建文本显示区域"""
        font_name = self.config.get("font_name", "Consolas")
        font_size = self.config.get("font_size", 11)
        font_weight = self.config.get("font_weight", "bold")
        
        # 验证字体是否存在
        available_fonts = tkfont.families()
        if font_name not in available_fonts:
            logging.warning(f"字体 '{font_name}' 不可用，使用默认字体")
            font_name = "Consolas"  # 回退到默认字体
        
        try:
            # 创建字体配置
            font_config = (font_name, font_size)
            if font_weight != "normal":
                font_config = (font_name, font_size, font_weight)
            
            # 测试字体是否可用
            test_font = tkfont.Font(font=font_config)
            _ = test_font.measure("test")
        except Exception as e:
            logging.error(f"字体配置失败: {str(e)}，使用系统默认字体")
            font_config = ("TkDefaultFont", font_size)
            
        # 创建文本显示组件
        # 根据透明模式设置不同的背景
        text_bg = self.config.get("bg_color", "#000000")  # 文本区域使用与窗口相同的背景色
        
        # 根据换行设置决定 wrap 模式
        auto_wrap = self.config.get("auto_wrap", False)
        wrap_mode = tk.WORD if auto_wrap else tk.NONE  # 新增
        
        self.text = tk.Text(
            self,
            bg=text_bg,
            fg=self.normal_color,
            font=font_config,
            borderwidth=0,
            insertwidth=0,
            wrap=wrap_mode,  # 修改：根据配置设置换行模式
            height=self.display_lines,
            state='disabled'
        )
        self.text.pack(expand=True, fill='both')
        
        # 仅在非不可选中模式下启用拖动功能
        if not self.click_through:
            self.text.bind("<ButtonPress-1>", self._handle_drag_start)
            self.text.bind("<B1-Motion>", self._handle_drag_move)
        else:
            logging.info("不可选中模式已启用，拖动功能已禁用")
        
        # 立即显示日志内容
        self._update_display()

    def _setup_keyboard_shortcuts(self):
        """设置键盘快捷键 - Alt+P关闭程序, Alt+U重置位置（当全局快捷键不可用时启用）"""
        self.bind("<Alt-KeyPress-p>", self._on_close_shortcut)
        self.bind("<Alt-KeyPress-P>", self._on_close_shortcut)
        self.bind("<Alt-KeyPress-u>", self._on_reset_position_shortcut)
        self.bind("<Alt-KeyPress-U>", self._on_reset_position_shortcut)
        self.bind("<Alt-KeyPress-i>", self._on_transparent_toggle_shortcut)
        self.bind("<Alt-KeyPress-I>", self._on_transparent_toggle_shortcut)
        self.bind("<Alt-KeyPress-n>", self._on_click_through_toggle_shortcut)
        self.bind("<Alt-KeyPress-N>", self._on_click_through_toggle_shortcut)
        self.bind("<Alt-KeyPress-k>", self._on_second_style_toggle_shortcut)
        self.bind("<Alt-KeyPress-K>", self._on_second_style_toggle_shortcut)
        # 新增：P键隐藏/显示窗口（只在窗口内生效）
        self.bind("<KeyPress-p>", self._on_toggle_visibility_shortcut)
        self.bind("<KeyPress-P>", self._on_toggle_visibility_shortcut)
        # 新增：Alt+B 立即备份
        self.bind("<Alt-KeyPress-b>", self._on_backup_shortcut)
        self.bind("<Alt-KeyPress-B>", self._on_backup_shortcut)
            
        # 簡單的日誌記錄，不依賴於 hotkeys_registered
        if KEYBOARD_AVAILABLE:
            logging.info("全局快捷键可用，窗口内快捷键也已設置（備份）")
        else:
            logging.info("全局快捷键不可用，已启用窗口内快捷键")
            
        self.focus_set()  # 确保窗口能够接收键盘事件

    def show_temp_message(self, text, duration=2):
        """显示临时消息（类似警告行），持续 duration 秒后自动消失"""
        self.temp_message = text
        self.temp_message_expiry = time.time() + duration
        # 强制立即刷新显示
        self._force_immediate_display_update()
        # 设定定时器，到期后再次刷新以清除消息
        self.after(int(duration * 1000), self._clear_temp_message)

    def _clear_temp_message(self):
        """清除过期的临时消息（仅当消息已过期时才清除）"""
        if self.temp_message and time.time() >= self.temp_message_expiry:
            self.temp_message = None
            self._force_immediate_display_update()

    def _on_backup_shortcut(self, event=None):
        """Alt+B 立即备份"""
        if not self.reader.backup_enabled:
            self.show_temp_message("⚠️ 备份未启用", 2)
            return

        # 显示备份中
        self.show_temp_message("⏳ 立即备份中...", 2)

        # 执行备份（同步）
        try:
            success = self.reader.backup_now(manual=True)
            if success:
                self.show_temp_message("✅ 备份成功", 2)
            else:
                self.show_temp_message("❌ 备份失败", 2)
        except Exception as e:
            logging.error(f"手动备份异常: {str(e)}")
            self.show_temp_message("❌ 备份失败", 2)

    def _on_toggle_visibility_shortcut(self, event=None):
        """P键快捷键处理函数 - 切换窗口显示/隐藏"""
        try:
            if self.is_hidden:
                # 如果窗口是隐藏状态，恢复正常显示
                self._restore_normal_display()
            else:
                # 如果窗口是正常显示状态，切换到隐藏状态
                self._switch_to_hidden_state()
                
        except Exception as e:
            logging.error(f"切换窗口显示/隐藏失败: {str(e)}")
            
    def _switch_to_hidden_state(self):
        """切换到隐藏状态"""
        self.is_hidden = True
        logging.info("进入隐藏状态 - 日志悬浮窗停用中")
        
        # 停止自动刷新（但仍然在后台运行备份功能）
        self._stop_auto_refresh()
        
        # 保存当前窗口位置和大小
        self.normal_window_geometry = self.geometry()
        
        # 保存当前窗口样式状态，以便恢复时使用
        self.normal_bg_color = self.text.cget("bg")
        self.normal_fg_color = self.text.cget("fg")
        self.normal_window_alpha = self.attributes('-alpha')
        self.normal_transparentcolor = self.attributes('-transparentcolor')
        self.normal_font_config = self.text.cget("font")  # 保存当前字体配置
        
        # 设置隐藏状态样式：黑色背景、红色文字、不透明、固定字体15
        hidden_bg_color = "#000000"  # 黑色背景
        hidden_fg_color = "#FF0000"  # 红色文字
        hidden_font_size = 15  # 固定字体大小15
        
        # 获取当前字体名称和粗细
        font_name = self.config.get("font_name", "Consolas")
        font_weight = self.config.get("font_weight", "bold")
        
        # 设置隐藏状态字体配置
        if font_weight != "normal":
            self.hidden_font_config = (font_name, hidden_font_size, font_weight)
        else:
            self.hidden_font_config = (font_name, hidden_font_size)
        
        # 设置窗口不透明
        self.attributes('-alpha', 1.0)
        self.attributes('-transparentcolor', '')
        
        # 设置窗口背景色
        self.configure(bg=hidden_bg_color)
        
        # 清空文本显示区域
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        
        # 设置文本组件样式
        self.text.config(
            bg=hidden_bg_color,
            fg=hidden_fg_color,
            font=self.hidden_font_config  # 使用固定字体15
        )
        
        # 配置居中标签
        self.text.tag_configure("center", justify='center')

        # 显示停用信息并居中
        self.text.insert(tk.END, self.hidden_message, "center")
        self.text.config(state='disabled')
        
        # 调整窗口大小以适应停用信息（使用字体15计算）
        self._adjust_window_for_hidden_state()
        
        # 更新窗口标题
        self.title("BetterGI日志悬浮窗 - 停用中")
        
    def _stop_auto_refresh(self):
        """停止自动刷新（但仍然运行备份功能）"""
        self.monitor_running = False


    def _restore_normal_display(self):
        """恢复正常显示"""
        self.is_hidden = False
        logging.info("恢复正常显示状态")
        
        # 恢复自动刷新
        self._start_auto_refresh()
        
        # 恢复窗口大小和位置
        if hasattr(self, 'normal_window_geometry'):
            self.geometry(self.normal_window_geometry)
            
        # 删除居中标签
        if "center" in self.text.tag_names():
            self.text.tag_delete("center")
        
        # 恢复窗口样式状态
        if hasattr(self, 'normal_bg_color'):
            # 恢复背景色
            self.configure(bg=self.normal_bg_color)
            self.text.config(bg=self.normal_bg_color)
        
        if hasattr(self, 'normal_fg_color'):
            # 恢复文字颜色
            self.text.config(fg=self.normal_fg_color)
        
        # 恢复字体配置
        if hasattr(self, 'normal_font_config'):
            self.text.config(font=self.normal_font_config)
        
        # 恢复透明设置
        if hasattr(self, 'normal_window_alpha'):
            if self.transparent_mode:
                # 如果是透明模式，使用透明设置
                bg_color = self.config.get("bg_color", "#000000")
                self.configure(bg=bg_color)
                self.attributes('-alpha', 1.0)
                self.attributes('-transparentcolor', bg_color)
                self.text.config(bg=bg_color)
            else:
                # 如果是正常模式
                self.attributes('-transparentcolor', '')
                self.attributes('-alpha', self.normal_window_alpha)
        
        # 恢复窗口标题
        self.title("BetterGI日志悬浮窗")
        
        # 立即更新显示
        self._force_immediate_display_update()
        
        # 清理保存的样式变量
        if hasattr(self, 'normal_bg_color'):
            del self.normal_bg_color
        if hasattr(self, 'normal_fg_color'):
            del self.normal_fg_color
        if hasattr(self, 'normal_window_alpha'):
            del self.normal_window_alpha
        if hasattr(self, 'normal_transparentcolor'):
            del self.normal_transparentcolor
        if hasattr(self, 'normal_font_config'):
            del self.normal_font_config
        if hasattr(self, 'hidden_font_config'):
            del self.hidden_font_config

    def _adjust_window_for_hidden_state(self):
        """调整窗口大小以适应隐藏状态（使用字体15计算）"""
        try:
            # 计算停用信息的宽度（使用固定字体15）
            font_name = self.config.get("font_name", "Consolas")
            font_size = 15  # 固定字体大小15
            
            # 创建临时字体计算宽度
            temp_font = tkfont.Font(family=font_name, size=font_size, weight="bold")
            text_width = temp_font.measure(self.hidden_message)
            
            # 加上边距（左右各30像素）
            window_width = min(text_width + 40, 300)  # 最大不超过400像素
            
            # 固定高度为一行的高度加上边距
            line_height = temp_font.metrics('linespace')
            window_height = line_height + 20  # 一行高度加边距
            
            # 保持当前位置
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            
            # 设置新的大小
            self.geometry(f"{window_width}x{window_height}+{current_x}+{current_y}")
            
        except Exception as e:
            logging.error(f"调整隐藏状态窗口大小失败: {str(e)}")
            # 使用默认大小（足够显示文字）
            self.geometry(f"300x50+{self.winfo_x()}+{self.winfo_y()}")


    def _on_transparent_toggle_shortcut(self, event=None):
        """Alt+I 快捷键处理函数 - 切换透明背景模式"""
        try:
            self.transparent_mode = not self.transparent_mode
            
            # 更新配置中的值
            self.config.config["transparent_mode"] = self.transparent_mode
            self.config.user_config["transparent_mode"] = self.transparent_mode
            
            if self.transparent_mode:
                # 进入透明背景模式
                bg_color = self.config.get("bg_color", "#000000")
                self.configure(bg=bg_color)
                self.attributes('-alpha', 1.0)  
                self.attributes('-transparentcolor', bg_color)
                self.text.config(bg=bg_color)
                
                logging.info("进入透明背景模式")
            else:
                # 退出透明背景模式
                bg_color = self.config.get("bg_color", "#000000")
                self.attributes('-transparentcolor', '')
                self.configure(bg=bg_color)
                window_alpha = self.config.get("window_alpha", 0.7)
                self.attributes('-alpha', window_alpha)
                self.text.config(bg=bg_color)
                
                logging.info("退出透明背景模式")
                
            # 强制刷新显示
            self._update_display()
            
        except Exception as e:
            logging.error(f"切换透明模式失败: {str(e)}")

    def _on_click_through_toggle_shortcut(self, event=None):
        """Alt+N 快捷键处理函数 - 切换不可选中模式"""
        try:
            self.click_through = not self.click_through
            
            # 更新配置中的值
            self.config.config["click_through"] = self.click_through
            self.config.user_config["click_through"] = self.click_through
            
            # 设置鼠标穿透
            success = self._set_window_click_through(self.click_through)
            
            if self.click_through:
                if success:
                    # 禁用拖动功能
                    self.text.unbind("<ButtonPress-1>")
                    self.text.unbind("<B1-Motion>")
                    logging.info("进入不可选中模式 - 鼠标穿透已启用，拖动功能已禁用")
                else:
                    logging.warning("进入不可选中模式失败")
                    self.click_through = False  # 回滚状态
            else:
                if success:
                    # 启用拖动功能
                    self.text.bind("<ButtonPress-1>", self._handle_drag_start)
                    self.text.bind("<B1-Motion>", self._handle_drag_move)
                    logging.info("退出不可选中模式 - 鼠标穿透已禁用，拖动功能已启用")
                else:
                    logging.warning("退出不可选中模式失败")
                    self.click_through = True  # 回滚状态
                    
        except Exception as e:
            logging.error(f"切换不可选中模式失败: {str(e)}")
            self.click_through = not self.click_through  # 发生异常时回滚状态
    
    # 修改 _set_window_click_through 方法，增加更详细的错误处理
    def _set_window_click_through(self, enable):
        """设置窗口鼠标穿透（仅在Windows且全局快捷键可用时生效）"""
        if not KEYBOARD_AVAILABLE or os.name != 'nt':
            return False
        
        try:
            # 定义Windows API常量
            GWL_EXSTYLE = -20
            WS_EX_TRANSPARENT = 0x00000020
            
            # 获取窗口句柄
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            
            if not hwnd:
                logging.warning("无法获取窗口句柄")
                return False
                
            # 获取当前扩展样式
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            if enable:
                # 添加透明样式 - 鼠标穿透
                new_style = ex_style | WS_EX_TRANSPARENT
                logging.debug("启用窗口鼠标穿透")
            else:
                # 移除透明样式 - 恢复正常
                new_style = ex_style & ~WS_EX_TRANSPARENT
                logging.debug("禁用窗口鼠标穿透")
                
            # 设置新的扩展样式
            result = ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
            if result == 0:
                error_code = ctypes.windll.kernel32.GetLastError()
                logging.error(f"设置窗口样式失败，错误代码: {error_code}")
                return False
                
            # 强制刷新窗口
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
            return True
            
        except Exception as e:
            logging.error(f"设置窗口鼠标穿透失败: {str(e)}")
            return False

    def _on_second_style_toggle_shortcut(self, event=None):
        """Alt+K 快捷键处理函数 - 切换第二样式"""
        # 切换状态
        self.author_style2_active = not self.author_style2_active
        
        if self.author_style2_active:
            # 应用第二样式
            self.config.apply_second_style()
            logging.info("应用第二样式")
        else:
            # 恢复用户自定义样式
            self.config.restore_user_style()
            logging.info("恢复用户自定义样式")
        
        # 确保配置状态同步
        self.config.config["author_style2"] = self.author_style2_active
        self.config.user_config["author_style2"] = self.author_style2_active
        
        # 重新设置窗口和UI
        self._refresh_ui_after_style_change()
        
        # 强制立即刷新显示，不等待下一次自动刷新
        self._force_immediate_display_update()

    def _force_immediate_display_update(self):
        """强制立即更新显示，不依赖日志内容变化"""
        # 清除之前的内容缓存，确保强制更新
        self._prev_content = []
        self.last_change_time = datetime.now()
        
        # 强制调用更新显示
        self._update_display()
        
        # 确保窗口完全刷新
        self.update_idletasks()
        self.update()

    def clear_font_cache(self):
        """清理字体缓存"""
        if self._font_cache:
            self._font_cache = None
            self._last_font_config = None
            logging.debug("字体缓存已清理")

    def _refresh_ui_after_style_change(self):
        """样式变更后刷新UI"""
        # 从配置中重新读取所有设置
        self.normal_color = self.config.get("normal_color", "#00FF00")
        self.stale_color = self.config.get("stale_color", "#FF0000")
        self.high_freq_color = self.config.get("high_freq_color", "#FFA500")
        self.debug_color = self.config.get("debug_color", "#808080")
        self.error_color = self.config.get("error_color", "#FF6B6B")
        self.warning_color = self.config.get("warning_color", "#FFD700")
        self.backup_msg_color = self.config.get("backup_msg_color", "#FFD700")
        
        # 更新临时消息颜色
        self.temp_message_color = self.backup_msg_color
        
        # 更新窗口属性
        self.max_width = self.config.get("max_width", 460)
        self.max_height = self.config.get("max_height", 220)
        self.display_lines = self.config.get("display_lines", 11)
        self.refresh_interval = self.config.get("refresh_interval", 1000)
        
        # 清理字体缓存
        self.clear_font_cache()
        
        # 删除所有文本标签
        self.text.tag_delete("config_header")
        self.text.tag_delete("task_header")
        self.text.tag_delete("high_freq_warning")
        
        # 更新窗口视觉设置
        bg_color = self.config.get("bg_color", "#000000")

        # 先清除所有特殊属性
        self.attributes('-transparentcolor', '')
        
        if self.transparent_mode:
            # 透明模式下使用 transparentcolor
            self.configure(bg=bg_color)
            self.attributes('-alpha', 1.0)
            self.attributes('-transparentcolor', bg_color)
        else:
            # 正常模式
            self.configure(bg=bg_color)
            window_alpha = self.config.get("window_alpha", 0.7)
            self.attributes('-alpha', window_alpha)
        
        # 更新文本组件
        font_name = self.config.get("font_name", "Consolas")
        font_size = self.config.get("font_size", 11)
        font_weight = self.config.get("font_weight", "bold")
        
        # 验证字体是否存在
        available_fonts = tkfont.families()
        if font_name not in available_fonts:
            logging.warning(f"字体 '{font_name}' 不可用，使用默认字体")
            font_name = "Consolas"
        
        font_config = (font_name, font_size)
        if font_weight != "normal":
            font_config = (font_name, font_size, font_weight)
            
        # 根据换行设置决定 wrap 模式
        auto_wrap = self.config.get("auto_wrap", False)
        wrap_mode = tk.WORD if auto_wrap else tk.NONE
        
        # 更新文本组件背景和字体
        self.text.config(
            bg=bg_color,
            fg=self.normal_color,
            font=font_config,
            height=self.display_lines,
            wrap=wrap_mode
        )
        
        # 更新窗口尺寸
        current_x = self.winfo_x()
        current_y = self.winfo_y()
        self.geometry(f"{self.max_width}x{self.max_height}+{current_x}+{current_y}")
        
        # 重要：重新創建 SmartLogReader 以應用新的配置
        initial_log_config = self.config.get_initial_log_config()
        log_dir = initial_log_config["log_path"]
        log_filename_prefix = initial_log_config["log_filename_prefix"]
        log_path_configured = initial_log_config["log_path_configured"]
        skip_debug_log = self.config.get("skip_debug_log", False)
        auto_wrap = self.config.get("auto_wrap", False)
        dynamic_height = self.config.get("dynamic_height", False)
        
        # 准备字体配置
        font_config_dict = {
            "font_name": font_name,
            "font_size": font_size,
            "font_weight": font_weight
        }
        
        # 獲取備份相關配置
        backup_path = self.config.get("backup_path", "")
        backup_interval = self.config.get("backup_interval", 60)
        backup_debug = self.config.get("backup_debug", False)
        backup_enabled = self.config.get("backup_enabled", False)
        backup_keep_days = self.config.get("backup_keep_days", 10)
        backup_align_to_clock = self.config.get("backup_align_to_clock", False)
        
        # 重新創建 reader 以應用新的配置
        self.reader = SmartLogReader(
            log_dir, 
            log_filename_prefix, 
            log_path_configured, 
            self.display_lines, 
            skip_debug_log,
            dynamic_height,
            auto_wrap,
            self.max_width,
            font_config_dict,
            backup_path,
            backup_interval,
            backup_debug,
            backup_enabled,
            backup_keep_days,
            backup_align_to_clock
        )
        
        # 強制刷新顯示
        self._update_display()
        
        # 确保窗口完全刷新
        self.update_idletasks()
        self.update()

    def _on_reset_position_shortcut(self, event=None):
        """Alt+U 快捷键处理函数 - 重置窗口位置到预设位置"""
        logging.info(f"检测到 Alt+U 快捷键，重置窗口位置到预设位置: ({self.preset_x}, {self.preset_y})")
        self.geometry(f"+{self.preset_x}+{self.preset_y}")
        # 立即保存重置后的位置到config.txt
        self.config.save_window_state(self.preset_x, self.preset_y, self.transparent_mode, self.click_through, self.author_style2_active)

    def _on_close_shortcut(self, event=None):
        """Alt+P 快捷键处理函数"""
        logging.info("检测到 Alt+P 快捷键，关闭程序")
        self.destroy()

    def _handle_drag_start(self, event):
        """处理拖动开始事件 - 记录起始位置"""
        if not self.click_through:  # 仅在非不可选中模式下允许拖动
            self.drag_start_pos = {'x': event.x_root, 'y': event.y_root}

    def _handle_drag_move(self, event):
        """处理拖动移动事件 - 计算并更新窗口位置"""
        if self.drag_start_pos and not self.click_through:  # 仅在非不可选中模式下允许拖动
            delta_x = event.x_root - self.drag_start_pos['x']
            delta_y = event.y_root - self.drag_start_pos['y']
            self.geometry(f"+{self.winfo_x() + delta_x}+{self.winfo_y() + delta_y}")
            self.drag_start_pos = {'x': event.x_root, 'y': event.y_root}

    def _start_auto_refresh(self):
        """启动自动刷新"""
        self.monitor_running = True
        # 重新启动自动刷新循环
        def update_loop():
            try:
                self._update_display()
                if self.monitor_running:
                    self.after(self.refresh_interval, update_loop)
            except Exception as e:
                logging.critical(f"刷新循环异常: {str(e)}")

        update_loop()

    # 只比较日志内容，不包括状态行
    def _get_content_hash(self, content):
        """获取内容的哈希值用于比较变化"""
        if not content:
            return hash(str(content))
        
        # 检查是否是错误信息
        if content and "日志路径配置错误" in content[0]:
            return hash(tuple(content))
        
        # 动态确定状态行数
        status_lines = 2  # 默认：配置组行 + 任务行
        
        # 如果有高频警告，状态行数增加1
        if content and content[0].startswith("⚠️"):
            status_lines = 3  # 高频警告行 + 配置组行 + 任务行
        
        # 如果有临时消息，再增加1
        if self.temp_message and time.time() < self.temp_message_expiry:
            status_lines += 1

        # 跳过状态行，只比较日志内容
        if len(content) <= status_lines:
            return hash(tuple(content))
        
        log_content = content[status_lines:]
        return hash(tuple(log_content))
    
    def _update_display(self):
        """更新显示内容 - 核心刷新逻辑"""
        try:
            # 如果窗口是隐藏状态，只进行必要的后台处理但不更新显示
            if self.is_hidden:
                # 仍然获取日志内容以确保备份功能正常运行
                # 但不更新显示界面
                try:
                    # 获取日志内容但不显示
                    new_content = self.reader.get_content()
                    # 备份功能会在 reader 内部自动运行
                except Exception as e:
                    logging.debug(f"隐藏状态下获取日志内容时出错（正常继续）: {str(e)}")
                return
            
            new_content = self.reader.get_content()
            current_time = datetime.now()

            # 初始化变量
            content_changed = False
            color_changed = False
            text_color = self.normal_color  # 默认颜色

            # 如果返回的是错误信息，直接显示错误信息
            if new_content and "日志路径配置错误" in new_content[0]:
                display_content = new_content
                # 使用用户配置的 stale_color 显示错误信息
                text_color = self.stale_color
                content_changed = True  # 错误信息总是需要显示
                color_changed = True    # 颜色也需要更新
            else:
                # 构建显示内容：配置组 + 任务状态 + 日志内容
                config_display = f"[当前配置组] [{self.reader.current_config_progress}] {self.reader.current_config}"
                task_display = f"[当前任务] [{self.reader.current_progress}] {self.reader.current_task}"
                
                display_content = [
                    config_display,
                    task_display
                ] + new_content

                # 添加高频切换警告状态行
                if self.reader.high_frequency_warning:
                    display_content.insert(0, f"⚠️ 任务切换过于频繁 ({len(self.reader.task_switch_times)}次/分钟) ⚠️")
                
                # 新增：如果存在临时消息且未过期，插入到最顶部
                if self.temp_message and time.time() < self.temp_message_expiry:
                    display_content.insert(0, self.temp_message)

                # 如果启用自动换行，处理状态行的截断
                if self.config.get("auto_wrap", False):
                    display_content = self._truncate_status_lines(display_content)
                    
                # 限制最多显示行数
                max_display_lines = self.display_lines + 2  # 加上 2 行状态行
                if len(display_content) > max_display_lines:
                    display_content = display_content[:max_display_lines]

                # 判断是否需要更新
                stale_seconds = (current_time - self.last_change_time).total_seconds()
                # 比较日志内容
                content_hash = self._get_content_hash(display_content)
                prev_content_hash = self._get_content_hash(self._prev_content)
                content_changed = content_hash != prev_content_hash
                
                # 确定文本颜色（优先级：高频警告 > 超时警告 > 正常）
                if self.reader.high_frequency_warning:
                    text_color = self.high_freq_color
                elif stale_seconds > 60:  # 超过 60 秒无更新显示红色警告
                    text_color = self.stale_color
                else:
                    text_color = self.normal_color
                    
                color_changed = self.text.cget("fg") != text_color

                # 如果内容和颜色都未变化，跳过更新（除非是强制更新）
                if not content_changed and not color_changed and not hasattr(self, '_force_update'):
                    return

            # 动态调整窗口宽度
            self._adjust_window_width(display_content)

            # 执行界面更新
            self.text.config(state=tk.NORMAL)
            self.text.delete(1.0, tk.END)
            # 插入所有行
            self.text.insert(tk.END, '\n'.join(display_content))
            # 设置基本文本颜色
            self.text.config(fg=text_color)
            
            # 为DBG日志行添加特殊颜色
            if text_color == self.normal_color:  # 只在正常颜色模式下应用debug颜色
                self._apply_log_level_colors(display_content)

            # 根据状态行数动态计算索引
            if not (display_content and "日志路径配置错误" in display_content[0]):
                # 动态计算状态行数
                status_lines = 2
                if self.reader.high_frequency_warning:
                    status_lines = 3
                if self.temp_message and time.time() < self.temp_message_expiry:
                    status_lines += 1
                
                # 获取状态行和任务行颜色 - 从当前配置中获取最新值
                status_color = self.config.get("status_header_color", "#87CEFA")
                task_color = self.config.get("task_header_color", "#87CEFA")
                
                # 获取当前字体配置
                font_name = self.config.get("font_name", "Consolas")
                font_size = self.config.get("font_size", 10)
                font_weight = self.config.get("font_weight", "bold")
                
                # 配置字体样式
                status_font_config = (font_name, font_size, font_weight)
                task_font_config = (font_name, font_size, font_weight)
                # 删除现有标签（确保样式切换时标签被清除）
                self.text.tag_delete("config_header")
                self.text.tag_delete("task_header")
                self.text.tag_delete("high_freq_warning")
                self.text.tag_delete("temp_message")
                
                # 临时消息行样式（最顶部）
                if self.temp_message and time.time() < self.temp_message_expiry:
                    self.text.tag_configure("temp_message", foreground=self.temp_message_color)
                    self.text.tag_add("temp_message", "1.0", "1.end")
                    # 如果还有高频警告，它的行索引会变成第2行
                    warning_line_offset = 1
                else:
                    warning_line_offset = 0
                
                # 高频警告行样式
                if self.reader.high_frequency_warning:
                    warning_line = 1 + warning_line_offset
                    self.text.tag_configure(
                        "high_freq_warning",
                        foreground=self.high_freq_color,
                        font=(font_name, font_size, font_weight)
                    )
                    self.text.tag_add("high_freq_warning", f"{warning_line}.0", f"{warning_line}.end")
                    config_line = warning_line + 1
                else:
                    config_line = 1 + warning_line_offset
                
                # 配置组行样式
                self.text.tag_configure(
                    "config_header",
                    foreground=status_color,
                    font=status_font_config
                )
                self.text.tag_add("config_header", f"{config_line}.0", f"{config_line}.end")
                
                # 任务行样式
                task_line = config_line + 1
                self.text.tag_configure(
                    "task_header",
                    foreground=task_color,
                    font=task_font_config,
                    relief=tk.RIDGE,
                    borderwidth=2
                )
                self.text.tag_add("task_header", f"{task_line}.0", f"{task_line}.end")

            # 重新禁用编辑
            self.text.config(state='disabled')

            # 更新状态记录
            if content_changed:
                self.last_change_time = current_time
                self._prev_content = display_content
                
            # 清除强制更新标志
            if hasattr(self, '_force_update'):
                delattr(self, '_force_update')
                
            # 动态调整窗口高度
            if self.dynamic_height:
                try:
                    total_lines = int(self.text.index('end-1c').split('.')[0])
                    line_height = tkfont.Font(font=self.text['font']).metrics('linespace')
                    max_lines = self.display_lines + 2
                    # new_height = self.max_height
                    
                    new_height = min(total_lines, max_lines) * line_height
                    new_height = min(new_height, self.max_height)  # 限制不能超过 max_height

                    current_x = self.winfo_x()
                    current_y = self.winfo_y()
                    self.geometry(f"{self.current_width}x{int(new_height)}+{current_x}+{current_y}")
                except Exception as e:
                    logging.error(f"动态调整窗口高度失败: {str(e)}")
                    
        except Exception as e:
            # 记录详细的错误信息
            import traceback
            error_details = traceback.format_exc()
            logging.critical(f"更新显示时发生错误: {str(e)}")
            logging.critical(f"错误详情:\n{error_details}")
            
           # 尝试显示错误信息
            try:
                self.text.config(state=tk.NORMAL)
                self.text.delete(1.0, tk.END)
                self.text.insert(tk.END, f"错误: {str(e)}\n请检查日志获取详细信息")
                self.text.config(state='disabled')
            except:
                pass

    def _apply_log_level_colors(self, display_content):
        """为不同级别的日志行添加特殊颜色"""
        # 获取文本行数
        total_lines = int(self.text.index('end-1c').split('.')[0])
        
        #  计算状态行数（可能包含高頻警告行和临时消息）
        status_lines = 2  # 默认：配置组行 + 任务行
        if self.reader.high_frequency_warning:
            status_lines = 3  # 高频警告行 + 配置组行 + 任务行
        if self.temp_message and time.time() < self.temp_message_expiry:
            status_lines += 1  # 临时消息行
        
        # 从状态行之后开始检查不同级别的日志
        for tag_name in list(self.text.tag_names()):
            if tag_name.startswith("debug_") or tag_name.startswith("error_") or tag_name.startswith("warning_"):
                self.text.tag_delete(tag_name)
        
        # 從狀態行之後開始檢查不同級別的日誌
        current_line = status_lines + 1
        while current_line <= total_lines:
            # 获取行文本
            line_start = f"{current_line}.0"
            line_end = f"{current_line}.end"
            line_text = self.text.get(line_start, line_end)
            
            # 检查日志级别并设置对应颜色
            if ' DBG]' in line_text:
                color = self.debug_color
                tag_prefix = "debug"
            elif ' ERR]' in line_text:
                color = self.error_color
                tag_prefix = "error"
            elif ' WRN]' in line_text:
                color = self.warning_color
                tag_prefix = "warning"
            else:
                # 如果不是這些級別，檢查下一行
                current_line += 1
                continue
            
            # 创建唯一的标签名
            tag_name = f"{tag_prefix}_{current_line}"
            
            # 配置标签颜色
            self.text.tag_configure(tag_name, foreground=color)
            
            # 应用标签到整行
            self.text.tag_add(tag_name, line_start, line_end)
            
            # 處理換行後的後續行（如果有縮進標記，則視為同一日誌行的延續）
            next_line = current_line + 1
            while next_line <= total_lines:
                next_line_start = f"{next_line}.0"
                next_line_end = f"{next_line}.end"
                next_line_text = self.text.get(next_line_start, next_line_end)
                
                # 檢查是否是換行後的延續行（以縮進開頭）
                if next_line_text.startswith('　　') or next_line_text.startswith('  '):
                    # 創建延續行的標籤
                    next_tag_name = f"{tag_prefix}_cont_{next_line}"
                    self.text.tag_configure(next_tag_name, foreground=color)
                    self.text.tag_add(next_tag_name, next_line_start, next_line_end)
                    next_line += 1
                else:
                    break
            
            current_line = next_line  # 跳過已處理的行
    
    def _truncate_status_lines(self, content):
        """截断状态行，确保不换行"""
        if not content or len(content) < 2:
            return content
            
        # 确定状态行数
        status_lines = 2  # 默认：配置组行 + 任务行
        if content and content[0].startswith("⚠️"):
            status_lines = 3  # 高频警告行 + 配置组行 + 任务行
        
        # 对状态行进行硬截断
        truncated_content = []
        for i, line in enumerate(content):
            if i < status_lines:
                # 状态行：硬截断到 max_width 字符数（估算）
                max_chars = self.max_width // 8  # 估算字符数
                if len(line) > max_chars:
                    truncated_content.append(line[:max_chars])
                else:
                    truncated_content.append(line)
            else:
                # 日志内容行：保持原样，由换行逻辑处理
                truncated_content.append(line)
                
        return truncated_content

    def _adjust_window_width(self, content):
        """根據內容動態調整窗口尺寸 - 自適應寬度"""
        # 如果啟用自動換行，固定寬度為 max_width
        if self.config.get("auto_wrap", False):
            new_width = self.max_width
            if new_width != self.current_width:
                self.current_width = new_width
                current_x = self.winfo_x()
                current_y = self.winfo_y()
                self.geometry(f"{new_width}x{self.max_height}+{current_x}+{current_y}")
            return
        
        if not content:
            return
        
        try:
            # 使用字體緩存優化性能
            current_font_config = self.text['font']
            
            # 檢查字體配置是否發生變化
            if (self._font_cache is None or 
                self._last_font_config != current_font_config):
                
                self._font_cache = tkfont.Font(font=current_font_config)
                self._last_font_config = current_font_config
                logging.debug("字體緩存已更新")
            
            font = self._font_cache
            max_width = 0
            
            # 計算每行文本的像素寬度
            for line in content:
                try:
                    # 確保 measure 返回數值
                    line_width = float(font.measure(line))
                    if line_width > max_width:
                        max_width = line_width
                except (ValueError, TypeError) as e:
                    logging.warning(f"寬度計算失敗，行: {line[:50]}..., 錯誤: {str(e)}")
                    # 使用字符數估算
                    estimated_width = len(line) * 8  # 假設每個字符8像素
                    if estimated_width > max_width:
                        max_width = estimated_width
            
            # 添加邊距（左右各4像素）
            max_width += 8
            
            # 應用寬度限制（使用max_width作為最大寬度）
            try:
                config_max_width = float(self.max_width)
                max_width = min(max_width, config_max_width)
            except (ValueError, TypeError):
                # 如果轉換失敗，使用默認值
                max_width = min(max_width, 460)
                
            # 檢查是否需要調整寬度
            if max_width != self.current_width:
                self.current_width = int(max_width)
                
                # 使用當前窗口位置，而不是初始位置
                current_x = self.winfo_x()
                current_y = self.winfo_y()
                self.geometry(f"{int(max_width)}x{self.max_height}+{current_x}+{current_y}")

        except Exception as e:
            logging.error(f"寬度計算失敗: {str(e)}")
            self._fallback_width_calculation(content)

    def _fallback_width_calculation(self, content):
        """回退的宽度计算方法（当主要方法失败时使用）"""
        if content and any(content):  # 确保content有实际内容
            max_chars = max(len(line) for line in content)
            new_width = max_chars * 8 + 2# 8像素边距  # 估算字符宽度
            new_width = min(new_width, self.max_width)  # 不超过最大宽度
            if new_width != self.current_width:
                self.current_width = new_width
                # 使用当前窗口位置
                current_x = self.winfo_x()
                current_y = self.winfo_y()
                self.geometry(f"{new_width}x{self.max_height}+{current_x}+{current_y}")

    def destroy(self):
        """安全关闭程序 - 保存窗口位置和状态到config.txt"""
        # 如果在隐藏状态，先恢复显示以确保正确保存状态
        if self.is_hidden:
            self._restore_normal_display()
        
        # 清理字體緩存
        if hasattr(self, '_font_cache'):
            self._font_cache = None
        if hasattr(self.reader, '_font_cache'):
            self.reader._font_cache = None
            
        # 停止日志备份功能
        if hasattr(self, 'reader') and hasattr(self.reader, 'stop_backup'):
            self.reader.stop_backup()
        
        # 停止全局快捷键监听
        if hasattr(self, 'shortcut_manager'):
            self.shortcut_manager.stop_listening()
        
        # 确保禁用鼠标穿透
        self._set_window_click_through(False)
        
        # 使用当前窗口位置
        current_x = self.winfo_x()
        current_y = self.winfo_y()
        self.config.save_window_state(current_x, current_y, self.transparent_mode, self.click_through, self.author_style2_active)
        logging.info(f"程序关闭，保存窗口位置到config.txt: ({current_x}, {current_y}), 透明模式: {self.transparent_mode}, 不可选中模式: {self.click_through}, 仿BGI日志窗口样式: {self.author_style2_active}")
        
        self.monitor_running = False
        super().destroy()

if __name__ == "__main__":
    try:
        # 加载配置并启动程序
        config_loader = ConfigLoader("config.txt")
        
        # 可選：保留日誌記錄，移除print
        backup_path = config_loader.get("backup_path", "")
        if backup_path:
            logging.info(f"備份功能已啟用 - 路徑: {backup_path}")
            logging.info(f"備份間隔: {config_loader.get('backup_interval', 60)} 分鐘, 保留天數: {config_loader.get('backup_keep_days', 10)} 天")
        
        viewer = FloatingLogViewer(config_loader)
        viewer.mainloop()
    except Exception as e:
        logging.critical(f"程序崩溃: {str(e)}")
        # 使用頂部導入的 KEYBOARD_MODULE，避免重複導入
        if KEYBOARD_AVAILABLE and KEYBOARD_MODULE is not None:
            try:
                KEYBOARD_MODULE.unhook_all()  # 使用保存的模組引用
                logging.info("程序崩溃时清理全局快捷键")
            except Exception as cleanup_error:
                logging.warning(f"清理快捷键时发生错误: {cleanup_error}")
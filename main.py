# 1.3.5
__author__ = "蜜柑魚"

import ctypes
import tkinter as tk
import tkinter.font as tkfont
import re
import time
import os
import sys
import logging
from datetime import datetime 
from pathlib import Path
from collections import deque
import threading
import queue
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    logging.warning("keyboard 库未安装，全局快捷键不可用")
    # 创建虚拟的 KeyboardEvent 类以避免 NameError
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
    def __init__(self, config_file="config.txt"):
        """配置文件加载器 - 从config.txt读取用户设置"""
        script_dir = get_base_path()
        self.config_file = Path(script_dir) / config_file
        
        # 默认配置值
        self.default_config = {
            "log_path": "",  # 原神日志文件目录路径
            "log_filename_prefix": "better-genshin-impact",  # 日志文件名前缀
            "skip_debug_log": False,  # 是否跳过调试日志
            "window_alpha": 0.7,      # 窗口透明度
            "bg_color": "#000000",    # 背景颜色
            "normal_color": "#00FF00",# 正常状态文字颜色
            "stale_color": "#FF0000", # 超时警告颜色
            "high_freq_color": "#FFA500", # 高频切换警告颜色
            "status_header_color": "#87CEFA",  # 状态行标题颜色（配置组行）
            "task_header_color": "#87CEFA",    # 任务行标题颜色
            "font_name": "Consolas",  # 字体名称
            "font_size": 11,          # 字体大小
            "font_weight": "bold",    # 字体粗细
            "max_height": 220,        # 窗口最大高度
            "max_width": 460,        # 窗口最大宽度
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
            "status_header_color": "#00FF00",  # 第二样式的状态行颜色
            "task_header_color": "#00FFFF",   # 第二样式的任务行颜色
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
        
        # 加载所有配置
        self.load_all_settings()
        
        # 保存初始的日志路径配置
        self.initial_log_path = self.config.get("log_path", "")
        self.initial_log_filename_prefix = self.config.get("log_filename_prefix", "better-genshin-impact")
        self.initial_log_path_configured = self.log_path_configured
        
        # 如果配置中启用了第二样式，则应用
        if self.config.get("author_style2", False):
            self.apply_second_style()

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
                # 简化处理：空字符串或无效值都设为 None
                if value and value.strip():
                    self.config[key] = int(value)
                    self.user_config[key] = int(value)
                else:
                    self.config[key] = None
                    self.user_config[key] = None
                    
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
                        # 保留行尾的注释
                        comment_part = ""
                        if '#' in original_value:
                            value_part, comment_part = original_value.split('#', 1)
                            comment_part = '#' + comment_part
                        
                        # 更新配置值
                        new_line = f"{key}={updates[key]}{comment_part}\n"
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
        
    def start_listening(self):
        """启动全局快捷键监听"""
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
        if not KEYBOARD_AVAILABLE:
            return
        try:
            keyboard.unhook_all()
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
            
            # 注册全局快捷键 - 使用更简单的lambda函数
            keyboard.add_hotkey('alt+p', self._create_event_callback('close'), suppress=True)
            keyboard.add_hotkey('alt+u', self._create_event_callback('reset_position'), suppress=True)
            keyboard.add_hotkey('alt+i', self._create_event_callback('toggle_transparent'), suppress=True)
            keyboard.add_hotkey('alt+n', self._create_event_callback('toggle_click_through'), suppress=True)
            keyboard.add_hotkey('alt+k', self._create_event_callback('toggle_second_style'), suppress=True)
            
            self.hotkeys_registered = True
            logging.info("全局快捷键注册完成: Alt+P(关闭), Alt+U(重置位置), Alt+I(透明模式), Alt+N(不可选中), Alt+K(第二样式)")
            return True
            
        except Exception as e:
            logging.error(f"注册全局快捷键失败: {str(e)}")
            self.hotkeys_registered = False
            return False
    
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
                
        except Exception as e:
            logging.error(f"处理快捷键事件失败: {str(e)}")
            # 不重新抛出异常，防止事件处理循环中断
    
    def stop_listening(self):
        """停止监听 - 增强版本"""
        self.listening = False
        self._safe_unhook_all()
        logging.info("全局快捷键监听已停止")

class SmartLogReader:
    def __init__(self, log_dir, log_filename_prefix, log_path_configured, display_lines=11, skip_debug_log=False, dynamic_height=False, auto_wrap=False, max_width=460, font_config=None):
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
        
        # 任务进度信息
        self.current_progress = "0/0"
        self.task_progress = {}  # 任务进度缓存
        
        # 任务切换频率监测
        self.task_switch_times = deque(maxlen=10)  # 存储最近10次任务切换时间
        self.high_frequency_warning = False  # 高频切换警告状态
        self.high_frequency_start = None     # 高频状态开始时间

        # 任务检测正则表达式 - 匹配不同类型的任务
        self.task_patterns = {
            "JS脚本": re.compile(r'→ 开始执行JS脚本: "(.+?)"'),
            "配置文件": re.compile(r'assets/(.+?\.json)'),
            "地图任务": re.compile(r'→ 开始执行(?:地图|路径)追踪任务: "(.+?)"'),
            "钓鱼点": re.compile(r'当前钓鱼点:\s*([^\n]+)'),
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
            "组任务进度": re.compile(r'开始处理第\s*(\d+)\s*组第\s*(\d+)/(\d+)\s*个([^\.]+\.json)'),
            "钓鱼点进度": re.compile(r'当前钓鱼点:[^(]+\(进度:\s*(\d+)/(\d+)\)'),  # 新增钓鱼点进度
            "产出进度": re.compile(r'当前产出(?:（.*?）)?：\s*(\d+)(?:/(\d+))?\s*个'),
            "运行时间进度": re.compile(r'当前运行时间：([\d.]+)/(\d+)分钟'),  # 保持不变，只匹配有总时间的情况
            # 新增：循环执行进度格式 - 匹配 "正在执行 夏栎木 第 9/56 次循环"
            "循环执行进度": re.compile(r'正在执行\s+([^\s]+)\s+第\s*(\d+)/(\d+)\s*次循环')
        }

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
        if today != self.current_date:
            logging.info(f"检测到日期变更 {self.current_date} → {today}")
            self.current_date = today
            self._update_log_file()
            return True
        return False

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
        """高效获取文件尾部内容 - 优化大文件处理性能"""
        if not self.log_path_valid or not self._current_file or not self._current_file.exists():
            return None

        try:
            with open(self._current_file, 'rb') as f:
                f.seek(0, 2)  # 移动到文件末尾
                file_size = f.tell()
                block_size = 1024
                data = []
                lines_found = 0

                # 逆向块读取 - 从文件末尾向前读取
                while lines_found < lines and file_size > 0:
                    read_size = min(block_size, file_size)
                    file_size -= read_size
                    f.seek(file_size)
                    block = f.read(read_size)
                    decoded = block.decode('utf-8', 'ignore')
                    
                    # 过滤空行并统计
                    non_empty_lines = [line for line in decoded.split('\n') if line.strip()]
                    lines_found += len(non_empty_lines)
                    data.append('\n'.join(non_empty_lines))

                # 合并处理结果 - 保持原始顺序（旧在上，新在下）
                text = ''.join(reversed(data)).splitlines()
                return text[-lines:]  # 返回最后lines行
        except Exception as e:
            logging.error(f"文件读取错误: {str(e)}")
            return None

    def _filter_debug_logs(self, lines):
        """过滤调试日志 - 跳过包含[DBG]的行"""
        if not self.skip_debug_log:
            return lines
            
        filtered_lines = []
        for line in lines:
            # 跳过包含[DBG]的调试日志行
            if '[DBG]' not in line:
                filtered_lines.append(line)
        
        return filtered_lines

    def _detect_task_switching(self, new_task):
        """检测任务切换频率 - 识别异常高频切换（修复版本）"""
        now = time.time()
        
        # 只在任务实际变化时记录
        if new_task != self.current_task and new_task != "无当前任务":
            self.task_switch_times.append(now)
            
            # 清理超过1分钟的记录
            while self.task_switch_times and (now - self.task_switch_times[0] > 60):
                self.task_switch_times.popleft()
            
            # 检查1分钟内是否超过5次切换
            if len(self.task_switch_times) >= 5:
                if not self.high_frequency_warning:
                    self.high_frequency_warning = True
                    self.high_frequency_start = now
                    logging.warning("任务切换过于频繁！")
                    # 注意：这里不进行任何可能影响快捷键的操作
            else:
                # 只有当切换次数真正减少时才取消警告
                if self.high_frequency_warning and len(self.task_switch_times) < 3:
                    self.high_frequency_warning = False
                    logging.info("高频任务切换状态结束")
                
        # 检查高频状态是否已结束（超过2分钟无新警告）
        if self.high_frequency_warning and (now - self.high_frequency_start > 120):
            self.high_frequency_warning = False
            logging.info("高频任务切换状态自动结束")
            
    def _format_log_line(self, line):
        """格式化日志行 - 移除类名部分，简化显示"""
        match = self.log_format_pattern.match(line)
        if match:
            timestamp = match.group(1)
            log_level = match.group(2)
            message = match.group(3) or ""  # 确保消息不为None
            
            # 特殊处理配置组信息 - 保持完整显示
            if "配置组" in message:
                return f"{timestamp[:-5]} {log_level}] {message}"
            
            # 完全移除类名部分 - 简化显示
            return f"{timestamp[:-5]} {log_level}] {message}"
        return line  # 如果无法匹配，返回原始行

    def _extract_progress_info(self, line):
        """从日志行中提取进度信息 - 支持多种进度格式"""
        for progress_type, pattern in self.progress_patterns.items():
            match = pattern.search(line)
            if match:
                groups = match.groups()
                try:
                    if progress_type == "任务开始进度" and len(groups) >= 3:
                        current, total, task_name = groups[:3]
                        # 缓存这个任务的进度信息
                        self.task_progress[task_name] = f"{current}/{total}"
                        return f"{current}/{total}"
                    elif progress_type == "当前进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return f"{current}/{total}"
                    elif progress_type == "组任务进度" and len(groups) >= 4:
                        group_num, current, total, task_name = groups[:4]
                        return f"{current}/{total}"
                    # 新增：钓鱼点进度格式
                    elif progress_type == "钓鱼点进度" and len(groups) >= 2:
                        current, total = groups[:2]
                        return f"{current}/{total}"
                     # 新增：循环执行进度格式
                    elif progress_type == "循环执行进度" and len(groups) >= 3:
                        item_name, current, total = groups[:3]
                        # 对于循环执行，我们可以显示为 "9/56次" 或者直接 "9/56"
                        return f"{current}/{total}"
                    # 修改：产出进度格式 - 处理无目标值的情况
                    elif progress_type == "产出进度":
                        if len(groups) >= 2:
                            current, total = groups[:2]
                            if total is not None:  # 有目标值
                                return f"{current}/{total}个"
                            else:  # 无目标值
                                return f"{current}/∞个"
                        elif len(groups) >= 1 and groups[0] is not None:
                            # 只有当前值，无目标值
                            return f"{groups[0]}/∞个"
                    # 修改：运行时间进度格式 - 确保正确处理
                    elif progress_type == "运行时间进度" and len(groups) >= 2:
                        # 礦JS本體做好日志秒數顯示轉換的話
                        # current_time, total_time = groups[:2]
                        # return f"{current_time}/{total_time}分钟"  # 添加單位

                        current_time, total_time = groups[:2]
                        # 将小数分钟转换为分钟:秒格式（秒数四舍五入）
                        try:
                            current_minutes = float(current_time)
                            minutes = int(current_minutes)
                            seconds = round((current_minutes - minutes) * 60)  # 四舍五入到整数秒
                            
                            # 处理四舍五入后可能出现60秒的情况
                            if seconds == 60:
                                minutes += 1
                                seconds = 0
                                
                            # 格式化为 分钟.秒 (秒数显示两位数)
                            formatted_time = f"{minutes}.{seconds:02d}"
                            return f"{formatted_time}/{total_time}分钟"
                        except (ValueError, TypeError):
                            # 如果转换失败，返回原始格式
                            return f"{current_time}/{total_time}分钟"
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
        latest_progress = self.current_progress

        # 优先搜索进度信息，然后才是任务和配置信息
        progress_found = False
        task_found = False
        config_found = False
        
        # 逆向搜索日志内容 - 从最新日志开始搜索
        for line in reversed(full_content):
            # 1. 优先搜索进度信息（最重要）
            if not progress_found:
                progress_info = self._extract_progress_info(line)
                if progress_info:
                    latest_progress = progress_info
                    progress_found = True
            
            # 2. 然后搜索配置信息
            if not config_found:
                if config_match := self.config_pattern.search(line):
                    config_name = config_match.group(1)
                    # 只更新"加载完成"或"开始执行"的配置组
                    if "加载完成" in line or "开始执行" in line:
                        latest_config = config_name
                        config_found = True
            
            # 3. 最后搜索任务信息
            if not task_found:
                for task_type, pattern in self.task_patterns.items():
                    if match := pattern.search(line):
                        task_name = match.group(1).strip()
                        
                        # 特殊处理：对于钓鱼点任务，保持完整的任务名称
                        if task_type == "钓鱼点":
                            # 钓鱼点任务名称保持原样，不进行路径和扩展名处理
                            latest_task = f"{task_type}: {task_name}"
                        else:
                            # 其他任务类型：提取纯文件名（不含路径和扩展名）
                            if '/' in task_name or '\\' in task_name:
                                # 提取文件名（含扩展名）
                                base_name = os.path.basename(task_name)
                                # 移除扩展名，获取纯文件名
                                task_name = os.path.splitext(base_name)[0]
                            elif '.' in task_name:
                                # 如果只有文件名但包含扩展名，也移除扩展名
                                task_name = os.path.splitext(task_name)[0]
                            
                            latest_task = f"{task_type}: {task_name}"
                        task_found = True
                        break  # 一行通常只匹配一个任务类型
            
            # 如果所有信息都已找到，提前退出循环
            if progress_found and task_found and config_found:
                break

        # 最终更新状态
        self.current_config = latest_config
        self.current_task = latest_task
        self.current_progress = latest_progress

        # 检测任务切换频率
        self._detect_task_switching(previous_task)

        # 格式化日志行（只对要显示的内容进行格式化）
        display_content = filtered_content[-self.display_lines:] if len(filtered_content) > self.display_lines else filtered_content
        
        # 新增：如果启用自动换行，处理换行
        if self.auto_wrap:
            formatted_content = []
            for line in display_content:
                formatted_line = self._format_log_line(line)
                wrapped_lines = self._wrap_text_line(formatted_line)
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
        if not self.auto_wrap or not line.strip():
            return [line]
            
        font = self._get_font()
        if not font:
            return [line]  # 无法获取字体时返回原行
            
        try:
             # 计算缩进宽度（两个全角空格）
            indent = "　　"
            indent_width = font.measure(indent)
            # 计算可用宽度（减去边距）
            available_width = self.max_width - indent_width - 2# 8像素边距
            
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
            auto_wrap,        # 新增
            max_width,        # 新增
            font_config       # 新增
        )
        self._prev_content = []  # 上一次显示的内容
        self.last_change_time = datetime.now()  # 最后内容变更时间
        
        # 颜色配置
        self.normal_color = config.get("normal_color", "#00FF00")
        self.stale_color = config.get("stale_color", "#FF0000")
        self.high_freq_color = config.get("high_freq_color", "#FFA500")
        
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
        if not KEYBOARD_AVAILABLE:
            # 只有全局快捷键不可用时才设置窗口内快捷键
            self.bind("<Alt-KeyPress-p>", self._on_close_shortcut)
            self.bind("<Alt-KeyPress-P>", self._on_close_shortcut)
            self.bind("<Alt-KeyPress-u>", self._on_reset_position_shortcut)
            self.bind("<Alt-KeyPress-U>", self._on_reset_position_shortcut)
            self.bind("<Alt-KeyPress-i>", self._on_transparent_toggle_shortcut)
            self.bind("<Alt-KeyPress-I>", self._on_transparent_toggle_shortcut)
            self.bind("<Alt-KeyPress-n>", self._on_click_through_toggle_shortcut)
            self.bind("<Alt-KeyPress-N>", self._on_click_through_toggle_shortcut)
            logging.info("全局快捷键不可用，已启用窗口内快捷键: Alt+P(关闭), Alt+U(重置位置), Alt+I(透明模式), Alt+N(不可选中)")
        else:
            logging.info("全局快捷键可用，窗口内快捷键已禁用")
            
        self.focus_set()  # 确保窗口能够接收键盘事件

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
        
        # 更新窗口属性 - 使用max_width和max_height
        self.max_width = self.config.get("max_width", 460)
        self.max_height = self.config.get("max_height", 220)
        self.display_lines = self.config.get("display_lines", 11)
        self.refresh_interval = self.config.get("refresh_interval", 1000)
        
        # 清理字体缓存
        self.clear_font_cache()
        
        # 删除所有文本标签，确保样式完全重置
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
        
        # 更新窗口尺寸 - 使用max_width和max_height
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
            font_config_dict
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
        """启动自动刷新循环 - 定时更新日志显示"""
        def update_loop():
            try:
                self._update_display()
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
        
        # 跳过状态行，只比较日志内容
        if len(content) <= status_lines:
            return hash(tuple(content))
        
        log_content = content[status_lines:]
        return hash(tuple(log_content))
    
    def _update_display(self):
        """更新显示内容 - 核心刷新逻辑"""
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
            # 构建显示内容：配置组+任务状态 + 日志内容
            task_display = f"[当前任务] [{self.reader.current_progress}] {self.reader.current_task}"
            
            display_content = [
                f"[当前配置组] {self.reader.current_config}",
                task_display
            ] + new_content

            # 添加高频切换警告状态行
            if self.reader.high_frequency_warning:
                display_content.insert(0, f"⚠️ 任务切换过于频繁 ({len(self.reader.task_switch_times)}次/分钟) ⚠️")
                
            # 如果启用自动换行，处理状态行的截断
            if self.config.get("auto_wrap", False):
                display_content = self._truncate_status_lines(display_content)
                
            # 限制最多显示行数
            max_display_lines = self.display_lines + 2  # 加上2行状态行
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
            elif stale_seconds > 60:  # 超过60秒无更新显示红色警告
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
        self.text.insert(tk.END, '\n'.join(display_content))
        self.text.config(fg=text_color)

        # 根据状态行数动态计算索引
        if not (display_content and "日志路径配置错误" in display_content[0]):
            # 动态计算状态行数
            status_lines = 2
            if self.reader.high_frequency_warning:
                status_lines = 3
            
            # 获取分开的状态行和任务行颜色 - 从当前配置中获取最新值
            status_color = self.config.get("status_header_color", "#87CEFA")
            task_color = self.config.get("task_header_color", "#87CEFA")
            
            # 获取当前字体配置 - 从当前配置中获取最新值
            font_name = self.config.get("font_name", "Consolas")
            font_size = self.config.get("font_size", 10)
            font_weight = self.config.get("font_weight", "bold")
            
            # 配置字体样式 - 使用从配置中获取的最新值
            status_font_config = (font_name, font_size, font_weight)
            task_font_config = (font_name, font_size, font_weight)
            # 删除现有标签（确保样式切换时标签被清除）
            self.text.tag_delete("config_header")
            self.text.tag_delete("task_header")
            self.text.tag_delete("high_freq_warning")
            
            # 配置组行特殊样式 - 使用当前配置的状态行颜色和字体
            config_line = 1 if status_lines == 2 else 2
            self.text.tag_configure("config_header", 
                                foreground=status_color,
                                font=status_font_config)
            self.text.tag_add("config_header", f"{config_line}.0", f"{config_line}.end")
            
            # 任务行样式 - 使用当前配置的任务行颜色和字体
            task_line = 2 if status_lines == 2 else 3
            self.text.tag_configure("task_header", 
                                foreground=task_color,
                                font=task_font_config,
                                relief=tk.RIDGE,
                                borderwidth=2)
            self.text.tag_add("task_header", f"{task_line}.0", f"{task_line}.end")
            
            # 高频警告行样式
            if self.reader.high_frequency_warning:
                self.text.tag_configure("high_freq_warning", 
                                    foreground=self.high_freq_color,
                                    font=(font_name, font_size, font_weight))
                self.text.tag_add("high_freq_warning", "1.0", "1.end")

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
                max_lines =  self.display_lines+2
                new_height = self.max_height
                
                new_height = min(total_lines, max_lines) * line_height
                new_height = min(new_height, self.max_height)  # 限制不能超过 max_height

                current_x = self.winfo_x()
                current_y = self.winfo_y()
                self.geometry(f"{self.current_width}x{int(new_height)}+{current_x}+{current_y}")
            except Exception as e:
                logging.error(f"动态调整窗口高度失败: {str(e)}")

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
        """根据内容动态调整窗口尺寸 - 自适应宽度"""
        # 如果启用自动换行，固定宽度为 max_width
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
            # 使用字体缓存优化性能
            current_font_config = self.text['font']
            
            # 检查字体配置是否发生变化
            if (self._font_cache is None or 
                self._last_font_config != current_font_config):
                
                self._font_cache = tkfont.Font(font=current_font_config)
                self._last_font_config = current_font_config
                logging.debug("字体缓存已更新")
            
            font = self._font_cache
            max_width = 0
            
            # 计算每行文本的像素宽度
            for line in content:
                line_width = font.measure(line)
                if line_width > max_width:
                    max_width = line_width
            
            # 添加边距（左右各4像素）
            max_width += 2# 8像素边距
            
            # 应用宽度限制（使用max_width作为最大宽度）
            max_width = min(max_width, self.max_width)
                
            # 检查是否需要调整宽度
            if max_width != self.current_width:
                self.current_width = max_width
                
                # 使用当前窗口位置，而不是初始位置
                current_x = self.winfo_x()
                current_y = self.winfo_y()
                self.geometry(f"{max_width}x{self.max_height}+{current_x}+{current_y}")

        except Exception as e:
            logging.error(f"宽度计算失败: {str(e)}")
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
        viewer = FloatingLogViewer(config_loader)
        viewer.mainloop()
    except Exception as e:
        logging.critical(f"程序崩溃: {str(e)}")
        # 确保在崩溃时也清理全局快捷键
        if KEYBOARD_AVAILABLE:
            try:
                import keyboard
                keyboard.unhook_all()
                logging.info("程序崩溃时清理全局快捷键")
            except:
                pass
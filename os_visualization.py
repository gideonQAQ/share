import sys
import os
import time
import random
import threading
import multiprocessing
# 强制绑定Matplotlib Qt5后端（Windows绘图核心适配）
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches as patches
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, 
    QPushButton, QLabel, QListWidget, QTextEdit, QHBoxLayout
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QTextCharFormat, QFont

# ======================== 全局适配配置（Windows核心） ========================
# 1. 打包后路径适配（EXE运行时的资源路径）
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 2. Matplotlib字体适配（Windows自带字体）
def setup_matplotlib_font():
    try:
        # 优先加载微软雅黑（Windows默认）
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    except:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示
    plt.rcParams['figure.facecolor'] = 'white'  # 画布背景色（避免透明）

setup_matplotlib_font()

# ======================== 模块1：进程与线程的创建与管理 ========================
class ProcessThread(QThread):
    """模拟进程运行线程（触发状态变更信号）"""
    state_change_signal = pyqtSignal(int, str)  # (进程ID, 新状态)
    finished_signal = pyqtSignal(int)           # (进程ID)

    def __init__(self, pid, parent=None):
        super().__init__(parent)
        self.pid = pid
        self.running = False
        self.current_state = "就绪"  # 初始状态：就绪

    def run(self):
        """模拟进程运行逻辑"""
        self.running = True
        self.current_state = "运行"
        self.state_change_signal.emit(self.pid, self.current_state)
        # 模拟运行3-5秒后自动终止（可根据需要调整）
        run_time = random.randint(3, 5)
        for i in range(run_time):
            if not self.running:
                break
            self.msleep(1000)
        if self.running:
            self.current_state = "终止"
            self.state_change_signal.emit(self.pid, self.current_state)
            self.finished_signal.emit(self.pid)

    def block(self):
        """阻塞进程"""
        if self.current_state == "运行":
            self.current_state = "阻塞"
            self.state_change_signal.emit(self.pid, self.current_state)
            self.running = False

    def wake(self):
        """唤醒进程"""
        if self.current_state == "阻塞":
            self.current_state = "就绪"
            self.state_change_signal.emit(self.pid, self.current_state)

    def stop(self):
        """强制停止进程"""
        self.running = False

class ProcessManagement(QWidget):
    def __init__(self):
        super().__init__()
        # 进程状态管理
        self.process_id_counter = 0  # 进程ID计数器
        self.ready_queue = []        # 就绪队列
        self.running_process = None  # 运行中的进程（单核仅1个）
        self.blocked_queue = []      # 阻塞队列
        self.terminated_processes = []  # 终止进程
        self.process_threads = {}    # 进程线程映射 {pid: thread}
        # 可视化画布
        self.figure = plt.Figure(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        # 初始化UI
        self.init_ui()
        # 初始绘制可视化界面
        self.plot_process_states()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 1. 控制按钮区域
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("创建5个进程")
        self.create_btn.clicked.connect(self.create_processes)
        self.schedule_btn = QPushButton("调度运行（就绪→运行）")
        self.schedule_btn.clicked.connect(self.schedule_process)
        self.block_btn = QPushButton("阻塞当前进程（运行→阻塞）")
        self.block_btn.clicked.connect(self.block_running_process)
        self.wake_btn = QPushButton("唤醒首个阻塞进程（阻塞→就绪）")
        self.wake_btn.clicked.connect(self.wake_blocked_process)
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.schedule_btn)
        btn_layout.addWidget(self.block_btn)
        btn_layout.addWidget(self.wake_btn)
        layout.addLayout(btn_layout)

        # 2. 进程状态文字展示区
        state_text_layout = QHBoxLayout()
        self.ready_label = QLabel(f"就绪队列：{self.ready_queue}")
        self.ready_label.setStyleSheet("color: #4169E1; font-size: 14px;")
        self.running_label = QLabel(f"运行进程：{self.running_process if self.running_process else '无'}")
        self.running_label.setStyleSheet("color: #228B22; font-size: 14px;")
        self.blocked_label = QLabel(f"阻塞队列：{self.blocked_queue}")
        self.blocked_label.setStyleSheet("color: #FF8C00; font-size: 14px;")
        self.terminated_label = QLabel(f"终止进程：{self.terminated_processes}")
        self.terminated_label.setStyleSheet("color: #808080; font-size: 14px;")
        state_text_layout.addWidget(self.ready_label)
        state_text_layout.addWidget(self.running_label)
        state_text_layout.addWidget(self.blocked_label)
        state_text_layout.addWidget(self.terminated_label)
        layout.addLayout(state_text_layout)

        # 3. 可视化图形展示区
        plot_title = QLabel("<b>进程状态流转可视化（就绪=蓝/运行=绿/阻塞=橙/终止=灰）</b>")
        layout.addWidget(plot_title)
        layout.addWidget(self.canvas)

        # 4. 操作日志区
        self.log_label = QLabel("<b>进程操作日志</b>")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(120)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log)

        self.setLayout(layout)

    def plot_process_states(self):
        """绘制进程状态可视化图形（Windows适配）"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 20)
        ax.axis('off')  # 关闭坐标轴

        # 绘制区域标题（Windows字体适配）
        ax.text(15, 18, "就绪队列", fontsize=12, fontweight='bold', ha='center')
        ax.text(50, 18, "运行区", fontsize=12, fontweight='bold', ha='center')
        ax.text(85, 18, "阻塞队列", fontsize=12, fontweight='bold', ha='center')
        # 绘制区域分隔线
        ax.axvline(x=30, ymin=0.1, ymax=0.9, color='black', linestyle='--', linewidth=1)
        ax.axvline(x=70, ymin=0.1, ymax=0.9, color='black', linestyle='--', linewidth=1)

        # 状态颜色映射
        color_map = {
            "就绪": '#4169E1',
            "运行": '#228B22',
            "阻塞": '#FF8C00',
            "终止": '#808080'
        }

        # 1. 绘制就绪队列进程（左侧区域）
        ready_y = 15
        for pid in self.ready_queue:
            # 进程卡片：矩形+进程ID文字
            rect = patches.Rectangle((5, ready_y-2), 20, 3, 
                                   facecolor=color_map["就绪"], edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            ax.text(15, ready_y-0.5, f"进程{pid}", ha='center', va='center', 
                   fontsize=10, color='white', fontweight='bold')
            ready_y -= 4  # 向下排列

        # 2. 绘制运行进程（中间区域）
        if self.running_process is not None:
            rect = patches.Rectangle((35, 8), 30, 4, 
                                   facecolor=color_map["运行"], edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            ax.text(50, 10, f"进程{self.running_process}", ha='center', va='center', 
                   fontsize=12, color='white', fontweight='bold')

        # 3. 绘制阻塞队列进程（右侧区域）
        blocked_y = 15
        for pid in self.blocked_queue:
            rect = patches.Rectangle((75, blocked_y-2), 20, 3, 
                                   facecolor=color_map["阻塞"], edgecolor='black', linewidth=2)
            ax.add_patch(rect)
            ax.text(85, blocked_y-0.5, f"进程{pid}", ha='center', va='center', 
                   fontsize=10, color='white', fontweight='bold')
            blocked_y -= 4

        # 4. 绘制终止进程（底部区域）
        terminated_x = 5
        for pid in self.terminated_processes:
            rect = patches.Rectangle((terminated_x, 2), 8, 2, 
                                   facecolor=color_map["终止"], edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            ax.text(terminated_x+4, 3, f"进程{pid}", ha='center', va='center', 
                   fontsize=8, color='white')
            terminated_x += 10

        # 刷新画布（Windows强制刷新）
        self.canvas.draw()
        self.canvas.flush_events()

    def update_text_labels(self):
        """更新进程状态文字标签"""
        self.ready_label.setText(f"就绪队列：{self.ready_queue}")
        self.running_label.setText(f"运行进程：{self.running_process if self.running_process else '无'}")
        self.blocked_label.setText(f"阻塞队列：{self.blocked_queue}")
        self.terminated_label.setText(f"终止进程：{self.terminated_processes}")

    def add_log(self, text, color="black"):
        """添加操作日志（带时间戳，Windows线程安全）"""
        format_char = QTextCharFormat()
        color_map = {
            "就绪": QColor(65, 105, 225),
            "运行": QColor(34, 139, 34),
            "阻塞": QColor(255, 140, 0),
            "终止": QColor(128, 128, 128),
            "black": QColor(0, 0, 0)
        }
        format_char.setForeground(color_map.get(color, QColor(0,0,0)))
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(f"[{time.strftime('%H:%M:%S')}] {text}\n", format_char)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def create_processes(self):
        """创建5个进程，加入就绪队列"""
        new_pids = []
        for _ in range(5):
            self.process_id_counter += 1
            pid = self.process_id_counter
            self.ready_queue.append(pid)
            # 创建进程线程（初始就绪，未运行）
            self.process_threads[pid] = ProcessThread(pid)
            # 绑定状态变更信号
            self.process_threads[pid].state_change_signal.connect(self.on_process_state_change)
            self.process_threads[pid].finished_signal.connect(self.on_process_finished)
            new_pids.append(pid)
        # 更新UI
        self.update_text_labels()
        self.plot_process_states()
        self.add_log(f"创建5个进程：{new_pids}，加入就绪队列", "就绪")

    def schedule_process(self):
        """调度就绪队列首个进程到运行区"""
        if not self.ready_queue:
            self.add_log("就绪队列为空，无法调度！", "black")
            return
        if self.running_process is not None:
            self.add_log(f"当前已有运行进程{self.running_process}，无法调度！", "black")
            return
        # 取出就绪队列首个进程
        pid = self.ready_queue.pop(0)
        self.running_process = pid
        # 启动进程线程
        self.process_threads[pid].start()
        # 更新UI
        self.update_text_labels()
        self.plot_process_states()
        self.add_log(f"调度进程{pid}：就绪→运行", "运行")

    def block_running_process(self):
        """阻塞当前运行进程"""
        if self.running_process is None:
            self.add_log("无运行进程，无法阻塞！", "black")
            return
        pid = self.running_process
        # 阻塞进程线程
        self.process_threads[pid].block()
        # 从运行区移到阻塞队列
        self.running_process = None
        self.blocked_queue.append(pid)
        # 更新UI
        self.update_text_labels()
        self.plot_process_states()
        self.add_log(f"阻塞进程{pid}：运行→阻塞", "阻塞")

    def wake_blocked_process(self):
        """唤醒阻塞队列首个进程"""
        if not self.blocked_queue:
            self.add_log("阻塞队列为空，无法唤醒！", "black")
            return
        pid = self.blocked_queue.pop(0)
        # 唤醒进程线程
        self.process_threads[pid].wake()
        # 移到就绪队列
        self.ready_queue.append(pid)
        # 更新UI
        self.update_text_labels()
        self.plot_process_states()
        self.add_log(f"唤醒进程{pid}：阻塞→就绪", "就绪")

    def on_process_state_change(self, pid, new_state):
        """进程状态变更回调（更新UI）"""
        self.add_log(f"进程{pid}状态变更：{new_state}", new_state)
        self.update_text_labels()
        self.plot_process_states()

    def on_process_finished(self, pid):
        """进程终止回调"""
        # 从运行区移除，加入终止列表
        self.running_process = None
        self.terminated_processes.append(pid)
        # 停止进程线程
        self.process_threads[pid].stop()
        # 更新UI
        self.update_text_labels()
        self.plot_process_states()
        self.add_log(f"进程{pid}运行结束：运行→终止", "终止")

# ======================== 模块2：进程间通信（IPC）- 管道（修复除以0错误） ========================
class IPCProducerThread(QThread):
    """生产者线程（通过信号传递数据到主线程）"""
    send_signal = pyqtSignal(str)  # 发送数据信号
    count_signal = pyqtSignal(int) # 计数更新信号
    speed_signal = pyqtSignal(str) # 速率更新信号
    finished_signal = pyqtSignal() # 结束信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.data_count = 0
        self.start_time = 0

    def run(self):
        """线程执行逻辑（修复除以0错误）"""
        self.running = True
        self.start_time = time.time()
        count = 0
        while self.running:
            count += 1
            data = f"Data-{count}"
            # 发送数据信号（主线程处理）
            self.send_signal.emit(f"生产者发送：{data}")
            self.data_count += 1
            # 更新计数
            self.count_signal.emit(self.data_count)
            
            # ========== 核心修复：避免除以0 ==========
            elapsed = time.time() - self.start_time
            # 防止elapsed为0，设置极小值兜底
            if elapsed <= 1e-6:
                speed = "传输速率：0.0 条/秒"
            else:
                speed = f"传输速率：{self.data_count/elapsed:.1f} 条/秒"
            self.speed_signal.emit(speed)
            
            time.sleep(1)
        self.finished_signal.emit()

    def stop(self):
        self.running = False

class IPCConsumerThread(QThread):
    """消费者线程"""
    recv_signal = pyqtSignal(str)  # 接收数据信号
    finished_signal = pyqtSignal() # 结束信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False

    def run(self):
        self.running = True
        count = 0
        while self.running:
            count += 1
            data = f"Data-{count}"  # 模拟从管道接收（保留核心逻辑）
            self.recv_signal.emit(f"消费者接收：{data}")
            time.sleep(1)
        self.finished_signal.emit()

    def stop(self):
        self.running = False

class IPCVisualization(QWidget):
    def __init__(self):
        super().__init__()
        # 初始化属性
        self.data_count = 0
        self.producer_thread = None
        self.consumer_thread = None
        self.flow_timer = QTimer()
        # 初始化UI
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("启动生产者-消费者（管道IPC）")
        self.start_btn.clicked.connect(self.start_ipc)
        self.stop_btn = QPushButton("停止IPC")
        self.stop_btn.clicked.connect(self.stop_ipc)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 数据流可视化区
        flow_layout = QHBoxLayout()
        self.producer_label = QLabel("生产者：等待启动")
        self.producer_label.setStyleSheet("color: #2E8B57; font-size: 14px;")
        self.flow_ani = QLabel("→")
        self.flow_ani.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        self.consumer_label = QLabel("消费者：等待启动")
        self.consumer_label.setStyleSheet("color: #4169E1; font-size: 14px;")
        flow_layout.addWidget(self.producer_label)
        flow_layout.addWidget(self.flow_ani)
        flow_layout.addWidget(self.consumer_label)
        layout.addLayout(flow_layout)

        # 统计区
        self.data_label = QLabel(f"已传输数据量：{self.data_count} 条")
        self.speed_label = QLabel("传输速率：0 条/秒")
        layout.addWidget(self.data_label)
        layout.addWidget(self.speed_label)

        # 日志区
        self.log_label = QLabel("<b>IPC传输日志</b>")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log_label)
        layout.addWidget(self.log)

        # 数据流动画定时器
        self.flow_timer.timeout.connect(self.update_flow_ani)

        self.setLayout(layout)

    def add_log(self, text, color="black"):
        """主线程安全更新日志（Windows兼容）"""
        format_char = QTextCharFormat()
        color_map = {
            "green": QColor(0, 128, 0),
            "blue": QColor(0, 0, 255),
            "red": QColor(255, 0, 0),
            "black": QColor(0, 0, 0)
        }
        format_char.setForeground(color_map.get(color, QColor(0,0,0)))
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(f"[{time.strftime('%H:%M:%S')}] {text}\n", format_char)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def update_flow_ani(self):
        """数据流动画：切换箭头样式"""
        if self.flow_ani.text() == "→":
            self.flow_ani.setText("➡️")
        elif self.flow_ani.text() == "➡️":
            self.flow_ani.setText("→")

    def start_ipc(self):
        """启动IPC（主线程安全创建线程，Windows兼容）"""
        if self.producer_thread and self.producer_thread.isRunning():
            self.add_log("IPC已在运行中！", "red")
            return
        
        # 初始化线程
        self.producer_thread = IPCProducerThread()
        self.consumer_thread = IPCConsumerThread()

        # 绑定信号槽（核心：线程信号触发主线程UI更新）
        self.producer_thread.send_signal.connect(lambda msg: self.add_log(msg, "green"))
        self.producer_thread.count_signal.connect(self.update_data_count)
        self.producer_thread.speed_signal.connect(self.update_speed)
        self.consumer_thread.recv_signal.connect(lambda msg: self.add_log(msg, "blue"))

        # 启动线程
        self.producer_thread.start()
        self.consumer_thread.start()
        self.flow_timer.start(500)
        
        # 更新UI
        self.producer_label.setText("生产者：运行中")
        self.consumer_label.setText("消费者：运行中")
        self.add_log("启动生产者-消费者IPC（管道）", "black")

    def stop_ipc(self):
        """停止IPC（Windows线程安全停止）"""
        if not self.producer_thread or not self.producer_thread.isRunning():
            self.add_log("IPC未运行！", "red")
            return
        
        # 停止线程
        self.producer_thread.stop()
        self.consumer_thread.stop()
        self.producer_thread.wait()
        self.consumer_thread.wait()
        self.flow_timer.stop()
        
        # 更新UI
        self.producer_label.setText("生产者：已停止")
        self.consumer_label.setText("消费者：已停止")
        self.add_log(f"停止IPC模拟，总计传输：{self.data_count} 条数据", "red")

    def update_data_count(self, count):
        """更新数据计数（信号触发）"""
        self.data_count = count
        self.data_label.setText(f"已传输数据量：{self.data_count} 条")

    def update_speed(self, speed):
        """更新速率（信号触发）"""
        self.speed_label.setText(speed)

# ======================== 模块3：基于信号量的进程同步（图形+文字结合） ========================
class SemaphoreProducerThread(QThread):
    """信号量生产者线程（Windows兼容）"""
    log_signal = pyqtSignal(str, str)  # (日志内容, 颜色)
    sem_update_signal = pyqtSignal(int, int, int)  # (empty_val, full_val, mutex_val)
    buffer_signal = pyqtSignal(list)  # 缓冲区数据
    finished_signal = pyqtSignal()

    def __init__(self, empty, full, mutex, buffer_size, parent=None):
        super().__init__(parent)
        self.running = False
        self.empty = empty
        self.full = full
        self.mutex = mutex
        self.buffer_size = buffer_size
        self.buffer = [None]*buffer_size
        self.in_idx = 0
        # 手动跟踪信号量数值
        self.empty_val = buffer_size
        self.full_val = 0
        self.mutex_val = 1

    def run(self):
        self.running = True
        count = 0
        while self.running:
            count += 1
            # P(empty)：申请空缓冲区
            self.empty.acquire()
            self.empty_val -= 1
            self.log_signal.emit(f"生产者P(empty) → empty={self.empty_val}", "P")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            # P(mutex)：申请互斥锁
            self.mutex.acquire()
            self.mutex_val -= 1
            self.log_signal.emit(f"生产者P(mutex) → mutex={self.mutex_val}", "P")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            # 生产数据并写入缓冲区
            data = f"Item-{count}"
            self.buffer[self.in_idx] = data
            self.in_idx = (self.in_idx + 1) % self.buffer_size
            self.log_signal.emit(f"生产者写入缓冲区[{self.in_idx-1}]：{data}", "black")
            self.buffer_signal.emit(self.buffer.copy())

            # V(mutex)：释放互斥锁
            self.mutex.release()
            self.mutex_val += 1
            self.log_signal.emit(f"生产者V(mutex) → mutex={self.mutex_val}", "V")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            # V(full)：释放满缓冲区
            self.full.release()
            self.full_val += 1
            self.log_signal.emit(f"生产者V(full) → full={self.full_val}", "V")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            time.sleep(1)
        self.finished_signal.emit()

    def stop(self):
        self.running = False

class SemaphoreConsumerThread(QThread):
    """信号量消费者线程（Windows兼容）"""
    log_signal = pyqtSignal(str, str)  # (日志内容, 颜色)
    sem_update_signal = pyqtSignal(int, int, int)  # (empty_val, full_val, mutex_val)
    buffer_signal = pyqtSignal(list)  # 缓冲区数据
    finished_signal = pyqtSignal()

    def __init__(self, empty, full, mutex, buffer_size, parent=None):
        super().__init__(parent)
        self.running = False
        self.empty = empty
        self.full = full
        self.mutex = mutex
        self.buffer_size = buffer_size
        self.buffer = [None]*buffer_size  # 初始化缓冲区
        self.out_idx = 0
        # 手动跟踪信号量数值
        self.empty_val = buffer_size
        self.full_val = 0
        self.mutex_val = 1

    def run(self):
        self.running = True
        while self.running:
            # P(full)：申请满缓冲区
            self.full.acquire()
            self.full_val -= 1
            self.log_signal.emit(f"消费者P(full) → full={self.full_val}", "P")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            # P(mutex)：申请互斥锁
            self.mutex.acquire()
            self.mutex_val -= 1
            self.log_signal.emit(f"消费者P(mutex) → mutex={self.mutex_val}", "P")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            # 从缓冲区读取数据（修复Windows下索引越界）
            current_idx = self.out_idx % self.buffer_size
            data = self.buffer[current_idx]
            if data:
                self.buffer[current_idx] = None
                self.log_signal.emit(f"消费者读取缓冲区[{current_idx}]：{data}", "black")
                self.buffer_signal.emit(self.buffer.copy())
            self.out_idx = (self.out_idx + 1) % self.buffer_size

            # V(mutex)：释放互斥锁
            self.mutex.release()
            self.mutex_val += 1
            self.log_signal.emit(f"消费者V(mutex) → mutex={self.mutex_val}", "V")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            # V(empty)：释放空缓冲区
            self.empty.release()
            self.empty_val += 1
            self.log_signal.emit(f"消费者V(empty) → empty={self.empty_val}", "V")
            self.sem_update_signal.emit(self.empty_val, self.full_val, self.mutex_val)

            time.sleep(1)
        self.finished_signal.emit()

    def stop(self):
        self.running = False

class SemaphoreSync(QWidget):
    def __init__(self):
        super().__init__()
        # 信号量配置（Windows multiprocessing适配）
        self.buffer_size = 5
        self.empty = multiprocessing.Semaphore(self.buffer_size)
        self.full = multiprocessing.Semaphore(0)
        self.mutex = multiprocessing.Semaphore(1)
        # 手动跟踪信号量数值
        self.empty_val = self.buffer_size
        self.full_val = 0
        self.mutex_val = 1
        # 缓冲区
        self.buffer = [None]*self.buffer_size
        # 线程对象
        self.producer_thread = None
        self.consumer_thread = None
        # 初始化Matplotlib画布（Windows绘图适配）
        self.figure = plt.Figure(figsize=(8, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        # 初始化UI
        self.init_ui()
        # 初始绘制缓冲区图形
        self.plot_buffer(self.buffer)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 1. 控制按钮区域
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("启动生产者-消费者同步模拟")
        self.start_btn.clicked.connect(self.start_sync)
        self.stop_btn = QPushButton("停止模拟")
        self.stop_btn.clicked.connect(self.stop_sync)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # 2. 信号量数值文字展示区
        sem_layout = QHBoxLayout()
        self.empty_label = QLabel(f"空缓冲区信号量（empty）：{self.empty_val}")
        self.empty_label.setStyleSheet("color: #228B22; font-size: 14px; font-weight: bold;")
        self.full_label = QLabel(f"满缓冲区信号量（full）：{self.full_val}")
        self.full_label.setStyleSheet("color: #DC143C; font-size: 14px; font-weight: bold;")
        self.mutex_label = QLabel(f"互斥信号量（mutex）：{self.mutex_val}")
        self.mutex_label.setStyleSheet("color: #4169E1; font-size: 14px; font-weight: bold;")
        sem_layout.addWidget(self.empty_label)
        sem_layout.addWidget(self.full_label)
        sem_layout.addWidget(self.mutex_label)
        layout.addLayout(sem_layout)

        # 3. 缓冲区图形+文字结合展示区
        buffer_title = QLabel("<b>缓冲区状态（图形化）</b>")
        layout.addWidget(buffer_title)
        layout.addWidget(self.canvas)  # 图形画布
        self.buffer_text_label = QLabel(f"缓冲区文字状态：{[x if x else '空' for x in self.buffer]}")
        self.buffer_text_label.setStyleSheet("font-size: 12px; color: #333;")
        layout.addWidget(self.buffer_text_label)

        # 4. 操作日志文字展示区
        self.log_label = QLabel("<b>信号量操作日志（P=红色/V=绿色）</b>")
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)  # 限制日志高度
        layout.addWidget(self.log_label)
        layout.addWidget(self.log)

        self.setLayout(layout)

    def plot_buffer(self, buffer):
        """绘制缓冲区图形（Windows适配）"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xlim(0, self.buffer_size * 2)
        ax.set_ylim(0, 3)
        ax.axis('off')  # 关闭坐标轴

        # 绘制每个缓冲区槽位
        slot_width = 1.5
        slot_height = 1.8
        for idx in range(self.buffer_size):
            # 计算槽位位置
            x = idx * 2
            y = 0.5
            # 根据是否有数据设置颜色
            if buffer[idx] is not None:
                # 有数据：绿色背景
                rect = patches.Rectangle((x, y), slot_width, slot_height, 
                                       facecolor='#90EE90', edgecolor='black', linewidth=2)
                # 槽位内显示数据文字（Windows字体）
                ax.text(x + slot_width/2, y + slot_height/2, buffer[idx], 
                       ha='center', va='center', fontsize=10, fontweight='bold')
            else:
                # 空槽位：灰色背景
                rect = patches.Rectangle((x, y), slot_width, slot_height, 
                                       facecolor='#D3D3D3', edgecolor='black', linewidth=2)
                # 槽位内显示“空”
                ax.text(x + slot_width/2, y + slot_height/2, '空', 
                       ha='center', va='center', fontsize=10, color='#666')
            ax.add_patch(rect)
            # 槽位下方标注索引（Windows字体）
            ax.text(x + slot_width/2, 0.2, f'槽位{idx}', ha='center', va='center', fontsize=9)

        # 图形标题（Windows字体）
        ax.text(self.buffer_size, 2.8, '生产者-消费者缓冲区可视化', 
               ha='center', va='center', fontsize=12, fontweight='bold')
        # 强制刷新画布（Windows关键）
        self.canvas.draw()
        self.canvas.flush_events()

    def add_log(self, text, color="black"):
        """主线程安全更新日志（Windows兼容）"""
        format_char = QTextCharFormat()
        color_map = {
            "P": QColor(255, 0, 0),    # P操作红色
            "V": QColor(0, 128, 0),    # V操作绿色
            "black": QColor(0, 0, 0)
        }
        format_char.setForeground(color_map.get(color, QColor(0,0,0)))
        cursor = self.log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(f"[{time.strftime('%H:%M:%S')}] {text}\n", format_char)
        self.log.setTextCursor(cursor)
        self.log.ensureCursorVisible()

    def update_sem_labels(self, empty_val, full_val, mutex_val):
        """更新信号量数值文字标签"""
        self.empty_val = empty_val
        self.full_val = full_val
        self.mutex_val = mutex_val
        self.empty_label.setText(f"空缓冲区信号量（empty）：{self.empty_val}")
        self.full_label.setText(f"满缓冲区信号量（full）：{self.full_val}")
        self.mutex_label.setText(f"互斥信号量（mutex）：{self.mutex_val}")

    def update_buffer(self, buffer):
        """同步更新缓冲区图形和文字（Windows兼容）"""
        self.buffer = buffer
        # 更新文字标签
        self.buffer_text_label.setText(f"缓冲区文字状态：{[x if x else '空' for x in self.buffer]}")
        # 更新图形
        self.plot_buffer(buffer)

    def start_sync(self):
        """启动信号量模拟（Windows线程安全）"""
        if self.producer_thread and self.producer_thread.isRunning():
            self.add_log("同步模拟已在运行！", "black")
            return
        
        # 重置信号量和缓冲区
        self.empty_val = self.buffer_size
        self.full_val = 0
        self.mutex_val = 1
        self.buffer = [None]*self.buffer_size
        self.update_sem_labels(self.empty_val, self.full_val, self.mutex_val)
        self.update_buffer(self.buffer)

        # 创建线程（Windows multiprocessing适配）
        self.producer_thread = SemaphoreProducerThread(
            self.empty, self.full, self.mutex, self.buffer_size
        )
        self.consumer_thread = SemaphoreConsumerThread(
            self.empty, self.full, self.mutex, self.buffer_size
        )

        # 绑定信号槽（图形+文字联动更新）
        self.producer_thread.log_signal.connect(self.add_log)
        self.producer_thread.sem_update_signal.connect(self.update_sem_labels)
        self.producer_thread.buffer_signal.connect(self.update_buffer)
        self.consumer_thread.log_signal.connect(self.add_log)
        self.consumer_thread.sem_update_signal.connect(self.update_sem_labels)
        self.consumer_thread.buffer_signal.connect(self.update_buffer)

        # 启动线程
        self.producer_thread.start()
        self.consumer_thread.start()
        self.add_log("启动生产者-消费者信号量同步模拟（图形+文字联动）", "black")

    def stop_sync(self):
        """停止信号量模拟（Windows线程安全）"""
        if not self.producer_thread or not self.producer_thread.isRunning():
            self.add_log("同步模拟未运行！", "black")
            return
        
        # 停止线程
        self.producer_thread.stop()
        self.consumer_thread.stop()
        self.producer_thread.wait()
        self.consumer_thread.wait()

        # 重置状态（图形+文字）
        self.empty_val = self.buffer_size
        self.full_val = 0
        self.mutex_val = 1
        self.buffer = [None]*self.buffer_size
        self.update_sem_labels(self.empty_val, self.full_val, self.mutex_val)
        self.update_buffer(self.buffer)

        self.add_log("停止信号量同步模拟，已重置信号量和缓冲区状态", "black")

# ======================== 模块4：CPU调度算法展示与比较 ========================
class CPUScheduler(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        # 预设进程数据：[(进程ID, 到达时间, 执行时间, 优先级)]
        self.processes = [
            ("P1", 0, 5, 3),
            ("P2", 1, 3, 1),
            ("P3", 2, 2, 2),
            ("P4", 4, 4, 4)
        ]

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 算法选择按钮
        btn_layout = QHBoxLayout()
        self.fcfs_btn = QPushButton("FCFS（先来先服务）")
        self.fcfs_btn.clicked.connect(lambda: self.run_scheduler("FCFS"))
        self.rr_btn = QPushButton("RR（时间片轮转，片长=2）")
        self.rr_btn.clicked.connect(lambda: self.run_scheduler("RR"))
        self.sjf_btn = QPushButton("SJF（最短作业优先）")
        self.sjf_btn.clicked.connect(lambda: self.run_scheduler("SJF"))
        btn_layout.addWidget(self.fcfs_btn)
        btn_layout.addWidget(self.rr_btn)
        btn_layout.addWidget(self.sjf_btn)
        layout.addLayout(btn_layout)

        # 甘特图展示区（Windows绘图适配）
        self.figure = plt.Figure(figsize=(10, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # 调度结果展示
        self.result_label = QLabel("<b>调度性能指标（平均等待时间/平均周转时间）</b>")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def fcfs(self):
        """FCFS调度算法实现"""
        # 按到达时间排序
        sorted_procs = sorted(self.processes, key=lambda x: x[1])
        current_time = 0
        wait_times = []
        turnaround_times = []
        gantt_data = []

        for p in sorted_procs:
            pid, arr_time, exe_time, pri = p
            # 进程开始时间 = 最大(当前时间, 到达时间)
            start_time = max(current_time, arr_time)
            # 等待时间 = 开始时间 - 到达时间
            wait_time = start_time - arr_time
            # 周转时间 = 完成时间 - 到达时间
            finish_time = start_time + exe_time
            turnaround_time = finish_time - arr_time

            wait_times.append(wait_time)
            turnaround_times.append(turnaround_time)
            gantt_data.append((pid, start_time, finish_time))
            current_time = finish_time

        # 计算平均指标
        avg_wait = sum(wait_times) / len(wait_times)
        avg_turnaround = sum(turnaround_times) / len(turnaround_times)
        return gantt_data, avg_wait, avg_turnaround

    def rr(self):
        """RR调度算法实现（时间片=2，Windows兼容）"""
        time_slice = 2
        # 进程副本：(pid, 到达时间, 总执行时间, 优先级, 剩余执行时间)
        procs = [(pid, arr, exe, pri, exe) for pid, arr, exe, pri in self.processes]
        current_time = 0
        ready_queue = []
        wait_times = {p[0]: 0 for p in self.processes}  # 每个进程的等待时间
        turnaround_times = {}
        gantt_data = []
        completed = []

        while len(completed) < len(self.processes):
            # 把到达的进程加入就绪队列
            for p in procs:
                pid, arr, exe, pri, rem = p
                if arr <= current_time and pid not in [x[0] for x in ready_queue] and pid not in completed:
                    ready_queue.append(p)

            if not ready_queue:
                current_time += 1
                continue

            # 调度就绪队列首个进程
            current_proc = ready_queue.pop(0)
            pid, arr, exe, pri, rem = current_proc
            # 实际运行时间 = 最小(时间片, 剩余时间)
            run_time = min(time_slice, rem)
            start_time = current_time
            current_time += run_time
            rem -= run_time

            # 记录甘特图数据
            gantt_data.append((pid, start_time, current_time))

            # 更新就绪队列中其他进程的等待时间
            for q in ready_queue:
                qid = q[0]
                wait_times[qid] += run_time

            # 进程完成/未完成处理
            if rem == 0:
                completed.append(pid)
                turnaround_times[pid] = current_time - arr
            else:
                ready_queue.append((pid, arr, exe, pri, rem))

        # 计算平均指标
        avg_wait = sum(wait_times.values()) / len(wait_times)
        avg_turnaround = sum(turnaround_times.values()) / len(turnaround_times)
        return gantt_data, avg_wait, avg_turnaround

    def sjf(self):
        """SJF（最短作业优先）调度算法实现"""
        procs = [(pid, arr, exe, pri) for pid, arr, exe, pri in self.processes]
        current_time = 0
        wait_times = []
        turnaround_times = []
        gantt_data = []
        completed = []

        while len(completed) < len(procs):
            # 筛选已到达且未完成的进程
            available = [p for p in procs if p[1] <= current_time and p[0] not in completed]
            if not available:
                current_time += 1
                continue

            # 按执行时间升序排序（最短优先）
            available_sorted = sorted(available, key=lambda x: x[2])
            p = available_sorted[0]
            pid, arr_time, exe_time, pri = p

            # 计算时间指标
            start_time = max(current_time, arr_time)
            wait_time = start_time - arr_time
            finish_time = start_time + exe_time
            turnaround_time = finish_time - arr_time

            wait_times.append(wait_time)
            turnaround_times.append(turnaround_time)
            gantt_data.append((pid, start_time, finish_time))

            # 更新状态
            completed.append(pid)
            current_time = finish_time

        # 计算平均指标
        avg_wait = sum(wait_times) / len(wait_times)
        avg_turnaround = sum(turnaround_times) / len(turnaround_times)
        return gantt_data, avg_wait, avg_turnaround

    def plot_gantt(self, gantt_data, algo_name):
        """绘制调度甘特图（Windows适配）"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 进程颜色映射
        colors = {
            "P1": "#FF6347", "P2": "#32CD32", "P3": "#4169E1", 
            "P4": "#FFD700", "P5": "#9370DB"
        }
        # 绘制甘特图（Windows兼容）
        for pid, start, finish in gantt_data:
            ax.barh(
                pid, finish - start, left=start, 
                color=colors.get(pid, "#808080"), 
                edgecolor="black", alpha=0.8
            )
            # 标注时间范围（Windows字体）
            ax.text(start + (finish - start)/2, pid, f"{start}-{finish}", 
                   ha='center', va='center', fontsize=9, fontweight='bold')

        # 中文标签配置（Windows字体）
        ax.set_xlabel("时间（秒）", fontsize=12, fontweight='bold')
        ax.set_ylabel("进程ID", fontsize=12, fontweight='bold')
        ax.set_title(f"{algo_name} 调度算法甘特图", fontsize=14, fontweight="bold")
        ax.grid(axis="x", linestyle="--", alpha=0.7)
        # 强制刷新画布（Windows关键）
        self.canvas.draw()
        self.canvas.flush_events()

    def run_scheduler(self, algo):
        """执行指定调度算法并展示结果（Windows兼容）"""
        if algo == "FCFS":
            gantt_data, avg_wait, avg_turn = self.fcfs()
        elif algo == "RR":
            gantt_data, avg_wait, avg_turn = self.rr()
        elif algo == "SJF":
            gantt_data, avg_wait, avg_turn = self.sjf()
        else:
            return

        # 绘制甘特图
        self.plot_gantt(gantt_data, algo)
        # 展示结果
        result_text = f"""
        {algo} 调度结果：
        ├─ 甘特图数据：{gantt_data}
        ├─ 平均等待时间：{avg_wait:.2f} 秒
        └─ 平均周转时间：{avg_turn:.2f} 秒
        
        进程原始参数：
        {[(pid, f'到达={arr}', f'执行={exe}', f'优先级={pri}') for pid, arr, exe, pri in self.processes]}
        """
        self.result_text.setText(result_text)

# ======================== 主程序：整合所有模块（Windows核心适配） ========================
def main():
    # Windows高DPI适配（解决界面/图形模糊）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建QT应用
    app = QApplication(sys.argv)
    # 设置全局字体（Windows兼容）
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 主窗口
    main_window = QWidget()
    main_window.setWindowTitle("Windows适配版 - 操作系统核心模块可视化平台")
    main_window.resize(1200, 800)

    # 标签页整合4个核心模块
    tab_widget = QTabWidget()
    tab_widget.addTab(ProcessManagement(), "1. 进程/线程创建与管理")
    tab_widget.addTab(IPCVisualization(), "2. 进程间通信（管道IPC）")
    tab_widget.addTab(SemaphoreSync(), "3. 信号量同步（生产者-消费者）")
    tab_widget.addTab(CPUScheduler(), "4. CPU调度算法（FCFS/RR/SJF）")

    # 主布局
    main_layout = QVBoxLayout()
    main_layout.addWidget(tab_widget)
    main_window.setLayout(main_layout)

    # 显示窗口
    main_window.show()
    # 运行应用
    sys.exit(app.exec_())

if __name__ == "__main__":
    # PyInstaller打包必备（Windows多进程核心）
    multiprocessing.freeze_support()
    # Windows强制使用spawn模式（替代fork）
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    main()

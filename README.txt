OS 可视化平台 - Windows 版
============================

项目概述
--------
"操作系统核心模块可视化平台"的 Windows 适配版，基于 PyQt5 + Matplotlib。
支持：
   进程/线程创建与管理
   进程间通信（管道 IPC）
   信号量同步（生产者-消费者）图文联动
   CPU 调度算法（FCFS/RR/SJF）甘特图与指标

环境要求
--------
 操作系统：Windows 10/11（64 位推荐）
 Python 版本：3.83.12
 依赖库：PyQt5、Matplotlib、NumPy、Pillow（见 requirements.txt）

快速开始（克隆后 3 步启动）
---------------------------

1 克隆并进入目录：
   git clone https://github.com/gideonQAQ/share.git
   cd share

2 创建虚拟环境并安装依赖（推荐）：
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

3 启动应用：
   python os_visualization.py

 应用启动后会打开 GUI 窗口，支持 4 个操作系统模块的交互式演示。

无虚拟环境的快速方案（不推荐）
-----------------------------
pip install --user -r requirements.txt
python os_visualization.py

依赖说明
--------
 PyQt5 >= 5.15：图形界面与事件循环
 Matplotlib >= 3.7：绘图、甘特图、可视化
 NumPy、Pillow：数值与图像处理（Matplotlib 依赖）

所有依赖已固定版本于 requirements.txt 中，确保兼容性。

生成可执行文件（EXE）
-------------------
项目包含 PyInstaller 规格文件 OS_Visual_Windows.spec，可打包为独立 EXE：
   pip install pyinstaller
   pyinstaller OS_Visual_Windows.spec

生成的 EXE 位于 dist/OS_Visual_Windows/ 目录，可直接分发使用，
无需用户安装 Python 或依赖。

技术细节
--------
 强制 Qt5Agg 后端以支持 Windows 图形绘制
 中文字体自动适配（优先微软雅黑，备选回退）
 multiprocessing 使用 spawn 模式适配 Windows（PyInstaller 打包时必需）
 所有 Qt 信号-槽完全线程安全，支持并发进程模拟

常见问题排查
-----------

 Qt 平台插件错误（"Could not find the Qt platform plugin"）：
    确认虚拟环境正确激活
    重新安装 PyQt5：pip install --force-reinstall PyQt5==5.15.9
    检查是否混用多个 Python 版本

 字体显示异常（乱码或缺失）：
    确认系统安装了中文字体（微软雅黑或 SimHei）
    修改 setup_matplotlib_font() 函数指定其他字体

 图形无法绘制或闪烁：
    尝试更新显卡驱动
    禁用 GPU 硬件加速再试

项目结构
--------
share/
   os_visualization.py          主程序入口（包含 4 个模块）
   OS_Visual_Windows.spec       PyInstaller 打包配置
   requirements.txt              Python 依赖清单
   .gitignore                    Git 忽略规则（build/dist/等生成文件）
   README.txt                    本文档
   (build/dist 等在克隆时被忽略)

为何不提交 build/ 和 dist/?
----------------------------
 构建产物非常庞大（100+ MB），仓库会变得臃肿
 二进制文件无法 diff，commit 历史无意义
 可重现性：源码才是事实源，产物可在任何环境重建
 发行方式：EXE 应通过 GitHub Releases 或制品库分发，不用 Git 承载

许可证
------
请参阅项目主页或 LICENSE 文件。

联系与反馈
---------
GitHub: https://github.com/gideonQAQ/share

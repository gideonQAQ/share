项目概述
本项目为“操作系统核心模块可视化平台”的 Windows 适配版，基于 PyQt5 + Matplotlib 展示：
- 进程/线程的创建与管理
- 进程间通信（管道 IPC）
- 信号量同步（生产者-消费者）图文联动
- CPU 调度算法（FCFS/RR/SJF）甘特图与指标

运行环境
- 操作系统：Windows 10/11（推荐）
- Python：3.8–3.12（建议 64 位）

快速开始（克隆后直接运行）
1) 创建虚拟环境并安装依赖：
```powershell
cd d:\share
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
2) 启动应用：
```powershell
python os_visualization.py
```

说明：
- 代码中强制使用 Matplotlib 的 Qt5Agg 后端，需 PyQt5 正常安装。
- 字体首选 “Microsoft YaHei/微软雅黑”，在非中文 Windows 环境下会自动回退到其他字体。
- 脚本在 `if __name__ == "__main__"` 中启用 `multiprocessing.freeze_support()` 并强制 `spawn`，确保 Windows 下线程/子进程正常。

打包（生成 EXE）
已提供 PyInstaller 规格文件：`OS_Visual_Windows.spec`
```powershell
pip install pyinstaller
pyinstaller OS_Visual_Windows.spec
```
打包完成后生成的 `build/`、`dist/` 等目录均为构建产物，已通过 `.gitignore` 排除，不会推送到仓库。

为何不提交构建产物
- 仓库体积膨胀、克隆/拉取慢；二进制无法有效审查与做差分；
- 构建应可重现，源码才是“单一事实源”；
- 易引发无意义的合并冲突；分发建议使用 Release/Artifacts/LFS。

常见问题
- Qt 平台插件错误（如 "Could not load the Qt platform plugin windows"）：
	- 重新安装/升级 `PyQt5`，确保虚拟环境的 `pip show PyQt5` 可见；
	- 确认未混用多个 Python/虚拟环境。
- 字体显示异常：修改 `setup_matplotlib_font()` 或在系统中安装中文字体。

目录说明
- `os_visualization.py`：主程序入口（四大模块整合）。
- `OS_Visual_Windows.spec`：PyInstaller 打包规格文件。
- `requirements.txt`：运行时依赖清单。
- `.gitignore`：忽略构建输出与临时文件。


#!/usr/bin/env python3
"""
Jupyter 启动/管理脚本
用法:
  python3 start_jupyter.py          # 启动
  python3 start_jupyter.py status   # 查看状态
  python3 start_jupyter.py stop     # 停止
"""
import subprocess
import sys
import os
import json
import time

ACADEMIC_DIR = "/home/17635852864/AI/academic"
NOTEBOOK_DIR = "/home/17635852864/AI/academic/experiments"
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '../config')
os.makedirs(CONFIG_DIR, exist_ok=True)

JUPYTER_CONFIG = os.path.join(CONFIG_DIR, 'jupyter.json')
KERNEL_NAME = "academic"

def get_kernel_specs():
    """获取已安装的内核"""
    result = subprocess.run(['jupyter', 'kernelspec', 'list', '--json'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {}

def install_kernel():
    """安装学术研究专用 Python 内核"""
    # 创建内核规格
    kernel_spec = {
        "argv": [
            sys.executable, "-m", "ipykernel", "-f", "{connection_file}"
        ],
        "env": {
            "JUPYTER_ENV": "academic"
        },
        "display_name": "学术研究 (Python 3)",
        "language": "python"
    }
    
    kernel_dir = os.path.join(os.path.expanduser("~/.local/share/jupyter/kernels"), KERNEL_NAME)
    os.makedirs(kernel_dir, exist_ok=True)
    
    with open(os.path.join(kernel_dir, 'kernel.json'), 'w') as f:
        json.dump(kernel_spec, f, indent=2)
    
    print(f"✅ 内核 '{KERNEL_NAME}' 已安装")
    return True

def ensure_packages():
    """确保必要的包已安装"""
    required = ['pandas', 'numpy', 'matplotlib', 'scipy', 'statsmodels', 'seaborn', 'sklearn']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"📦 安装缺失的包: {', '.join(missing)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q'] + missing)
        print("✅ 包安装完成")
    
    return True

def start_jupyter():
    """启动 Jupyter Notebook"""
    # 检查是否已运行
    if is_running():
        print("✅ Jupyter 已在运行")
        return True
    
    print("🚀 启动 Jupyter Notebook...")
    
    # 确保实验目录存在
    os.makedirs(NOTEBOOK_DIR, exist_ok=True)
    
    # 启动命令
    cmd = [
        sys.executable, '-m', 'jupyter', 'notebook',
        '--notebook-dir', ACADEMIC_DIR,
        '--no-browser',
        '--ip', '0.0.0.0',
        '--port', '8888',
        '--allow-root',
        '--NotebookApp.token=', 
        '--NotebookApp.password=',
        '--KernelSpecManager.ensure_native_kernel=False',
    ]
    
    # 后台运行
    log_file = os.path.join(ACADEMIC_DIR, 'jupyter.log')
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
    
    # 保存 PID
    with open(os.path.join(CONFIG_DIR, 'jupyter.pid'), 'w') as f:
        f.write(str(proc.pid))
    
    # 等待启动
    time.sleep(3)
    
    if is_running():
        print(f"✅ Jupyter 已启动 (PID: {proc.pid})")
        print(f"📝 日志: {log_file}")
        print(f"🌐 访问: http://localhost:8888")
        return True
    else:
        print("❌ 启动失败，查看日志:")
        with open(log_file) as f:
            print(f.read()[-500:])
        return False

def is_running():
    """检查 Jupyter 是否在运行"""
    pid_file = os.path.join(CONFIG_DIR, 'jupyter.pid')
    if not os.path.exists(pid_file):
        return False
    
    with open(pid_file) as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def stop_jupyter():
    """停止 Jupyter"""
    pid_file = os.path.join(CONFIG_DIR, 'jupyter.pid')
    if not os.path.exists(pid_file):
        print("Jupyter 未运行")
        return
    
    with open(pid_file) as f:
        pid = int(f.read().strip())
    
    try:
        os.kill(pid, 9)
        print(f"✅ Jupyter 已停止 (PID: {pid})")
    except OSError:
        print("Jupyter 未运行")
    
    os.remove(pid_file)

def status():
    """查看状态"""
    if is_running():
        print("🟢 Jupyter 运行中")
    else:
        print("⚠️  Jupyter 未运行")
    
    specs = get_kernel_specs()
    print(f"\n📦 已安装内核: {', '.join(specs.get('kernelspecs', {}).keys())}")

def main():
    args = sys.argv[1:]
    
    if '--help' in args or not args:
        print(__doc__)
    
    if 'status' in args:
        status()
    elif 'stop' in args:
        stop_jupyter()
    elif 'install-kernel' in args:
        ensure_packages()
        install_kernel()
    else:
        ensure_packages()
        install_kernel()
        start_jupyter()

if __name__ == '__main__':
    main()

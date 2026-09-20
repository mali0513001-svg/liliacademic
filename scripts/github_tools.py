#!/usr/bin/env python3
"""
GitHub 仓库管理脚本
基于 gh CLI，认证信息已配置在 ~/.hermes/config/gh_credentials.json

用法:
  python3 github_tools.py repos                    # 列出所有仓库
  python3 github_tools.py create <name>            # 创建新仓库
  python3 github_tools.py clone <repo>             # 克隆仓库到当前目录
  python3 github_tools.py delete <repo>            # 删除仓库（需确认）
  python3 github_tools.py search <keyword>         # 搜索仓库
  python3 github_tools.py remote-add <name> <url>  # 添加 remote 到当前 git 项目
"""
import subprocess
import sys
import os
import json

GH_CONFIG = "/home/hermeswebui/.hermes/config/gh_credentials.json"

def gh(args, capture=True):
    """执行 gh 命令"""
    cmd = ['gh'] + args
    export_env = "export PATH=\"/home/hermeswebui/.hermes/home/.local/bin:$PATH\" && "
    full_cmd = export_env + ' '.join(cmd)
    
    if capture:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    else:
        result = subprocess.run(full_cmd, shell=True)
        return '', '', result.returncode

def get_user():
    """获取当前用户信息"""
    out, _, _ = gh(['api', 'user'])
    try:
        return json.loads(out)
    except:
        return {}

def list_repos(limit=20):
    """列出所有仓库"""
    user = get_user().get('login', '')
    if not user:
        print("❌ 未登录 GitHub")
        return
    
    out, _, rc = gh(['repo', 'list', user, '--limit', str(limit)])
    if rc != 0:
        print(f"❌ 错误: {out}")
        return
    
    if not out.strip():
        print(f"📭 {user} 还没有任何仓库")
        print("💡 使用 python3 github_tools.py create <仓库名> 创建第一个仓库")
        return
    
    print(f"📦 {user} 的仓库:\n")
    for line in out.strip().split('\n'):
        if line:
            parts = line.split('\t')
            name = parts[0] if parts else line
            desc = parts[1] if len(parts) > 1 else ''
            print(f"  {name}")
            if desc:
                print(f"    {desc}")
    print()

def create_repo(name, description='', private=True):
    """创建新仓库"""
    user = get_user().get('login', '')
    if not user:
        print("❌ 未登录 GitHub")
        return False
    
    args = ['repo', 'create', name, '--source', '.']
    if private:
        args.append('--private')
    else:
        args.append('--public')
    if description:
        args.extend(['--description', description])
    
    out, err, rc = gh(args)
    if rc != 0:
        print(f"❌ 创建失败: {err or out}")
        return False
    
    print(f"✅ 仓库已创建: https://github.com/{user}/{name}")
    return True

def clone_repo(repo_spec, dest=None):
    """克隆仓库"""
    user = get_user().get('login', '')
    
    # 解析 repo_spec（可能是 user/repo 或纯 repo 名）
    if '/' not in repo_spec:
        repo_spec = f"{user}/{repo_spec}"
    
    args = ['repo', 'clone', repo_spec]
    if dest:
        args.append(dest)
    
    out, err, rc = gh(args)
    if rc != 0:
        print(f"❌ 克隆失败: {err or out}")
        return False
    
    print(f"✅ 已克隆: {repo_spec}")
    return True

def delete_repo(repo_spec):
    """删除仓库"""
    user = get_user().get('login', '')
    if '/' not in repo_spec:
        repo_spec = f"{user}/{repo_spec}"
    
    confirm = input(f"⚠️  确定删除仓库 '{repo_spec}'？此操作不可撤销 (yes/no): ")
    if confirm.lower() != 'yes':
        print("取消删除")
        return False
    
    out, err, rc = gh(['repo', 'delete', repo_spec, '--yes'])
    if rc != 0:
        print(f"❌ 删除失败: {err or out}")
        return False
    
    print(f"✅ 已删除: {repo_spec}")
    return True

def search_repos(keyword):
    """搜索仓库"""
    out, err, rc = gh(['search', 'repos', keyword, '--limit', '10'])
    if rc != 0:
        print(f"❌ 搜索失败: {err or out}")
        return
    
    if not out.strip():
        print(f"未找到包含 '{keyword}' 的仓库")
        return
    
    print(f"🔍 搜索 '{keyword}' 的结果:\n")
    print(out)

def main():
    args = sys.argv[1:]
    
    if not args or '--help' in args:
        print(__doc__)
        user = get_user()
        if user:
            print(f"当前用户: {user.get('login', 'unknown')}")
        return
    
    cmd = args[0]
    
    if cmd == 'repos':
        list_repos()
    elif cmd == 'create':
        if len(args) < 2:
            print("用法: python3 github_tools.py create <仓库名> [描述]")
            return
        name = args[1]
        desc = args[2] if len(args) > 2 else ''
        create_repo(name, desc)
    elif cmd == 'clone':
        if len(args) < 2:
            print("用法: python3 github_tools.py clone <仓库名>")
            return
        clone_repo(args[1])
    elif cmd == 'delete':
        if len(args) < 2:
            print("用法: python3 github_tools.py delete <仓库名>")
            return
        delete_repo(args[1])
    elif cmd == 'search':
        if len(args) < 2:
            print("用法: python3 github_tools.py search <关键词>")
            return
        search_repos(args[1])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == '__main__':
    main()

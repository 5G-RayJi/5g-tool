#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批次 Git 分支版本號查詢工具
會針對指定的多個倉庫計算各遠端分支的 commit 數量，並輸出 version.txt
"""

import subprocess
import re
from pathlib import Path
from datetime import datetime


# 要遍歷的根目錄清單（會自動掃描這些目錄下的所有子資料夾）
REPOSITORY_DIRS = [
    r"C:\Users\RayJi\5g\git\game\2dx",
    r"C:\Users\RayJi\5g\git\game\cc_new",
    r"C:\Users\RayJi\5g\git\game\cc_old",
]

# 資料夾名稱正則表達式：Games-XXX-H5-XXXXX (XXX=3個英數字, XXXXX=5個數字)
FOLDER_PATTERN = re.compile(r'^Games-[A-Za-z0-9]{3}-H5-\d{5}$')

# 要檢查的分支
BRANCHES = ['origin/dev', 'origin/uat', 'origin/stage', 'origin/prod', 'origin/demo']

# 輸出檔案
OUTPUT_FILE = Path(__file__).resolve().parent / "version.txt"


def run_git_rev_count(repo_path: Path, branch: str) -> str:
    """在指定倉庫跑 git rev-list --count branch，返回字串結果"""
    try:
        result = subprocess.run(
            ['git', 'rev-list', '--count', branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return f"錯誤: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "超時"
    except FileNotFoundError:
        return "找不到 git 命令"
    except Exception as exc:
        return f"異常: {exc}"


def find_git_repositories(root_dir: Path) -> list:
    """遍歷根目錄，找出符合命名規則的 Git 倉庫（格式：Games-XXX-H5-XXXXX）"""
    repositories = []
    if not root_dir.exists() or not root_dir.is_dir():
        return repositories
    
    for item in root_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # 檢查資料夾名稱是否符合規則：Games-XXX-H5-XXXXX
            if FOLDER_PATTERN.match(item.name):
                git_dir = item / ".git"
                if git_dir.exists():
                    repositories.append(item)
    
    return repositories


def analyze_repository(repo_path: Path) -> dict:
    """回傳單一倉庫的各分支結果"""
    if not repo_path.exists():
        return {"__error__": "路徑不存在"}
    if not repo_path.is_dir():
        return {"__error__": "不是資料夾"}
    if not (repo_path / ".git").exists():
        return {"__error__": "不是 Git 倉庫"}

    results = {}
    for branch in BRANCHES:
        results[branch] = run_git_rev_count(repo_path, branch)
    return results


def format_results(all_results: dict) -> str:
    """轉成可寫入 version.txt 的字串（轉置格式）"""
    lines = []
    
    # 建立分支名稱對照表（移除 "origin/" 前綴）
    branch_headers = [branch.replace('origin/', '') for branch in BRANCHES]
    
    # 第一行：表頭（第一欄空白，後面是分支名稱）
    lines.append('\t' + '\t'.join(branch_headers))
    
    # 後續行：每個倉庫的各分支版本號
    for repo_name, data in all_results.items():
        if "__error__" in data:
            # 如果有錯誤，跳過這個倉庫
            continue
        
        # 提取倉庫名稱（資料夾名稱）
        repo_path = Path(repo_name)
        repo_folder_name = repo_path.name
        
        # 提取每個分支的版本號
        values = [repo_folder_name]  # 第一欄是倉庫名稱
        for branch in BRANCHES:
            version = data.get(branch, '')
            # 如果版本號包含"錯誤"等文字，只保留數字部分或留空
            if version.isdigit():
                values.append(version)
            else:
                values.append('')
        
        # 用 tab 分隔各分支版本號
        lines.append('\t'.join(values))
    
    return '\n'.join(lines)


def main():
    all_results = {}
    
    # 遍歷所有根目錄，找出 Git 倉庫
    for repo_dir in REPOSITORY_DIRS:
        root_path = Path(repo_dir)
        repositories = find_git_repositories(root_path)
        
        for repo_path in repositories:
            repo_name = str(repo_path)
            all_results[repo_name] = analyze_repository(repo_path)

    output_text = format_results(all_results)

    OUTPUT_FILE.write_text(output_text, encoding="utf-8")
    print("檢查完成，結果已寫入 version.txt")


if __name__ == "__main__":
    main()



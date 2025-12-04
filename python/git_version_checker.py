#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git 分支版本號檢查工具
可以透過拖曳資料夾來執行，會自動檢查各分支的 commit 數量
"""

import sys
import os
import subprocess
from pathlib import Path


def run_git_command(folder_path, branch):
    """執行 git rev-list --count 命令並返回結果"""
    try:
        # 切換到指定資料夾
        original_dir = os.getcwd()
        os.chdir(folder_path)
        
        # 執行 git 命令
        result = subprocess.run(
            ['git', 'rev-list', '--count', branch],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"錯誤: {result.stderr.strip()}"
            
    except subprocess.TimeoutExpired:
        return "超時"
    except FileNotFoundError:
        return "找不到 git 命令"
    except Exception as e:
        return f"異常: {str(e)}"


def check_git_repository(folder_path):
    """檢查是否為 git 倉庫"""
    git_dir = os.path.join(folder_path, '.git')
    return os.path.exists(git_dir) or os.path.isdir(git_dir)


def main():
    """主函數"""
    # 獲取拖曳進來的資料夾路徑
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        # 如果沒有參數，嘗試從當前目錄執行
        folder_path = os.getcwd()
        print("未提供資料夾路徑，使用當前目錄...")
    
    # 轉換為絕對路徑並正規化
    folder_path = os.path.abspath(folder_path)
    
    # 檢查路徑是否存在
    if not os.path.exists(folder_path):
        print(f"錯誤: 路徑不存在: {folder_path}")
        input("\n按 Enter 鍵退出...")
        return
    
    if not os.path.isdir(folder_path):
        print(f"錯誤: 這不是一個資料夾: {folder_path}")
        input("\n按 Enter 鍵退出...")
        return
    
    # 檢查是否為 git 倉庫
    if not check_git_repository(folder_path):
        print(f"錯誤: 這不是一個 Git 倉庫: {folder_path}")
        input("\n按 Enter 鍵退出...")
        return
    
    print(f"\n正在檢查 Git 倉庫: {folder_path}")
    print("=" * 60)
    
    # 要檢查的分支列表
    branches = ['origin/dev', 'origin/uat', 'origin/stage', 'origin/prod', 'origin/demo']
    
    # 執行檢查並收集結果
    results = {}
    for branch in branches:
        print(f"正在檢查分支: {branch}...", end=" ")
        count = run_git_command(folder_path, branch)
        results[branch] = count
        print(count)
    
    # 顯示整理後的結果
    print("\n" + "=" * 60)
    print("各分支版本號統計:")
    print("=" * 60)
    
    for branch in branches:
        print(f"{branch:10s}: {results[branch]}")
    
    print("=" * 60)
    
    # 保持視窗開啟（Windows 下拖曳執行時會自動關閉）
    input("\n按 Enter 鍵退出...")


if __name__ == "__main__":
    main()


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
線上版本號批次查詢工具
會讀取 gid.txt 中的所有 GID，依序下載各環境的 version.json 並整合結果到 output.txt
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
import time


# 輸入和輸出檔案路徑
GID_FILE = Path(__file__).resolve().parent / "gid.txt"
OUTPUT_FILE = Path(__file__).resolve().parent / "output.txt"

# 環境列表（對應 URL_LIST 的順序）
ENVIRONMENTS = ['dev', 'uat', 'stage', 'prod', 'demo']

# URL 列表（對應不同環境）
URL_LIST = [
    "https://download-dev.5gg.win",      # dev
    "https://download-uat.5gg.win",      # uat
    "https://download-hk.5gg.dev",       # stage
    "https://download.figoogoo.com",     # prod
    "https://download-hk.5gg.dev",       # demo
]

# 請求超時時間（秒）
REQUEST_TIMEOUT = 10


def read_gids(gid_file: Path) -> List[str]:
    """讀取 gid.txt 中的所有 GID"""
    if not gid_file.exists():
        print(f"錯誤：找不到檔案 {gid_file}")
        return []
    
    gids = []
    with open(gid_file, 'r', encoding='utf-8') as f:
        for line in f:
            gid = line.strip()
            if gid:  # 跳過空行
                gids.append(gid)
    
    return gids


def extract_gid_path(gid: str) -> str:
    """從完整 GID 中提取用於 URL 的路徑部分
    例如：Games-S5G-H5-99963 -> S5G-H5-99963
    """
    if gid.startswith("Games-"):
        return gid[6:]  # 移除 "Games-" 前綴
    return gid


def download_version_json(gid: str, base_url: str) -> Optional[int]:
    """下載指定 GID 和環境的 version.json 並解析，只返回 rev 值"""
    gid_path = extract_gid_path(gid)
    url = f"{base_url}/{gid_path}/version.json" + "?t=" + str(time.time())
    
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # 如果狀態碼不是 200，會拋出異常
        
        data = response.json()
        rev = data.get("rev")
        return rev if rev is not None else None
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def format_output(all_results: Dict[str, List[Optional[int]]]) -> str:
    """將所有結果格式化為輸出文字（格式與 version.txt 相同）"""
    lines = []
    
    # 表頭：第一欄空白，後面是環境名稱
    lines.append('\t' + '\t'.join(ENVIRONMENTS))
    
    # 按 GID 排序
    sorted_gids = sorted(all_results.keys())
    
    for gid in sorted_gids:
        revs = all_results[gid]
        # 第一欄是 GID，後面是各環境的 rev 值
        values = [gid]
        for rev in revs:
            if rev is not None:
                values.append(str(rev))
            else:
                values.append('')
        lines.append('\t'.join(values))
    
    return '\n'.join(lines)


def main():
    """主函數"""
    print("開始讀取 GID 列表...")
    gids = read_gids(GID_FILE)
    
    if not gids:
        print("沒有找到任何 GID，程式結束")
        return
    
    print(f"找到 {len(gids)} 個 GID，開始下載各環境版本資訊...")
    print(f"環境列表：{', '.join(ENVIRONMENTS)}")
    
    all_results = {}
    
    total_requests = len(gids) * len(URL_LIST)
    
    for i, gid in enumerate(gids, 1):
        print(f"[{i}/{len(gids)}] 處理 {gid}...")
        revs = []
        
        for env, base_url in zip(ENVIRONMENTS, URL_LIST):
            rev = download_version_json(gid, base_url)
            revs.append(rev)
            
            if rev is not None:
                print(f"  {env}: rev={rev} [OK]")
            else:
                print(f"  {env}: 失敗 [FAIL]")
        
        all_results[gid] = revs
    
    print("\n開始整合結果...")
    output_text = format_output(all_results)
    
    OUTPUT_FILE.write_text(output_text, encoding="utf-8")
    print(f"完成！結果已寫入 {OUTPUT_FILE}")
    
    # 統計資訊
    total_success = sum(1 for revs in all_results.values() for rev in revs if rev is not None)
    total_fail = total_requests - total_success
    print(f"總請求數：{total_requests}，成功：{total_success} 個，失敗：{total_fail} 個")


if __name__ == "__main__":
    main()


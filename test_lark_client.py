#!/usr/bin/env python3
"""
測試 Lark Client 功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.lark_client import LarkClient
from app.config import create_default_config, load_config

def test_lark_client():
    """測試 Lark Client 基本功能"""
    
    # 建立預設設定檔（如果不存在）
    if not os.path.exists('config.yaml'):
        print("建立預設設定檔...")
        create_default_config()
        print("請編輯 config.yaml 檔案，填入正確的 Lark App ID 和 Secret")
        return
    
    # 載入設定
    settings = load_config()
    
    if not settings.lark.app_id or not settings.lark.app_secret:
        print("請在 config.yaml 中設定 Lark App ID 和 Secret")
        return
    
    # 初始化 Lark Client
    print("初始化 Lark Client...")
    client = LarkClient()
    
    # 測試連接
    print("測試連接...")
    if client.test_connection():
        print("✅ Lark Client 連接成功")
        
        # 顯示效能統計
        stats = client.get_performance_stats()
        print(f"📊 效能統計: {stats}")
        
    else:
        print("❌ Lark Client 連接失敗")
        print("請檢查 config.yaml 中的 App ID 和 Secret 是否正確")

if __name__ == "__main__":
    test_lark_client()
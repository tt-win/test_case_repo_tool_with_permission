# Test Case Repository Web Tool - Development Status

## 專案概述

這是一個基於 FastAPI + Bootstrap 的測試案例管理系統，旨在整合 Lark 多維表格作為資料源，提供類似 TestRail 的網頁介面來管理測試案例和測試執行。

## 技術架構

- **後端**: FastAPI (Python 3.9+)
- **前端**: Bootstrap 5 + Jinja2 Templates + JavaScript
- **資料庫**: SQLite (用於設定和暫存資料)
- **外部整合**: Lark API, JIRA API
- **資料格式**: JSON
- **設定檔格式**: YAML (config.yaml)

## 目前開發進度

### ✅ 已完成 (Phase 0: 專案規劃)
- [x] 專案目錄結構已建立
- [x] 需求規格文件 (spec.md) 已完成
- [x] 技術架構文件 (architecture.md) 已完成
- [x] 任務分解清單 (task.md) 已完成
- [x] 開發計劃 (plan/plan.txt) 已完成
- [x] Python 相依套件清單 (requirements.txt) 已定義
- [x] 所有核心檔案結構已建立但內容為空

### 🔄 進行中 (Phase 1: 專案基礎設定)
需要開始實作以下基礎設定：
- [ ] 建立 Python 虛擬環境並安裝套件
- [ ] 初始化 Git 版本控制
- [ ] 實作基礎 FastAPI 應用程式 (app/main.py)
- [ ] 設定 SQLite 資料庫連線 (app/database.py)
- [ ] 設定 YAML 設定檔讀取功能 (app/config.py)

### ⏳ 待完成 (Phase 2-5)
- Phase 2: 後端核心功能 (資料模型、服務層)
- Phase 3: 後端 API 開發 (RESTful APIs)
- Phase 4: 前端介面開發 (HTML Templates + JavaScript)
- Phase 5: 測試與完成 (Unit Tests + Integration Tests)

## 核心功能需求

### 1. 團隊管理
- 管理各團隊的 Lark Test Case Repo URL
- 提供 URL 連線驗證功能
- 儲存團隊設定到 SQLite

### 2. 測試案例管理
- 從 Lark 多維表格讀取/寫入測試案例
- 提供搜尋、過濾、排序功能
- 支援批次操作 (刪除、修改)
- 行內編輯功能
- Markdown 支援與預覽
- 附件上傳與管理
- 自訂欄位支援

### 3. 測試執行管理
- 從 Lark Test Run 表格讀取資料
- 結果截圖上傳
- JIRA Bug 連結整合
- 測試結果通知功能

## 檔案結構現況

```
/Users/hideman/code/test_case_repo_web_tool/
├── 📋 規劃文件
│   ├── spec.md              ✅ 完整需求規格
│   ├── architecture.md      ✅ 技術架構說明
│   ├── task.md             ✅ 開發任務分解
│   ├── plan/plan.txt       ✅ 開發計劃
│   └── README.md           ⚠️  空檔案
├── 🔧 設定檔案
│   ├── requirements.txt    ✅ 相依套件清單 (已更新支援 YAML)
│   └── config.yaml        ❌ 尚未建立
├── 💻 應用程式碼
│   └── app/               ⚠️  目錄結構已建立但檔案內容為空
│       ├── main.py        ❌ 空檔案
│       ├── config.py      ❌ 空檔案
│       ├── database.py    ❌ 空檔案
│       ├── models/        ❌ 所有模型檔案為空
│       ├── services/      ❌ 所有服務檔案為空
│       ├── static/        ❌ 所有靜態資源為空
│       └── templates/     ❌ 所有模板檔案為空
└── 🧪 測試程式碼
    └── tests/             ❌ 所有測試檔案為空
```

## 下一步建議

1. **立即需要**: 開始 Phase 1 基礎設定，從建立虛擬環境和基礎 FastAPI 應用開始
2. **參考資源**: 
   - Lark Client: `/Users/hideman/code/jira_sync_v3/lark_client.py`
   - JIRA Client: `/Users/hideman/code/jira_sync_v3/jira_client.py`
   - 前端風格: `/Users/hideman/code/user_story_map_converter`
3. **開發優先順序**: 建議按照 task.md 中的階段順序進行開發

## 注意事項

- 所有核心檔案已建立但內容為空，需要從頭實作
- 專案尚未初始化 Git 版本控制
- 需要建立 config.yaml 檔案來管理設定
- 開發時需要遵循簡潔性原則，避免過於複雜的實作方式
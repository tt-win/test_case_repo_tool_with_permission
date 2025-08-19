# 專案開發任務清單 (Project Task Breakdown)

## 階段一：專案基礎設定 (Phase 1: Project Foundation)

- [ ] 建立 Python 虛擬環境
- [ ] 根據 `requirements.txt` 安裝所有相依套件
- [ ] 初始化 Git 版本控制
- [ ] 在 `app/main.py` 中設定一個基本的 "Hello World" FastAPI 應用
- [ ] 在 `app/database.py` 中完成 SQLite 資料庫的連線設定
- [ ] 在 `app/config.py` 中設定讀取 `config.yaml` 設定檔的功能

## 階段二：後端核心功能 (Phase 2: Backend Core)

### 2.1 資料模型 (Data Models)
- [ ] 在 `app/models/` 目錄下，為 Team, TestCase, TestRun 定義 Pydantic 資料模型

### 2.2 服務層 (Services)
- [ ] **Lark Client** (`app/services/lark_client.py`)
    - [ ] 實作認證機制
    - [ ] 實作讀取 Lark 多維表格的功能
    - [ ] 實作寫入 Lark 多維表格的功能
- [ ] **JIRA Client** (`app/services/jira_client.py`)
    - [ ] 實作認證機制
    - [ ] 實作新增 JIRA Bug 連結的功能

### 2.3 資料庫
- [ ] 建立初始的資料庫結構 (Schema/Tables)

## 階段三：後端 API 開發 (Phase 3: Backend API)

- [ ] **團隊管理 API**
    - [ ] `GET /api/teams` - 取得所有團隊列表
    - [ ] `POST /api/teams` - 新增一個團隊（及其 Lark Repo URL）
    - [ ] `POST /api/teams/validate` - 驗證 Lark Repo 的連線
- [ ] **測試案例管理 API**
    - [ ] `GET /api/teams/{team_id}/testcases` - 取得測試案例（包含搜尋、過濾、排序）
    - [ ] `POST /api/teams/{team_id}/testcases` - 建立新的測試案例
    - [ ] `PUT /api/teams/{team_id}/testcases/{case_id}` - 更新指定的測試案例
    - [ ] `DELETE /api/teams/{team_id}/testcases/{case_id}` - 刪除指定的測試案例
    - [ ] `POST /api/teams/{team_id}/testcases/batch` - 執行批次操作
- [ ] **測試執行管理 API**
    - [ ] `POST /api/teams/{team_id}/testruns` - 根據 Lark URL 建立一個測試執行
    - [ ] `GET /api/teams/{team_id}/testruns/{run_id}` - 取得測試執行的詳細資料
    - [ ] `POST /api/teams/{team_id}/testruns/{run_id}/results` - 新增一筆測試結果
- [ ] **其他 API**
    - [ ] 實作附件上傳與管理的 API
    - [ ] 實作發送測試結果到 Lark 的通知服務 API

## 階段四：前端介面開發 (Phase 4: Frontend UI)

- [ ] **基礎樣板**
    - [ ] 在 `app/templates/base.html` 中建立包含 Bootstrap 5 的基礎 HTML 樣板
- [ ] **頁面開發**
    - [ ] 實作團隊選擇首頁 (`index.html`)
    - [ ] 實作團隊管理頁面 (`team_management.html`)
    - [ ] 實作測試案例管理頁面 (`test_case_management.html`)
        - [ ] 列表檢視
        - [ ] 搜尋與過濾功能
        - [ ] 行內編輯 (Inline Editing)
        - [ ] 詳細內容的彈出視窗或側邊欄
        - [ ] Markdown 內容的渲染與編輯器
        - [ ] 附件管理介面
    - [ ] 實作測試執行管理頁面 (`test_run_management.html`)
        - [ ] 檢視介面
        - [ ] 截圖上傳功能
        - [ ] 新增 JIRA 連結功能
- [ ] **前端邏輯**
    - [ ] 在 `app/static/js/app.js` 中撰寫 JavaScript 程式碼
    - [ ] 串接後端 API，取得並渲染資料
    - [ ] 處理所有使用者互動事件（點擊、表單提交等）
    - [ ] 將使用者的操作設定儲存在瀏覽器中

## 階段五：測試與完成 (Phase 5: Testing & Finalization)

- [ ] 為 Services 撰寫單元測試 (`tests/test_clients.py`)
- [ ] 為 API Endpoints 撰寫整合測試 (`tests/test_api.py`)
- [ ] 撰寫 `README.md`，包含完整的專案設定與執行說明
- [ ] 最終程式碼審查與清理

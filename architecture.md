### 採用技術細節

*   **後端 (Backend)**:
    *   **框架**: **FastAPI**。這是一個現代、高效能的 Python Web 框架，非常適合開發 RESTful API。它內建了基於 Pydantic 的資料驗證，能確保 API 的穩定性。
    *   **語言**: Python 3.9+。

*   **前端 (Frontend)**:
    *   **框架**: **Bootstrap 5**。根據 `spec.md` 的要求，這將是主要的 CSS 框架，用於快速建構響應式且美觀的介面。
    *   **樣板引擎**: **Jinja2**。FastAPI 官方支援的樣板引擎，可以方便地將後端資料渲染到 HTML 頁面中。
    *   **核心技術**: HTML, CSS, JavaScript。

*   **資料庫 (Database)**:
    *   **資料庫**: **SQLite**。根據 `spec.md`，它將用於儲存應用程式設定和暫存資料，其輕量、免安裝的特性非常適合這個專案的初期階段。

*   **API 與資料交換**:
    *   **格式**: **JSON**。前後端將透過 JSON 格式進行資料交換。

### 專案目錄結構

```
/Users/hideman/code/test_case_repo_web_tool/
├── app/                      # 主要應用程式目錄
│   ├── __init__.py
│   ├── main.py               # FastAPI 應用主程式 (API 路由)
│   ├── config.py             # 應用程式設定管理
│   ├── database.py           # 資料庫連線與設定 (SQLite)
│   ├── models/               # Pydantic 資料模型 (用於 API)
│   │   ├── __init__.py
│   │   ├── team.py
│   │   ├── test_case.py
│   │   └── test_run.py
│   ├── services/             # 核心商業邏輯 (Lark/JIRA Client)
│   │   ├── __init__.py
│   │   ├── lark_client.py
│   │   └── jira_client.py
│   ├── static/               # 靜態檔案 (CSS, JS, 圖片)
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/            # Jinja2 HTML 樣板
│       ├── base.html
│       ├── index.html
│       ├── team_management.html
│       ├── test_case_management.html
│       └── test_run_management.html
│
├── tests/                    # 測試程式碼
│   ├── __init__.py
│   ├── test_api.py
│   └── test_clients.py
│
├── .env                      # 環境變數設定檔
├── .gitignore                # Git 忽略清單
├── requirements.txt          # Python 相依套件
├── README.md                 # 專案說明
├── plan/
│   └── plan.txt
└── spec.md                   # 需求規格文件
```

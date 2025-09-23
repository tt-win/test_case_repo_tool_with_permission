"""
資料庫表格模型定義

使用 SQLAlchemy 建立資料庫結構，包含 Team, TestCase, TestRun 表格
以及相關的關聯表格。
"""

import logging

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum,
    Boolean,
    Float,
    UniqueConstraint,
    Index,
    and_,
    select,
    text,
)
from sqlalchemy.orm import relationship, declarative_base, foreign, column_property
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

# 從現有的資料模型導入枚舉類型
from .lark_types import Priority, TestResultStatus
from .team import TeamStatus
from .test_run_config import TestRunStatus

# 導入認證相關枚舉
from ..auth.models import UserRole, PermissionType

Base = declarative_base()


class SyncStatus(PyEnum):
    """本地與遠端（Lark）同步狀態"""
    SYNCED = "synced"
    PENDING = "pending"         # 本地有變更，待推送到 Lark
    CONFLICT = "conflict"       # 本地與遠端同時修改，需人工處理

class Team(Base):
    """團隊表格"""
    __tablename__ = "teams"
    __table_args__ = {
        # 確保 SQLite 使用 AUTOINCREMENT，避免刪除紀錄後重複使用既有 ID
        'sqlite_autoincrement': True
    }
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Lark 相關配置
    wiki_token = Column(String(255), nullable=False)
    test_case_table_id = Column(String(255), nullable=False)
    # 移除 test_run_table_id，改用 TestRunConfig 表格處理
    
    # JIRA 相關配置
    jira_project_key = Column(String(10), nullable=True)
    default_assignee = Column(String(255), nullable=True)
    issue_type = Column(String(50), default="Bug")
    
    # 團隊設定
    enable_notifications = Column(Boolean, default=True, nullable=False)
    auto_create_bugs = Column(Boolean, default=False, nullable=False)
    default_priority = Column(Enum(Priority), default=Priority.MEDIUM)
    
    # 狀態與時間
    status = Column(Enum(TeamStatus), default=TeamStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 統計資訊
    test_case_count = Column(Integer, default=0)
    last_sync_at = Column(DateTime, nullable=True)
    
    # 關聯關係
    test_run_configs = relationship("TestRunConfig", back_populates="team")


class TestRunConfig(Base):
    """測試執行配置表格"""
    __tablename__ = "test_run_configs"
    __table_args__ = {
        # 持續遞增 ID，避免後續建立的配置重複既有編號
        'sqlite_autoincrement': True
    }
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # 基本資訊
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 測試執行元資料
    test_version = Column(String(50), nullable=True)
    test_environment = Column(String(100), nullable=True)
    build_number = Column(String(100), nullable=True)
    
    # TP 開發單票號欄位
    related_tp_tickets_json = Column(Text, nullable=True, 
                                   comment="相關 TP 開發單票號 JSON 陣列")
    tp_tickets_search = Column(String(1000), nullable=True, index=True,
                             comment="TP 票號搜尋索引欄位")
    
    # 通知設定
    notifications_enabled = Column(Boolean, default=False, nullable=False,
                                 comment="是否啟用通知")
    notify_chat_ids_json = Column(Text, nullable=True,
                                comment="選擇的 Lark chat IDs（JSON 陣列）")
    notify_chat_names_snapshot = Column(Text, nullable=True,
                                      comment="群組名稱快照（JSON 陣列）")
    notify_chats_search = Column(String(1000), nullable=True, index=True,
                               comment="群組名稱搜尋索引")
    
    # 狀態與時間
    status = Column(Enum(TestRunStatus), default=TestRunStatus.DRAFT)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # 統計資訊
    total_test_cases = Column(Integer, default=0)
    executed_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    
    # 系統欄位
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)
    
    # 關聯關係
    team = relationship("Team", back_populates="test_run_configs")
    # 本地測試執行項目
    items = relationship("TestRunItem", back_populates="config", cascade="all, delete-orphan")


class TCGRecord(Base):
    """TCG 記錄表格"""
    __tablename__ = "tcg_records"
    
    # 使用 TCG 單號作為主鍵，避免重複
    tcg_number = Column(String(50), primary_key=True)
    record_id = Column(String(255), nullable=False, index=True)
    title = Column(Text, nullable=True)
    
    # 系統欄位
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestRunItem(Base):
    """本地儲存的測試執行項目（來自本產品挑選的 Test Case）"""
    __tablename__ = "test_run_items"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("test_run_configs.id"), nullable=False, index=True)

    # 使用 Test Case 編號建立唯一識別，其他詳情從 Test Case 讀取
    test_case_number = Column(String(100), nullable=False, index=True)

    # 執行資訊
    assignee_id = Column(String(64), nullable=True)
    assignee_name = Column(String(255), nullable=True)
    assignee_en_name = Column(String(255), nullable=True)
    assignee_email = Column(String(255), nullable=True)
    assignee_json = Column(Text, nullable=True)  # 原始 assignee 結構（JSON 字串）
    test_result = Column(Enum(TestResultStatus), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_duration = Column(Integer, nullable=True)
    # 注意：環境與版本屬於 TestRunConfig 層級，不在項目層儲存

    # 多值/關聯/原始欄位（JSON 字串保存）
    attachments_json = Column(Text, nullable=True)
    execution_results_json = Column(Text, nullable=True)
    user_story_map_json = Column(Text, nullable=True)
    tcg_json = Column(Text, nullable=True)
    parent_record_json = Column(Text, nullable=True)
    raw_fields_json = Column(Text, nullable=True)
    bug_tickets_json = Column(Text, nullable=True)  # Bug Tickets（JSON Array 格式存多個 JIRA ticket 編號）

    # 結果檔案追蹤欄位
    result_files_uploaded = Column(Boolean, default=False, nullable=False, 
                                 comment="測試結果檔案是否已上傳到對應 Test Case")
    result_files_count = Column(Integer, default=0, nullable=False,
                              comment="上傳的結果檔案數量")
    upload_history_json = Column(Text, nullable=True,
                               comment="檔案上傳歷史記錄（JSON 格式）")

    # 系統欄位
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    config = relationship("TestRunConfig", back_populates="items")
    # 歷程關聯（若存在）
    histories = relationship("TestRunItemResultHistory", back_populates="item", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('config_id', 'test_case_number', name='uq_test_run_item_config_case'),
        Index('ix_test_run_items_team', 'team_id'),
        Index('ix_test_run_items_result', 'test_result'),
        Index('ix_test_run_items_files_uploaded', 'result_files_uploaded'),
    )

    # 只讀關聯：提供即時 Test Case 詳細資料
    test_case = relationship(
        "TestCaseLocal",
        primaryjoin="and_(TestRunItem.test_case_number == foreign(TestCaseLocal.test_case_number), "
                    "TestRunItem.team_id == foreign(TestCaseLocal.team_id))",
        viewonly=True,
        uselist=False,
    )


class TestRunItemResultHistory(Base):
    """測試結果歷程表"""
    __tablename__ = "test_run_item_result_history"

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    config_id = Column(Integer, ForeignKey("test_run_configs.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("test_run_items.id", ondelete="CASCADE"), nullable=False, index=True)

    prev_result = Column(Enum(TestResultStatus), nullable=True)
    new_result = Column(Enum(TestResultStatus), nullable=True)
    prev_executed_at = Column(DateTime, nullable=True)
    new_executed_at = Column(DateTime, nullable=True)

    changed_by_id = Column(String(64), nullable=True)
    changed_by_name = Column(String(255), nullable=True)
    change_source = Column(String(32), nullable=True)  # single, batch, api, sync, revert
    change_reason = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

    # 關聯
    item = relationship("TestRunItem", back_populates="histories")

    __table_args__ = (
        Index('ix_result_history_team_config', 'team_id', 'config_id'),
        Index('ix_result_history_item_time', 'item_id', 'changed_at'),
    )


class LarkDepartment(Base):
    """Lark 部門信息表"""
    __tablename__ = "lark_departments"
    
    # 主鍵使用 Lark 部門 ID
    department_id = Column(String(100), primary_key=True)
    parent_department_id = Column(String(100), nullable=True, index=True)
    
    # 組織層級
    level = Column(Integer, default=0, index=True)
    path = Column(Text, nullable=True)  # 部門路徑，如: /root/dept1/dept2
    
    # Lark 部門屬性（JSON 存儲原始 API 響應）
    leaders_json = Column(Text, nullable=True)  # 部門領導信息
    group_chat_employee_types_json = Column(Text, nullable=True)  # 群聊員工類型
    
    # 統計信息
    direct_user_count = Column(Integer, default=0)  # 直屬用戶數
    total_user_count = Column(Integer, default=0)   # 總用戶數（包含子部門）
    
    # 狀態與時間
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)
    
    # 關聯關係
    users = relationship("LarkUser", back_populates="primary_department")
    
    # 索引
    __table_args__ = (
        Index('ix_lark_dept_status', 'status'),
    )


class TestCaseLocal(Base):
    """測試案例本地中介資料表

    作為所有對 Lark Test Case 表的操作中介層，支援本地 upsert/update、索引查詢與差異同步。
    """
    __tablename__ = "test_cases"

    # 主鍵與關聯
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)

    # 與 Lark 的關聯鍵
    lark_record_id = Column(String(255), nullable=True, unique=True, index=True)

    # 核心欄位
    test_case_number = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    precondition = Column(Text, nullable=True)
    steps = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)

    # 測試結果與人員（對應 Lark 欄位，必要時使用 JSON 紀錄詳細結構）
    test_result = Column(Enum(TestResultStatus), nullable=True)
    assignee_json = Column(Text, nullable=True)

    # 關聯與多值欄位（JSON 字串保存）
    attachments_json = Column(Text, nullable=True)
    test_results_files_json = Column(Text, nullable=True)
    user_story_map_json = Column(Text, nullable=True)
    tcg_json = Column(Text, nullable=True)
    parent_record_json = Column(Text, nullable=True)
    raw_fields_json = Column(Text, nullable=True)

    # 版本與同步控制
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.SYNCED, nullable=False, index=True)
    local_version = Column(Integer, default=1, nullable=False)
    lark_version = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True, index=True)  # 可用來快速比較內容變更（例如 sha256 前 64）

    # 時間欄位策略
    # 注意：除初始同步（init）外，created_at/updated_at 以本地為主，不從 Lark 覆蓋
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)

    # 保留 Lark 系統時間戳做為參考（毫秒 epoch 轉換後的 UTC）
    lark_created_at = Column(DateTime, nullable=True)
    lark_updated_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('team_id', 'test_case_number', name='uq_test_cases_team_case_number'),
        Index('ix_test_cases_team_result', 'team_id', 'test_result'),
        Index('ix_test_cases_team_priority', 'team_id', 'priority'),
        Index('ix_test_cases_number', 'test_case_number'),
    )


# Backward-compatible computed columns for TestRunItem snapshots
TestRunItem.title = column_property(
    select(TestCaseLocal.title)
    .where(
        TestCaseLocal.team_id == TestRunItem.team_id,
        TestCaseLocal.test_case_number == TestRunItem.test_case_number
    )
    .correlate_except(TestCaseLocal)
    .scalar_subquery()
)

TestRunItem.priority = column_property(
    select(TestCaseLocal.priority)
    .where(
        TestCaseLocal.team_id == TestRunItem.team_id,
        TestCaseLocal.test_case_number == TestRunItem.test_case_number
    )
    .correlate_except(TestCaseLocal)
    .scalar_subquery()
)

TestRunItem.precondition = column_property(
    select(TestCaseLocal.precondition)
    .where(
        TestCaseLocal.team_id == TestRunItem.team_id,
        TestCaseLocal.test_case_number == TestRunItem.test_case_number
    )
    .correlate_except(TestCaseLocal)
    .scalar_subquery()
)

TestRunItem.steps = column_property(
    select(TestCaseLocal.steps)
    .where(
        TestCaseLocal.team_id == TestRunItem.team_id,
        TestCaseLocal.test_case_number == TestRunItem.test_case_number
    )
    .correlate_except(TestCaseLocal)
    .scalar_subquery()
)

TestRunItem.expected_result = column_property(
    select(TestCaseLocal.expected_result)
    .where(
        TestCaseLocal.team_id == TestRunItem.team_id,
        TestCaseLocal.test_case_number == TestRunItem.test_case_number
    )
    .correlate_except(TestCaseLocal)
    .scalar_subquery()
)


class LarkUser(Base):
    """Lark 用戶信息表"""
    __tablename__ = "lark_users"
    
    # 主鍵使用 Lark 用戶 ID
    user_id = Column(String(100), primary_key=True)
    open_id = Column(String(100), nullable=True, unique=True, index=True)
    union_id = Column(String(100), nullable=True, unique=True, index=True)
    
    # 基本信息
    name = Column(String(255), nullable=True, index=True)
    en_name = Column(String(255), nullable=True)
    enterprise_email = Column(String(255), nullable=True, unique=True, index=True)
    
    # 部門歸屬
    primary_department_id = Column(String(100), ForeignKey("lark_departments.department_id"), nullable=True, index=True)
    department_ids_json = Column(Text, nullable=True)  # JSON 存儲所有部門ID列表
    
    # 職位信息
    description = Column(String(500), nullable=True)  # 職位描述
    job_title = Column(String(255), nullable=True)    # 職稱
    employee_type = Column(Integer, nullable=True, index=True)    # 員工類型（1=正式，6=實習等）
    employee_no = Column(String(100), nullable=True)  # 工號
    
    # 聯絡信息
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    work_station = Column(String(255), nullable=True)
    mobile_visible = Column(Boolean, default=True)
    
    # 狀態信息（來自 Lark status 對象）
    is_activated = Column(Boolean, default=True, index=True)
    is_exited = Column(Boolean, default=False, index=True)
    is_frozen = Column(Boolean, default=False)
    is_resigned = Column(Boolean, default=False)
    is_unjoin = Column(Boolean, default=False)
    is_tenant_manager = Column(Boolean, default=False)
    
    # 頭像信息
    avatar_240 = Column(String(500), nullable=True)   # 240x240 頭像 URL
    avatar_640 = Column(String(500), nullable=True)   # 640x640 頭像 URL
    avatar_origin = Column(String(500), nullable=True) # 原始頭像 URL
    
    # 時間信息
    join_time = Column(Integer, nullable=True)  # Lark 入職時間戳
    
    # 系統欄位
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)
    
    # 關聯關係
    primary_department = relationship("LarkDepartment", back_populates="users")
    
    # 索引
    __table_args__ = (
        Index('ix_lark_user_status', 'is_activated', 'is_exited'),
    )


class SyncHistory(Base):
    """同步歷史記錄表"""
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    
    # 同步操作信息
    sync_type = Column(String(20), nullable=False, index=True)  # full, departments, users
    trigger_type = Column(String(20), nullable=False)  # manual, scheduled, api
    trigger_user = Column(String(255), nullable=True)  # 觸發用戶（手動同步時）
    
    # 同步狀態
    status = Column(String(20), nullable=False, index=True)  # started, running, completed, failed
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # 同步結果統計
    departments_discovered = Column(Integer, default=0)
    departments_created = Column(Integer, default=0)
    departments_updated = Column(Integer, default=0)
    users_discovered = Column(Integer, default=0)
    users_created = Column(Integer, default=0)
    users_updated = Column(Integer, default=0)
    users_duplicated = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    
    # 錯誤信息
    error_message = Column(Text, nullable=True)
    error_details_json = Column(Text, nullable=True)  # JSON 存儲詳細錯誤信息
    
    # 同步結果詳情（JSON）
    result_summary_json = Column(Text, nullable=True)  # 完整結果摘要
    department_result_json = Column(Text, nullable=True)  # 部門同步結果
    user_result_json = Column(Text, nullable=True)  # 用戶同步結果
    
    # 系統欄位
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯關係
    team = relationship("Team")
    
    # 索引
    __table_args__ = (
        Index('ix_sync_history_team_time', 'team_id', 'start_time'),
    )


# ===================== 認證系統相關表格 =====================

class User(Base):
    """使用者表格（認證系統）"""
    __tablename__ = "users"
    __table_args__ = {
        'sqlite_autoincrement': True
    }
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # 基本資訊
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER, index=True)
    
    # 狀態設定
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # 時間欄位
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # 關聯關係
    team_permissions = relationship(
        "UserTeamPermission", 
        back_populates="user", 
        cascade="all, delete-orphan",
        foreign_keys="UserTeamPermission.user_id"
    )
    active_sessions = relationship("ActiveSession", back_populates="user", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('ix_users_role_active', 'role', 'is_active'),
        Index('ix_users_email_active', 'email', 'is_active'),
        {'sqlite_autoincrement': True}
    )


class UserTeamPermission(Base):
    """使用者團隊權限表格"""
    __tablename__ = "user_team_permissions"
    __table_args__ = {
        'sqlite_autoincrement': True
    }
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(Enum(PermissionType), nullable=False, index=True)
    
    # 時間欄位
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 關聯關係
    user = relationship("User", back_populates="team_permissions", foreign_keys=[user_id])
    team = relationship("Team")
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    
    # 唯一索引：同一使用者在同一團隊只能有一種權限
    __table_args__ = (
        UniqueConstraint('user_id', 'team_id', name='uq_user_team_permission'),
        Index('ix_user_team_perms_user', 'user_id'),
        Index('ix_user_team_perms_team', 'team_id'),
        Index('ix_user_team_perms_permission', 'permission'),
        {'sqlite_autoincrement': True}
    )


class ActiveSession(Base):
    """活躍会話表格（用於Token管理與撤銷）"""
    __tablename__ = "active_sessions"
    __table_args__ = {
        'sqlite_autoincrement': True
    }
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # JWT Token 資訊
    jti = Column(String(36), unique=True, nullable=False, index=True)  # JWT ID (UUID)
    token_type = Column(String(20), default="access", nullable=False)  # access, refresh
    
    # 会話資訊
    ip_address = Column(String(45), nullable=True)  # 支持 IPv6
    user_agent = Column(String(500), nullable=True)
    
    # 狀態與時間
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(100), nullable=True)  # logout, admin_revoke, expired, etc.
    
    # 關聯關係
    user = relationship("User", back_populates="active_sessions")
    
    # 索引
    __table_args__ = (
        Index('ix_sessions_user_active', 'user_id', 'is_revoked'),
        Index('ix_sessions_expires', 'expires_at'),
        Index('ix_sessions_jti_active', 'jti', 'is_revoked'),
        {'sqlite_autoincrement': True}
    )


class PasswordResetToken(Base):
    """密碼重設令牌表格"""
    __tablename__ = "password_reset_tokens"
    __table_args__ = {
        'sqlite_autoincrement': True
    }
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 令牌資訊
    token = Column(String(64), unique=True, nullable=False, index=True)  # 隨機產生的令牌
    
    # 狀態與時間
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    
    # 安全資訊
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # 關聯關係
    user = relationship("User")
    
    # 索引
    __table_args__ = (
        Index('ix_reset_tokens_user', 'user_id', 'is_used'),
        Index('ix_reset_tokens_expires', 'expires_at'),
        {'sqlite_autoincrement': True}
    )


# 建立資料庫表格的函數
logger = logging.getLogger(__name__)


def _migrate_legacy_auth_tables(engine):
    """遷移舊的認證相關表格到新的結構"""
    with engine.begin() as conn:
        # 檢查舊 users 表格的結構
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = 'users'
        """))
        has_old_users = result.fetchone() is not None
        
        if has_old_users:
            # 檢查表格結構是否為舊版本
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]
            
            # 如果是舊版本的 users 表（有 lark_id 但沒有 username/email）
            if 'lark_id' in columns and 'username' not in columns:
                logger.info("檢測到舊版 users 表格，進行結構遷移...")
                
                # 備份舊表格
                conn.execute(text("CREATE TABLE users_legacy_backup AS SELECT * FROM users"))
                logger.info("已備份舊 users 表格至 users_legacy_backup")
                
                # 刪除舊表格
                conn.execute(text("DROP TABLE users"))
                
                # 由 SQLAlchemy 重新創庺新表格（在 Base.metadata.create_all 中處理）
                logger.info("已刪除舊 users 表，將由 SQLAlchemy 重新創庺")
            else:
                logger.info("現有 users 表格結構已為新版，無需遷移")
                
        # 處理 roles 表格（新系統不需要獨立的 roles 表）
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = 'roles'
        """))
        has_old_roles = result.fetchone() is not None
        
        if has_old_roles:
            logger.info("檢測到舊的 roles 表格，備份後刪除...")
            conn.execute(text("CREATE TABLE roles_legacy_backup AS SELECT * FROM roles"))
            conn.execute(text("DROP TABLE roles"))
            logger.info("舊 roles 表格已備份至 roles_legacy_backup 並刪除")


def create_database_tables():
    """創建所有主資料庫表格（包含認證系統）"""
    # 使用同步引擎進行表格創庺與遷移
    from app.database import get_sync_engine
    
    sync_engine = get_sync_engine()
    
    # 遷移舊的認證表格（如果存在）
    _migrate_legacy_auth_tables(sync_engine)
    
    # 創庺所有表格
    Base.metadata.create_all(bind=sync_engine)
    
    try:
        ensure_test_run_item_history_fk(sync_engine)
    except Exception as exc:
        logger.exception("修正 test_run_item_result_history 外鍵失敗: %s", exc)
    
    logger.info("主資料庫表格已創庺完成")


async def create_audit_database_tables():
    """創建審計系統獨立資料庫表格"""
    from ..audit.database import audit_db_manager, create_audit_tables
    
    if not audit_db_manager.is_initialized:
        await audit_db_manager.initialize()
    
    await create_audit_tables()
    logger.info("審計資料庫表格已創建完成")


def create_all_database_tables():
    """創建所有資料庫表格（主資料庫 + 審計資料庫）"""
    # 創建主資料庫表格
    create_database_tables()
    
    # 創建審計資料庫表格（需要在事件迴圈中執行）
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # 如果已經在事件迴圈中，創建任務
        loop.create_task(create_audit_database_tables())
        logger.info("已排程審計資料庫表格創建")
    else:
        # 否則直接執行
        loop.run_until_complete(create_audit_database_tables())


def ensure_test_run_item_history_fk(engine) -> None:
    """修復 test_run_item_result_history 表格仍引用舊備份表的外鍵。"""
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        row = connection.execute(
            text(
                "SELECT sql FROM sqlite_master "
                "WHERE type='table' AND name='test_run_item_result_history'"
            )
        ).fetchone()
        if not row or not row[0] or "test_run_items_backup_snapshot" not in row[0]:
            return

        logger.info("偵測到 test_run_item_result_history 外鍵引用備份表，開始修復")
        legacy_name = "test_run_item_result_history_legacy_fk"
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        try:
            connection.execute(text(f"ALTER TABLE test_run_item_result_history RENAME TO {legacy_name}"))

            indexes = connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND tbl_name=:tbl AND name NOT LIKE 'sqlite_autoindex%'"
                ),
                {"tbl": legacy_name},
            ).fetchall()
            for (index_name,) in indexes:
                if index_name:
                    connection.execute(text(f'DROP INDEX IF EXISTS "{index_name}"'))

            TestRunItemResultHistory.__table__.create(bind=connection)

            available_cols = connection.execute(
                text(f"PRAGMA table_info('{legacy_name}')")
            ).fetchall()
            available = {row[1] for row in available_cols}
            target_columns = [
                col.name
                for col in TestRunItemResultHistory.__table__.c
                if col.name in available
            ]
            if target_columns:
                columns_csv = ", ".join(f'"{col}"' for col in target_columns)
                connection.execute(
                    text(
                        f'INSERT INTO test_run_item_result_history ({columns_csv}) '
                        f'SELECT {columns_csv} FROM {legacy_name}'
                    )
                )

            connection.execute(text(f"DROP TABLE {legacy_name}"))

            try:
                connection.execute(
                    text(
                        "UPDATE sqlite_sequence SET seq = "
                        "COALESCE((SELECT MAX(id) FROM test_run_item_result_history), 0) "
                        "WHERE name='test_run_item_result_history'"
                    )
                )
            except Exception:
                pass
            logger.info("test_run_item_result_history 外鍵修復完成")
        finally:
            connection.execute(text("PRAGMA foreign_keys=ON"))

#!/usr/bin/env python3
"""
測試模型驗證腳本

驗證 TestCase 和 TestRun 模型是否能正確處理真實的 Lark 資料
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('/Users/hideman/code/jira_sync_v3')

from app.models.test_case import TestCase, TestCaseFieldMapping
from app.models.test_run import TestRun, TestRunFieldMapping
from app.models.lark_types import LarkUser, LarkAttachment, LarkRecord
from lark_client import LarkClient
import json
from pprint import pprint


def test_with_real_data():
    """使用真實的 Lark 資料測試模型"""
    
    # 初始化 Lark Client
    lark_client = LarkClient(
        app_id='cli_a8d1077685be102f',
        app_secret='kS35CmIAjP5tVib1LpPIqUkUJjuj3pIt'
    )
    
    wiki_token = 'Q4XxwaS2Cif80DkAku9lMKuAgof'
    lark_client.set_wiki_token(wiki_token)
    
    print("=" * 60)
    print("開始模型驗證測試")
    print("=" * 60)
    
    # 測試 TestCase 模型
    print("\n1. 測試 TestCase 模型...")
    test_case_table_id = 'tbl4SVQt73VfL690'
    
    try:
        # 獲取 TestCase 資料
        all_test_case_records = lark_client.get_all_records(test_case_table_id)
        
        # 先查看前幾筆記錄的欄位內容
        print(f"總共獲取到 {len(all_test_case_records)} 筆 TestCase 記錄")
        for i, record in enumerate(all_test_case_records[:3], 1):
            fields = record.get('fields', {})
            print(f"\n記錄 {i} 的欄位:")
            for field_id, value in fields.items():
                if isinstance(value, str) and value.strip():
                    print(f"  {field_id}: {value[:50]}...")
                elif value:
                    print(f"  {field_id}: {type(value).__name__}")
        
        # 篩選有效記錄（放寬條件，不一定要以 TCG- 開頭）
        valid_records = []
        for record in all_test_case_records:
            fields = record.get('fields', {})
            test_case_number = fields.get('Test Case Number', '')
            title = fields.get('Title', '')
            # 放寬條件，只要有內容就算有效
            if (isinstance(test_case_number, str) and test_case_number.strip()) or \
               (isinstance(title, str) and title.strip()):
                valid_records.append(record)
                if len(valid_records) >= 2:  # 只測試前2筆有效記錄
                    break
        
        print(f"\n獲取到 {len(valid_records)} 筆有效的 TestCase 記錄")
        
        for i, record in enumerate(valid_records, 1):
            print(f"\n--- TestCase 記錄 {i} ---")
            print(f"Record ID: {record.get('record_id')}")
            
            # 轉換為 TestCase 模型（暫時放寬驗證）
            try:
                test_case = TestCase.from_lark_record(record, team_id=1)
            except Exception as e:
                print(f"模型轉換失敗: {e}")
                # 顯示原始欄位資料以便除錯
                fields = record.get('fields', {})
                print("原始欄位資料:")
                for field_id, value in fields.items():
                    print(f"  {field_id}: {value}")
                continue
            
            print(f"測試案例編號: {test_case.test_case_number}")
            print(f"標題: {test_case.title}")
            print(f"優先級: {test_case.priority}")
            print(f"指派人員: {test_case.assignee.display_name if test_case.assignee else 'None'}")
            print(f"測試結果: {test_case.test_result}")
            print(f"附件數量: {test_case.get_attachment_count()}")
            print(f"TCG 編號: {test_case.get_tcg_number()}")
            print(f"User Story: {test_case.get_user_story()}")
            
            # 測試轉換回 Lark 格式
            lark_fields = test_case.to_lark_fields()
            print(f"Lark 欄位數量: {len(lark_fields)}")
            
            # 驗證欄位映射
            mappings = TestCaseFieldMapping.get_all_field_ids()
            print(f"欄位映射數量: {len(mappings)}")
            
    except Exception as e:
        print(f"TestCase 模型測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # 測試 TestRun 模型
    print("\n2. 測試 TestRun 模型...")
    test_run_table_id = 'tbltzUlFtQPNX7t2'
    
    try:
        # 獲取 TestRun 資料
        all_test_run_records = lark_client.get_all_records(test_run_table_id)
        
        # 篩選有效記錄（有 ticket_number 和 title）
        valid_run_records = []
        for record in all_test_run_records:
            fields = record.get('fields', {})
            test_case_number = fields.get('Test Case Number', '').strip()
            title = fields.get('Title', '').strip()
            if test_case_number and title and test_case_number.startswith('TCG-'):
                valid_run_records.append(record)
                if len(valid_run_records) >= 2:  # 只測試前2筆有效記錄
                    break
        
        print(f"獲取到 {len(valid_run_records)} 筆有效的 TestRun 記錄")
        
        for i, record in enumerate(valid_run_records, 1):
            print(f"\n--- TestRun 記錄 {i} ---")
            print(f"Record ID: {record.get('record_id')}")
            
            # 轉換為 TestRun 模型
            test_run = TestRun.from_lark_record(record, team_id=1)
            
            print(f"測試案例編號: {test_run.test_case_number}")
            print(f"標題: {test_run.title}")
            print(f"優先級: {test_run.priority}")
            print(f"執行人員: {test_run.assignee.display_name if test_run.assignee else 'None'}")
            print(f"測試結果: {test_run.test_result}")
            print(f"一般附件數量: {len(test_run.attachments)}")
            print(f"執行結果附件數量: {test_run.get_execution_result_count()}")
            print(f"總附件數量: {test_run.get_total_attachment_count()}")
            print(f"是否已執行: {test_run.is_executed()}")
            print(f"是否有執行截圖: {len(test_run.get_execution_screenshots())} 張")
            
            # 測試轉換回 Lark 格式
            lark_fields = test_run.to_lark_fields()
            print(f"Lark 欄位數量: {len(lark_fields)}")
            
            # 測試執行摘要
            summary = test_run.get_execution_summary()
            print(f"執行摘要: {summary}")
            
            # 驗證欄位映射
            mappings = TestRunFieldMapping.get_all_field_ids()
            print(f"欄位映射數量: {len(mappings)}")
            
    except Exception as e:
        print(f"TestRun 模型測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    # 測試基礎資料類型
    print("\n3. 測試基礎資料類型...")
    
    # 測試 LarkUser
    if valid_run_records:
        sample_record = valid_run_records[0]
        assignee_data = sample_record.get('fields', {}).get('Assignee')  # Assignee field
        if assignee_data:
            print("\n--- LarkUser 測試 ---")
            print(f"原始資料: {assignee_data}")
            
            from app.models.lark_types import parse_lark_user
            user = parse_lark_user(assignee_data)
            if user:
                print(f"解析後: {user}")
                print(f"顯示名稱: {user.display_name}")
                print(f"字串表示: {str(user)}")
    
    # 測試 LarkAttachment
    if valid_run_records:
        sample_record = valid_run_records[0]
        execution_result_data = sample_record.get('fields', {}).get('Execution Result')  # Execution Result field
        if execution_result_data:
            print("\n--- LarkAttachment 測試 ---")
            print(f"原始資料數量: {len(execution_result_data)}")
            
            from app.models.lark_types import parse_lark_attachments
            attachments = parse_lark_attachments(execution_result_data)
            for att in attachments:
                print(f"檔案: {att.name}")
                print(f"大小: {att.size_mb} MB")
                print(f"是否為圖片: {att.is_image}")
                print(f"副檔名: {att.file_extension}")
    
    print("\n=" * 60)
    print("模型驗證測試完成")
    print("=" * 60)


def test_model_creation():
    """測試模型的建立和驗證"""
    
    print("\n4. 測試模型建立...")
    
    # 測試 TestCase 建立
    try:
        test_case = TestCase(
            test_case_number="TCG-99999.001.001",
            title="測試案例標題",
            priority="Medium",
            precondition="這是前置條件",
            steps="1. 步驟一\n2. 步驟二",
            expected_result="預期結果",
            team_id=1
        )
        
        print("TestCase 建立成功:")
        print(f"  編號: {test_case.test_case_number}")
        print(f"  標題: {test_case.title}")
        print(f"  步驟列表: {test_case.get_steps_list()}")
        print(f"  是否通過: {test_case.is_passed()}")
        
    except Exception as e:
        print(f"TestCase 建立失敗: {e}")
    
    # 測試 TestRun 建立
    try:
        test_run = TestRun(
            test_case_number="TCG-99999.001.001",
            title="測試執行標題",
            priority="High",
            test_result="Passed",
            team_id=1
        )
        
        print("\nTestRun 建立成功:")
        print(f"  編號: {test_run.test_case_number}")
        print(f"  標題: {test_run.title}")
        print(f"  是否已執行: {test_run.is_executed()}")
        print(f"  是否通過: {test_run.is_passed()}")
        
        # 測試統計功能
        from app.models.test_run import TestRunStatistics
        stats = TestRunStatistics(
            total_runs=10,
            executed_runs=8,
            passed_runs=6,
            failed_runs=1,
            retest_runs=1,
            not_available_runs=0
        )
        
        print(f"\n統計測試:")
        print(f"  執行率: {stats.execution_rate}%")
        print(f"  通過率: {stats.pass_rate}%")
        print(f"  總通過率: {stats.total_pass_rate}%")
        
    except Exception as e:
        print(f"TestRun 建立失敗: {e}")


if __name__ == "__main__":
    test_with_real_data()
    test_model_creation()
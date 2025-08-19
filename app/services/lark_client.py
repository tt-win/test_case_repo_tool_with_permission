import logging
import requests
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from ..config import settings


class LarkAuthManager:
    """Lark 認證管理器"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or settings.lark.app_id
        self.app_secret = app_secret or settings.lark.app_secret
        
        # Token 快取
        self._tenant_access_token = None
        self._token_expire_time = None
        self._token_lock = threading.Lock()
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkAuthManager")
        
        # API 配置
        self.auth_url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        self.timeout = 30
    
    def get_tenant_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """獲取 Tenant Access Token"""
        with self._token_lock:
            # 檢查是否需要刷新
            if (not force_refresh and 
                self._tenant_access_token and 
                self._token_expire_time and 
                datetime.now() < self._token_expire_time):
                return self._tenant_access_token
            
            # 獲取新 Token
            try:
                response = requests.post(
                    self.auth_url,
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Token 獲取失敗，HTTP {response.status_code}")
                    return None
                
                result = response.json()
                
                if result.get('code') != 0:
                    self.logger.error(f"Token 獲取失敗: {result.get('msg')}")
                    return None
                
                # 快取 Token
                self._tenant_access_token = result['tenant_access_token']
                expire_seconds = result.get('expire', 7200)
                self._token_expire_time = datetime.now() + timedelta(seconds=expire_seconds - 300)
                
                return self._tenant_access_token
                
            except Exception as e:
                self.logger.error(f"Token 獲取異常: {e}")
                return None
    
    def is_token_valid(self) -> bool:
        """檢查 Token 是否有效"""
        return (self._tenant_access_token is not None and 
                self._token_expire_time is not None and 
                datetime.now() < self._token_expire_time)


class LarkTableManager:
    """Lark 表格管理器"""
    
    def __init__(self, auth_manager: LarkAuthManager):
        self.auth_manager = auth_manager
        
        # 快取
        self._obj_tokens = {}     # wiki_token -> obj_token
        self._cache_lock = threading.Lock()
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkTableManager")
        
        # API 配置
        self.base_url = "https://open.larksuite.com/open-apis"
        self.timeout = 30
    
    def get_obj_token(self, wiki_token: str) -> Optional[str]:
        """從 Wiki Token 獲取 Obj Token"""
        with self._cache_lock:
            if wiki_token in self._obj_tokens:
                return self._obj_tokens[wiki_token]
        
        try:
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                return None
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/wiki/v2/spaces/get_node?token={wiki_token}"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code != 200:
                self.logger.error(f"Wiki Token 解析失敗，HTTP {response.status_code}")
                return None
            
            result = response.json()
            if result.get('code') != 0:
                self.logger.error(f"Wiki Token 解析失敗: {result.get('msg')}")
                return None
            
            obj_token = result['data']['node']['obj_token']
            
            # 快取結果
            with self._cache_lock:
                self._obj_tokens[wiki_token] = obj_token
            
            return obj_token
            
        except Exception as e:
            self.logger.error(f"Wiki Token 解析異常: {e}")
            return None
    
    def get_table_fields(self, obj_token: str, table_id: str) -> List[Dict[str, Any]]:
        """獲取表格的完整欄位結構"""
        try:
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                return []
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/fields"
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code != 200:
                self.logger.error(f"獲取表格欄位失敗，HTTP {response.status_code}: {response.text}")
                return []
            
            result = response.json()
            if result.get('code') != 0:
                self.logger.error(f"獲取表格欄位失敗: {result.get('msg')}")
                return []
            
            fields = result.get('data', {}).get('items', [])
            self.logger.debug(f"獲取表格 {table_id} 的 {len(fields)} 個欄位")
            return fields
            
        except Exception as e:
            self.logger.error(f"獲取表格欄位異常: {e}")
            return []
    
    def get_available_field_names(self, obj_token: str, table_id: str) -> List[str]:
        """獲取表格中所有可用的欄位名稱"""
        fields = self.get_table_fields(obj_token, table_id)
        return [field.get('field_name', '') for field in fields if field.get('field_name')]


class LarkRecordManager:
    """Lark 記錄管理器"""
    
    def __init__(self, auth_manager: LarkAuthManager):
        self.auth_manager = auth_manager
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkRecordManager")
        
        # API 配置
        self.base_url = "https://open.larksuite.com/open-apis"
        self.timeout = 60
        self.max_page_size = 500
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict]:
        """統一的 HTTP 請求方法"""
        try:
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                self.logger.error("無法獲取 Access Token")
                return None
            
            headers = kwargs.pop('headers', {})
            headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
            
            response = requests.request(
                method, url, 
                headers=headers, 
                timeout=self.timeout,
                **kwargs
            )
            
            if response.status_code != 200:
                self.logger.error(f"API 請求失敗，HTTP {response.status_code}: {response.text}")
                return None
            
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"API 請求失敗: {error_msg}")
                return None
            
            return result.get('data', {})
            
        except Exception as e:
            self.logger.error(f"API 請求異常: {e}")
            return None
    
    def get_all_records(self, obj_token: str, table_id: str) -> List[Dict]:
        """獲取表格所有記錄（高效全表掃描）"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records"
        
        all_records = []
        page_token = None
        
        while True:
            params = {'page_size': self.max_page_size}
            if page_token:
                params['page_token'] = page_token
            
            result = self._make_request('GET', url, params=params)
            if not result:
                break
            
            records = result.get('items', [])
            all_records.extend(records)
            
            # 檢查是否還有更多記錄
            page_token = result.get('page_token')
            if not page_token or not result.get('has_more', False):
                break
        
        self.logger.info(f"全表掃描完成，共獲取 {len(all_records)} 筆記錄")
        return all_records
    
    def create_record(self, obj_token: str, table_id: str, fields: Dict) -> Optional[str]:
        """創建單筆記錄"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records"
        
        data = {'fields': fields}
        result = self._make_request('POST', url, json=data)
        
        if result:
            record = result.get('record', {})
            return record.get('record_id')
        return None
    
    def update_record(self, obj_token: str, table_id: str, record_id: str, fields: Dict) -> bool:
        """更新單筆記錄"""
        url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/{record_id}"
        
        data = {'fields': fields}
        result = self._make_request('PUT', url, json=data)
        return result is not None
    
    def batch_create_records(self, obj_token: str, table_id: str, 
                           records_data: List[Dict]) -> Tuple[bool, List[str], List[str]]:
        """批次創建記錄"""
        if not records_data:
            return True, [], []
        
        max_batch_size = 500
        success_ids = []
        error_messages = []
        
        # 分批處理
        for i in range(0, len(records_data), max_batch_size):
            batch_data = records_data[i:i + max_batch_size]
            
            # 準備批次數據
            records = [{'fields': fields} for fields in batch_data]
            data = {'records': records}
            
            url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/batch_create"
            result = self._make_request('POST', url, json=data)
            
            if result:
                records = result.get('records', [])
                batch_ids = [record.get('record_id') for record in records if record.get('record_id')]
                success_ids.extend(batch_ids)
            else:
                error_messages.append(f"批次 {i//max_batch_size + 1} 創建失敗")
        
        overall_success = len(error_messages) == 0
        self.logger.info(f"批次創建完成，成功: {len(success_ids)}, 失敗: {len(error_messages)}")
        
        return overall_success, success_ids, error_messages
    
    def batch_update_records(self, obj_token: str, table_id: str, 
                           updates: List[Tuple[str, Dict[str, Any]]]) -> bool:
        """批量更新記錄（自動分批處理）"""
        if not updates:
            return True
        
        batch_size = 500
        
        # 分批處理
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # 準備批次數據
            payload = {
                'records': [
                    {
                        'record_id': record_id,
                        'fields': fields
                    }
                    for record_id, fields in batch
                ]
            }
            
            url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/batch_update"
            result = self._make_request('POST', url, json=payload)
            
            if not result:
                self.logger.error(f"批次更新失敗 {i+1}-{i+len(batch)}/{len(updates)}")
                return False
            
            self.logger.info(f"批次更新記錄 {i+1}-{i+len(batch)}/{len(updates)} 成功")
        
        self.logger.info(f"成功批量更新 {len(updates)} 筆記錄")
        return True
    
    def batch_delete_records(self, obj_token: str, table_id: str, 
                           record_ids: List[str]) -> bool:
        """批次刪除記錄"""
        if not record_ids:
            return True
        
        max_batch_size = 500
        
        # 分批處理
        for i in range(0, len(record_ids), max_batch_size):
            batch_ids = record_ids[i:i + max_batch_size]
            
            # 準備批次刪除數據
            data = {'records': batch_ids}
            
            url = f"{self.base_url}/bitable/v1/apps/{obj_token}/tables/{table_id}/records/batch_delete"
            result = self._make_request('POST', url, json=data)
            
            if not result:
                self.logger.error(f"批次刪除失敗")
                return False
        
        self.logger.info(f"批次刪除完成，共刪除 {len(record_ids)} 筆記錄")
        return True


class LarkClient:
    """Lark Base Client - 專注於高效的全表掃描功能"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or settings.lark.app_id
        self.app_secret = app_secret or settings.lark.app_secret
        
        # 設定日誌
        self.logger = logging.getLogger(f"{__name__}.LarkClient")
        
        # 初始化管理器
        self.auth_manager = LarkAuthManager(self.app_id, self.app_secret)
        self.table_manager = LarkTableManager(self.auth_manager)
        self.record_manager = LarkRecordManager(self.auth_manager)
        
        # 當前 Wiki Token
        self._current_wiki_token = None
        self._current_obj_token = None
        
        self.logger.info("Lark Client 初始化完成")
    
    def set_wiki_token(self, wiki_token: str) -> bool:
        """設定當前使用的 Wiki Token"""
        self._current_wiki_token = wiki_token
        
        # 立即解析 Obj Token
        obj_token = self.table_manager.get_obj_token(wiki_token)
        if obj_token:
            self._current_obj_token = obj_token
            self.logger.info(f"Wiki Token 設定成功")
            return True
        else:
            self.logger.error(f"Wiki Token 設定失敗")
            return False
    
    def test_connection(self, wiki_token: str = None) -> bool:
        """測試連接"""
        try:
            # 測試認證
            token = self.auth_manager.get_tenant_access_token()
            if not token:
                self.logger.error("認證失敗")
                return False
            
            # 如果提供了 wiki_token，測試 Obj Token 解析
            if wiki_token:
                obj_token = self.table_manager.get_obj_token(wiki_token)
                if not obj_token:
                    self.logger.error("Wiki Token 解析失敗")
                    return False
            
            self.logger.info("連接測試成功")
            return True
            
        except Exception as e:
            self.logger.error(f"連接測試異常: {e}")
            return False
    
    def get_all_records(self, table_id: str, wiki_token: str = None) -> List[Dict]:
        """獲取表格所有記錄（主要功能）"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return []
        
        return self.record_manager.get_all_records(obj_token, table_id)
    
    def create_record(self, table_id: str, fields: Dict, wiki_token: str = None) -> Optional[str]:
        """創建單筆記錄"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return None
        
        return self.record_manager.create_record(obj_token, table_id, fields)
    
    def update_record(self, table_id: str, record_id: str, fields: Dict,
                     wiki_token: str = None) -> bool:
        """更新單筆記錄"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return False
        
        return self.record_manager.update_record(obj_token, table_id, record_id, fields)
    
    def get_table_fields(self, table_id: str, wiki_token: str = None) -> List[Dict[str, Any]]:
        """獲取表格的完整欄位結構"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return []
        
        return self.table_manager.get_table_fields(obj_token, table_id)
    
    def get_available_field_names(self, table_id: str, wiki_token: str = None) -> List[str]:
        """獲取表格中所有可用的欄位名稱"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return []
        
        return self.table_manager.get_available_field_names(obj_token, table_id)
    
    def batch_create_records(self, table_id: str, records: List[Dict],
                           wiki_token: str = None) -> Tuple[bool, List[str], List[str]]:
        """批次創建記錄"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return False, [], ['無法獲取 Obj Token']
        
        return self.record_manager.batch_create_records(obj_token, table_id, records)
    
    def batch_delete_records(self, table_id: str, record_ids: List[str],
                           wiki_token: str = None) -> bool:
        """批次刪除記錄"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return False
        
        return self.record_manager.batch_delete_records(obj_token, table_id, record_ids)
    
    def batch_update_records(self, table_id: str, updates: List[Tuple[str, Dict]],
                           wiki_token: str = None) -> bool:
        """批次更新記錄"""
        obj_token = self._get_obj_token(wiki_token)
        if not obj_token:
            return False
        
        return self.record_manager.batch_update_records(obj_token, table_id, updates)
    
    def _get_obj_token(self, wiki_token: str = None) -> Optional[str]:
        """獲取 Obj Token（內部方法）"""
        if wiki_token:
            return self.table_manager.get_obj_token(wiki_token)
        elif self._current_obj_token:
            return self._current_obj_token
        elif self._current_wiki_token:
            obj_token = self.table_manager.get_obj_token(self._current_wiki_token)
            if obj_token:
                self._current_obj_token = obj_token
            return obj_token
        else:
            self.logger.error("沒有可用的 Wiki Token")
            return None
    
    def get_performance_stats(self) -> Dict:
        """獲取效能統計資訊"""
        return {
            'auth_token_valid': self.auth_manager.is_token_valid(),
            'obj_token_cache_size': len(self.table_manager._obj_tokens),
            'client_type': 'LarkClient',
            'features': ['全表掃描', '批次操作']
        }
    
    def clear_caches(self):
        """清理所有快取"""
        with self.table_manager._cache_lock:
            self.table_manager._obj_tokens.clear()
        
        self.logger.info("所有快取已清理")
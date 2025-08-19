import yaml
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel

class LarkConfig(BaseModel):
    app_id: str = ""
    app_secret: str = ""
    tenant_token: str = ""

class JiraConfig(BaseModel):
    server_url: str = ""
    username: str = ""
    api_token: str = ""

class AppConfig(BaseModel):
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./test_case_repo.db"
    
class Settings(BaseModel):
    app: AppConfig = AppConfig()
    lark: LarkConfig = LarkConfig()
    jira: JiraConfig = JiraConfig()

def load_config(config_path: str = "config.yaml") -> Settings:
    """€Ö YAML -š”"""
    if not os.path.exists(config_path):
        # ‚œ-š”X(Þ³--š
        return Settings()
    
    with open(config_path, 'r', encoding='utf-8') as file:
        config_data = yaml.safe_load(file) or {}
    
    return Settings(**config_data)

def create_default_config(config_path: str = "config.yaml") -> None:
    """úË--š”"""
    default_config = {
        "app": {
            "debug": False,
            "host": "0.0.0.0",
            "port": 8000,
            "database_url": "sqlite:///./test_case_repo.db"
        },
        "lark": {
            "app_id": "",
            "app_secret": "",
            "tenant_token": ""
        },
        "jira": {
            "server_url": "",
            "username": "",
            "api_token": ""
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as file:
        yaml.dump(default_config, file, default_flow_style=False, allow_unicode=True)

# hß-šæ‹
settings = load_config()
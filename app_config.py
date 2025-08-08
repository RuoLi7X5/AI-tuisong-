from __future__ import annotations

import json
import os
from typing import Any, Dict


def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as exc:  # noqa: BLE001
        print(f"[配置] 读取 {path} 失败: {exc}")
        return {}


def get_config() -> Dict[str, Any]:
    """Load configuration from config.json at project root (if present)."""
    root = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(root, "config.json")
    return _load_json(cfg_path)


def get_wxpusher_config() -> Dict[str, str]:
    cfg = get_config().get("wxpusher", {})
    return {
        "app_token": cfg.get("app_token", ""),
        "uid": cfg.get("uid", ""),
    }


def get_openai_config() -> Dict[str, str]:
    cfg = get_config().get("openai", {})
    return {
        "api_key": cfg.get("api_key", ""),
        "base_url": cfg.get("base_url", "https://openrouter.ai/api/v1"),
        "model": cfg.get("model", "openai/gpt-4o-mini"),
    }



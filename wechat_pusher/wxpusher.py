import os
import requests
from app_config import get_wxpusher_config


class WxPusherPusher:
    def __init__(self, token: str | None = None, uid: str | None = None) -> None:
        # Priority: env > args > config.json
        cfg = get_wxpusher_config()
        self.token = (os.getenv("WXPUSHER_APP_TOKEN") or token or cfg.get("app_token", "") or "").strip()
        self.uid = (os.getenv("WXPUSHER_UID") or uid or cfg.get("uid", "") or "").strip()

    def push(self, news_item):
        # news_item: dict, 包含title/summary/url
        url = "https://wxpusher.zjiecode.com/api/send/message"
        content = (
            f"标题：{news_item.get('title', '')}\n"
            f"摘要：{news_item.get('summary', '')}\n"
            f"标签：{', '.join(news_item.get('tags', [])) if news_item.get('tags') else ''}\n"
            f"链接：{news_item.get('url', '')}"
        )
        data = {
            "appToken": self.token,
            "content": content,
            "contentType": 1,
            "uids": [self.uid] if self.uid else [],
        }
        try:
            if not self.token or not self.uid:
                print("[推送提示] 未配置WxPusher token或uid，已跳过发送。")
                return
            resp = requests.post(url, json=data, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"微信推送失败: {e}")

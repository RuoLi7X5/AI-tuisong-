# wechat_pusher/wxpusher.py
# 用WxPusher推送到微信
import requests

class WxPusherPusher:
    def __init__(self, token=None, uid=None):
        self.token = token or "AT_ShKlAaJrnseK9qDfpuVGHGlw66jLChDn"
        self.uid = uid or "UID_EeV66gptdcw4iwmYGpLSheBLv4Zf"

    def push(self, news_item):
        # news_item: dict, 包含title/summary/url
        url = "http://wxpusher.zjiecode.com/api/send/message"
        data = {
            "appToken": self.token,
            "content": f"标题：{news_item['title']}\n摘要：{news_item.get('summary', '')}\n链接：{news_item['url']}",
            "contentType": 1,
            "uids": [self.uid],
        }
        try:
            resp = requests.post(url, json=data)
            resp.raise_for_status()
        except Exception as e:
            print(f"微信推送失败: {e}")

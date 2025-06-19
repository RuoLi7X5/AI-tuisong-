# wechat_pusher/__init__.py
from .wxpusher import WxPusherPusher

def push_to_wechat(news_item):
    # 预留：可切换不同推送方式
    pusher = WxPusherPusher()
    pusher.push(news_item)

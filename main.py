# main.py
# 主入口，调度爬虫、摘要、推送
import schedule
import time
from news_crawler import run_all_crawlers
from summarizer import summarize_news
from wechat_pusher import push_to_wechat
import sys

class Logger(object):
    def __init__(self, filename="print.log"):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    def flush(self):
        self.terminal.flush()
        self.log.flush()
sys.stdout = Logger("print.log")
sys.stderr = Logger("print.log")

def job():
    # 1. 获取新闻
    news_list = run_all_crawlers()
    print(f"抓取到新闻数量: {len(news_list)}")
    # 2. AI摘要
    summarized = [summarize_news(news) for news in news_list]
    print("AI摘要示例：", summarized[0] if summarized else "无摘要")
    # 3. 微信推送
    for item in summarized:
        print("推送内容：", item)
        push_to_wechat(item)

if __name__ == "__main__":
    from wechat_pusher.wxpusher import WxPusherPusher
    pusher = WxPusherPusher()
    test_news = {
        "title": "测试推送",
        "summary": "这是一条来自本地的WxPusher推送测试消息。",
        "url": "https://wxpusher.zjiecode.com/"
    }
    print("推送内容：", test_news)
    pusher.push(test_news)
    print("测试推送已执行，请检查你的微信！")
    job()  # 启动时立即执行一次
    schedule.every().hour.at(":00").do(job)  # 每个整点执行一次
    print("AI新闻推送工具已启动...")
    while True:
        schedule.run_pending()
        time.sleep(60)

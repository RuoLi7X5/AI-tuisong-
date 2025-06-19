# main.py
# 主入口，调度爬虫、摘要、推送
import schedule
import time
from news_crawler import run_all_crawlers
from summarizer import summarize_news
from wechat_pusher import push_to_wechat

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
    job()  # 启动时立即执行一次
    schedule.every().hour.at(":00").do(job)  # 每个整点执行一次
    print("AI新闻推送工具已启动...")
    while True:
        schedule.run_pending()
        time.sleep(60)

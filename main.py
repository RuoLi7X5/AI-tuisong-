# main.py
# 主入口，调度爬虫、摘要、推送
import argparse
import schedule
import time
from news_crawler import run_all_crawlers
from summarizer import summarize_news
from summarizer.openai_summarizer import summarize_batch
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
    # 2. AI摘要（并行）
    summarized = summarize_batch(news_list, max_workers=4)
    print("AI摘要示例：", summarized[0] if summarized else "无摘要")
    # 3. 微信推送
    for item in summarized:
        print("推送内容：", item)
        push_to_wechat(item)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 新闻推送工具")
    parser.add_argument("--once", action="store_true", help="只执行一次后退出（CI/工作流模式）")
    parser.add_argument("--interval-mins", type=int, default=60, help="循环模式下的运行间隔（分钟）")
    args = parser.parse_args()

    job()  # 启动时立即执行一次

    if args.once:
        sys.exit(0)

    # 循环模式：按间隔分钟运行
    schedule.clear()
    schedule.every(args.interval_mins).minutes.do(job)
    print("AI新闻推送工具已启动（循环模式）...")
    while True:
        schedule.run_pending()
        time.sleep(5)

# main.py
# 主入口，调度爬虫、摘要、推送
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
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
    # 分类：核心一（基金板块/黄金）、政策扩展、核心二（AI行业）
    core1_items = []
    policy_items = []
    ai_items = []
    for it in news_list:
        tags = it.get("tags", [])
        if "AI行业" in tags:
            ai_items.append(it)
        elif "政策类" in tags:
            policy_items.append(it)
        else:
            core1_items.append(it)

    # 时间窗口控制（Asia/Shanghai）
    now_cn = datetime.now(ZoneInfo("Asia/Shanghai"))
    hhmm = now_cn.strftime("%H:%M")
    core1_allowed_times = {"11:50", "18:00"}
    allow_core1 = hhmm in core1_allowed_times

    # 条数限制：政策<=5，AI<=8；核心一不限制但仅在允许时间推送
    selected_items = []
    if allow_core1:
        selected_items.extend(core1_items)
    selected_items.extend(policy_items[:5])
    selected_items.extend(ai_items[:8])

    print(
        f"本次分类：核心一 {len(core1_items)} 条（允许推送={allow_core1}），政策 {len(policy_items)} 条→{len(policy_items[:5])}，AI {len(ai_items)} 条→{len(ai_items[:8])}"
    )

    # 2. AI摘要（并行）
    summarized = summarize_batch(selected_items, max_workers=4)
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

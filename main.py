# main.py
# 主入口，调度爬虫、摘要、推送
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import schedule
import time
from news_crawler import run_all_crawlers
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
    print(f"=== [VERSION 2.0] AGGREGATED PUSH LOGIC START ===")
    # 1. 获取新闻
    print(f"[{datetime.now()}] 开始抓取任务...")
    news_list = run_all_crawlers()
    print(f"抓取到新内容数量: {len(news_list)}")

    # 分类
    cctv_items = []
    policy_items = []
    market_items = []

    for it in news_list:
        tags = it.get("tags", [])
        if "新闻联播" in tags or "政治" in tags:
            # 优先归为 CCTV/时政
            if "新闻联播" in tags or "政治" in tags: 
                 # 注意：CCTVNewsCrawler 的 item 会有 "新闻联播" tag
                 # PolicyWatchCrawler 的 item 会有 "政策类" tag
                 if "新闻联播" in tags:
                     cctv_items.append(it)
                 else:
                     policy_items.append(it)
        elif "政策类" in tags:
            policy_items.append(it)
        else:
            market_items.append(it)

    # 限制每批次处理数量，防止过多
    # CCTV 通常只有1条，不限制
    policy_items = policy_items[:10]
    market_items = market_items[:15]

    print(f"分类结果：CCTV {len(cctv_items)} 条，时政/政策 {len(policy_items)} 条，股市/行业 {len(market_items)} 条")

    # 2. 摘要 (CCTV 已经是摘要或原文，暂不通过 AI 摘要，除非内容过长)
    # 仅对政策和市场新闻进行 AI 摘要
    items_to_summarize = policy_items + market_items
    if items_to_summarize:
        print(f"正在生成摘要，共 {len(items_to_summarize)} 条...")
        summarized_items = summarize_batch(items_to_summarize, max_workers=4)
    else:
        summarized_items = []

    # 重新归类摘要后的内容
    policy_sums = []
    market_sums = []
    
    # 建立映射以便快速归类
    sum_map = {id(it): it for it in summarized_items} # 这里 id 可能不准，因为 summarize_batch 返回新对象
    # summarize_batch 通常保留原对象字段，我们通过 url/title 匹配
    # 简单处理：遍历 summarized_items，检查 tags
    
    for item in summarized_items:
        tags = item.get("tags", [])
        if "政策类" in tags or "政治" in tags:
             policy_sums.append(item)
        else:
             market_sums.append(item)

    # 3. 微信推送 (聚合发送)
    
    # A. 新闻联播 (单独推送)
    for item in cctv_items:
        # 格式化一下
        title = f"【新闻联播】{item.get('title')}"
        # 如果是 crawler 抓取的“主要内容”，通常 content 就是列表
        push_to_wechat({
            "title": title,
            "summary": item.get('content'), # 直接使用 content，通常是摘要
            "url": item.get('url')
        })
        print(f"已推送 CCTV 内容: {title}")

    # B. 时政/政策 (聚合)
    if policy_sums:
        content_lines = []
        for idx, item in enumerate(policy_sums, 1):
            summary = item.get('summary', (item.get('content') or "")[:100]).replace('\n', ' ')
            content_lines.append(f"{idx}. {item['title']}\n   {summary}")
        
        full_text = "\n\n".join(content_lines)
        title = f"【时政与政策速递】 {datetime.now().strftime('%m-%d %H:%M')}"
        push_to_wechat({
            "title": title,
            "summary": full_text,
            "url": ""
        })
        print(f"已推送政策聚合: {title}")

    # C. 股市/行业 (聚合)
    if market_sums:
        content_lines = []
        for idx, item in enumerate(market_sums, 1):
            summary = item.get('summary', (item.get('content') or "")[:100]).replace('\n', ' ')
            content_lines.append(f"{idx}. {item['title']}\n   {summary}")
        
        full_text = "\n\n".join(content_lines)
        title = f"【市场与行业动态】 {datetime.now().strftime('%m-%d %H:%M')}"
        push_to_wechat({
            "title": title,
            "summary": full_text,
            "url": ""
        })
        print(f"已推送市场聚合: {title}")

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
    print(f"AI新闻推送工具已启动（循环模式），间隔 {args.interval_mins} 分钟...")
    while True:
        schedule.run_pending()
        time.sleep(5)

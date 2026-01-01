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
from pending_store import PendingStore

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

def _classify(news_list):
    cctv_items = []
    policy_items = []
    market_items = []
    for it in news_list:
        tags = it.get("tags", []) or []
        if "新闻联播" in tags:
            cctv_items.append(it)
        elif "政策类" in tags or "政治" in tags:
            policy_items.append(it)
        else:
            market_items.append(it)
    return cctv_items, policy_items, market_items


def fast_job():
    """高频执行：抓取新内容后立即推送“快讯”（不等待AI）。"""
    print("=== FAST JOB START ===")
    print(f"[{datetime.now()}] 开始抓取任务(快讯)...")
    news_list = run_all_crawlers()
    if not news_list:
        print("无新内容。")
        return

    cctv_items, policy_items, market_items = _classify(news_list)
    print(f"快讯分类：CCTV {len(cctv_items)} 条，政策 {len(policy_items)} 条，市场 {len(market_items)} 条")

    # CCTV：依旧即时推送全文/摘要
    for item in cctv_items:
        title = f"【新闻联播】{item.get('title')}"
        push_to_wechat({
            "title": title,
            "summary": item.get("content", ""),
            "url": item.get("url", ""),
            "tags": item.get("tags", []),
        })
        print(f"已推送 CCTV 内容: {title}")

    # 政策/市场：即时快讯只发标题+链接，避免被AI摘要阻塞
    now_ts = datetime.now().strftime("%m-%d %H:%M")
    pending = PendingStore()

    if policy_items:
        lines = []
        for idx, it in enumerate(policy_items[:15], 1):
            lines.append(f"{idx}. {it.get('title','')}\n   {it.get('url','')}")
        push_to_wechat({
            "title": f"【政策快讯】{now_ts}",
            "summary": "\n\n".join(lines),
            "url": "",
            "tags": ["政策类"],
        })
        # 避免队列无限膨胀：只入队一部分，后续靠高频轮询持续补充
        pending.add_many(policy_items[:30])

    if market_items:
        lines = []
        for idx, it in enumerate(market_items[:20], 1):
            lines.append(f"{idx}. {it.get('title','')}\n   {it.get('url','')}")
        push_to_wechat({
            "title": f"【市场快讯】{now_ts}",
            "summary": "\n\n".join(lines),
            "url": "",
            "tags": ["市场"],
        })
        pending.add_many(market_items[:40])


def analysis_job():
    """低频执行：从待分析队列取出内容，做AI摘要后再推送深度聚合。"""
    print("=== ANALYSIS JOB START ===")
    pending = PendingStore()
    # 每轮只处理有限数量，避免AI摘要拖慢；未处理的留到下一轮
    items = pending.pop_many(30)
    if not items:
        print("无待分析内容。")
        return

    cctv_items, policy_items, market_items = _classify(items)
    # CCTV 不做AI摘要，直接忽略（已在快讯里发过）
    policy_items = policy_items[:10]
    market_items = market_items[:15]
    items_to_summarize = policy_items + market_items

    print(f"待分析：政策 {len(policy_items)} 条，市场 {len(market_items)} 条，共 {len(items_to_summarize)} 条")
    if not items_to_summarize:
        return

    print(f"正在生成摘要，共 {len(items_to_summarize)} 条...")
    summarized_items = summarize_batch(items_to_summarize, max_workers=4)

    policy_sums = []
    market_sums = []
    for item in summarized_items:
        tags = item.get("tags", []) or []
        if "政策类" in tags or "政治" in tags:
            policy_sums.append(item)
        else:
            market_sums.append(item)

    now_ts = datetime.now().strftime("%m-%d %H:%M")
    if policy_sums:
        content_lines = []
        for idx, item in enumerate(policy_sums, 1):
            summary = (item.get("summary") or (item.get("content") or "")[:120]).replace("\n", " ")
            content_lines.append(f"{idx}. {item.get('title','')}\n   {summary}")
        push_to_wechat({
            "title": f"【时政与政策速递】{now_ts}",
            "summary": "\n\n".join(content_lines),
            "url": "",
        })
        print("已推送政策深度聚合。")

    if market_sums:
        content_lines = []
        for idx, item in enumerate(market_sums, 1):
            summary = (item.get("summary") or (item.get("content") or "")[:120]).replace("\n", " ")
            content_lines.append(f"{idx}. {item.get('title','')}\n   {summary}")
        push_to_wechat({
            "title": f"【市场与行业动态】{now_ts}",
            "summary": "\n\n".join(content_lines),
            "url": "",
        })
        print("已推送市场深度聚合。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI 新闻推送工具")
    parser.add_argument("--once", action="store_true", help="只执行一次后退出（CI/工作流模式）")
    parser.add_argument("--poll-seconds", type=int, default=180, help="快讯抓取轮询间隔（秒，越小越即时）")
    parser.add_argument("--analysis-mins", type=int, default=60, help="AI深度分析聚合间隔（分钟）")
    parser.add_argument("--interval-mins", type=int, default=None, help="兼容旧参数：循环间隔（分钟，已弃用）")
    args = parser.parse_args()

    # 兼容旧参数：若用户仍传了 --interval-mins，则映射到 poll-seconds
    if args.interval_mins is not None:
        args.poll_seconds = max(30, int(args.interval_mins) * 60)

    fast_job()  # 启动时立即执行一次快讯

    if args.once:
        # once 模式下额外跑一次分析，尽量把快讯补上深度解读
        analysis_job()
        sys.exit(0)

    # 循环模式：快讯高频轮询 + 分析低频聚合
    schedule.clear()
    schedule.every(args.poll_seconds).seconds.do(fast_job)
    schedule.every(args.analysis_mins).minutes.do(analysis_job)
    print(f"AI新闻推送工具已启动：快讯轮询 {args.poll_seconds}s，深度分析 {args.analysis_mins}min")
    while True:
        schedule.run_pending()
        time.sleep(5)

# summarizer/__init__.py
from .openai_summarizer import OpenAISummarizer

def summarize_news(news_item):
    # 预留：可切换不同AI摘要方式
    summarizer = OpenAISummarizer()
    return summarizer.summarize(news_item)

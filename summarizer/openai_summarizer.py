"""
News summarization via OpenRouter (OpenAI Python SDK v1 style).

This implementation avoids hardcoded secrets, reads configuration from
environment variables, and gracefully degrades to the original content when
the AI call fails. It is suitable for CI environments (e.g., GitHub Actions).
"""

import os
from typing import Dict, Any

from openai import OpenAI
from app_config import get_openai_config
import concurrent.futures


class OpenAISummarizer:
    """Summarize news items using an OpenRouter-compatible OpenAI client.

    Environment variables:
    - OPENROUTER_API_KEY: API key for OpenRouter
    - OPENAI_BASE_URL: Optional base URL override. Defaults to OpenRouter v1
    - OPENAI_MODEL: Optional model id. Defaults to 'openai/gpt-4o-mini'
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_tokens: int = 500,
    ) -> None:
        cfg = get_openai_config()
        resolved_api_key = (api_key or os.getenv("OPENROUTER_API_KEY", "") or cfg.get("api_key", "")).strip()
        resolved_base_url = (base_url or os.getenv("OPENAI_BASE_URL", "") or cfg.get("base_url", "https://openrouter.ai/api/v1")).strip()
        resolved_model = (model or os.getenv("OPENAI_MODEL", "") or cfg.get("model", "openai/gpt-4o-mini")).strip()

        self.model: str = resolved_model
        self.max_tokens: int = max_tokens
        self.client = OpenAI(api_key=resolved_api_key or None, base_url=resolved_base_url)

    def _build_prompt(self, news_item: Dict[str, Any]) -> str:
        content = news_item.get("content", "")
        title = news_item.get("title", "")
        tags = news_item.get("tags") or []
        tag_line = f"关注标签：{', '.join(tags)}\n" if tags else ""
        return (
            "你是资深卖方行业分析师。请以清晰、简洁、准确的语言总结以下内容，并重点评估其对目标板块/基金的影响：\n"
            f"标题：{title}\n"
            f"正文：{content}\n\n"
            f"{tag_line}"
            "总结要求：\n"
            "1) 新闻/政策/会议的关键结论；若为AI行业新闻，请说明：主体公司、模型名称/代号、来源/演进脉络、能力特长（推理/多模态/代码/工具调用等）、开放/商用情况；\n"
            "2) 对稀土、白酒、半导体/芯片、创新药、雅江水电工程/水电、光伏等板块的影响路径（需求/供给/成本/价格/估值/政策风险）；\n"
            "3) 对基金市场的影响：可能的申赎/持仓/资金流向变动；\n"
            "4) 交易建议（短/中/长期），风险点与触发条件。\n"
            "请分条列出，内容务必专业、实用。"
        )

    def summarize(self, news_item: Dict[str, Any]) -> Dict[str, str]:
        prompt = self._build_prompt(news_item)
        summary_text: str
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )
            if hasattr(response, "choices") and response.choices:
                summary_text = (response.choices[0].message.content or "").strip()
            else:
                summary_text = ""
        except Exception as exc:  # noqa: BLE001 - broad by design to gracefully degrade
            summary_text = f"摘要失败: {exc}"

        if not summary_text or summary_text.startswith("摘要失败"):
            tags = news_item.get("tags")
            tag_hint = f" [标签: {', '.join(tags)}]" if tags else ""
            fallback = news_item.get("content", "") or news_item.get("title", "")
            summary_text = fallback[:500]
            summary_text = summary_text + tag_hint

        return {
            "title": news_item.get("title", ""),
            "summary": summary_text,
            "url": news_item.get("url", ""),
        }


def summarize_batch(items: list[Dict[str, Any]], max_workers: int = 4) -> list[Dict[str, str]]:
    """Summarize a batch of news items in parallel.

    Returns a list of summarized dicts preserving order as best effort.
    """
    summarizer = OpenAISummarizer()
    results: list[Dict[str, str]] = [None] * len(items)  # type: ignore

    def _wrap(idx: int, it: Dict[str, Any]):
        try:
            results[idx] = summarizer.summarize(it)
        except Exception as exc:  # noqa: BLE001
            results[idx] = {
                "title": it.get("title", ""),
                "summary": f"摘要失败: {exc}",
                "url": it.get("url", ""),
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(_wrap, i, it) for i, it in enumerate(items)]
        concurrent.futures.wait(futures)
    return results  # type: ignore

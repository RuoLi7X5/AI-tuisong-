"""Domain config for sector-focused monitoring.

We focus on the following sectors and related keywords/policies:
- 稀土板块
- 白酒板块
- 半导体板块
- 创新药板块
- 雅江水电工程板块
- 光伏板块

Additionally, we fetch gold price (黄金价格，非零售加工价) from reliable public sources.
"""

from __future__ import annotations

from typing import List


TARGET_SECTORS: List[str] = [
    "稀土",  # 稀土板块
    "白酒",
    "半导体",
    "芯片",
    "集成电路",
    "创新药",
    "医药创新",
    "雅江水电",
    "雅砻江",
    "抽水蓄能",
    "光伏",
    "光伏组件",
    "硅料",
    "水电",
]

POLICY_KEYWORDS: List[str] = [
    "政策",
    "监管",
    "批复",
    "通知",
    "征求意见",
    "文件",
    "规范",
    "指导意见",
    # 重大会议/外交/经贸
    "会议",
    "峰会",
    "会晤",
    "谈判",
    "磋商",
    "公报",
    "声明",
    "协定",
    "合意",
    "合作框架",
    "禁令",
    "禁运",
    "制裁",
    "关税",
    "出口管制",
]

GOLD_KEYWORDS: List[str] = [
    "黄金",
    "金价",
    "伦敦金",
    "COMEX黄金",
    "上海黄金交易所",
]

# AI 行业关键词（用于识别最新大模型/发布/评测/生态动态）
AI_KEYWORDS: List[str] = [
    "AI",
    "大模型",
    "模型",
    "LLM",
    "SOTA",
    "对齐",
    "推理",
    "多模态",
    "R1",
    "Llama",
    "Gemini",
    "Claude",
    "GPT",
    "o3",
    "Mistral",
    "xAI",
    "Grok",
    "Hugging Face",
    "OpenAI",
    "Anthropic",
    "Meta AI",
    "Google AI",
    "Microsoft",
    "DeepSeek",
    "Qwen",
    "通义千问",
    "Yi",
    "Baichuan",
    "智谱",
    "GLM",
]


def match_keywords(text: str) -> List[str]:
    """Return matched tags among sectors/policies/gold keywords.

    This simple matcher is case-sensitive for Chinese and works well enough
    for our purpose. You can replace with more robust NLP if needed.
    """
    tags: List[str] = []
    policy_hit = False
    for kw in TARGET_SECTORS:
        if kw in text:
            tags.append(kw)
    for kw in POLICY_KEYWORDS:
        if kw in text:
            tags.append(kw)
            policy_hit = True
    for kw in GOLD_KEYWORDS:
        if kw in text:
            tags.append(kw)
    ai_hit = False
    for kw in AI_KEYWORDS:
        if kw in text:
            tags.append(kw)
            ai_hit = True
    if ai_hit:
        tags.append("AI行业")
    if policy_hit:
        tags.append("政策类")
    # de-duplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped



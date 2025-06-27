# summarizer/openai_summarizer.py
# 用OpenAI API进行新闻摘要
import openai

class OpenAISummarizer:
    def __init__(self, api_key=None):
        # 优先使用用户提供的openrouter API Key
        self.api_key = api_key or "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"
        openai.api_key = self.api_key
        openai.base_url = "https://openrouter.ai/api/v1"  # openrouter专用

    def summarize(self, news_item):
        # news_item: dict, 包含title/content/url
        prompt = (
            f"请以清晰、简洁、准确的语言总结以下新闻内容：\n"
            f"{news_item['content']}\n"
            "\n总结要求：\n"
            "1. 先用简明扼要的语言总结新闻要点。\n"
            "2. 在总结下方，分析新闻涉及的市场经济形势，指出对哪些行业有何影响，利好哪些产业，对基金和股票市场的影响，存在哪些机会。\n"
            "3. 最后提出具有指导性的投资或关注建议。\n"
            "请分条列出，内容务必专业、实用。"
        )
        # 这里只做结构预留，实际调用需补充API Key和异常处理
        try:
            response = openai.chat.completions.create(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            print("[AI调试] openai返回：", response)
            # 检查返回内容是否为HTML（如网页、报错页等）
            if isinstance(response, str) and response.strip().startswith('<!DOCTYPE html>'):
                summary = "AI摘要失败：API返回异常网页"
            elif hasattr(response, 'choices') and response.choices:
                summary = response.choices[0].message.content.strip()
            elif isinstance(response, dict) and 'choices' in response:
                summary = response['choices'][0]['message']['content'].strip()
            else:
                summary = f"AI返回异常: {response}"
        except Exception as e:
            summary = f"摘要失败: {e}"
        # 如果AI摘要失败，降级为推送原始新闻内容
        if not summary or summary.startswith("AI摘要失败"):
            summary = news_item.get('content', '')[:500] or news_item.get('title', '')
        return {"title": news_item['title'], "summary": summary, "url": news_item['url']}

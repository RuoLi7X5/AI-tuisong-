

# AI 财政新闻推送工具

## 项目结构

- news_crawler/ 新闻爬虫模块，预留多网站爬虫位置
- summarizer/ AI 摘要模块，支持多种大模型 API
- wechat_pusher/ 微信推送模块，支持 wxpusher 等
- main.py 主入口，定时任务调度
- requirements.txt 依赖

## 使用说明

1. 配置 `requirements.txt` 并安装依赖。
2. 在 `news_crawler/` 目录下添加各新闻网站爬虫。
3. 配置 `summarizer/` 选择 AI 摘要方式。
4. 配置 `wechat_pusher/` 填写推送 API 信息。
5. 运行 `main.py` 启动服务。

## 依赖建议

- requests
- beautifulsoup4
- openai 或 dashscope 或 qianwen
- wxpusher
- schedule 或 APScheduler

详细用法见各模块注释。


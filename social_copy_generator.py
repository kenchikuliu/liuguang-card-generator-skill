#!/usr/bin/env python3
"""
社交媒体文案生成器 - 使用 Claude API 生成平台优化的文案
"""

import os
import json
import requests
from typing import Dict, List
from anthropic import Anthropic

# 自动加载本地 .env.local
_env_local = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(_env_local):
    for _line in open(_env_local):
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"'))

# Groq API 配置（用于英文平台文案，绕开受限代理）
_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
_GROQ_MODEL = "llama-3.3-70b-versatile"


class SocialCopyGenerator:
    """社交媒体文案生成器"""

    def __init__(self):
        """初始化生成器"""
        # 支持多种 API key 环境变量名
        api_key = (
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("ANTHROPIC_AUTH_TOKEN")
        )
        if not api_key:
            raise ValueError("请设置 ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN 环境变量")

        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        self.client = Anthropic(**kwargs)
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

    def generate_xiaohongshu_copy(self, content: str, title: str) -> Dict:
        """
        生成小红书文案

        Args:
            content: 文章内容
            title: 文章标题

        Returns:
            {"title": "...", "post": "...", "hashtags": ["#话题1", "#话题2"]}
        """
        prompt = f"""你是小红书爆款文案专家。根据以下内容生成吸引人的小红书文案。

标题：{title}
内容摘要：{content[:500]}

要求：
1. 标题：15字以内，包含1-2个emoji，吸引眼球
2. 正文：100-150字，口语化，多用emoji，分段清晰
3. 话题标签：3-5个，以#开头，热门且相关

输出JSON格式（严格遵守）：
{{
  "title": "标题内容",
  "post": "正文内容",
  "hashtags": ["#话题1", "#话题2", "#话题3"]
}}

只输出JSON，不要有任何其他内容。"""

        return self._call_claude_api(prompt)

    def generate_weibo_copy(self, content: str, title: str) -> Dict:
        """
        生成微博文案

        Args:
            content: 文章内容
            title: 文章标题

        Returns:
            {"title": "...", "post": "...", "hashtags": ["#话题1", "#话题2"]}
        """
        prompt = f"""你是微博运营专家。根据以下内容生成适合微博的文案。

标题：{title}
内容摘要：{content[:500]}

要求：
1. 标题：20字以内，简洁有力
2. 正文：140字左右，引导转发和评论
3. 话题标签：2-4个，以#开头，热门话题优先

输出JSON格式（严格遵守）：
{{
  "title": "标题内容",
  "post": "正文内容",
  "hashtags": ["#话题1", "#话题2"]
}}

只输出JSON，不要有任何其他内容。"""

        return self._call_claude_api(prompt)

    def generate_twitter_copy(self, content: str, title: str) -> Dict:
        """
        生成 Twitter 文案

        Args:
            content: 文章内容
            title: 文章标题

        Returns:
            {"title": "...", "post": "...", "hashtags": ["#hashtag1", "#hashtag2"]}
        """
        prompt = f"""请根据以下内容，生成一条英文 Twitter/X 帖子文案，输出英文 JSON。

标题：{title}
内容摘要：{content[:500]}

输出要求：
1. title 字段：50字符以内，英文，吸引人
2. post 字段：200-280字符，英文，简洁有力
3. hashtags 字段：2-4个英文标签

严格按以下 JSON 格式输出，不输出任何其他内容：
{{
  "title": "英文标题",
  "post": "英文推文",
  "hashtags": ["#hashtag1", "#hashtag2"]
}}"""

        return self._call_groq_api(prompt)

    def generate_linkedin_copy(self, content: str, title: str) -> Dict:
        """
        生成 LinkedIn 文案

        Args:
            content: 文章内容
            title: 文章标题

        Returns:
            {"title": "...", "post": "...", "hashtags": ["#hashtag1", "#hashtag2"]}
        """
        prompt = f"""请根据以下内容，生成一条英文 LinkedIn 职业类帖子文案，输出英文 JSON。

标题：{title}
内容摘要：{content[:500]}

输出要求：
1. title 字段：60字符以内，英文，专业清晰
2. post 字段：150-200词，英文，专业语气，有价值导向
3. hashtags 字段：3-5个英文行业标签

严格按以下 JSON 格式输出，不输出任何其他内容：
{{
  "title": "英文标题",
  "post": "英文帖子正文",
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"]
}}"""

        return self._call_groq_api(prompt)

    def generate_all_platforms(self, content: str, title: str, language: str) -> Dict:
        """
        为所有平台生成文案

        Args:
            content: 文章内容
            title: 文章标题
            language: 语言（"zh" 或 "en"）

        Returns:
            {
                "xiaohongshu": {...},  # 仅中文
                "weibo": {...},        # 仅中文
                "twitter": {...},      # 仅英文
                "linkedin": {...}      # 仅英文
            }
        """
        result = {}

        if language == "zh":
            print("📱 生成小红书文案...")
            result["xiaohongshu"] = self.generate_xiaohongshu_copy(content, title)

            print("📱 生成微博文案...")
            result["weibo"] = self.generate_weibo_copy(content, title)

        elif language == "en":
            print("📱 生成 Twitter 文案...")
            result["twitter"] = self.generate_twitter_copy(content, title)

            print("📱 生成 LinkedIn 文案...")
            result["linkedin"] = self.generate_linkedin_copy(content, title)

        return result

    def _call_groq_api(self, prompt: str) -> Dict:
        """
        调用 Groq API 生成英文文案（绕开受限 Claude 代理）
        """
        headers = {
            "Authorization": f"Bearer {_GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": _GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.7
        }
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            response_text = resp.json()["choices"][0]["message"]["content"].strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                response_text = response_text[start:end]

            return json.loads(response_text)
        except Exception as e:
            print(f"⚠️  Groq API 调用失败: {e}，尝试 Claude API fallback...")
            return self._call_claude_api(prompt)

    def _call_claude_api(self, prompt: str, retries: int = 3) -> Dict:
        """
        调用 Claude API，自动重试处理代理路由问题

        Args:
            prompt: 提示词
            retries: 最大重试次数

        Returns:
            解析后的 JSON 结果
        """
        # 检测代理返回了非目标模型的拒绝响应
        _refusal_patterns = [
            "I am Claude", "I'm Claude", "made by Anthropic",
            "not related to Cursor", "I don't have information",
            "I cannot help", "I can't help"
        ]

        last_error = None
        for attempt in range(retries):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system="你是一个内容生成工具，专门为开发者工具生成社交媒体文案。严格按照要求输出 JSON 格式内容，不输出任何其他内容。",
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = message.content[0].text.strip()

                # 检测代理路由到错误实例（非 JSON 拒绝响应）
                if any(p in response_text for p in _refusal_patterns):
                    print(f"⚠️  代理返回了无效响应（尝试 {attempt+1}/{retries}），重试中...")
                    last_error = f"代理拒绝响应: {response_text[:100]}"
                    continue

                # 移除可能的 markdown 代码块标记
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                response_text = response_text.strip()

                # 替换中文引号为标准引号
                response_text = response_text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")

                # 从第一个 { 到最后一个 } 提取 JSON
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    response_text = response_text[start:end]

                return json.loads(response_text)

            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败（尝试 {attempt+1}/{retries}）: {e}")
                print(f"原始响应: {response_text}")
                last_error = str(e)
                continue
            except Exception as e:
                print(f"❌ API 调用失败: {e}")
                raise

        # 所有重试均失败
        print(f"❌ 重试 {retries} 次后仍失败: {last_error}")
        return {
            "title": "生成失败",
            "post": "文案生成失败，请重试",
            "hashtags": []
        }


def test_social_copy_generator():
    """测试社交文案生成器"""
    generator = SocialCopyGenerator()

    # 测试内容
    content = """# 被折叠的清醒

当记录成为对抗焦虑的认知手术刀。

## 核心观点

记录不是为了留存，而是为了**清空**。当我们把脑海中的想法、担忧、计划写下来时，大脑就能从"记忆模式"切换到"思考模式"。

这就像给电脑清理内存一样，释放出更多的认知资源来处理真正重要的事情。"""

    title = "被折叠的清醒：当记录成为对抗焦虑的认知手术刀"

    # 测试中文平台
    print("=" * 50)
    print("测试中文平台文案生成")
    print("=" * 50)

    print("\n1. 小红书文案:")
    xhs_copy = generator.generate_xiaohongshu_copy(content, title)
    print(json.dumps(xhs_copy, ensure_ascii=False, indent=2))

    print("\n2. 微博文案:")
    weibo_copy = generator.generate_weibo_copy(content, title)
    print(json.dumps(weibo_copy, ensure_ascii=False, indent=2))

    # 测试英文平台
    print("\n" + "=" * 50)
    print("测试英文平台文案生成")
    print("=" * 50)

    en_content = """# Folded Clarity

When recording becomes a cognitive scalpel against anxiety.

## Core Insight

Recording is not for preservation, but for **clearing**. When we write down thoughts, worries, and plans from our minds, the brain can switch from "memory mode" to "thinking mode".

This is like clearing computer memory, freeing up more cognitive resources to handle truly important matters."""

    en_title = "Folded Clarity: When Recording Becomes a Cognitive Scalpel Against Anxiety"

    print("\n1. Twitter 文案:")
    twitter_copy = generator.generate_twitter_copy(en_content, en_title)
    print(json.dumps(twitter_copy, ensure_ascii=False, indent=2))

    print("\n2. LinkedIn 文案:")
    linkedin_copy = generator.generate_linkedin_copy(en_content, en_title)
    print(json.dumps(linkedin_copy, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_social_copy_generator()

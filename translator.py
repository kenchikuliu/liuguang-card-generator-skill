#!/usr/bin/env python3
"""
翻译模块 - 使用 Claude API 进行翻译
"""

import os
import json
from typing import Optional
from anthropic import Anthropic


class Translator:
    """翻译器 - 使用 Claude API"""

    def __init__(self):
        """初始化翻译器"""
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

        self.client = Anthropic(timeout=60.0, **kwargs)
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    def detect_language(self, content: str) -> str:
        """
        检测内容语言

        Args:
            content: 要检测的内容

        Returns:
            "zh" 或 "en"
        """
        # 统计中文字符（CJK 统一表意文字）
        cjk_count = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        total_chars = len(content.strip())

        if total_chars == 0:
            return "zh"  # 默认中文

        ratio = cjk_count / total_chars

        # 如果中文字符超过 30%，判定为中文
        if ratio > 0.3:
            return "zh"
        # 如果中文字符少于 10%，判定为英文
        elif ratio < 0.1:
            return "en"
        else:
            # 混合内容，使用 LLM 判断主要语言
            return self._detect_with_llm(content)

    def _detect_with_llm(self, content: str) -> str:
        """
        使用 LLM 检测混合内容的主要语言

        Args:
            content: 要检测的内容

        Returns:
            "zh" 或 "en"
        """
        prompt = f"""请判断以下内容的主要语言是中文还是英文。
只需回答 "zh" 或 "en"，不要有其他内容。

内容：
{content[:500]}
"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )

            result = message.content[0].text.strip().lower()
            return "zh" if "zh" in result else "en"
        except Exception as e:
            print(f"⚠️  LLM 语言检测失败: {e}")
            return "zh"  # 默认中文

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        翻译文本

        Args:
            text: 要翻译的文本
            source_lang: 源语言（"zh" 或 "en"）
            target_lang: 目标语言（"zh" 或 "en"）

        Returns:
            翻译后的文本
        """
        if source_lang == target_lang:
            return text

        # 构建翻译 prompt
        prompt = self._build_translation_prompt(text, source_lang, target_lang)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()
        except Exception as e:
            print(f"❌ 翻译失败: {e}")
            raise

    def _build_translation_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        构建翻译 prompt

        Args:
            text: 要翻译的文本
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            翻译 prompt
        """
        lang_names = {
            "zh": "中文",
            "en": "英文"
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        prompt = f"""请将以下{source_name}内容翻译成{target_name}。

要求：
1. 保持原文的段落结构和换行
2. 保持 Markdown 格式（如 **粗体**、*斜体*、# 标题等）
3. 保持语义完整性和准确性
4. 翻译要自然流畅，符合目标语言的表达习惯
5. 只输出翻译结果，不要有任何解释或额外内容

原文：
{text}

翻译："""

        return prompt

    def translate_title(self, title: str, source_lang: str, target_lang: str) -> str:
        """
        翻译标题（针对标题优化）

        Args:
            title: 要翻译的标题
            source_lang: 源语言
            target_lang: 目标语言

        Returns:
            翻译后的标题
        """
        if source_lang == target_lang:
            return title

        lang_names = {
            "zh": "中文",
            "en": "英文"
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        prompt = f"""请将以下{source_name}标题翻译成{target_name}。

要求：
1. 保持标题的简洁性和吸引力
2. 符合目标语言的标题习惯
3. 只输出翻译结果，不要有任何解释

标题：
{title}

翻译："""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()
        except Exception as e:
            print(f"❌ 标题翻译失败: {e}")
            raise


def test_translator():
    """测试翻译器"""
    translator = Translator()

    # 测试语言检测
    print("测试语言检测...")
    zh_text = "这是一段中文文本，用于测试语言检测功能。"
    en_text = "This is an English text for testing language detection."

    print(f"中文检测: {translator.detect_language(zh_text)}")  # 应该是 zh
    print(f"英文检测: {translator.detect_language(en_text)}")  # 应该是 en

    # 测试翻译
    print("\n测试翻译...")
    zh_content = """# 被折叠的清醒

当记录成为对抗焦虑的认知手术刀。

## 核心观点

记录不是为了留存，而是为了**清空**。"""

    print("原文（中文）:")
    print(zh_content)

    print("\n翻译为英文:")
    en_content = translator.translate_text(zh_content, "zh", "en")
    print(en_content)

    print("\n翻译回中文:")
    zh_back = translator.translate_text(en_content, "en", "zh")
    print(zh_back)


if __name__ == "__main__":
    test_translator()

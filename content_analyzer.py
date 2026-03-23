#!/usr/bin/env python3
"""
内容分析器 - 智能分析文章结构，优化卡片分割
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ContentSection:
    """内容段落"""
    text: str
    type: str  # 'title', 'subtitle', 'paragraph', 'quote', 'list'
    importance: int  # 1-5，重要性评分
    char_count: int


class ContentAnalyzer:
    """内容分析器"""

    def __init__(self):
        self.max_chars_per_card = 250  # 每张卡片最大字数
        self.min_chars_per_card = 150  # 每张卡片最小字数

    def analyze(self, content: str) -> Dict:
        """分析内容结构"""
        sections = self._parse_sections(content)

        return {
            'total_chars': sum(s.char_count for s in sections),
            'sections': sections,
            'recommended_cards': self._calculate_card_count(sections),
            'structure': self._analyze_structure(sections)
        }

    def _parse_sections(self, content: str) -> List[ContentSection]:
        """解析内容段落"""
        sections = []

        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        for para in paragraphs:
            section_type = self._detect_type(para)
            importance = self._calculate_importance(para, section_type)

            sections.append(ContentSection(
                text=para,
                type=section_type,
                importance=importance,
                char_count=len(para)
            ))

        return sections

    def _detect_type(self, text: str) -> str:
        """检测段落类型"""
        # 标题：短句，以冒号或问号结尾
        if len(text) <= 20 and ('？' in text or '：' in text):
            return 'subtitle'

        # 引用：包含引号
        if '"' in text or '"' in text or '「' in text:
            return 'quote'

        # 列表：以数字或符号开头
        if re.match(r'^[\d\-\*•]', text):
            return 'list'

        return 'paragraph'

    def _calculate_importance(self, text: str, section_type: str) -> int:
        """计算段落重要性（1-5）"""
        score = 3  # 默认中等重要

        # 类型加分
        if section_type == 'subtitle':
            score += 1
        elif section_type == 'quote':
            score += 1

        # 关键词加分
        keywords = ['核心', '关键', '重要', '必须', '最', '倍', '%']
        if any(kw in text for kw in keywords):
            score += 1

        # 问号加分
        if '？' in text:
            score += 1

        return min(5, score)

    def _calculate_card_count(self, sections: List[ContentSection]) -> int:
        """计算推荐的卡片数量"""
        total_chars = sum(s.char_count for s in sections)

        # 基于总字数计算
        cards = (total_chars + self.max_chars_per_card - 1) // self.max_chars_per_card

        # 限制在 1-5 张
        return max(1, min(5, cards))

    def _analyze_structure(self, sections: List[ContentSection]) -> Dict:
        """分析内容结构"""
        return {
            'has_subtitles': any(s.type == 'subtitle' for s in sections),
            'has_quotes': any(s.type == 'quote' for s in sections),
            'has_lists': any(s.type == 'list' for s in sections),
            'high_importance_count': sum(1 for s in sections if s.importance >= 4)
        }

    def smart_split(self, sections: List[ContentSection], num_cards: int) -> List[List[ContentSection]]:
        """智能分割内容到多张卡片"""
        if num_cards <= 0:
            return []

        # 初始化卡片
        cards = [[] for _ in range(num_cards)]
        card_chars = [0] * num_cards

        # 目标字数
        target_chars = sum(s.char_count for s in sections) // num_cards

        current_card = 0
        for section in sections:
            # 如果当前卡片已满，且不是最后一张
            if (card_chars[current_card] >= target_chars * 0.9 and
                current_card < num_cards - 1):
                current_card += 1

            # 添加到当前卡片
            cards[current_card].append(section)
            card_chars[current_card] += section.char_count

        return cards

    def format_card_content(self, sections: List[ContentSection]) -> str:
        """格式化卡片内容"""
        parts = []

        for section in sections:
            if section.type == 'subtitle':
                # 小标题：居中加粗
                parts.append(f'<p class="text-align-center"><strong>{section.text}</strong></p>')
            elif section.type == 'quote':
                # 引用：斜体
                parts.append(f'<p><em>{section.text}</em></p>')
            elif section.importance >= 4:
                # 高重要性：加粗
                parts.append(f'<p><strong>{section.text}</strong></p>')
            else:
                # 普通段落
                parts.append(f'<p>{section.text}</p>')

        return ''.join(parts)


def main():
    """测试"""
    content = """
OpenClaw 是什么？

OpenClaw 是一个开源的 AI Agent 平台。

核心特性：
- 支持多种 AI 模型
- 可扩展的插件系统
- 强大的工作流引擎

"让 AI 更好地服务人类" —— 这是我们的愿景。

通过 OpenClaw，你可以轻松构建自己的 AI 助手。
    """

    analyzer = ContentAnalyzer()
    result = analyzer.analyze(content)

    print(f"总字数: {result['total_chars']}")
    print(f"推荐卡片数: {result['recommended_cards']}")
    print(f"结构分析: {result['structure']}")
    print()

    # 智能分割
    cards = analyzer.smart_split(result['sections'], result['recommended_cards'])

    for i, card_sections in enumerate(cards, 1):
        print(f"卡片 {i}:")
        for section in card_sections:
            print(f"  [{section.type}] {section.text[:30]}...")
        print()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
图片处理模块 - 处理内容中的图片，计算图片占用的等效字节
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
import requests
from PIL import Image
from io import BytesIO


@dataclass
class ImageInfo:
    """图片信息"""
    alt: str
    url: str
    position: int  # 在原文中的位置
    size_category: str  # 'small', 'medium', 'large'
    byte_cost: int  # 占用的等效字节
    width: int = 0
    height: int = 0


class ImageHandler:
    """图片处理器"""

    def __init__(self):
        # 图片占用的等效字节（根据图片在卡片中的显示大小）
        # 卡片尺寸：440x586
        # 假设图片显示宽度为卡片宽度的80%（352px）
        self.image_byte_cost = {
            'small': 60,    # 小图（高度约100px）：约占2-3行文字空间
            'medium': 100,  # 中图（高度约150px）：约占4-5行文字空间
            'large': 150,   # 大图（高度约200px）：约占6-7行文字空间
            'full': 200,    # 全尺寸（高度约250px）：约占8-10行文字空间
        }

        # 每行文字约占20字节（按照卡片排版）
        self.bytes_per_line = 20

    def extract_images_from_markdown(self, content: str) -> List[ImageInfo]:
        """从Markdown内容中提取图片"""
        images = []

        # 匹配 Markdown 图片语法：![alt](url)
        pattern = r'!\[(.*?)\]\((.*?)\)'

        for match in re.finditer(pattern, content):
            alt = match.group(1)
            url = match.group(2)
            position = match.start()

            # 估算图片大小
            size_category = self._estimate_size_from_url(url)
            byte_cost = self.image_byte_cost[size_category]

            images.append(ImageInfo(
                alt=alt,
                url=url,
                position=position,
                size_category=size_category,
                byte_cost=byte_cost
            ))

        return images

    def extract_images_from_html(self, content: str) -> List[ImageInfo]:
        """从HTML内容中提取图片"""
        images = []

        # 匹配 HTML img 标签
        pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'

        for match in re.finditer(pattern, content):
            url = match.group(1)
            position = match.start()

            # 尝试提取 alt 属性
            alt_match = re.search(r'alt=["\']([^"\']+)["\']', match.group(0))
            alt = alt_match.group(1) if alt_match else ""

            size_category = self._estimate_size_from_url(url)
            byte_cost = self.image_byte_cost[size_category]

            images.append(ImageInfo(
                alt=alt,
                url=url,
                position=position,
                size_category=size_category,
                byte_cost=byte_cost
            ))

        return images

    def _estimate_size_from_url(self, url: str) -> str:
        """根据URL估算图片大小"""
        url_lower = url.lower()

        # 根据URL中的关键词判断
        if any(kw in url_lower for kw in ['thumb', 'thumbnail', 'small', 'icon']):
            return 'small'
        elif any(kw in url_lower for kw in ['large', 'full', 'original', 'hd']):
            return 'large'
        elif any(kw in url_lower for kw in ['banner', 'hero', 'cover']):
            return 'full'
        else:
            return 'medium'

    def get_actual_image_size(self, url: str, timeout: int = 5) -> Tuple[int, int]:
        """获取图片的实际尺寸"""
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()

            # 只读取图片头部信息
            img = Image.open(BytesIO(response.content))
            return img.size  # (width, height)

        except Exception as e:
            print(f"⚠️  无法获取图片尺寸: {url} - {e}")
            return (0, 0)

    def calculate_byte_cost_from_size(self, width: int, height: int) -> int:
        """根据图片实际尺寸计算占用的等效字节"""
        if width == 0 or height == 0:
            return self.image_byte_cost['medium']

        # 卡片宽度：440px
        # 图片显示宽度：352px (80%)
        display_width = 352

        # 计算显示高度（保持宽高比）
        display_height = int(height * display_width / width)

        # 根据显示高度计算占用的行数
        # 假设每行高度约25px
        lines_occupied = display_height / 25

        # 转换为等效字节
        byte_cost = int(lines_occupied * self.bytes_per_line)

        # 限制在合理范围内
        return max(50, min(250, byte_cost))

    def enrich_images_with_actual_size(self, images: List[ImageInfo]) -> List[ImageInfo]:
        """获取图片的实际尺寸并更新 byte_cost"""
        enriched_images = []

        for img in images:
            width, height = self.get_actual_image_size(img.url)

            if width > 0 and height > 0:
                # 根据实际尺寸重新计算 byte_cost
                byte_cost = self.calculate_byte_cost_from_size(width, height)

                enriched_images.append(ImageInfo(
                    alt=img.alt,
                    url=img.url,
                    position=img.position,
                    size_category=img.size_category,
                    byte_cost=byte_cost,
                    width=width,
                    height=height
                ))
            else:
                # 无法获取尺寸，使用原始估算
                enriched_images.append(img)

        return enriched_images

    def remove_images_from_content(self, content: str) -> str:
        """从内容中移除图片标记（Markdown和HTML）"""
        # 移除 Markdown 图片
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

        # 移除 HTML img 标签
        content = re.sub(r'<img[^>]+>', '', content)

        # 清理多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content.strip()

    def split_content_with_images(self, content: str, num_cards: int = 5,
                                  base_capacity: int = 250, language: str = "zh") -> List[Dict]:
        """
        智能分割内容，考虑图片占用的空间
        目标：创建正好 num_cards 张卡片，每张约 base_capacity 字节

        Args:
            content: 要分割的内容
            num_cards: 卡片数量
            base_capacity: 每张卡片的基础容量（字节）
            language: 语言（"zh" 或 "en"）

        返回格式：
        [
            {
                'text': '文字内容',
                'images': [ImageInfo, ...],
                'capacity_used': 实际使用的字节数
            },
            ...
        ]
        """
        # 1. 提取图片
        images = self.extract_images_from_markdown(content)

        if not images:
            # 没有图片，直接按文字分割
            return self._split_text_only(content, num_cards, base_capacity)

        # 2. 移除图片标记，得到纯文字内容
        text_content = self.remove_images_from_content(content)

        # 3. 按段落分割
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]

        # 4. 计算总内容大小
        total_text_bytes = sum(len(p) for p in paragraphs)
        total_image_bytes = sum(img.byte_cost for img in images)
        total_bytes = total_text_bytes + total_image_bytes

        # 5. 计算每张卡片的目标大小
        target_per_card = total_bytes / num_cards

        # 6. 按位置排序图片
        images_sorted = sorted(images, key=lambda x: x.position)

        # 7. 创建内容项列表（段落和图片混合，按原始位置排序）
        content_items = []

        # 为每个段落记录其在原文中的大致位置
        text_position = 0
        for para in paragraphs:
            # 在原文中查找段落位置
            pos = content.find(para, text_position)
            if pos == -1:
                pos = text_position
            content_items.append({
                'type': 'text',
                'content': para,
                'bytes': len(para),
                'position': pos
            })
            text_position = pos + len(para)

        # 添加图片
        for img in images_sorted:
            content_items.append({
                'type': 'image',
                'content': img,
                'bytes': img.byte_cost,
                'position': img.position
            })

        # 按位置排序所有内容项
        content_items.sort(key=lambda x: x['position'])

        # 8. 分配内容到卡片
        cards = []
        current_card = {
            'text': [],
            'images': [],
            'capacity_used': 0
        }

        for item in content_items:
            # 检查是否需要开始新卡片
            # 条件：当前卡片已经接近目标大小，且还没达到最后一张卡片
            if (current_card['capacity_used'] >= target_per_card and
                len(cards) < num_cards - 1 and
                (current_card['text'] or current_card['images'])):
                cards.append(current_card)
                current_card = {
                    'text': [],
                    'images': [],
                    'capacity_used': 0
                }

            # 添加内容项到当前卡片
            if item['type'] == 'text':
                current_card['text'].append(item['content'])
                current_card['capacity_used'] += item['bytes']
            else:  # image
                current_card['images'].append(item['content'])
                current_card['capacity_used'] += item['bytes']

        # 添加最后一张卡片
        if current_card['text'] or current_card['images']:
            cards.append(current_card)

        # 9. 如果卡片数量不足，尝试拆分最大的卡片
        while len(cards) < num_cards:
            # 找到最大的卡片
            max_idx = 0
            max_size = 0
            for i, card in enumerate(cards):
                if card['capacity_used'] > max_size and len(card['text']) > 1:
                    max_size = card['capacity_used']
                    max_idx = i

            if max_size == 0:
                # 无法再拆分
                break

            # 拆分这张卡片
            card_to_split = cards[max_idx]
            mid = len(card_to_split['text']) // 2

            new_card1 = {
                'text': card_to_split['text'][:mid],
                'images': card_to_split['images'],  # 图片放在第一张
                'capacity_used': sum(len(t) for t in card_to_split['text'][:mid]) + sum(img.byte_cost for img in card_to_split['images'])
            }

            new_card2 = {
                'text': card_to_split['text'][mid:],
                'images': [],
                'capacity_used': sum(len(t) for t in card_to_split['text'][mid:])
            }

            cards[max_idx] = new_card1
            cards.insert(max_idx + 1, new_card2)

        # 10. 如果卡片数量过多，合并最小的卡片
        while len(cards) > num_cards:
            # 找到最小的相邻卡片对
            min_total = float('inf')
            min_idx = 0
            for i in range(len(cards) - 1):
                total = cards[i]['capacity_used'] + cards[i + 1]['capacity_used']
                if total < min_total:
                    min_total = total
                    min_idx = i

            # 合并这两张卡片
            cards[min_idx]['text'].extend(cards[min_idx + 1]['text'])
            cards[min_idx]['images'].extend(cards[min_idx + 1]['images'])
            cards[min_idx]['capacity_used'] += cards[min_idx + 1]['capacity_used']
            cards.pop(min_idx + 1)

        # 11. 格式化输出
        formatted_cards = []
        for card in cards:
            formatted_cards.append({
                'text': '\n\n'.join(card['text']),
                'images': card['images'],
                'capacity_used': card['capacity_used']
            })

        return formatted_cards

    def _split_text_only(self, content: str, num_cards: int, base_capacity: int) -> List[Dict]:
        """纯文字分割（无图片）- 创建正好 num_cards 张卡片，每张约 base_capacity 字节"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if not paragraphs:
            return []

        # 计算总字节数
        total_bytes = sum(len(p) for p in paragraphs)

        # 计算每张卡片的目标字节数（平均分配）
        target_per_card = total_bytes / num_cards

        cards = []
        current_card = {
            'text': [],
            'images': [],
            'capacity_used': 0
        }

        for i, para in enumerate(paragraphs):
            para_bytes = len(para)

            # 先添加段落到当前卡片
            current_card['text'].append(para)
            current_card['capacity_used'] += para_bytes

            # 计算已使用的总字节数
            used_bytes = sum(c['capacity_used'] for c in cards) + current_card['capacity_used']
            remaining_bytes = total_bytes - used_bytes
            remaining_cards = num_cards - len(cards) - 1  # 减1因为当前卡片还没加入

            # 如果已经是最后一张卡片，继续添加
            if remaining_cards == 0:
                continue

            # 计算如果现在开始新卡片，剩余卡片的平均大小
            avg_remaining = remaining_bytes / remaining_cards if remaining_cards > 0 else 0

            # 检查是否应该开始新卡片
            # 条件：当前卡片已达到目标大小，且剩余内容足够分配
            should_start_new = (
                current_card['capacity_used'] >= target_per_card * 0.85 and  # 达到85%的目标
                avg_remaining >= target_per_card * 0.5  # 剩余卡片平均至少有50%的目标大小
            )

            if should_start_new:
                cards.append(current_card)
                current_card = {
                    'text': [],
                    'images': [],
                    'capacity_used': 0
                }

        # 添加最后一张卡片
        if current_card['text']:
            cards.append(current_card)

        # 格式化输出（先转为字符串列表）
        formatted = [{
            'text': '\n\n'.join(card['text']),
            'images': card['images'],
            'capacity_used': card['capacity_used']
        } for card in cards]

        # 如果卡片数不足 num_cards，拆分最大的卡片补足
        while len(formatted) < num_cards:
            # 找最大的卡片（按字节数）
            largest_idx = max(range(len(formatted)), key=lambda i: formatted[i]['capacity_used'])
            largest = formatted[largest_idx]
            text = largest['text']

            # 按句子边界拆分（中英文标点均支持）
            sentences = re.split(r'(?<=[。！？.!?\n])\s*', text)
            sentences = [s for s in sentences if s.strip()]

            if len(sentences) <= 1:
                # 只有一句话，强制从中间拆开
                mid = len(text) // 2
                part1 = text[:mid].strip()
                part2 = text[mid:].strip()
            else:
                mid = len(sentences) // 2
                part1 = ' '.join(sentences[:mid]).strip()
                part2 = ' '.join(sentences[mid:]).strip()

            card1 = {'text': part1, 'images': [], 'capacity_used': len(part1)}
            card2 = {'text': part2, 'images': [], 'capacity_used': len(part2)}
            formatted = formatted[:largest_idx] + [card1, card2] + formatted[largest_idx+1:]

        return formatted


def main():
    """测试"""
    content = """
# AI Agent 开发指南

![AI Agent架构图](https://example.com/images/architecture.png)

AI Agent 是一个强大的工具。

## 核心特性

![特性对比图](https://example.com/images/features-small.png)

- 支持多种模型
- 可扩展的插件系统

## 使用示例

这是一个简单的示例。

![示例截图](https://example.com/images/example-large.png)

通过这个示例，你可以快速上手。
    """

    handler = ImageHandler()

    # 提取图片
    images = handler.extract_images_from_markdown(content)
    print(f"找到 {len(images)} 张图片:")
    for img in images:
        print(f"  - {img.alt}: {img.size_category} ({img.byte_cost} 字节)")

    print()

    # 分割内容
    cards = handler.split_content_with_images(content, num_cards=3, base_capacity=250)
    print(f"分割为 {len(cards)} 张卡片:")
    for i, card in enumerate(cards, 1):
        print(f"\n卡片 {i}:")
        print(f"  文字: {len(card['text'])} 字节")
        print(f"  图片: {len(card['images'])} 张")
        print(f"  总占用: {card['capacity_used']} 字节")
        if card['images']:
            for img in card['images']:
                print(f"    - {img.alt}")


if __name__ == '__main__':
    main()

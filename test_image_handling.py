#!/usr/bin/env python3
"""
测试图片处理功能
"""

import sys
sys.path.insert(0, '/Users/Yuki/.claude/skills/liuguang-card-generator')

from image_handler import ImageHandler

# 测试内容（包含图片）
content = """
# AI Agent 开发指南

![AI Agent架构图](https://example.com/images/architecture.png)

AI Agent 是一个强大的工具，可以帮助你快速构建智能应用。

## 核心特性

以下是 AI Agent 的核心特性：

![特性对比图](https://example.com/images/features-small.png)

- 支持多种 AI 模型
- 可扩展的插件系统
- 强大的工作流引擎

## 使用示例

这是一个简单的使用示例。通过这个示例，你可以快速上手。

![示例截图](https://example.com/images/example-large.png)

按照上面的步骤，你就可以开始使用 AI Agent 了。

## 总结

AI Agent 是一个非常实用的工具，值得尝试。
"""

print("=" * 60)
print("测试图片处理功能")
print("=" * 60)
print()

handler = ImageHandler()

# 1. 提取图片
print("1. 提取图片信息:")
print("-" * 60)
images = handler.extract_images_from_markdown(content)
print(f"找到 {len(images)} 张图片:")
for img in images:
    print(f"  - {img.alt}")
    print(f"    URL: {img.url}")
    print(f"    大小类别: {img.size_category}")
    print(f"    占用字节: {img.byte_cost}")
    print()

# 2. 分割内容（考虑图片）
print("2. 智能分割内容（考虑图片占用空间）:")
print("-" * 60)
cards = handler.split_content_with_images(content, num_cards=3, base_capacity=250)

print(f"分割为 {len(cards)} 张卡片:")
print()

for i, card in enumerate(cards, 1):
    print(f"卡片 {i}:")
    print(f"  文字字节: {len(card['text'])}")
    print(f"  图片数量: {len(card['images'])}")
    print(f"  总占用: {card['capacity_used']} 字节")
    print(f"  剩余容量: {250 - card['capacity_used']} 字节")

    if card['images']:
        print(f"  包含图片:")
        for img in card['images']:
            print(f"    - {img.alt} ({img.byte_cost} 字节)")

    if card['text']:
        preview = card['text'][:80].replace('\n', ' ')
        print(f"  文字预览: {preview}...")

    print()

# 3. 对比：不考虑图片的分割
print("3. 对比：纯文字分割（不考虑图片）:")
print("-" * 60)

# 移除图片后的纯文字
text_only = handler.remove_images_from_content(content)
text_cards = handler._split_text_only(text_only, num_cards=3, base_capacity=250)

print(f"分割为 {len(text_cards)} 张卡片:")
print()

for i, card in enumerate(text_cards, 1):
    print(f"卡片 {i}:")
    print(f"  文字字节: {len(card['text'])}")
    print(f"  总占用: {card['capacity_used']} 字节")

    preview = card['text'][:80].replace('\n', ' ')
    print(f"  文字预览: {preview}...")
    print()

print("=" * 60)
print("测试完成")
print("=" * 60)
print()
print("💡 观察:")
print("  - 考虑图片时，每张卡片的文字容量会相应减少")
print("  - 图片占用的等效字节根据图片大小计算")
print("  - 这样可以避免卡片内容溢出")

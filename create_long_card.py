#!/usr/bin/env python3
"""
流光卡片生成器 - 长图版本
先生成一张长图，然后切割成6张卡片
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

def create_long_card(title, content, ai_image_path, icon_path, author="小红书号：charlii"):
    """
    创建长图并切割成6张卡片

    Args:
        title: 标题
        content: 正文内容
        ai_image_path: AI生成的封面图片路径
        icon_path: 作者头像路径
        author: 作者信息
    """

    # 卡片尺寸
    card_width = 440
    card_height = 586
    num_cards = 6
    long_height = card_height * num_cards  # 3516

    # 创建长图（浅蓝色渐变背景）
    long_card = Image.new('RGB', (card_width, long_height), '#6ec1e4')
    draw = ImageDraw.Draw(long_card)

    # 绘制渐变背景
    for y in range(long_height):
        ratio = y / long_height
        r = int(110 + (74 - 110) * ratio)
        g = int(193 + (158 - 193) * ratio)
        b = int(228 + (196 - 228) * ratio)
        draw.line([(0, y), (card_width, y)], fill=(r, g, b))

    # 加载字体
    font_path = "/System/Library/Fonts/PingFang.ttc"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

    try:
        font_title = ImageFont.truetype(font_path, 32)  # 标题字体
        font_content = ImageFont.truetype(font_path, 16)  # 正文字体
        font_footer = ImageFont.truetype(font_path, 12)  # 页脚字体
    except:
        font_title = ImageFont.load_default()
        font_content = ImageFont.load_default()
        font_footer = ImageFont.load_default()

    # 当前Y坐标
    current_y = 40
    margin_x = 30
    content_width = card_width - 2 * margin_x

    # 1. 绘制标题（居中、粗体）
    # 标题换行处理
    title_lines = []
    if len(title) > 15:
        # 按15个字符分行
        for i in range(0, len(title), 15):
            title_lines.append(title[i:i+15])
    else:
        title_lines = [title]

    for line in title_lines[:2]:  # 最多2行
        bbox = draw.textbbox((0, 0), line, font=font_title)
        text_width = bbox[2] - bbox[0]
        x = (card_width - text_width) // 2
        draw.text((x, current_y), line, font=font_title, fill='#1a1a1a')
        current_y += 45

    current_y += 20

    # 2. 插入AI图片
    if ai_image_path and os.path.exists(ai_image_path):
        ai_image = Image.open(ai_image_path).convert('RGB')

        # 图片尺寸（保持比例，宽度填满）
        image_width = content_width
        image_height = 300

        # 调整图片大小
        ai_width, ai_height = ai_image.size
        ai_ratio = ai_width / ai_height
        target_ratio = image_width / image_height

        if ai_ratio > target_ratio:
            new_height = ai_height
            new_width = int(ai_height * target_ratio)
            left = (ai_width - new_width) // 2
            ai_image = ai_image.crop((left, 0, left + new_width, new_height))
        else:
            new_width = ai_width
            new_height = int(ai_width / target_ratio)
            top = (ai_height - new_height) // 2
            ai_image = ai_image.crop((0, top, new_width, top + new_height))

        ai_image = ai_image.resize((image_width, image_height), Image.Resampling.LANCZOS)

        # 粘贴图片
        long_card.paste(ai_image, (margin_x, current_y))
        current_y += image_height + 30

    # 3. 绘制正文内容
    paragraphs = content.split('\n\n')

    for para in paragraphs:
        if not para.strip():
            continue

        # 段落换行处理
        lines = []
        words = para.strip()
        max_chars = 24  # 每行最多24个字符

        for i in range(0, len(words), max_chars):
            lines.append(words[i:i+max_chars])

        for line in lines:
            # 检查是否会超出长图范围
            if current_y > long_height - 100:
                break

            draw.text((margin_x, current_y), line, font=font_content, fill='#1a1a1a')
            current_y += 28

        current_y += 10  # 段落间距

    # 4. 在每张卡片底部绘制页码和作者信息
    for i in range(num_cards):
        card_y = i * card_height
        footer_y = card_y + card_height - 40

        # 页码
        pagination = f"{i+1:02d}"
        draw.text((card_width - 60, footer_y), pagination, font=font_footer, fill='#64748b')

        # 作者信息（只在第一张显示）
        if i == 0:
            draw.text((margin_x, footer_y), author, font=font_footer, fill='#64748b')

            # 作者头像（如果有）
            if icon_path and os.path.exists(icon_path):
                icon = Image.open(icon_path).convert('RGB')
                icon_size = 28
                icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

                # 创建圆形遮罩
                mask = Image.new('L', (icon_size, icon_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([(0, 0), (icon_size, icon_size)], fill=255)

                # 粘贴头像
                icon_rgba = icon.convert('RGBA')
                long_card.paste(icon_rgba, (card_width - 100, footer_y - 2), mask)

    # 5. 保存长图
    long_card_path = "/tmp/long_card.png"
    long_card.save(long_card_path, 'PNG', quality=95)
    print(f"✅ 长图已生成: {long_card_path}")

    # 6. 切割成6张卡片
    card_paths = []
    for i in range(num_cards):
        y_start = i * card_height
        y_end = (i + 1) * card_height

        card = long_card.crop((0, y_start, card_width, y_end))
        card_path = f"/tmp/cards/card_{i+1:02d}.png"
        card.save(card_path, 'PNG', quality=95)
        card_paths.append(card_path)
        print(f"✅ 卡片 {i+1} 已保存: {card_path}")

    return long_card_path, card_paths


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 create_long_card.py <标题> <内容文件> <AI图片> [icon路径]")
        sys.exit(1)

    title = sys.argv[1]
    content_file = sys.argv[2]
    ai_image = sys.argv[3]
    icon = sys.argv[4] if len(sys.argv) > 4 else ""

    # 读取内容
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 创建输出目录
    os.makedirs("/tmp/cards", exist_ok=True)

    # 生成卡片
    long_path, card_paths = create_long_card(title, content, ai_image, icon)

    print(f"\n🎉 完成！")
    print(f"长图: {long_path}")
    print(f"卡片: {len(card_paths)} 张")

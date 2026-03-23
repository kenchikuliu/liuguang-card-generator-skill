#!/usr/bin/env python3
"""
现代封面生成器：参考小红书卡片风格
设计原则：
1. 浅色渐变背景（浅蓝/青色）
2. 白色圆角卡片容器
3. 大标题（粗体、黑色）
4. 清晰的层次结构
5. 舒适的留白和间距
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import sys
import os

def create_modern_cover(
    title: str,
    content: str,
    ai_image_path: str,
    output_path: str,
    pagination: str = "01",
    author: str = "小红书号：charlii",
    date: str = "",
    icon_path: str = ""
):
    """创建现代风格的封面卡片"""

    try:
        # 1. 卡片尺寸（3:4 比例）
        card_width = 440
        card_height = 586

        # 2. 创建渐变背景（更柔和的蓝色渐变）
        card = Image.new('RGB', (card_width, card_height), '#6ec1e4')
        draw = ImageDraw.Draw(card)

        # 绘制渐变背景（从浅蓝到深蓝）
        for y in range(card_height):
            # 从 #6ec1e4 渐变到 #4a9ec4
            ratio = y / card_height
            r = int(110 + (74 - 110) * ratio)
            g = int(193 + (158 - 193) * ratio)
            b = int(228 + (196 - 228) * ratio)
            draw.line([(0, y), (card_width, y)], fill=(r, g, b))

        # 3. 创建白色圆角卡片容器
        container_margin = 20
        container_x = container_margin
        container_y = container_margin
        container_width = card_width - 2 * container_margin
        container_height = card_height - 2 * container_margin

        # 绘制容器阴影（更柔和）
        shadow = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [(container_x + 2, container_y + 2),
             (container_x + container_width + 2, container_y + container_height + 2)],
            radius=24,
            fill=(0, 0, 0, 20)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
        card.paste(shadow, (0, 0), shadow)

        # 绘制白色容器（纯白色，不用渐变）
        container_draw = ImageDraw.Draw(card)
        container_draw.rounded_rectangle(
            [(container_x, container_y),
             (container_x + container_width, container_y + container_height)],
            radius=24,
            fill=(255, 255, 255)
        )

        # 添加圆角遮罩
        mask = Image.new('L', (card_width, card_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [(container_x, container_y),
             (container_x + container_width, container_y + container_height)],
            radius=24,
            fill=255
        )

        # 应用遮罩
        rounded_card = Image.new('RGB', (card_width, card_height), '#5eb3d6')
        rounded_draw = ImageDraw.Draw(rounded_card)
        for y in range(card_height):
            ratio = y / card_height
            r = int(94 + (61 - 94) * ratio)
            g = int(179 + (143 - 179) * ratio)
            b = int(214 + (181 - 214) * ratio)
            rounded_draw.line([(0, y), (card_width, y)], fill=(r, g, b))

        rounded_card.paste(card, (0, 0), mask)
        card = rounded_card
        draw = ImageDraw.Draw(card)

        # 4. 加载字体（使用更好的字体）
        font_path = "/System/Library/Fonts/PingFang.ttc"
        if not os.path.exists(font_path):
            font_path = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

        try:
            font_date = ImageFont.truetype(font_path, 12)
            font_title = ImageFont.truetype(font_path, 26)  # 标题适中，避免溢出
            font_content = ImageFont.truetype(font_path, 14)  # 正文
            font_footer = ImageFont.truetype(font_path, 11)
        except:
            font_date = ImageFont.load_default()
            font_title = ImageFont.load_default()
            font_content = ImageFont.load_default()
            font_footer = ImageFont.load_default()

        # 5. 内容区域定义
        content_x = container_x + 24  # 减少左右边距，增加内容空间
        content_width = container_width - 48

        # 如果没有标题（内容卡片），从更上方开始，避免底部遮挡
        if not title or title.strip() == "":
            current_y = container_y + 15  # 内容卡片：从更上方开始
        else:
            current_y = container_y + 24  # 封面卡片：正常位置

        # 6. 绘制顶部引言/标签（如果有日期）
        if date:
            draw.text(
                (content_x, current_y),
                date,
                font=font_date,
                fill='#64748b'
            )
            current_y += 28
        else:
            # 如果没有日期，添加一个小标签
            tag_text = "💡 科技洞察"
            draw.text(
                (content_x, current_y),
                tag_text,
                font=font_date,
                fill='#64748b'
            )
            current_y += 28

        # 7. 绘制标题（粗体、大字号、更好的间距）
        # 标题换行处理 - 支持两行标题
        title_lines = []
        max_title_width = content_width

        # 智能标题换行（中英文混合友好）
        def smart_title_wrap(text, max_chars=13):
            """按标点或词边界换行，避免截断英文单词"""
            if '\n' in text:
                return [l.strip() for l in text.split('\n') if l.strip()]
            # 判断是否主要为英文（ASCII 字符占多数）
            ascii_ratio = sum(1 for c in text if ord(c) < 128 and c.isalpha()) / max(len(text), 1)
            is_english = ascii_ratio > 0.5
            if is_english:
                # 英文：按像素宽度估算，约每行 16 个字符（font size 26）
                max_en_chars = 16
                if len(text) <= max_en_chars:
                    return [text]
                # 在空格处断行
                words = text.split(' ')
                line1, line2 = [], []
                for w in words:
                    if sum(len(x) + 1 for x in line1) + len(w) <= max_en_chars:
                        line1.append(w)
                    else:
                        line2.append(w)
                result = [' '.join(line1)]
                if line2:
                    result.append(' '.join(line2))
                return result
            # 中文：优先在标点处分割
            for sep in ['：', '，', '、', '—']:
                if sep in text:
                    parts = text.split(sep, 1)
                    return [parts[0] + sep, parts[1]]
            if len(text) <= max_chars:
                return [text]
            # 找合适的断点：优先在空格断（保护英文单词），其次在中文字符边界
            best = max_chars
            for i in range(max_chars, 0, -1):
                if text[i] == ' ':
                    return [text[:i].strip(), text[i:].strip()]
                if ord(text[i-1]) > 127 and text[i] != ' ':
                    best = i
                    break
            return [text[:best].strip(), text[best:].strip()]

        title_lines = smart_title_wrap(title)

        # 最多显示两行标题
        for line in title_lines[:2]:
            draw.text(
                (content_x, current_y),
                line,
                font=font_title,
                fill='#1a1a1a'  # 更深的黑色
            )
            current_y += 36  # 行距

        current_y += 12  # 标题和图片之间的间距

        # 8. 叠加 AI 图片（更大、更突出）
        if ai_image_path and os.path.exists(ai_image_path):
            ai_image = Image.open(ai_image_path).convert('RGB')

            # 图片区域（更大）
            image_width = int(content_width)
            image_height = 260

            # 调整图片大小（保持比例，裁剪）
            ai_width, ai_height = ai_image.size
            ai_ratio = ai_width / ai_height
            target_ratio = image_width / image_height

            if ai_ratio > target_ratio:
                # 图片更宽，裁剪左右
                new_height = ai_height
                new_width = int(ai_height * target_ratio)
                left = (ai_width - new_width) // 2
                ai_image = ai_image.crop((left, 0, left + new_width, new_height))
            else:
                # 图片更高，裁剪上下
                new_width = ai_width
                new_height = int(ai_width / target_ratio)
                top = (ai_height - new_height) // 2
                ai_image = ai_image.crop((0, top, new_width, top + new_height))

            ai_image = ai_image.resize((image_width, image_height), Image.Resampling.LANCZOS)

            # 创建圆角遮罩（更大的圆角）
            image_mask = Image.new('L', (image_width, image_height), 0)
            image_mask_draw = ImageDraw.Draw(image_mask)
            image_mask_draw.rounded_rectangle(
                [(0, 0), (image_width, image_height)],
                radius=20,
                fill=255
            )

            # 添加图片阴影（更柔和）
            image_shadow = Image.new('RGBA', (image_width + 6, image_height + 6), (0, 0, 0, 0))
            image_shadow_draw = ImageDraw.Draw(image_shadow)
            image_shadow_draw.rounded_rectangle(
                [(3, 3), (image_width + 3, image_height + 3)],
                radius=20,
                fill=(0, 0, 0, 25)
            )
            image_shadow = image_shadow.filter(ImageFilter.GaussianBlur(radius=8))

            image_x = content_x
            card.paste(image_shadow, (image_x - 3, current_y - 3), image_shadow)

            # 粘贴图片
            ai_image_rgba = ai_image.convert('RGBA')
            card.paste(ai_image_rgba, (image_x, current_y), image_mask)

            current_y += image_height + 24

        # 9. 绘制图片下方的核心观点/引言
        # 提取内容的第一句或前80个字符作为引言，清除 Markdown 标记
        quote_text = content.split('\n')[0] if '\n' in content else content
        import re as _re
        quote_text = _re.sub(r'[*_#`]', '', quote_text).strip()
        if len(quote_text) > 80:
            quote_text = quote_text[:80] + "..."

        # 如果引言和标题不同，则显示
        if quote_text.strip() and quote_text.strip() != title.strip():
            # 按词语自动换行（中文按字符，英文按空格）
            def wrap_text(text, max_chars_per_line):
                import unicodedata
                lines = []
                current_line = ""
                words = text.split(' ') if any(ord(c) < 128 for c in text if c.isalpha()) else list(text)
                # 判断是否英文为主
                en_ratio = sum(1 for c in text if ord(c) < 128 and c.isalpha()) / max(len(text), 1)
                if en_ratio > 0.5:
                    # 英文：按空格分词换行
                    for word in text.split(' '):
                        if len(current_line) + len(word) + 1 <= max_chars_per_line:
                            current_line += (' ' if current_line else '') + word
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = word
                    if current_line:
                        lines.append(current_line)
                else:
                    # 中文：按字符换行
                    for ch in text:
                        if len(current_line) >= max_chars_per_line:
                            lines.append(current_line)
                            current_line = ch
                        else:
                            current_line += ch
                    if current_line:
                        lines.append(current_line)
                return lines

            quote_lines = wrap_text(quote_text, 22)

            for line in quote_lines[:3]:  # 最多3行
                if current_y > container_y + container_height - 100:
                    break
                draw.text(
                    (content_x, current_y),
                    line,
                    font=font_content,
                    fill='#64748b'
                )
                current_y += 22

        # 10. 绘制内容文字（如果还有空间）
        content_lines = content.split('\n')
        # 跳过第一行（已作为引言显示）
        for line in content_lines[1:]:
            line = line.strip()
            if not line:
                continue

            # 文字换行处理
            words = line
            max_chars_per_line = 20

            if len(words) > max_chars_per_line:
                wrapped_lines = [words[i:i+max_chars_per_line]
                               for i in range(0, len(words), max_chars_per_line)]
            else:
                wrapped_lines = [words]

            for wrapped_line in wrapped_lines:
                if current_y > container_y + container_height - 80:
                    break  # 避免溢出

                draw.text(
                    (content_x, current_y),
                    wrapped_line,
                    font=font_content,
                    fill='#334155'
                )
                current_y += 28

        # 11. 绘制底部信息
        footer_y = container_y + container_height - 40

        # 左下角：如果有 icon，显示圆形头像
        if icon_path and os.path.exists(icon_path):
            icon_image = Image.open(icon_path).convert('RGB')
            icon_size = 32
            icon_image = icon_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

            # 创建圆形遮罩
            icon_mask = Image.new('L', (icon_size, icon_size), 0)
            icon_mask_draw = ImageDraw.Draw(icon_mask)
            icon_mask_draw.ellipse([(0, 0), (icon_size, icon_size)], fill=255)

            # 粘贴圆形头像（左下角）
            icon_rgba = icon_image.convert('RGBA')
            card.paste(icon_rgba, (content_x, footer_y - 4), icon_mask)

            # 作者信息（头像右侧）
            author_x = content_x + icon_size + 8
        else:
            author_x = content_x

        # 作者信息
        draw.text(
            (author_x, footer_y),
            author,
            font=font_footer,
            fill='#64748b'
        )

        # 右下角：再次显示圆形头像（装饰性）
        if icon_path and os.path.exists(icon_path):
            icon_image_right = Image.open(icon_path).convert('RGB')
            icon_size_right = 28  # 稍小一点
            icon_image_right = icon_image_right.resize((icon_size_right, icon_size_right), Image.Resampling.LANCZOS)

            # 创建圆形遮罩
            icon_mask_right = Image.new('L', (icon_size_right, icon_size_right), 0)
            icon_mask_draw_right = ImageDraw.Draw(icon_mask_right)
            icon_mask_draw_right.ellipse([(0, 0), (icon_size_right, icon_size_right)], fill=255)

            # 计算右下角位置（页码左侧）
            icon_right_x = container_x + container_width - icon_size_right - 16
            icon_right_y = footer_y - 2

            # 粘贴圆形头像（右下角）
            icon_rgba_right = icon_image_right.convert('RGBA')
            card.paste(icon_rgba_right, (icon_right_x, icon_right_y), icon_mask_right)

        # 页码（右侧，白色圆角背景）
        pagination_text = pagination
        pagination_bbox = draw.textbbox((0, 0), pagination_text, font=font_footer)
        pagination_width = pagination_bbox[2] - pagination_bbox[0] + 24
        pagination_height = pagination_bbox[3] - pagination_bbox[1] + 8
        pagination_x = container_x + container_width - pagination_width - 16
        pagination_y = footer_y - 4

        draw.rounded_rectangle(
            [(pagination_x, pagination_y),
             (pagination_x + pagination_width, pagination_y + pagination_height)],
            radius=12,
            fill='white'
        )

        draw.text(
            (pagination_x + 12, pagination_y + 4),
            pagination_text,
            font=font_footer,
            fill='#0f172a'
        )

        # 11. 保存
        card.save(output_path, 'PNG', quality=95)
        print(f"✅ 现代封面已生成: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("用法: python3 create_modern_cover.py <标题> <内容> <AI图片> <输出路径> [页码] [作者] [日期] [icon路径]")
        sys.exit(1)

    title = sys.argv[1]
    content = sys.argv[2]
    ai_image = sys.argv[3]
    output = sys.argv[4]
    pagination = sys.argv[5] if len(sys.argv) > 5 else "01"
    author = sys.argv[6] if len(sys.argv) > 6 else "小红书号：charlii"
    date = sys.argv[7] if len(sys.argv) > 7 else ""
    icon = sys.argv[8] if len(sys.argv) > 8 else ""

    result = create_modern_cover(title, content, ai_image, output, pagination, author, date, icon)

    if result:
        print("\n🎉 成功！")
        sys.exit(0)
    else:
        print("\n❌ 失败！")
        sys.exit(1)

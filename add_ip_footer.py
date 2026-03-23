#!/usr/bin/env python3
"""
为最后一张卡片添加IP信息区
包括头像、名称、简介和页码
"""

from PIL import Image, ImageDraw, ImageFont
import sys

def add_ip_footer(card_path: str, avatar_path: str, output_path: str, page_num: str = "06"):
    """在卡片底部添加IP信息区"""

    try:
        # 1. 加载卡片
        card = Image.open(card_path).convert("RGBA")
        card_width, card_height = card.size

        # 2. 加载头像
        avatar = Image.open(avatar_path).convert("RGBA")

        # 3. 头像尺寸：60x60 像素
        avatar_size = 60
        avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

        # 4. 创建圆形遮罩
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        # 5. 应用圆形遮罩
        avatar_circle = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_circle.paste(avatar, (0, 0), mask)

        # 6. 添加白色边框
        border_width = 2
        border_mask = Image.new('L', (avatar_size, avatar_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        border_draw.ellipse((border_width, border_width,
                           avatar_size-border_width, avatar_size-border_width), fill=0)

        border = Image.new('RGBA', (avatar_size, avatar_size), (255, 255, 255, 255))
        avatar_with_border = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_with_border.paste(border, (0, 0), border_mask)
        avatar_with_border.paste(avatar_circle, (0, 0), avatar_circle)

        # 7. 计算底部IP区域位置
        # IP信息应该在卡片内容区域的底部（不是整个画布底部）
        # 卡片内容区域大约从上边距60px开始，到下边距60px结束
        footer_height = 80
        footer_y = card_height - 140  # 距离底部140px，留出空间

        # 头像位置：左侧
        avatar_x = 80  # 从左边距80px开始
        avatar_y = footer_y + (footer_height - avatar_size) // 2

        # 8. 合成头像到卡片
        card.paste(avatar_with_border, (avatar_x, avatar_y), avatar_with_border)

        # 9. 添加IP文字信息
        draw = ImageDraw.Draw(card)

        # 尝试加载中文字体
        try:
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc"
            ]
            name_font = None
            desc_font = None
            page_font = None

            for font_path in font_paths:
                try:
                    name_font = ImageFont.truetype(font_path, 20)
                    desc_font = ImageFont.truetype(font_path, 16)
                    page_font = ImageFont.truetype(font_path, 18)
                    break
                except:
                    continue

            if not name_font:
                name_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
                page_font = ImageFont.load_default()
        except:
            name_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            page_font = ImageFont.load_default()

        # IP名称位置：头像右侧
        text_x = avatar_x + avatar_size + 15
        name_y = footer_y + 15
        desc_y = name_y + 26

        # 绘制IP名称
        draw.text((text_x, name_y), "AI博士Charlii", font=name_font, fill=(50, 50, 50, 255))

        # 绘制简介
        draw.text((text_x, desc_y), "分享AIGC与实用技能", font=desc_font, fill=(120, 120, 120, 255))

        # 10. 添加页码（右下角）
        page_text = page_num
        page_bbox = draw.textbbox((0, 0), page_text, font=page_font)
        page_width = page_bbox[2] - page_bbox[0]
        page_x = card_width - page_width - 30
        page_y = footer_y + (footer_height - (page_bbox[3] - page_bbox[1])) // 2

        draw.text((page_x, page_y), page_text, font=page_font, fill=(100, 100, 100, 200))

        # 11. 保存结果
        card = card.convert("RGB")
        card.save(output_path, "PNG", quality=95)

        print(f"✅ IP信息区已添加: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ 添加失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 add_ip_footer.py <卡片路径> <头像路径> <输出路径> [页码]")
        sys.exit(1)

    card_path = sys.argv[1]
    avatar_path = sys.argv[2]
    output_path = sys.argv[3]
    page_num = sys.argv[4] if len(sys.argv) > 4 else "06"

    result = add_ip_footer(card_path, avatar_path, output_path, page_num)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

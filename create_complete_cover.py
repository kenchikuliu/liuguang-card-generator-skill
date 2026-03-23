#!/usr/bin/env python3
"""
完整封面合成器：将博客封面、标题文字、头像icon融合成一张精美的封面
设计原则：视觉冲击力、情绪共鸣、层次分明、品牌一致性
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import sys

def create_complete_cover(
    blog_image_path: str,
    avatar_path: str,
    title: str,
    output_path: str
):
    """创建完整的封面设计"""

    try:
        # 1. 加载博客封面
        blog_image = Image.open(blog_image_path).convert("RGB")

        # 2. 目标尺寸：3:4比例
        target_width = 1200
        target_height = 1600

        # 3. 智能裁剪博客图片
        blog_width, blog_height = blog_image.size
        blog_ratio = blog_width / blog_height
        target_ratio = target_width / target_height

        if blog_ratio > target_ratio:
            new_height = blog_height
            new_width = int(blog_height * target_ratio)
            left = (blog_width - new_width) // 2
            blog_image = blog_image.crop((left, 0, left + new_width, new_height))
        else:
            new_width = blog_width
            new_height = int(blog_width / target_ratio)
            top = (blog_height - new_height) // 2
            blog_image = blog_image.crop((0, top, new_width, top + new_height))

        blog_image = blog_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # 4. 创建更有冲击力的设计：清晰背景 + 高对比
        # 保持博客图片清晰，但增强对比度
        enhancer_contrast = ImageEnhance.Contrast(blog_image)
        blog_image = enhancer_contrast.enhance(1.3)  # 提高对比度

        enhancer_color = ImageEnhance.Color(blog_image)
        blog_image = enhancer_color.enhance(1.2)  # 提高饱和度

        blog_image_rgba = blog_image.convert('RGBA')

        # 5. 不添加渐变，保持图片清晰

        # 6. 添加标题文字（更有冲击力的排版）
        draw = ImageDraw.Draw(blog_image_rgba)

        # 尝试加载中文字体（优先使用粗体）
        try:
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc"
            ]
            # 更大的字体尺寸，增强视觉冲击力
            title_font_large = None
            title_font_medium = None
            for font_path in font_paths:
                try:
                    title_font_large = ImageFont.truetype(font_path, 100)  # 从85增加到100
                    title_font_medium = ImageFont.truetype(font_path, 85)  # 从70增加到85
                    break
                except:
                    continue
            if not title_font_large:
                title_font_large = ImageFont.load_default()
                title_font_medium = ImageFont.load_default()
        except:
            title_font_large = ImageFont.load_default()
            title_font_medium = ImageFont.load_default()

        # 三行设计，更有节奏感
        line1 = '我被信息淹没'
        line2 = '差点崩溃'
        line3 = '直到我做了这件事'

        y_offset = 180
        left_margin = 100

        lines = [
            (line1, title_font_large),
            (line2, title_font_large),
            (line3, title_font_medium)
        ]

        for idx, (line, font) in enumerate(lines):
            # 计算文字尺寸
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            text_x = left_margin
            text_y = y_offset

            # 添加半透明黑色背景块
            padding = 20
            bg_x1 = text_x - padding
            bg_y1 = text_y - padding // 2
            bg_x2 = text_x + text_width + padding
            bg_y2 = text_y + text_height + padding // 2

            # 绘制圆角矩形背景
            bg_overlay = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(bg_overlay)
            bg_draw.rounded_rectangle(
                [(bg_x1, bg_y1), (bg_x2, bg_y2)],
                radius=10,
                fill=(0, 0, 0, 180)  # 半透明黑色
            )
            blog_image_rgba = Image.alpha_composite(blog_image_rgba, bg_overlay)

            # 重新获取 draw 对象
            draw = ImageDraw.Draw(blog_image_rgba)

            # 绘制纯白文字
            draw.text((text_x, text_y), line, font=font, fill=(255, 255, 255, 255))

            # 第三行后增加更大间距
            if idx == 1:
                y_offset += text_height + 50  # 更大的间距
            else:
                y_offset += text_height + 20  # 正常间距

        # 7. 添加头像（左下角，更大更突出）
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar_size = 180  # 更大的头像
        avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

        # 创建圆形遮罩
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        avatar_circle = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_circle.paste(avatar, (0, 0), mask)

        # 添加白色边框
        border_width = 6
        border_mask = Image.new('L', (avatar_size, avatar_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        border_draw.ellipse((border_width, border_width,
                           avatar_size-border_width, avatar_size-border_width), fill=0)

        border = Image.new('RGBA', (avatar_size, avatar_size), (255, 255, 255, 255))
        avatar_with_border = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_with_border.paste(border, (0, 0), border_mask)
        avatar_with_border.paste(avatar_circle, (0, 0), avatar_circle)

        # 头像阴影
        shadow = Image.new('RGBA', (avatar_size + 20, avatar_size + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((10, 10, avatar_size + 10, avatar_size + 10), fill=(0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))

        # 头像位置（左下角）
        avatar_x = 100
        avatar_y = target_height - avatar_size - 100

        blog_image_rgba = Image.alpha_composite(blog_image_rgba,
            shadow.resize((target_width, target_height), Image.Resampling.LANCZOS))
        blog_image_rgba.paste(avatar_with_border, (avatar_x, avatar_y), avatar_with_border)

        # 9. 保存结果
        final_image = blog_image_rgba.convert('RGB')
        final_image.save(output_path, 'PNG', quality=95)

        print(f"✅ 完整封面已生成: {output_path}")
        print(f"   设计元素：")
        print(f"   - 博客封面图（增强对比度）")
        print(f"   - 蓝绿渐变叠加（品牌一致性）")
        print(f"   - 标题文字（带半透明背景）")
        print(f"   - 圆形头像（右下角，带阴影）")
        print(f"   - 暗角效果（聚焦中心）")

        return output_path

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("用法: python3 create_complete_cover.py <博客封面> <头像> <标题> <输出路径>")
        sys.exit(1)

    blog_image = sys.argv[1]
    avatar = sys.argv[2]
    title = sys.argv[3]
    output = sys.argv[4]

    result = create_complete_cover(blog_image, avatar, title, output)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

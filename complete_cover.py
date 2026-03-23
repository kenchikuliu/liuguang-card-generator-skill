#!/usr/bin/env python3
"""
完整封面生成器：在流光卡片上叠加博客配图和头像
设计原则：视觉层次、留白、可读性、品牌一致性
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path
import sys

def create_complete_cover(
    base_card_path: str,
    blog_image_path: str,
    avatar_path: str,
    output_path: str
):
    """在流光卡片上叠加博客配图和头像 - 优化版"""

    try:
        # 1. 加载基础卡片
        card = Image.open(base_card_path).convert("RGBA")
        card_width, card_height = card.size

        # 2. 加载博客配图
        blog_image = Image.open(blog_image_path).convert("RGB")

        # 3. 设计优化：更大的图片区域，更好的视觉冲击力
        # 标题区域：顶部 80px
        # 图片区域：从 80px 到底部 120px
        # 底部留白：120px（用于头像和页码）
        image_start_y = 80
        image_end_y = card_height - 120
        available_height = image_end_y - image_start_y

        # 图片宽度：占卡片宽度的 90%（更大气）
        image_width = int(card_width * 0.90)

        # 4. 智能裁剪：使用中心裁剪保持构图
        blog_width, blog_height = blog_image.size
        blog_ratio = blog_width / blog_height
        target_ratio = image_width / available_height

        if blog_ratio > target_ratio:
            # 图片更宽，裁剪左右
            new_height = blog_height
            new_width = int(blog_height * target_ratio)
            left = (blog_width - new_width) // 2
            blog_image = blog_image.crop((left, 0, left + new_width, new_height))
        else:
            # 图片更高，裁剪上下
            new_width = blog_width
            new_height = int(blog_width / target_ratio)
            top = (blog_height - new_height) // 2
            blog_image = blog_image.crop((0, top, new_width, top + new_height))

        # 5. 调整到目标尺寸
        blog_image = blog_image.resize((image_width, available_height), Image.Resampling.LANCZOS)

        # 6. 计算博客配图位置（水平居中）
        image_x = (card_width - image_width) // 2
        image_y = image_start_y

        # 7. 创建圆角遮罩（更大的圆角，更现代）
        mask = Image.new('L', (image_width, available_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        radius = 20  # 增大圆角
        mask_draw.rounded_rectangle(
            [(0, 0), (image_width, available_height)],
            radius=radius,
            fill=255
        )

        # 8. 添加微妙的阴影效果（增加层次感）
        shadow = Image.new('RGBA', (image_width + 10, available_height + 10), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [(5, 5), (image_width + 5, available_height + 5)],
            radius=radius,
            fill=(0, 0, 0, 30)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))
        card.paste(shadow, (image_x - 5, image_y - 5), shadow)

        # 9. 将博客配图转换为 RGBA 并合成
        blog_image_rgba = blog_image.convert("RGBA")
        card.paste(blog_image_rgba, (image_x, image_y), mask)

        # 10. 加载并处理头像（更大更突出）
        avatar = Image.open(avatar_path).convert("RGBA")

        # 头像尺寸：100x100 像素（从 80 增大到 100）
        avatar_size = 100
        avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

        # 11. 创建圆形遮罩（头像）
        avatar_mask = Image.new('L', (avatar_size, avatar_size), 0)
        avatar_mask_draw = ImageDraw.Draw(avatar_mask)
        avatar_mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        # 12. 应用圆形遮罩
        avatar_circle = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_circle.paste(avatar, (0, 0), avatar_mask)

        # 13. 添加白色边框（更粗，更明显）
        border_width = 4
        border_mask = Image.new('L', (avatar_size, avatar_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        border_draw.ellipse((border_width, border_width,
                           avatar_size-border_width, avatar_size-border_width), fill=0)

        border = Image.new('RGBA', (avatar_size, avatar_size), (255, 255, 255, 255))
        avatar_with_border = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_with_border.paste(border, (0, 0), border_mask)
        avatar_with_border.paste(avatar_circle, (0, 0), avatar_circle)

        # 14. 头像阴影（增加立体感）
        avatar_shadow = Image.new('RGBA', (avatar_size + 10, avatar_size + 10), (0, 0, 0, 0))
        avatar_shadow_draw = ImageDraw.Draw(avatar_shadow)
        avatar_shadow_draw.ellipse((5, 5, avatar_size + 5, avatar_size + 5), fill=(0, 0, 0, 50))
        avatar_shadow = avatar_shadow.filter(ImageFilter.GaussianBlur(radius=6))

        # 15. 计算头像位置（左下角，与图片底部对齐）
        avatar_x = 30  # 左边距
        avatar_y = image_end_y - avatar_size // 2  # 一半在图片内，一半在外

        # 16. 合成头像阴影和头像到卡片
        card.paste(avatar_shadow, (avatar_x - 5, avatar_y - 5), avatar_shadow)
        card.paste(avatar_with_border, (avatar_x, avatar_y), avatar_with_border)

        # 17. 保存结果
        card = card.convert("RGB")
        card.save(output_path, "PNG", quality=95)

        print(f"✅ 完整封面已生成: {output_path}")
        print(f"   设计优化：")
        print(f"   - 图片区域扩大至 90% 宽度")
        print(f"   - 智能中心裁剪保持构图")
        print(f"   - 头像增大至 100x100px")
        print(f"   - 头像位置优化至左下角")
        print(f"   - 添加阴影增加层次感")
        return output_path

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("用法: python3 complete_cover.py <基础卡片> <博客配图> <头像> <输出路径>")
        sys.exit(1)

    base_card = sys.argv[1]
    blog_image = sys.argv[2]
    avatar = sys.argv[3]
    output = sys.argv[4]

    result = create_complete_cover(base_card, blog_image, avatar, output)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

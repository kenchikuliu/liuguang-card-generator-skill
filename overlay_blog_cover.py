#!/usr/bin/env python3
"""
博客封面叠加器：只叠加博客封面图，不叠加头像
因为流光卡片API会自动在右上角显示icon（头像）
"""

from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import sys

def overlay_blog_cover(
    base_card_path: str,
    blog_image_path: str,
    output_path: str
):
    """在流光卡片上只叠加博客配图，不叠加头像"""

    try:
        # 1. 加载基础卡片
        card = Image.open(base_card_path).convert("RGBA")
        card_width, card_height = card.size

        # 2. 加载博客配图
        blog_image = Image.open(blog_image_path).convert("RGB")

        # 3. 设计优化：更合理的图片区域
        # 标题区域：顶部 100px（给标题更多空间）
        # 图片区域：从 100px 到底部 80px
        # 底部留白：80px（用于页码）
        image_start_y = 100
        image_end_y = card_height - 80
        available_height = image_end_y - image_start_y

        # 图片宽度：占卡片宽度的 85%（稍微小一点，更精致）
        image_width = int(card_width * 0.85)

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

        # 7. 创建圆角遮罩
        mask = Image.new('L', (image_width, available_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        radius = 20
        mask_draw.rounded_rectangle(
            [(0, 0), (image_width, available_height)],
            radius=radius,
            fill=255
        )

        # 8. 添加微妙的阴影效果
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

        # 10. 保存结果
        card = card.convert("RGB")
        card.save(output_path, "PNG", quality=95)

        print(f"✅ 博客封面已叠加: {output_path}")
        print(f"   设计优化：")
        print(f"   - 图片区域扩大至 90% 宽度")
        print(f"   - 智能中心裁剪保持构图")
        print(f"   - 添加阴影增加层次感")
        print(f"   - 头像由流光卡片API自动显示在右上角")
        return output_path

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 overlay_blog_cover.py <基础卡片> <博客配图> <输出路径>")
        sys.exit(1)

    base_card = sys.argv[1]
    blog_image = sys.argv[2]
    output = sys.argv[3]

    result = overlay_blog_cover(base_card, blog_image, output)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

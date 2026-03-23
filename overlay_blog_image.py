#!/usr/bin/env python3
"""
在流光卡片基础上叠加博客配图
保持流光卡片的排版，只替换图片区域
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

def overlay_blog_image_on_card(
    base_card_path: str,
    blog_image_path: str,
    output_path: str
):
    """在流光卡片上叠加博客配图"""

    try:
        # 1. 加载基础卡片
        card = Image.open(base_card_path).convert("RGBA")
        card_width, card_height = card.size

        # 2. 加载博客配图
        blog_image = Image.open(blog_image_path).convert("RGB")

        # 3. 计算图片区域（流光卡片的 icon 区域）
        # 流光卡片布局：标题在上方（约 80-120px），图片在中间，底部有分页
        # 图片区域：从 120px 开始，到 card_height - 100px 结束
        image_start_y = 120
        image_end_y = card_height - 100
        available_height = image_end_y - image_start_y

        # 图片宽度：占卡片的 80%，居中
        image_width = int(card_width * 0.80)

        # 根据可用高度调整图片尺寸，保持原始比例
        blog_width, blog_height = blog_image.size
        blog_ratio = blog_width / blog_height

        # 计算合适的图片尺寸
        if available_height * blog_ratio > image_width:
            # 宽度受限
            final_width = image_width
            final_height = int(image_width / blog_ratio)
        else:
            # 高度受限
            final_height = available_height
            final_width = int(available_height * blog_ratio)

        # 调整博客配图尺寸
        blog_image = blog_image.resize((final_width, final_height), Image.Resampling.LANCZOS)

        # 4. 计算图片位置（居中）
        image_x = (card_width - final_width) // 2
        image_y = image_start_y + (available_height - final_height) // 2

        # 5. 创建圆角遮罩
        mask = Image.new('L', (final_width, final_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        radius = 15
        mask_draw.rounded_rectangle(
            [(0, 0), (final_width, final_height)],
            radius=radius,
            fill=255
        )

        # 6. 将博客配图转换为 RGBA
        blog_image_rgba = blog_image.convert("RGBA")

        # 7. 合成到卡片上
        card.paste(blog_image_rgba, (image_x, image_y), mask)

        # 8. 保存结果
        card = card.convert("RGB")
        card.save(output_path, "PNG", quality=95)

        print(f"✅ 已将博客配图叠加到流光卡片: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ 叠加失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 overlay_blog_image.py <基础卡片> <博客配图> <输出路径>")
        sys.exit(1)

    base_card = sys.argv[1]
    blog_image = sys.argv[2]
    output = sys.argv[3]

    result = overlay_blog_image_on_card(base_card, blog_image, output)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

#!/usr/bin/env python3
"""
AI封面生成器：将博客封面和头像合成后，用AI重新设计
"""

from PIL import Image, ImageDraw, ImageFilter
import sys
import os

def create_ai_ready_cover(blog_image_path: str, avatar_path: str, output_path: str):
    """
    将博客封面和头像合成为一张图，供AI重新设计
    设计思路：头像作为视觉焦点，放在左下角，与博客封面自然融合
    """

    try:
        # 1. 加载博客封面
        blog_image = Image.open(blog_image_path).convert("RGB")
        blog_width, blog_height = blog_image.size

        # 2. 目标尺寸：保持博客封面的宽高比，但调整到合适的尺寸
        target_width = 1200
        target_height = int(target_width * blog_height / blog_width)
        blog_image = blog_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # 3. 创建画布（稍微大一点，为头像留出空间）
        canvas_height = target_height + 100
        canvas = Image.new('RGB', (target_width, canvas_height), (255, 255, 255))

        # 4. 将博客封面贴到画布上
        canvas.paste(blog_image, (0, 0))

        # 5. 加载头像
        avatar = Image.open(avatar_path).convert("RGBA")

        # 6. 头像尺寸：120x120（更大更突出）
        avatar_size = 120
        avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

        # 7. 创建圆形遮罩
        mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)

        # 8. 应用圆形遮罩
        avatar_circle = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_circle.paste(avatar, (0, 0), mask)

        # 9. 添加白色边框
        border_width = 5
        border_mask = Image.new('L', (avatar_size, avatar_size), 0)
        border_draw = ImageDraw.Draw(border_mask)
        border_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        border_draw.ellipse((border_width, border_width,
                           avatar_size-border_width, avatar_size-border_width), fill=0)

        border = Image.new('RGBA', (avatar_size, avatar_size), (255, 255, 255, 255))
        avatar_with_border = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_with_border.paste(border, (0, 0), border_mask)
        avatar_with_border.paste(avatar_circle, (0, 0), avatar_circle)

        # 10. 头像阴影
        shadow = Image.new('RGBA', (avatar_size + 20, avatar_size + 20), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((10, 10, avatar_size + 10, avatar_size + 10), fill=(0, 0, 0, 80))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=10))

        # 11. 计算头像位置（左下角，一半在图片内）
        avatar_x = 40
        avatar_y = target_height - avatar_size // 2

        # 12. 转换画布为RGBA以支持透明度
        canvas_rgba = canvas.convert('RGBA')

        # 13. 合成阴影和头像
        canvas_rgba.paste(shadow, (avatar_x - 10, avatar_y - 10), shadow)
        canvas_rgba.paste(avatar_with_border, (avatar_x, avatar_y), avatar_with_border)

        # 14. 保存为PNG
        canvas_rgba = canvas_rgba.convert('RGB')
        canvas_rgba.save(output_path, 'PNG', quality=95)

        print(f"✅ AI封面素材已生成: {output_path}")
        print(f"   尺寸: {target_width}x{canvas_height}")
        print(f"   头像位置: 左下角")

        return output_path

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 create_ai_cover.py <博客封面> <头像> <输出路径>")
        sys.exit(1)

    blog_image = sys.argv[1]
    avatar = sys.argv[2]
    output = sys.argv[3]

    result = create_ai_ready_cover(blog_image, avatar, output)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

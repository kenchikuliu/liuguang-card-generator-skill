#!/usr/bin/env python3
"""
封面重新设计：基于设计原则创建吸引人的封面
设计原则：视觉冲击力、情绪共鸣、层次分明、留白艺术、品牌一致性
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import sys

def redesign_cover(blog_image_path: str, output_path: str):
    """重新设计封面：增强视觉冲击力和情绪共鸣"""

    try:
        # 1. 加载原始博客封面
        blog_image = Image.open(blog_image_path).convert("RGB")

        # 2. 目标尺寸：3:4比例，适合卡片
        target_width = 1200
        target_height = 1600

        # 3. 调整博客图片尺寸并裁剪
        blog_width, blog_height = blog_image.size
        blog_ratio = blog_width / blog_height
        target_ratio = target_width / target_height

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

        # 4. 调整到目标尺寸
        blog_image = blog_image.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # 5. 增强视觉冲击力：提高对比度和饱和度
        enhancer_contrast = ImageEnhance.Contrast(blog_image)
        blog_image = enhancer_contrast.enhance(1.2)  # 提高20%对比度

        enhancer_color = ImageEnhance.Color(blog_image)
        blog_image = blog_image  # 保持原色彩，不过度饱和

        # 6. 创建渐变叠加层（蓝绿渐变，增强品牌一致性）
        gradient = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # 从顶部到底部的蓝绿渐变
        for y in range(target_height):
            # 渐变从深蓝到青绿
            ratio = y / target_height
            r = int(20 + (50 - 20) * ratio)
            g = int(150 + (200 - 150) * ratio)
            b = int(180 + (150 - 180) * ratio)
            alpha = int(40 + (20 - 40) * ratio)  # 顶部更深，底部更浅
            draw.line([(0, y), (target_width, y)], fill=(r, g, b, alpha))

        # 7. 合成渐变层
        blog_image_rgba = blog_image.convert('RGBA')
        blog_image_rgba = Image.alpha_composite(blog_image_rgba, gradient)

        # 8. 添加微妙的暗角效果（增强视觉焦点）
        vignette = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
        vignette_draw = ImageDraw.Draw(vignette)

        # 从中心到边缘的暗角
        center_x, center_y = target_width // 2, target_height // 2
        max_distance = ((target_width / 2) ** 2 + (target_height / 2) ** 2) ** 0.5

        for y in range(target_height):
            for x in range(target_width):
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                alpha = int((distance / max_distance) * 60)  # 边缘最多60透明度
                if alpha > 0:
                    vignette_draw.point((x, y), fill=(0, 0, 0, alpha))

        # 应用暗角（使用高斯模糊使其更自然）
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=50))
        blog_image_rgba = Image.alpha_composite(blog_image_rgba, vignette)

        # 9. 保存结果
        blog_image_final = blog_image_rgba.convert('RGB')
        blog_image_final.save(output_path, 'PNG', quality=95)

        print(f"✅ 封面重新设计完成: {output_path}")
        print(f"   设计优化：")
        print(f"   - 提高对比度20%，增强视觉冲击力")
        print(f"   - 添加蓝绿渐变叠加，强化品牌一致性")
        print(f"   - 应用暗角效果，聚焦视觉中心")
        print(f"   - 3:4比例，完美适配卡片")

        return output_path

    except Exception as e:
        print(f"❌ 重新设计失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 redesign_cover.py <博客封面> <输出路径>")
        sys.exit(1)

    blog_image = sys.argv[1]
    output = sys.argv[2]

    result = redesign_cover(blog_image, output)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

#!/usr/bin/env python3
"""
使用流光卡片 API 生成带自定义图片的封面卡片
"""

import requests
import json
import sys
import base64
from pathlib import Path

def upload_image_to_base64(image_path: str) -> str:
    """将本地图片转换为 base64 data URL"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
        base64_data = base64.b64encode(image_data).decode('utf-8')

        # 检测图片格式
        if image_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif image_path.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/jpeg'

        return f"data:{mime_type};base64,{base64_data}"

def generate_cover_card(
    image_path: str,
    title: str,
    output_path: str
):
    """生成流光卡片封面"""

    try:
        print(f"📤 上传图片...")
        # 将图片转换为 base64
        icon_url = upload_image_to_base64(image_path)
        print(f"✅ 图片已转换为 base64")

        # 构建卡片数据
        form_data = {
            "icon": icon_url,
            "title": f"<blockquote><p><strong>{title}</strong></p></blockquote>",
            "content": "",
            "pagination": "01"
        }

        style_data = {
            "backgroundName": "vertical-blue-color-29",
            "font": "Alibaba-PuHuiTi-Regular",
            "width": 440,
            "height": 586
        }

        # 调用流光卡片 API
        print(f"🎨 调用流光卡片 API...")

        response = requests.post(
            "https://fireflycard-api.302ai.cn/api/saveImg",
            data={
                "form": json.dumps(form_data),
                "style": json.dumps(style_data),
                "temp": "tempA"
            },
            timeout=60
        )

        if response.status_code == 200:
            # 保存图片
            with open(output_path, 'wb') as f:
                f.write(response.content)

            print(f"✅ 封面卡片已生成: {output_path}")
            return output_path
        else:
            print(f"❌ API 调用失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return None

    except Exception as e:
        print(f"❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 cover_with_image.py <图片路径> <标题> <输出路径>")
        sys.exit(1)

    image_path = sys.argv[1]
    title = sys.argv[2]
    output_path = sys.argv[3]

    result = generate_cover_card(image_path, title, output_path)

    if result:
        print(f"\n🎉 成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 失败！")
        sys.exit(1)

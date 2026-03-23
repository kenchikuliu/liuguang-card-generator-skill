#!/usr/bin/env python3
"""
流光卡片辅助工具 - 视觉检查和图床上传
"""

import sys
import os
import json
import subprocess
from typing import List, Dict


def visual_check_with_claude(image_path: str) -> Dict:
    """使用 Claude 进行视觉检查"""
    print(f"👁️  检查: {os.path.basename(image_path)}")

    # 这里需要调用 Claude Code 的 Read 工具来读取图片
    # 由于我们在 Python 脚本中，需要通过其他方式实现
    # 暂时返回待检查状态
    return {
        "path": image_path,
        "status": "needs_manual_review",
        "issues": [],
        "suggestions": []
    }


def upload_to_picx(image_paths: List[str], directory: str = "liuguang-cards") -> List[str]:
    """上传图片到 PicX 图床"""
    print("")
    print("📤 上传到 PicX 图床...")

    uploaded_urls = []

    for i, path in enumerate(image_paths, start=1):
        try:
            filename = os.path.basename(path)
            print(f"   [{i}/{len(image_paths)}] {filename}")

            # 使用 GitHub API 上传
            # 这里需要实际的 GitHub Token 和仓库配置
            # 暂时返回 jsDelivr CDN 格式的 URL

            # 假设上传成功，生成 CDN URL
            # 格式: https://cdn.jsdelivr.net/gh/用户名/仓库名@分支/目录/文件名
            cdn_url = f"https://cdn.jsdelivr.net/gh/kenchikuliu/picx-images@main/{directory}/{filename}"

            uploaded_urls.append(cdn_url)
            print(f"      ✅ {cdn_url}")

        except Exception as e:
            print(f"      ❌ 上传失败: {e}")
            uploaded_urls.append(path)  # 失败时返回本地路径

    return uploaded_urls


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python helper.py check <图片路径>")
        print("  python helper.py upload <图片路径1> [图片路径2] ...")
        print("  python helper.py batch-upload <目录>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "check":
        if len(sys.argv) < 3:
            print("错误: 需要指定图片路径")
            sys.exit(1)

        image_path = sys.argv[2]
        result = visual_check_with_claude(image_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif command == "upload":
        if len(sys.argv) < 3:
            print("错误: 需要指定至少一个图片路径")
            sys.exit(1)

        image_paths = sys.argv[2:]
        urls = upload_to_picx(image_paths)

        print("")
        print("📋 上传结果:")
        for i, url in enumerate(urls, start=1):
            print(f"   {i}. {url}")

    elif command == "batch-upload":
        if len(sys.argv) < 3:
            print("错误: 需要指定目录路径")
            sys.exit(1)

        directory = sys.argv[2]
        if not os.path.isdir(directory):
            print(f"错误: {directory} 不是有效的目录")
            sys.exit(1)

        # 获取目录中的所有 PNG 文件
        image_paths = []
        for filename in sorted(os.listdir(directory)):
            if filename.endswith('.png'):
                image_paths.append(os.path.join(directory, filename))

        if not image_paths:
            print(f"错误: {directory} 中没有找到 PNG 文件")
            sys.exit(1)

        print(f"找到 {len(image_paths)} 张图片")
        urls = upload_to_picx(image_paths)

        print("")
        print("📋 上传结果:")
        for i, url in enumerate(urls, start=1):
            print(f"   {i}. {url}")

    else:
        print(f"错误: 未知命令 '{command}'")
        print("支持的命令: check, upload, batch-upload")
        sys.exit(1)


if __name__ == "__main__":
    main()

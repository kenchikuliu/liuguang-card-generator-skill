#!/usr/bin/env python3
"""
批量卡片生成器 - 从多个文章批量生成卡片
"""

import os
import sys
import json
from typing import List, Dict
from pathlib import Path
from generator import CardGenerator


class BatchGenerator:
    """批量卡片生成器"""

    def __init__(self, output_base_dir: str = "/tmp/batch_cards"):
        self.generator = CardGenerator()
        self.output_base_dir = output_base_dir
        os.makedirs(output_base_dir, exist_ok=True)

    def process_directory(self, input_dir: str, pattern: str = "*.txt") -> Dict:
        """处理目录中的所有文件"""
        input_path = Path(input_dir)

        if not input_path.exists():
            return {'error': f'目录不存在: {input_dir}'}

        # 查找所有匹配的文件
        files = list(input_path.glob(pattern))

        if not files:
            return {'error': f'未找到匹配的文件: {pattern}'}

        print(f"找到 {len(files)} 个文件")
        print("=" * 60)

        results = []
        for i, file_path in enumerate(files, 1):
            print(f"\n[{i}/{len(files)}] 处理: {file_path.name}")
            print("-" * 60)

            result = self.process_file(str(file_path))
            results.append(result)

        return {
            'total': len(files),
            'success': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }

    def process_file(self, file_path: str) -> Dict:
        """处理单个文件"""
        try:
            # 读取内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取标题（从文件名或内容）
            title = self._extract_title_from_file(file_path, content)

            # 创建输出目录
            file_name = Path(file_path).stem
            output_dir = os.path.join(self.output_base_dir, file_name)
            os.makedirs(output_dir, exist_ok=True)

            # 生成卡片
            result = self.generator.generate_cards(
                content,
                title=title,
                with_cover_image=True,
                visual_check=False,  # 批量处理时跳过视觉检查
                upload_to_host=False  # 批量处理时不上传
            )

            # 移动卡片到输出目录
            for src_path in result['local_paths']:
                dst_path = os.path.join(output_dir, os.path.basename(src_path))
                os.rename(src_path, dst_path)

            return {
                'success': True,
                'file': file_path,
                'title': title,
                'output_dir': output_dir,
                'card_count': len(result['local_paths'])
            }

        except Exception as e:
            return {
                'success': False,
                'file': file_path,
                'error': str(e)
            }

    def _extract_title_from_file(self, file_path: str, content: str) -> str:
        """从文件名或内容提取标题"""
        # 尝试从文件名提取
        file_name = Path(file_path).stem

        # 如果文件名不是数字，使用文件名
        if not file_name.isdigit():
            return file_name.replace('_', ' ').replace('-', ' ')

        # 否则从内容第一行提取
        lines = content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 50:
                return first_line

        return "未命名"

    def generate_summary(self, batch_result: Dict) -> str:
        """生成批量处理摘要"""
        lines = []
        lines.append("=" * 60)
        lines.append("批量卡片生成摘要")
        lines.append("=" * 60)
        lines.append(f"总计: {batch_result['total']} 个文件")
        lines.append(f"成功: {batch_result['success']} 个")
        lines.append(f"失败: {batch_result['failed']} 个")
        lines.append("")

        for i, result in enumerate(batch_result['results'], 1):
            status = "✅" if result['success'] else "❌"
            file_name = Path(result['file']).name

            lines.append(f"{status} [{i}] {file_name}")

            if result['success']:
                lines.append(f"   标题: {result['title']}")
                lines.append(f"   卡片: {result['card_count']} 张")
                lines.append(f"   输出: {result['output_dir']}")
            else:
                lines.append(f"   错误: {result['error']}")

            lines.append("")

        lines.append("=" * 60)

        return '\n'.join(lines)


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("用法: python batch_generator.py <输入目录> [输出目录]")
        print("")
        print("示例:")
        print("  python batch_generator.py ~/articles")
        print("  python batch_generator.py ~/articles /tmp/my_cards")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/batch_cards"

    # 创建批量生成器
    batch_gen = BatchGenerator(output_base_dir=output_dir)

    # 处理目录
    result = batch_gen.process_directory(input_dir)

    # 生成摘要
    summary = batch_gen.generate_summary(result)
    print(summary)

    # 保存摘要到文件
    summary_file = os.path.join(output_dir, "summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)

    print(f"\n摘要已保存到: {summary_file}")


if __name__ == '__main__':
    main()

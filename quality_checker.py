#!/usr/bin/env python3
"""
卡片质量检查器 - 检查生成的卡片是否符合质量标准
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from PIL import Image
import subprocess


@dataclass
class QualityIssue:
    """质量问题"""
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggestion: str


class CardQualityChecker:
    """卡片质量检查器"""

    def __init__(self):
        self.min_width = 400
        self.min_height = 500
        self.max_file_size = 500 * 1024  # 500KB
        self.target_width = 440
        self.target_height = 586

    def check_card(self, card_path: str) -> Dict:
        """检查单张卡片"""
        issues = []

        # 1. 检查文件是否存在
        if not os.path.exists(card_path):
            issues.append(QualityIssue(
                severity='error',
                message='文件不存在',
                suggestion='重新生成卡片'
            ))
            return {'path': card_path, 'passed': False, 'issues': issues}

        # 2. 检查文件大小
        file_size = os.path.getsize(card_path)
        if file_size > self.max_file_size:
            issues.append(QualityIssue(
                severity='warning',
                message=f'文件过大 ({file_size // 1024}KB)',
                suggestion='考虑压缩图片'
            ))

        # 3. 检查图片尺寸
        try:
            with Image.open(card_path) as img:
                width, height = img.size

                if width < self.min_width or height < self.min_height:
                    issues.append(QualityIssue(
                        severity='error',
                        message=f'尺寸过小 ({width}x{height})',
                        suggestion=f'最小尺寸应为 {self.min_width}x{self.min_height}'
                    ))

                if width != self.target_width or height != self.target_height:
                    issues.append(QualityIssue(
                        severity='info',
                        message=f'尺寸不标准 ({width}x{height})',
                        suggestion=f'建议尺寸为 {self.target_width}x{self.target_height}'
                    ))

                # 4. 检查图片模式
                if img.mode not in ['RGB', 'RGBA']:
                    issues.append(QualityIssue(
                        severity='warning',
                        message=f'颜色模式不标准 ({img.mode})',
                        suggestion='建议使用 RGB 或 RGBA 模式'
                    ))

        except Exception as e:
            issues.append(QualityIssue(
                severity='error',
                message=f'无法读取图片: {e}',
                suggestion='检查图片是否损坏'
            ))

        # 5. 视觉检查（使用 Claude Code 的 Read 工具）
        visual_issues = self._visual_check(card_path)
        issues.extend(visual_issues)

        # 判断是否通过
        has_errors = any(i.severity == 'error' for i in issues)
        passed = not has_errors

        return {
            'path': card_path,
            'passed': passed,
            'issues': issues,
            'file_size': file_size,
            'dimensions': (width, height) if 'width' in locals() else None
        }

    def _visual_check(self, card_path: str) -> List[QualityIssue]:
        """视觉检查（需要 AI 辅助）"""
        issues = []

        # 这里可以调用 Claude Code 的 Read 工具来读取图片
        # 并让 AI 判断是否有视觉问题
        # 例如：文字溢出、排版混乱、颜色对比度不足等

        # 暂时返回空列表，实际使用时需要集成 AI 视觉检查
        return issues

    def check_all_cards(self, card_paths: List[str]) -> Dict:
        """检查所有卡片"""
        results = []
        total_passed = 0

        for path in card_paths:
            result = self.check_card(path)
            results.append(result)
            if result['passed']:
                total_passed += 1

        return {
            'total': len(card_paths),
            'passed': total_passed,
            'failed': len(card_paths) - total_passed,
            'results': results
        }

    def generate_report(self, check_result: Dict) -> str:
        """生成检查报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("卡片质量检查报告")
        lines.append("=" * 60)
        lines.append(f"总计: {check_result['total']} 张")
        lines.append(f"通过: {check_result['passed']} 张")
        lines.append(f"失败: {check_result['failed']} 张")
        lines.append("")

        for i, result in enumerate(check_result['results'], 1):
            status = "✅" if result['passed'] else "❌"
            lines.append(f"{status} 卡片 {i}: {os.path.basename(result['path'])}")

            if result['dimensions']:
                w, h = result['dimensions']
                lines.append(f"   尺寸: {w}x{h}")

            lines.append(f"   大小: {result['file_size'] // 1024}KB")

            if result['issues']:
                lines.append("   问题:")
                for issue in result['issues']:
                    icon = "🔴" if issue.severity == 'error' else "⚠️" if issue.severity == 'warning' else "ℹ️"
                    lines.append(f"     {icon} {issue.message}")
                    lines.append(f"        建议: {issue.suggestion}")

            lines.append("")

        lines.append("=" * 60)

        return '\n'.join(lines)


def main():
    """测试"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python quality_checker.py <卡片目录>")
        sys.exit(1)

    card_dir = sys.argv[1]

    # 获取所有卡片
    card_paths = sorted([
        os.path.join(card_dir, f)
        for f in os.listdir(card_dir)
        if f.endswith('.png')
    ])

    if not card_paths:
        print(f"❌ 未找到卡片: {card_dir}")
        sys.exit(1)

    # 检查卡片
    checker = CardQualityChecker()
    result = checker.check_all_cards(card_paths)

    # 生成报告
    report = checker.generate_report(result)
    print(report)

    # 返回状态码
    sys.exit(0 if result['failed'] == 0 else 1)


if __name__ == '__main__':
    main()

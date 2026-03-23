#!/bin/bash
# 流光卡片生成器 v1.2 测试脚本

set -e

SKILL_DIR="$HOME/.claude/skills/liuguang-card-generator"
TEST_DIR="/tmp/liuguang_test"

echo "============================================================"
echo "流光卡片生成器 v1.2 测试"
echo "============================================================"
echo ""

# 1. 准备测试环境
echo "📁 准备测试环境..."
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR/articles"

# 2. 创建测试文章
echo "📝 创建测试文章..."

cat > "$TEST_DIR/articles/article1.txt" << 'EOF'
OpenClaw 是什么？

OpenClaw 是一个开源的 AI Agent 平台。

核心特性：
- 支持多种 AI 模型
- 可扩展的插件系统
- 强大的工作流引擎

"让 AI 更好地服务人类" —— 这是我们的愿景。

通过 OpenClaw，你可以轻松构建自己的 AI 助手。
EOF

cat > "$TEST_DIR/articles/article2.txt" << 'EOF'
AI Agent 开发实践

本文分享 AI Agent 开发的最佳实践。

第一步：选择合适的模型
第二步：设计工作流
第三步：测试和优化

记住：简单就是美。
EOF

echo "✅ 测试文章已创建"
echo ""

# 3. 测试内容分析器
echo "============================================================"
echo "测试 1: 内容分析器"
echo "============================================================"

cat > "$TEST_DIR/test_analyzer.py" << 'EOF'
import sys
sys.path.insert(0, '/Users/Yuki/.claude/skills/liuguang-card-generator')

from content_analyzer import ContentAnalyzer

with open('/tmp/liuguang_test/articles/article1.txt', 'r') as f:
    content = f.read()

analyzer = ContentAnalyzer()
result = analyzer.analyze(content)

print(f"总字数: {result['total_chars']}")
print(f"推荐卡片数: {result['recommended_cards']}")
print(f"结构分析: {result['structure']}")
EOF

python3 "$TEST_DIR/test_analyzer.py"
echo ""

# 4. 测试单个卡片生成
echo "============================================================"
echo "测试 2: 单个卡片生成"
echo "============================================================"

python3 "$SKILL_DIR/generator.py" \
  "$TEST_DIR/articles/article1.txt" \
  --title "OpenClaw 使用指南" \
  --no-cover-image \
  --no-visual-check \
  --no-upload

echo ""

# 5. 测试质量检查
echo "============================================================"
echo "测试 3: 质量检查"
echo "============================================================"

python3 "$SKILL_DIR/quality_checker.py" /tmp/cards
echo ""

# 6. 测试批量生成
echo "============================================================"
echo "测试 4: 批量生成"
echo "============================================================"

python3 "$SKILL_DIR/batch_generator.py" \
  "$TEST_DIR/articles" \
  "$TEST_DIR/output"

echo ""

# 7. 总结
echo "============================================================"
echo "测试完成"
echo "============================================================"
echo ""
echo "📂 测试文件位置:"
echo "   - 单个卡片: /tmp/cards/"
echo "   - 批量卡片: $TEST_DIR/output/"
echo ""
echo "🔍 查看结果:"
echo "   open /tmp/cards/"
echo "   open $TEST_DIR/output/"
echo ""

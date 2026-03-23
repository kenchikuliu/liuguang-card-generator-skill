---
name: liuguang-card-generator
description: |
  流光卡片生成器 v1.3。将博客文章转换为中文 + 英文双语各 6 张卡片，遵循 charlii 卡片规范。
  - 第 1 张：封面（AI 生成图片 + 标题 + 引言）
  - 第 2-6 张：纯文字内容卡片（观点先行，防溢出，自动拆句）
  - 自动翻译生成双语版本，输出到 /tmp/cards/zh/ 和 /tmp/cards/en/
  - 同步生成小红书/微博/Twitter/LinkedIn 社交文案
  - 遵循 CHARLII_SPEC_v1.0.md 排版规范（防溢出 + 中英混排保护）
  使用 Jimeng API 生成封面，流光卡片 API 渲染卡片，Claude API 翻译。
  触发词："生成图文笔记"、"做成卡片"、"生成流光卡片"、"转成卡片"、"博客转卡片"
version: 1.3.0
metadata:
  emoji: "🎴"
  tags:
    - card-generation
    - visual-content
    - blog-to-cards
    - bilingual
    - charlii-spec
  updated: 2026-03-22
---

# 流光卡片生成器 v1.2

将博客文章转换为 6 张精美的图文卡片，适合小红书、微信公众号等平台发布。

## ✨ 核心特性

- 🎨 **AI 封面图片**：使用 Gemini Imagen 3.0 生成专业封面（1:1 方形）
- 📱 **智能内容分割**：自动将文章均匀分为 5 张内容卡片（每张约 310 字节）
- 🖼️ **图片处理**：自动检测并移除文章中的图片（Markdown/HTML 格式）
- 🎯 **纯文字卡片**：内容卡片只显示文字，不嵌入图片，保持简洁
- ✨ **智能排版**：自动识别关键内容（emoji、短标题、冒号结尾）并居中加粗
- 🚀 **一键生成**：从博客文章到图片全自动，保存到 `/tmp/cards/`

## 📋 内容要求

### 推荐长度
- **总字数**：1000-1500 字（约 1500-2500 字节）
- **段落数**：10-20 个段落
- 超过建议长度会有警告，但仍可生成

### 卡片结构
1. **第 1 张（封面）**：
   - 标题（加粗居中，最多 15 字符）
   - AI 生成的视觉图片（Gemini Imagen 3.0）
   - 核心观点/引言（自动提取）
   - 分页：01

2. **第 2-6 张（内容）**：
   - 纯文字内容（不显示标题）
   - 每张约 310 字节（自动均匀分配）
   - 文章中的图片已移除
   - 关键行自动居中加粗
   - 分页：02-06

### 2. 卡片生成流程

#### Step 1: 内容预处理

```python
# 1. 检测并移除图片
from image_handler import ImageHandler
handler = ImageHandler()

# 检测 Markdown 和 HTML 格式的图片
images = handler.extract_images_from_markdown(content)
print(f"检测到 {len(images)} 张图片")

# 移除图片，只保留纯文字
text_only = handler.remove_images_from_content(content)

# 2. 分析内容长度
total_bytes = len(text_only.encode('utf-8'))

# 3. 提取核心观点作为封面
cover_title = extract_title(text_only)
cover_quote = extract_key_quote(text_only)

# 4. 智能分割内容为 5 部分（每张约 310 字节）
content_parts = handler._split_text_only(text_only, num_cards=5, base_capacity=310)
```

**图片处理说明**：
- ✅ 支持 Markdown 格式：`![alt](url)`
- ✅ 支持 HTML 格式：`<img src="url">`
- ✅ 自动移除所有图片标记
- ✅ 保留纯文字内容用于卡片生成
- ⚠️ 图片不会显示在内容卡片上（只有封面有 AI 生成的图片）

#### Step 2: 生成封面图片

使用 Jimeng API 生成封面的视觉图片：

```bash
# 调用 Jimeng API
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "根据内容生成的视觉描述",
    "model": "kolors",
    "aspect_ratio": "3:4",
    "quality": "high"
  }'
```

#### Step 3: 调用流光卡片 API

为每张卡片调用 API：

```bash
# 卡片 1（封面）
curl -X POST https://fireflycard-api.302ai.cn/api/saveImg \
  -F 'form={"icon":"生成的图片URL","title":"<blockquote><p><strong>标题</strong></p></blockquote>","content":"<p>引言内容</p>","pagination":"01"}' \
  -F 'style={"backgroundName":"vertical-blue-color-29","font":"Alibaba-PuHuiTi-Regular","width":440,"height":586}' \
  -F 'temp=tempA'

# 卡片 2-6（内容）
curl -X POST https://fireflycard-api.302ai.cn/api/saveImg \
  -F 'form={"title":"<blockquote><p><strong>小节标题</strong></p></blockquote>","content":"<p>内容</p>","pagination":"02"}' \
  -F 'style={"backgroundName":"vertical-blue-color-29","font":"Alibaba-PuHuiTi-Regular","width":440,"height":586}' \
  -F 'temp=tempA'
```

### 3. 模板配置

#### 默认模板（tempA）

```json
{
  "temp": "tempA",
  "style": {
    "backgroundName": "vertical-blue-color-29",
    "font": "Alibaba-PuHuiTi-Regular",
    "width": 440,
    "height": 586,
    "align": "left"
  }
}
```

#### 可选背景色

```javascript
// 蓝色系
"vertical-blue-color-29"
"vertical-blue-color-30"
"vertical-blue-color-31"

// 渐变色
"vertical-gradient-color-1"
"vertical-gradient-color-2"

// 纯色
"vertical-pure-color-white"
"vertical-pure-color-black"
```

#### 可选字体

```javascript
// 推荐字体
"Alibaba-PuHuiTi-Regular"  // 阿里巴巴普惠体（默认）
"SourceHanSerifCN_Bold"     // 思源宋体粗体
"DouyinSansBold"            // 抖音黑体粗体
"HarmonyOS_Sans_SC_Bold"    // 鸿蒙黑体粗体
```

### 4. 内容格式化

#### HTML 格式规范

```html
<!-- 标题 -->
<blockquote><p><strong>这是标题</strong></p></blockquote>

<!-- 正文段落 -->
<p>这是正文内容。</p>
<p>这是另一段内容。</p>

<!-- 强调 -->
<p><strong>重点内容</strong></p>

<!-- 引用 -->
<blockquote><p>引用的内容</p></blockquote>
```

#### 内容分割策略

```python
def split_content(content: str, num_parts: int = 5) -> list[str]:
    """
    将内容分割成指定数量的部分

    策略：
    1. 按段落分割
    2. 确保每部分长度相近
    3. 保持语义完整性
    4. 每部分不超过 150 字节
    """
    paragraphs = content.split('\n\n')
    parts = []
    current_part = []
    current_bytes = 0
    target_bytes = len(content.encode('utf-8')) // num_parts

    for para in paragraphs:
        para_bytes = len(para.encode('utf-8'))
        if current_bytes + para_bytes > target_bytes and current_part:
            parts.append('\n\n'.join(current_part))
            current_part = [para]
            current_bytes = para_bytes
        else:
            current_part.append(para)
            current_bytes += para_bytes

    if current_part:
        parts.append('\n\n'.join(current_part))

    return parts
```

## 使用示例

### 示例 1: 简单文字内容

**用户输入**：
```
生成图文笔记：

谦卑终将战胜傲慢，开源必将超越闭源，利他终将胜过优绩。

这是一个关于价值观的思考。在当今快速发展的科技世界中，我们常常看到傲慢的巨头被谦卑的创新者超越。

开源社区的力量正在改变世界。从 Linux 到 Kubernetes，从 TensorFlow 到 PyTorch，开源项目正在定义未来。

利他主义不是软弱，而是一种更高级的智慧。当我们帮助他人成功时，我们自己也在成长。
```

**系统处理**：

1. **分析内容**：
   - 总字节数：约 300 字节
   - 核心观点：谦卑、开源、利他
   - 分割为 6 部分

2. **生成封面图片**：
   ```json
   {
     "prompt": "abstract concept of humility defeating arrogance, open source community, altruism, minimalist design, blue gradient background",
     "model": "kolors",
     "aspect_ratio": "3:4"
   }
   ```

3. **生成 6 张卡片**：
   - 卡片 1：封面 + 核心观点
   - 卡片 2：关于傲慢与谦卑
   - 卡片 3：关于开源的力量
   - 卡片 4：开源项目案例
   - 卡片 5：关于利他主义
   - 卡片 6：总结与展望

4. **返回结果**：
   ```
   ✅ 已生成 6 张流光卡片！

   📍 卡片 1（封面）：https://...
   📍 卡片 2：https://...
   📍 卡片 3：https://...
   📍 卡片 4：https://...
   📍 卡片 5：https://...
   📍 卡片 6：https://...

   💾 已保存到：/tmp/cards/
   ```

### 示例 2: 带标题的长文

**用户输入**：
```
生成图文笔记：

标题：AI 时代的思考

正文：
人工智能正在改变我们的生活方式。从智能助手到自动驾驶，从医疗诊断到艺术创作，AI 的应用无处不在。

但我们也需要思考 AI 带来的挑战。隐私保护、算法偏见、就业影响等问题都需要我们认真对待。

未来属于那些能够与 AI 协作的人。我们不应该害怕 AI，而应该学会利用它来增强我们的能力。
```

**系统处理**：

1. **提取标题**：AI 时代的思考
2. **生成封面图片**：AI、未来、科技感
3. **分割内容**：3 个段落 → 5 张内容卡片（部分段落拆分）
4. **生成卡片**：封面 + 5 张内容卡片

## 实现细节

### Python 脚本结构

```python
# /Users/Yuki/.claude/skills/liuguang-card-generator/generator.py

import requests
import json
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Card:
    """卡片数据结构"""
    title: str
    content: str
    pagination: str
    icon: str = ""  # 封面图片 URL（仅第一张）

@dataclass
class CardStyle:
    """卡片样式"""
    backgroundName: str = "vertical-blue-color-29"
    font: str = "Alibaba-PuHuiTi-Regular"
    width: int = 440
    height: int = 586
    align: str = "left"

class CardGenerator:
    """流光卡片生成器"""

    def __init__(self):
        self.api_url = "https://fireflycard-api.302ai.cn/api/saveImg"
        self.jimeng_url = "http://localhost:8001/generate"
        self.template = "tempA"
        self.style = CardStyle()

    def generate_cover_image(self, content: str) -> str:
        """生成封面图片"""
        # 1. 分析内容，提取关键词
        keywords = self._extract_keywords(content)

        # 2. 构建 prompt
        prompt = self._build_image_prompt(keywords)

        # 3. 调用 Jimeng API
        response = requests.post(self.jimeng_url, json={
            "prompt": prompt,
            "model": "kolors",
            "aspect_ratio": "3:4",
            "quality": "high"
        })

        result = response.json()
        return result["data"]["url"]

    def split_content(self, content: str, num_parts: int = 5) -> List[str]:
        """分割内容"""
        # 实现内容分割逻辑
        pass

    def format_html(self, text: str, is_title: bool = False) -> str:
        """格式化为 HTML"""
        if is_title:
            return f'<blockquote><p><strong>{text}</strong></p></blockquote>'
        else:
            paragraphs = text.split('\n\n')
            html_parts = [f'<p>{p}</p>' for p in paragraphs if p.strip()]
            return ''.join(html_parts)

    def generate_card(self, card: Card) -> str:
        """生成单张卡片"""
        form_data = {
            "title": self.format_html(card.title, is_title=True),
            "content": self.format_html(card.content),
            "pagination": card.pagination
        }

        if card.icon:
            form_data["icon"] = card.icon

        style_data = {
            "backgroundName": self.style.backgroundName,
            "font": self.style.font,
            "width": self.style.width,
            "height": self.style.height,
            "align": self.style.align
        }

        response = requests.post(self.api_url, data={
            "form": json.dumps(form_data, ensure_ascii=False),
            "style": json.dumps(style_data),
            "temp": self.template
        })

        result = response.json()
        return result["data"]["url"]

    def generate_cards(self, content: str, title: str = "") -> List[str]:
        """生成完整的 6 张卡片"""
        cards = []

        # 1. 生成封面图片
        cover_image = self.generate_cover_image(content)

        # 2. 创建封面卡片
        cover_title = title or self._extract_title(content)
        cover_quote = self._extract_key_quote(content)

        cards.append(Card(
            title=cover_title,
            content=cover_quote,
            pagination="01",
            icon=cover_image
        ))

        # 3. 分割内容
        content_parts = self.split_content(content, num_parts=5)

        # 4. 创建内容卡片
        for i, part in enumerate(content_parts, start=2):
            cards.append(Card(
                title=f"Part {i-1}",
                content=part,
                pagination=f"{i:02d}"
            ))

        # 5. 生成所有卡片
        card_urls = []
        for card in cards:
            url = self.generate_card(card)
            card_urls.append(url)

        return card_urls

def main():
    """CLI 入口"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python generator.py <内容文件>")
        sys.exit(1)

    content_file = sys.argv[1]
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()

    generator = CardGenerator()
    urls = generator.generate_cards(content)

    print("✅ 已生成 6 张流光卡片！")
    for i, url in enumerate(urls, start=1):
        print(f"📍 卡片 {i}：{url}")

if __name__ == "__main__":
    main()
```

### CLI 使用方式

```bash
# 方式 1: 从文件生成
python /Users/Yuki/.claude/skills/liuguang-card-generator/generator.py content.txt

# 方式 2: 从标准输入
echo "内容" | python /Users/Yuki/.claude/skills/liuguang-card-generator/generator.py -

# 方式 3: 指定标题
python /Users/Yuki/.claude/skills/liuguang-card-generator/generator.py content.txt --title "标题"
```

## 与内容分发集成

生成卡片后，可以直接调用 smart-content-distributor 发布：

```bash
# 1. 生成卡片
python generator.py content.txt

# 2. 分析并推荐平台
# 系统会自动识别这是图文内容，推荐小红书

# 3. 发布到小红书
cd /Users/Yuki/.claude/skills/xiaohongshu-skills
python scripts/cli.py publish \
  --title-file title.txt \
  --content-file content.txt \
  --images card1.jpg card2.jpg card3.jpg card4.jpg card5.jpg card6.jpg
```

## 配置文件

在 `~/.liuguang-card-generator/config.json` 中保存配置：

```json
{
  "api_url": "https://fireflycard-api.302ai.cn/api/saveImg",
  "jimeng_url": "http://localhost:8001/generate",
  "default_template": "tempA",
  "default_style": {
    "backgroundName": "vertical-blue-color-29",
    "font": "Alibaba-PuHuiTi-Regular",
    "width": 440,
    "height": 586
  },
  "jimeng_model": "kolors",
  "jimeng_quality": "high"
}
```

## 依赖

- `requests` - HTTP 请求
- `Jimeng Free API` - 封面图片生成（需要先启动服务）
- `流光卡片 API` - 卡片生成（在线服务）

## 注意事项

1. **字节限制**：总内容不超过 800 字节（包括 tag）
2. **Jimeng 服务**：需要先启动 Jimeng API 服务
3. **图片生成**：封面图片生成可能需要 10-30 秒
4. **API 限制**：流光卡片 API 可能有频率限制
5. **内容分割**：确保每张卡片的内容语义完整

## 快速开始

```bash
# 1. 确保 Jimeng 服务运行
bash ~/.agent-reach/scripts/start-jimeng.sh

# 2. 创建内容文件
cat > /tmp/content.txt << 'EOF'
谦卑终将战胜傲慢，开源必将超越闭源，利他终将胜过优绩。
EOF

# 3. 生成卡片
python /Users/Yuki/.claude/skills/liuguang-card-generator/generator.py /tmp/content.txt

# 4. 查看结果
# 卡片 URL 会打印在控制台
```

---

## 🚀 高级功能（v1.2）

### 1. 智能内容分析器

自动分析文章结构，优化卡片分割：

```bash
python3 ~/.claude/skills/liuguang-card-generator/content_analyzer.py
```

**功能**：
- 自动识别段落类型（标题、引用、列表、正文）
- 计算段落重要性（1-5 分）
- 智能推荐卡片数量
- 保持语义完整性

**示例**：
```python
from content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()
result = analyzer.analyze(content)

print(f"推荐卡片数: {result['recommended_cards']}")
print(f"结构分析: {result['structure']}")

# 智能分割
cards = analyzer.smart_split(result['sections'], result['recommended_cards'])
```

### 2. 卡片质量检查器

检查生成的卡片是否符合质量标准：

```bash
python3 ~/.claude/skills/liuguang-card-generator/quality_checker.py /tmp/cards
```

**检查项**：
- ✅ 文件大小（建议 < 500KB）
- ✅ 图片尺寸（440x586）
- ✅ 颜色模式（RGB/RGBA）
- ✅ 视觉质量（AI 辅助）

**输出示例**：
```
============================================================
卡片质量检查报告
============================================================
总计: 6 张
通过: 6 张
失败: 0 张

✅ 卡片 1: card_01.png
   尺寸: 440x586
   大小: 131KB
```

### 3. 批量卡片生成器

从多个文章批量生成卡片：

```bash
python3 ~/.claude/skills/liuguang-card-generator/batch_generator.py ~/articles
```

**功能**：
- 自动处理目录中的所有 `.txt` 文件
- 为每篇文章创建独立的输出目录
- 生成批量处理摘要
- 跳过视觉检查和上传（提高速度）

**输出结构**：
```
/tmp/batch_cards/
├── article1/
│   ├── card_01.png
│   ├── card_02.png
│   └── ...
├── article2/
│   ├── card_01.png
│   └── ...
└── summary.txt
```

### 4. 集成工作流

#### 与 Smart Content Distributor 集成

生成卡片后，直接发布到小红书：

```bash
# 1. 生成卡片
python3 ~/.claude/skills/liuguang-card-generator/generator.py content.txt

# 2. 发布到小红书
cd ~/.claude/skills/xiaohongshu-skills
python scripts/cli.py publish \
  --title-file title.txt \
  --content-file content.txt \
  --images /tmp/cards/card_01.png /tmp/cards/card_02.png \
           /tmp/cards/card_03.png /tmp/cards/card_04.png \
           /tmp/cards/card_05.png /tmp/cards/card_06.png
```

---

## 📊 性能优化建议

### 1. 内容长度控制

| 卡片数 | 推荐字数 | 每张字数 |
|--------|----------|----------|
| 1 张   | 200-250  | 200-250  |
| 2 张   | 400-500  | 200-250  |
| 3 张   | 600-750  | 200-250  |
| 4 张   | 800-1000 | 200-250  |
| 5 张   | 1000-1250| 200-250  |

### 2. 封面图片生成

- **模型选择**：Gemini Imagen 3.0（高质量）
- **生成时间**：30-60 秒
- **备用方案**：如果 Gemini 失败，自动跳过封面图片

### 3. 批量处理优化

- 跳过视觉检查（`visual_check=False`）
- 跳过图床上传（`upload_to_host=False`）
- 并行处理（未来版本）

---

## 🔧 故障排除

### 问题 1: 卡片文字溢出

**原因**：内容过长，超过卡片容量

**解决**：
1. 减少内容字数（每张 < 250 字）
2. 增加卡片数量
3. 使用内容分析器优化分割

### 问题 2: 封面图片生成失败

**原因**：Gemini API 超时或限流

**解决**：
1. 使用 `--no-cover-image` 跳过封面图片
2. 检查 Gemini API 配置
3. 稍后重试

### 问题 3: 批量处理中断

**原因**：某个文件处理失败

**解决**：
1. 查看 `summary.txt` 找到失败的文件
2. 单独处理失败的文件
3. 检查文件内容是否有特殊字符

---

**版本**: 1.2.0
**创建日期**: 2026-03-19
**最后更新**: 2026-03-20
**作者**: Kiro AI Assistant
**最后更新**: 2026-03-19

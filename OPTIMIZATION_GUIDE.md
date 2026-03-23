# 流光卡片生成器优化指南

基于 cover-design-pro 封面设计系统提炼的关键优化点

## 🎯 核心优化原则（从封面设计提炼）

### 1. 文字是主体
**原则**：文字必须占据页面至少 70% 的空间

**应用到流光卡片**：
- ✅ 已实现：内容卡片不显示标题区域
- ✅ 已实现：隐藏顶部 icon 区域和底部装饰
- ⚠️ 待优化：封面卡片也应该隐藏日期和字数统计

```python
# 当前封面配置（需要优化）
if is_cover:
    switch_config = {
        "showIcon": False,
        "showDate": True,      # ❌ 应该改为 False
        "showTitle": True,
        "showContent": True,
        "showAuthor": False,
        "showTextCount": True,  # ❌ 应该改为 False
        "showQRCode": False,
        "showPageNum": True,
        "showWatermark": False,
        "showIcon2": False
    }
```

### 2. 视觉层次分明
**原则**：运用 3-4 种不同字号创造层次感，主标题字号需要比副标题大三倍以上

**应用到流光卡片**：
- ✅ 已实现：关键行（emoji 标题、短标题）居中加粗
- ⚠️ 待优化：可以增加更多字号层级

```python
# 当前格式化逻辑（可以增强）
def format_html(self, text: str, is_title: bool = False, is_cover: bool = False) -> str:
    if is_title:
        # 标题：加粗 + blockquote
        return f'<blockquote><p><strong>{text}</strong></p></blockquote>'

    # 可以增加：
    # - 超大标题（font-size: 200%）
    # - 大标题（font-size: 150%）
    # - 中标题（font-size: 120%）
    # - 正文（font-size: 100%）
```

### 3. 关键词突出
**原则**：主标题提取 2-3 个关键词，使用特殊处理（描边、高亮、不同颜色）

**应用到流光卡片**：
- ⚠️ 待实现：自动提取关键词并特殊处理
- ⚠️ 待实现：使用不同颜色或背景色高亮关键词

```python
# 新增功能：关键词提取和高亮
def extract_and_highlight_keywords(self, title: str, num: int = 3) -> str:
    """提取关键词并高亮"""
    import re
    words = re.split(r'[，。！？、\s]+', title)
    keywords = [w for w in words if len(w) >= 2][:num]

    # 高亮关键词
    highlighted_title = title
    for keyword in keywords:
        highlighted_title = highlighted_title.replace(
            keyword,
            f'<span style="color: #ff2442; font-weight: 900;">{keyword}</span>'
        )
    return highlighted_title
```

### 4. 内容分割优化
**原则**：每页字数合理，确保语义完整

**应用到流光卡片**：
- ✅ 已实现：MAX_CHARS_PER_PAGE = 150
- ⚠️ 建议优化：降到 120-130 字符

```python
# 当前配置
MAX_CHARS_PER_PAGE = 150  # ❌ 可能太多

# 建议配置
MAX_CHARS_PER_PAGE = 120  # ✅ 更合适
```

### 5. 留白艺术
**原则**：适当留白创造呼吸感，避免视觉拥挤

**应用到流光卡片**：
- ✅ 已实现：padding: 30px
- ⚠️ 待优化：可以根据内容长度动态调整 padding

```python
# 动态 padding
def calculate_padding(self, content_length: int) -> str:
    """根据内容长度计算合适的 padding"""
    if content_length < 100:
        return "40px"  # 内容少，多留白
    elif content_length < 150:
        return "30px"  # 中等内容
    else:
        return "25px"  # 内容多，少留白
```

### 6. 色彩运用
**原则**：使用色彩编码区分不同信息模块

**应用到流光卡片**：
- ✅ 已实现：backgroundName = "vertical-blue-color-29"
- ⚠️ 待实现：根据内容主题自动选择背景色

```python
# 主题色彩映射
THEME_COLORS = {
    "科技": "vertical-blue-color-29",
    "商务": "vertical-gradient-color-1",
    "教育": "vertical-pure-color-white",
    "创意": "vertical-gradient-color-2",
}

def detect_theme(self, content: str) -> str:
    """检测内容主题"""
    if any(word in content for word in ["AI", "科技", "技术", "编程"]):
        return "科技"
    elif any(word in content for word in ["商务", "管理", "战略"]):
        return "商务"
    # ...
    return "科技"  # 默认
```

## 📝 立即可以改的三个关键点

### 优化 1: 封面卡片隐藏日期和字数

```python
# 文件：generator.py
# 位置：~line 290

if is_cover:
    # 第1张封面卡片
    switch_config = {
        "showIcon": False,
        "showDate": False,      # ✅ 改为 False
        "showTitle": True,
        "showContent": True,
        "showAuthor": False,
        "showTextCount": False,  # ✅ 改为 False
        "showQRCode": False,
        "showPageNum": True,
        "showWatermark": False,
        "showIcon2": False
    }
```

### 优化 2: 减少每页字符数

```python
# 文件：generator.py
# 位置：~line 126

# 目标：每页约 100-120 字
MAX_CHARS_PER_PAGE = 120  # ✅ 从 150 改为 120
```

### 优化 3: 封面内容不重复标题

```python
# 文件：generator.py
# 位置：~line 418-426

# 2. 创建封面卡片（特殊处理）
cover_title = title or self._extract_title(content)
cover_quote = self._extract_key_quote(content)  # ✅ 只提取核心观点，不重复标题

cards_data.append(Card(
    title=cover_title,
    content=cover_quote,  # ✅ 不包含标题
    pagination="01",
    icon=cover_image
))
```

## 🚀 进阶优化（可选）

### 1. 关键词自动高亮
```python
def format_html_with_keywords(self, text: str, keywords: List[str]) -> str:
    """格式化 HTML 并高亮关键词"""
    html = self.format_html(text)
    for keyword in keywords:
        html = html.replace(
            keyword,
            f'<span style="color: #ff2442; font-weight: 900;">{keyword}</span>'
        )
    return html
```

### 2. 动态字号层级
```python
def apply_typography_hierarchy(self, text: str) -> str:
    """应用排版层级"""
    lines = text.split('\n')
    html_parts = []

    for line in lines:
        if len(line) < 10:  # 超短行 = 超大标题
            html_parts.append(f'<p style="font-size: 200%; font-weight: 900;">{line}</p>')
        elif line.startswith(('🚀', '✅', '❌')):  # emoji 标题 = 大标题
            html_parts.append(f'<p style="font-size: 150%; font-weight: 700;">{line}</p>')
        elif line.endswith('：'):  # 冒号结尾 = 中标题
            html_parts.append(f'<p style="font-size: 120%; font-weight: 700;">{line}</p>')
        else:  # 正文
            html_parts.append(f'<p>{line}</p>')

    return ''.join(html_parts)
```

### 3. 主题色彩自动选择
```python
def auto_select_background(self, content: str) -> str:
    """根据内容自动选择背景色"""
    theme = self.detect_theme(content)
    return THEME_COLORS.get(theme, "vertical-blue-color-29")
```

## 📊 优化前后对比

### 封面卡片
| 项目 | 优化前 | 优化后 |
|------|--------|--------|
| 日期显示 | ✅ 显示 | ❌ 隐藏 |
| 字数统计 | ✅ 显示 | ❌ 隐藏 |
| 标题重复 | ⚠️ 可能重复 | ✅ 不重复 |
| 文字占比 | ~60% | ~75% |

### 内容卡片
| 项目 | 优化前 | 优化后 |
|------|--------|--------|
| 每页字符数 | 150 | 120 |
| 关键词高亮 | ❌ 无 | ✅ 有 |
| 字号层级 | 2 级 | 4 级 |
| 主题色彩 | 固定 | 自动 |

## 🎨 设计风格参考

从 cover-design-pro 的 10 种风格中，最适合流光卡片的是：

1. **柔和科技卡片风** - 适合科技、AI 主题
2. **流动科技蓝风格** - 适合数据、信息主题
3. **软萌知识卡片风** - 适合教育、分享主题
4. **商务简约信息卡片风** - 适合商务、专业主题

可以考虑在流光卡片中增加风格选择功能。

## 📝 实施计划

### Phase 1: 立即优化（5 分钟）
- [ ] 封面隐藏日期和字数统计
- [ ] 减少每页字符数到 120
- [ ] 确保封面内容不重复标题

### Phase 2: 增强功能（30 分钟）
- [ ] 关键词自动提取和高亮
- [ ] 动态字号层级
- [ ] 主题色彩自动选择

### Phase 3: 风格系统（1 小时）
- [ ] 集成 cover-design-pro 的风格模板
- [ ] 支持用户选择风格
- [ ] 风格预览功能

---

**创建时间**: 2026-03-19
**基于**: cover-design-pro v1.0 封面设计系统

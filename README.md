# 流光卡片生成器 🎴

将博客文章一键转换为中英双语图文卡片，适合小红书、微信公众号、Twitter、LinkedIn 等平台发布。

**Liuguang Card Generator** — Turn any blog article into bilingual (ZH + EN) visual card sets, following the charlii card spec for clean, overflow-safe typography.

---

## ✨ 功能特性

- 📝 **智能内容拆分**：用 Groq / Claude API 将文章拆为 5 张主题分明的内容卡片
- 🎨 **AI 封面图片**：优先用 Jimeng API 生成封面，自动回退到 Gemini image-gen
- 🌍 **中英双语**：自动翻译，同步生成 ZH + EN 两套卡片
- 📐 **charlii 排版规范**：防溢出引擎 + 中英混排保护 + Markdown 富文本渲染
- 📱 **社交文案**：同步生成小红书、微博、Twitter、LinkedIn 文案
- 🔄 **多重回退**：Jimeng → image-gen → Gemini；Groq → Claude API

## 📋 卡片结构

| 卡片 | 内容 |
|------|------|
| 封面（01） | AI 生成图片 + 标题 + 核心观点 |
| 内容（02-06） | 纯文字，观点先行，Markdown 排版 |

## 🚀 快速开始

### 环境变量

```bash
export ANTHROPIC_API_KEY=your_claude_key
export GROQ_API_KEY=your_groq_key          # 可选，用于内容拆分
export GOOGLE_API_KEY=your_gemini_key       # 可选，用于封面图片
```

> Jimeng 封面图片需要本地运行 [jimeng-free-api](https://github.com/binjie09/jimeng-free-api)，监听 `localhost:8001`，并配置 `~/.agent-reach/tools/jimeng-free-api/.env`。

### 安装依赖

```bash
pip install anthropic requests pillow
```

### 生成卡片

```bash
python3 generator.py article.txt

# 指定源语言
python3 generator.py article.txt --source-language zh
python3 generator.py article.txt --source-language en
```

输出路径：
- `/tmp/cards/zh/card_01.png` … `card_06.png`
- `/tmp/cards/en/card_01.png` … `card_06.png`
- `/tmp/cards/zh/social_copy.json`
- `/tmp/cards/en/social_copy.json`

## 📁 文件结构

```
liuguang-card-generator/
├── generator.py              # 主生成器（核心）
├── card_preprocessor.py      # 防溢出排版引擎
├── create_modern_cover.py    # 现代封面生成器
├── image_handler.py          # 图片处理模块
├── social_copy_generator.py  # 社交媒体文案生成
├── translator.py             # 翻译模块
├── content_analyzer.py       # 内容分析器
├── quality_checker.py        # 卡片质量检查
├── batch_generator.py        # 批量生成
├── CHARLII_SPEC_v1.0.md      # 中文排版规范
├── CHARLII_SPEC_EN_v1.0.md   # 英文排版规范
└── SKILL.md                  # Claude Code Skill 定义
```

## 🔧 依赖服务

| 服务 | 用途 | 必须？ |
|------|------|--------|
| [Anthropic Claude API](https://anthropic.com) | 内容拆分、翻译、文案生成 | ✅ 必须 |
| [Groq API](https://groq.com) | 快速内容拆分（llama-3.3-70b） | 可选（有回退） |
| [Firefly Card API](https://fireflycard-api.302ai.cn) | 卡片渲染 | ✅ 必须 |
| Jimeng Free API | AI 封面图片 | 可选（有回退） |
| Google Gemini | 备用封面图片 | 可选 |

## 📐 charlii 卡片规范

卡片内容遵循 [charlii spec](CHARLII_SPEC_v1.0.md)：

- **观点先行**：结论放第一句
- **防溢出**：中文 22 字 / 英文 12 词自动拆行
- **Markdown 富文本**：`**加粗**`、`*斜体*`、`***金句***`、`→` 映射
- **英文居中**：EN 卡片全部居中对齐
- **中英混排保护**：英文单词禁止拆行

## 🎨 Firefly Card API — 模板与样式参数

卡片渲染使用 [302.ai Firefly Card API](https://fireflycard-api.302ai.cn)。

### 模板（`temp`）

目前使用 `tempA`（横向文字卡片）。API 支持多种模板，可在 `generator.py` 的 `CardGenerator.__init__` 中修改：

```python
self.template = "tempA"  # 可选: tempA, tempB, tempC, ...
```

### 背景（`backgroundName`）

当前默认：`vertical-blue-color-29`（蓝色渐变）。根据内容主题可选：

| 主题 | backgroundName | 效果 |
|------|----------------|------|
| 科技（默认） | `vertical-blue-color-29` | 蓝色渐变 |
| 商务 | `vertical-gradient-color-1` | 渐变色 |
| 教育 | `vertical-pure-color-white` | 纯白 |
| 创意 | `vertical-gradient-color-2` | 彩色渐变 |

修改 `generator.py` 中的 `CardStyle`：

```python
class CardStyle:
    backgroundName: str = "vertical-blue-color-29"  # 改这里
    font: str = "Alibaba-PuHuiTi-Regular"
    width: int = 440
    height: int = 586
    align: str = "left"
```

### 字体（`font`）

当前使用 `Alibaba-PuHuiTi-Regular`（阿里巴巴普惠体）。

### 卡片尺寸

固定 `440 × 586`（Portrait，适合手机屏幕和小红书）。

---

## 📄 License

MIT

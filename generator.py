#!/usr/bin/env python3
"""
流光卡片生成器 - 核心实现
将文字内容转换为 6 张精美的图文卡片
"""

import os
import requests
import json
import sys
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from card_preprocessor import preprocess_card_text

# 自动加载本地 .env.local（不提交到 git）
_env_local = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(_env_local):
    for _line in open(_env_local):
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"'))


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
        # 使用 Gemini 生图（通过 msuicode 第三方 API）
        self.gemini_url = "https://www.msuicode.com"
        self.gemini_api_key = os.environ.get("GOOGLE_API_KEY", "")
        self.template = "tempA"  # 使用原来的 tempA 模板
        self.style = CardStyle()

    def generate_cover_image(self, content: str, title: str = "", key_quote: str = "") -> str:
        """生成封面图片 - 优先使用 image-gen skill，失败时回退到 Gemini API"""
        # 1. 构建 prompt（包含标题和核心观点）
        prompt = self._build_image_prompt(content, title, key_quote)

        print(f"🎨 生成封面图片...")
        print(f"   Prompt: {prompt}")

        # 2. 优先尝试使用 Jimeng API（本地服务，速度快）
        import subprocess
        import tempfile
        import os
        import urllib.request
        import json as _json
        from pathlib import Path

        try:
            jimeng_env = Path.home() / ".agent-reach/tools/jimeng-free-api/.env"
            jimeng_token = ""
            if jimeng_env.exists():
                for line in jimeng_env.read_text().splitlines():
                    if line.startswith('JIMENG_TOKEN='):
                        jimeng_token = line.split('=', 1)[1].strip().strip('"')
                        break

            if jimeng_token:
                import http.client as _http
                payload = _json.dumps({
                    "model": "jimeng-image-4.5",
                    "prompt": prompt,
                    "n": 1,
                    "size": "768x1024"
                })
                conn = _http.HTTPConnection("localhost", 8001, timeout=60)
                conn.request("POST", "/v1/images/generations", payload, {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {jimeng_token}"
                })
                resp = conn.getresponse()
                result_data = _json.loads(resp.read().decode('utf-8'))
                conn.close()
                img_url = result_data.get("data", [{}])[0].get("url", "")
                if img_url:
                    # 用 curl 下载图片（绕开 Python 代理）
                    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.png')
                    os.close(tmp_fd)
                    dl = subprocess.run(
                        ["curl", "-sL", "--max-time", "30", "-o", tmp_path, img_url],
                        capture_output=True, timeout=35
                    )
                    if dl.returncode == 0 and os.path.getsize(tmp_path) > 0:
                        print(f"✅ Jimeng 封面图片已保存到: {tmp_path}")
                        return tmp_path
        except Exception as e:
            print(f"⚠️  Jimeng 失败: {e}，尝试 image-gen...")

        # 3. 备用：使用 image-gen skill（Google）
        try:
            # 创建临时文件
            tmp_fd, tmp_path = tempfile.mkstemp(suffix='.png')
            os.close(tmp_fd)

            # 设置环境变量
            env = os.environ.copy()
            env['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY', '')
            env['GOOGLE_BASE_URL'] = 'https://www.msuicode.com'

            # 调用 image-gen skill
            skill_dir = Path.home() / ".claude/skills/image-gen"
            result = subprocess.run(
                ["bun", str(skill_dir / "scripts/main.ts"),
                 "--prompt", prompt,
                 "--image", tmp_path,
                 "--ar", "3:4",
                 "--quality", "2k",
                 "--provider", "google",
                 "--model", "gemini-3.1-flash-image-preview"],
                capture_output=True,
                text=True,
                timeout=180,
                env=env
            )

            if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                print(f"✅ 封面图片已保存到: {tmp_path}")
                return tmp_path
            else:
                print(f"⚠️  image-gen skill 失败，尝试备用方案...")
                print(f"   错误: {result.stderr}")
        except Exception as e:
            print(f"⚠️  image-gen skill 失败: {e}，尝试备用方案...")

        # 3. 备用方案：调用 Gemini API（通过 msuicode 第三方服务）
        import urllib.request
        import ssl
        import base64

        try:
            # 构建 API URL
            model = "gemini-3-pro-image-preview"
            url = f"{self.gemini_url}/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"

            # 构建请求 payload
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "responseModalities": ["IMAGE", "TEXT"]  # 必须大写
                }
            }

            # 创建 SSL context
            ctx = ssl.create_default_context()
            proxy_cert = Path.home() / "proxy-certifi.pem"
            if proxy_cert.exists():
                try:
                    ctx.load_verify_locations(str(proxy_cert))
                except:
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
            else:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            # 发送请求
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Liuguang-Card-Generator/1.0"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120, context=ctx) as response:
                data = json.loads(response.read().decode('utf-8'))

                # 解析响应
                candidates = data.get("candidates", [])
                if not candidates:
                    print(f"❌ 封面图片生成失败: 无候选结果")
                    return ""

                content_data = candidates[0].get("content", {})
                parts = content_data.get("parts", [])

                # 提取图片数据
                image_base64 = None
                for part in parts:
                    if "inlineData" in part:
                        image_base64 = part["inlineData"]["data"]
                        break

                if not image_base64:
                    print(f"❌ 封面图片生成失败: 响应中无图片数据")
                    return ""

                # 保存 base64 图片到临时文件
                import tempfile
                import os

                image_data = base64.b64decode(image_base64)

                # 保存到临时文件
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False, dir='/tmp') as tmp_file:
                    tmp_file.write(image_data)
                    tmp_path = tmp_file.name

                print(f"✅ 封面图片已保存到: {tmp_path}")

                # 返回本地文件路径，后续需要上传
                return tmp_path

        except Exception as e:
            print(f"❌ 封面图片生成失败: {e}")
            return ""

    def _upload_to_picx(self, image_path: str) -> str:
        """上传图片到 PicX 图床"""
        import os
        import subprocess

        try:
            # 使用 GitHub API 上传到 PicX
            result = subprocess.run(
                ["python3", os.path.expanduser("~/.claude/skills/picx-image-host/upload.py"), image_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # 从输出中提取 URL
                output = result.stdout.strip()
                if output.startswith("http"):
                    return output

            print(f"⚠️  PicX 上传失败: {result.stderr}")
            return ""
        except Exception as e:
            print(f"⚠️  PicX 上传失败: {e}")
            return ""

    def _build_image_prompt(self, content: str, title: str = "", key_quote: str = "") -> str:
        """构建图片生成 prompt - 针对内容主题生成吸引人的封面，参考小红书风格"""
        # 提取核心观点作为 prompt 的一部分
        if not key_quote:
            key_quote = self._extract_key_quote(content)

        # 构建包含标题和核心观点的 prompt
        base_context = f"Title: '{title}', Key message: '{key_quote}'" if title else f"Key message: '{key_quote}'"

        # 根据内容主题生成专业的视觉化 prompt
        if "AI Agent" in content or "Agent" in content:
            prompt = f"{base_context}. A futuristic AI robot assistant collaborating with a human developer, holographic interface with flowing data streams, blue and purple neon gradient, modern tech aesthetic, clean minimalist composition, professional studio lighting, 3D rendered style, high quality"
        elif "编程" in content or "开发" in content or "programming" in content.lower() or "开源" in content:
            prompt = f"{base_context}. Abstract visualization of code and programming, flowing colorful code streams forming a network, neural network patterns, blue gradient background, modern minimalist tech aesthetic, clean composition, professional quality"
        elif "PDF" in content or "文档" in content:
            prompt = f"{base_context}. Digital document transformation concept, PDF files converting to editable text with AI magic, clean modern interface, blue gradient background, minimalist design, professional illustration style"
        elif "剪映" in content or "视频" in content or "video" in content.lower():
            prompt = f"{base_context}. Video editing automation concept, timeline with AI-powered effects, modern video editing interface, colorful gradient background, clean professional design, high quality illustration"
        else:
            # 通用科技主题
            prompt = f"{base_context}. Modern tech concept illustration, abstract geometric shapes, blue gradient background, minimalist professional design, clean composition, high quality"

        return prompt

    def _split_content_by_logic(self, content: str, language: str = "zh", base_capacity: int = 310) -> List[Dict]:
        """
        用 AI 把文章按逻辑分割成 5 个主题部分，每部分有标题和内容。
        适合小红书/X 发布的卡片逻辑结构。
        EN 使用 Groq API（避免代理拦截），ZH 使用 Claude API。
        """
        import os, json, requests as _req

        if language == "en":
            prompt = f"""You are the charlii card system content engine. Transform the article into exactly 5 English cards.

CARD ROLES:
- Card 2: Hook — relatable tension, make reader say "this is my problem"
- Card 3: Insight — give the answer early, one clear judgment + 3-part framework
- Card 4: Path A — who it's for, 3 key traits, 1 takeaway line
- Card 5: Path B — contrast with Card 4, who it's for, 3 key traits, 1 takeaway line
- Card 6: Summary — elevate the idea, method + how to use + final line worth remembering

HARD RULES (critical):
1. Max 10 lines per card (count blank lines too)
2. Max 8 words per line
3. NEVER break a word across lines (keep full words intact)
4. No paragraph-style writing — short blocks only
5. Every 2-3 lines: add a blank line (visual break)
6. Each card needs at least 1 contrast (Not X / But Y) and 1 standalone punchline
7. Write in spoken English — direct, confident, minimal
8. Rewrite for English rhythm, do NOT translate literally

FORMAT EXAMPLE (follow this exact rhythm):

You downloaded five AI tools.

Did it help?

Not really.

More tools, more noise.

Not more output.

The problem is not the tool.
The problem is the choice.

CHARLII STRUCTURAL PATTERNS:
- Contrast: "Not X\n\nBut Y" or "X feels right\n\nIt isn't"
- Punchline: short, strong, standalone line (use ***bold italic***)
- List (max 3-4 items): each item ≤ 6 words
- Mapping: "A → ..."

MARKDOWN FORMATTING (required):
- **bold**: 1 key term per block
- *italic*: contrast lines or analogies (1-2 per card)
- ***bold italic***: the single best punchline, standalone line
- ## Heading: section label when needed
- → mapping: replace all explanatory sentences

Article:
{content}

Output ONLY valid JSON array (no markdown fences, no other text):
[
  {{"title": "Hook title (≤6 words)", "content": "short-block content with **bold**, *italic*, ***punchline***"}},
  {{"title": "Insight title (≤6 words)", "content": "short-block content with **bold**, *italic*, ***punchline***"}},
  {{"title": "Path A title (≤6 words)", "content": "short-block content with **bold**, *italic*, ***punchline***"}},
  {{"title": "Path B title (≤6 words)", "content": "short-block content with **bold**, *italic*, ***punchline***"}},
  {{"title": "Summary title (≤6 words)", "content": "short-block content with **bold**, *italic*, ***punchline***"}}
]"""
        else:
            prompt = f"""你是 charlii 卡片系统的内容创作引擎。把博客文章转换成 5 张不溢出、有力量的社交媒体卡片。

## 核心原则：标记路径，不解释路径

卡片不是用来"讲清楚"，而是用来"让人秒懂"。
能一眼扫完 = 合格；需要读 = 太密；需要理解 = 太长；需要停顿 = 会溢出。

❌ 解释式（占满行，容易溢出）：
自动化信息获取适合需要快速获取大量信息的人。

✅ 标记式（省空间，更清晰）：
信息获取 → 快速拿信息

## ✅ 完整示例（参照此格式输出）

```
OpenClaw 的核心价值是：

**自动化信息获取与处理**

---

它可以拆成三条路径：

* 自动化信息获取
* 自动化信息处理
* 自动化决策

---

每一类，对应不同需求：

信息获取 → 快速拿到大量信息
信息处理 → 深度筛选与整理
自动决策 → 快速做出判断

---

***自动化，本质是放大你的效率。***
```

## 5张卡角色分工

**卡2｜问题卡**：让用户感到「这和我有关」
结构：场景 → 痛点 → 误区 → 过渡

**卡3｜结论卡**：直接给判断
结构：一句核心判断（单独成行）+ 三分法映射 + 金句
三分法格式：
A → 做什么
B → 做什么
C → 做什么

**卡4｜方案A卡**：解释第一条路径
结构：适合谁（标签式）+ 特点3条（→映射）+ 一句总结

**卡5｜方案B卡**：解释第二条路径，与卡4形成对比
结构：适合谁（标签式）+ 特点3条（→映射）+ 一句总结

**卡6｜总结卡**：升维+金句
结构：方法论（1-2句）+ 使用方式（标签式）+ 金句（单独成行）

## 防溢出规则（比字数更重要）

卡片占高度 = 行数 × 行高 × 段落密度，不是字数。

规则1：长句→压缩为映射
❌ 自动化信息获取适合需要快速获取大量信息的人
✅ 信息获取 → 快速拿到大量信息

规则2：并列项→统一列表+映射
* 项目A → 做什么
* 项目B → 做什么
* 项目C → 做什么

规则3：每3行必须断块（空行）

规则4：判断句必须单独占行
❌ 自动化是解放生产力的关键。
✅ 自动化，
本质是放大你的效率。

规则5：字数控制在180-240字，行数≤10行正文

## 排版标记
* **加粗**：每段核心词（1个）
* *斜体*：举例类比（每卡1-2次）
* ***加粗斜体***：全卡最核心金句，单独成行（每卡1次）
* → 映射符：替代所有解释性长句
* 空行：每3行强制断块

文章内容：
{content}

只输出 JSON 数组（不要有任何其他内容，不要用代码块）：
[
  {{"title": "😮 问题卡标题（让人感同身受）", "content": "180-240字，场景+痛点+误区+过渡，用标记式"}},
  {{"title": "💡 结论卡标题（给判断）", "content": "180-240字，核心判断+三分法→映射+金句"}},
  {{"title": "🔑 方案A标题", "content": "180-240字，适合谁+特点→映射+总结"}},
  {{"title": "🛠 方案B标题", "content": "180-240字，适合谁+特点→映射+总结"}},
  {{"title": "🎯 总结卡标题", "content": "180-240字，方法论+使用方式+金句单独成行"}}
]"""

        try:
            # 两种语言都用 Groq API，避免 api.kunkunout.cn 代理拦截/挂起
            _GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
            headers = {
                "Authorization": f"Bearer {_GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 6000,
                "temperature": 0.1
            }
            resp = _req.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()

            # 提取 JSON 数组
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                text = text[start:end]
            # 修复 JSON 字符串内的裸换行（LLM 常见问题）
            import re as _re
            def _fix_json_newlines(s):
                """把 JSON 字符串值里的裸换行转为 \\n"""
                result = []
                in_string = False
                escape = False
                for ch in s:
                    if escape:
                        result.append(ch)
                        escape = False
                    elif ch == '\\':
                        result.append(ch)
                        escape = True
                    elif ch == '"':
                        in_string = not in_string
                        result.append(ch)
                    elif in_string and ch == '\n':
                        result.append('\\n')
                    elif in_string and ch == '\r':
                        result.append('\\r')
                    elif in_string and ch == '\t':
                        result.append('\\t')
                    else:
                        result.append(ch)
                return ''.join(result)
            try:
                parts = json.loads(text)
            except json.JSONDecodeError:
                parts = json.loads(_fix_json_newlines(text))

            # 确保恰好5个
            if len(parts) >= 5:
                parts = parts[:5]
            else:
                while len(parts) < 5:
                    parts.append({"title": "", "content": ""})

            # 字数不足时自动扩充
            min_chars = 50 if language == 'en' else 160
            target_range = '6-9 lines, max 8 words per line, short blocks with blank lines between' if language == 'en' else '180-240字（不超过260字）'
            card_roles_zh = ['问题卡：场景+痛点+误区+过渡', '结论卡：核心判断+三分法+金句', '方案A卡：适合谁+3特点+场景+总结', '方案B卡：适合谁+3特点+场景+总结', '总结卡：方法论+使用方式+金句']
            card_roles_en = ['Hook: relatable tension+pain+misconception+bridge (contrast+punchline)', 'Insight: one judgment+3-part framework+standalone punchline', 'Path A: who fits+3 traits→mapping+takeaway line', 'Path B: contrast with A+who fits+3 traits→mapping+takeaway line', 'Summary: elevate idea+method+final line worth remembering']
            for i, part in enumerate(parts):
                c = part.get('content', '')
                if len(c) < min_chars and c.strip():
                    card_role = card_roles_zh[i] if language == 'zh' else card_roles_en[i]
                    if language == 'zh':
                        expand_prompt = f"""你是 charlii 卡片系统的内容创作引擎。
这张卡片草稿太短，请根据以下卡片角色完整重写。

卡片角色：{card_role}
目标格式：{target_range}

硬性规则：
1. 正文行数 ≤ 10 行
2. 每 2-3 行必须断块（空行）
3. 排版标记：**加粗** 核心词，*斜体* 类比举例，***加粗斜体*** 金句单独成行
4. 用 → 映射替代解释性长句
5. 包含至少 1 个对比（不是X / 而是Y）和 1 个独立金句
6. 只输出内容，不要标题，不要 JSON

原草稿（基于这个主题重写）：
{c}"""
                    else:
                        expand_prompt = f"""You are the charlii card system content engine.
This card draft is too short. Rewrite it fully for the following card role.

Card role: {card_role}
Target format: {target_range}

Hard rules:
1. Max 10 lines total
2. Max 8 words per line — split longer lines
3. Every 2-3 lines: blank line (visual break)
4. Use Markdown: **bold** for key terms, *italic* for contrast/analogy, ## for section headers
5. Include at least 1 contrast (Not X / But Y) and 1 standalone punchline (***bold italic***)
6. Direct, confident, spoken English — no filler
7. NEVER break a word across lines
8. Output content only — no title, no JSON

Source draft (use the topic, rewrite the content):
{c}"""
                    try:
                        expand_resp = _req.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": expand_prompt}], "max_tokens": 800, "temperature": 0.2},
                            timeout=30
                        )
                        expand_resp.raise_for_status()
                        expanded = expand_resp.json()["choices"][0]["message"]["content"].strip()
                        if len(expanded) > len(c):
                            parts[i]['content'] = expanded
                            print(f"   📝 卡片{i+2} 已扩充: {len(c)} → {len(expanded)} 字")
                    except Exception as ex:
                        print(f"   ⚠️ 卡片{i+2} 扩充失败: {ex}")

            return parts

        except Exception as e:
            print(f"⚠️  Groq 失败({e})，尝试 Claude API fallback...")
            try:
                import anthropic as _anthropic
                _api_key = os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN')
                _base_url = os.environ.get('ANTHROPIC_BASE_URL')
                _client_kwargs = {"api_key": _api_key}
                if _base_url:
                    _client_kwargs["base_url"] = _base_url
                _claude = _anthropic.Anthropic(**_client_kwargs)
                _model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-5-20250929')
                _msg = _claude.messages.create(
                    model=_model,
                    max_tokens=6000,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = _msg.content[0].text.strip()
                start = text.find('[')
                end = text.rfind(']') + 1
                if start >= 0 and end > start:
                    text = text[start:end]
                # 修复 JSON 字符串内的裸换行
                def _fix_nl(s):
                    res, in_str, esc = [], False, False
                    for ch in s:
                        if esc: res.append(ch); esc = False
                        elif ch == '\\': res.append(ch); esc = True
                        elif ch == '"' and not esc: in_str = not in_str; res.append(ch)
                        elif in_str and ch == '\n': res.append('\\n')
                        elif in_str and ch == '\r': res.append('\\r')
                        else: res.append(ch)
                    return ''.join(res)
                try:
                    parts = json.loads(text)
                except json.JSONDecodeError:
                    parts = json.loads(_fix_nl(text))
                if isinstance(parts, list) and len(parts) > 0:
                    print(f"✅ Claude API fallback 成功，获得 {len(parts)} 张卡片")
                    return parts[:5]
            except Exception as e2:
                print(f"⚠️  Claude API fallback 也失败({e2})，降级为字节切割")
            # 降级：字节切割
            raw_parts = self.split_content(content, num_parts=5, handle_images=False, language=language, base_capacity=base_capacity)
            result = []
            for part in raw_parts:
                lines = part.split('\n')
                title = ""
                body = part
                if lines and lines[0].startswith('#'):
                    title = lines[0].lstrip('#').strip()
                    body = '\n'.join(lines[1:]).strip()
                result.append({"title": title, "content": body})
            while len(result) < 5:
                result.append({"title": "", "content": ""})
            return result[:5]

    def _summarize_content(self, content: str, max_chars: int, language: str) -> str:
        """当内容超长时，智能按段落截取前 max_chars 字节"""
        if len(content) <= max_chars:
            return content
        paragraphs = content.split('\n\n')
        result = []
        total = 0
        for para in paragraphs:
            if total + len(para) + 2 > max_chars:
                break
            result.append(para)
            total += len(para) + 2
        if not result:
            return content[:max_chars]
        return '\n\n'.join(result)

    def _clean_markdown_content(self, content: str) -> str:
        """清理Markdown内容，只保留纯文本"""
        # 如果是 Jina reader 格式，只取 Markdown Content: 之后的正文
        if 'Markdown Content:' in content:
            content = content.split('Markdown Content:', 1)[1].strip()
            # 跳过导航区，找第一个 ## 二级标题（文章正文起点）
            h2_match = re.search(r'^##\s', content, re.MULTILINE)
            if h2_match:
                content = content[h2_match.start():].strip()
        # 移除图片链接
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        # 移除空锚点链接（Jina 常见：[](url) 或 [![](url)](url)）
        content = re.sub(r'\[\]\([^)]*\)', '', content)
        # 移除普通链接，但保留链接文字
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
        # 移除代码块
        content = re.sub(r'```[\s\S]*?```', '', content)
        # 移除行内代码
        content = re.sub(r'`[^`]+`', '', content)
        # 移除标题标记（只移除 # 符号，保留文字和段落结构供 format_html 处理）
        # 注意：不移除 ## 标题标记，因为 format_html 需要它们来渲染居中/加粗效果
        # 移除 Jina 元数据行（Title/URL Source/Published Time/作者/链接等）
        content = re.sub(r'^(Title|URL Source|Published Time|Markdown Content):.*$', '', content, flags=re.MULTILINE)
        # 移除作者信息区块（Jina 常见）
        content = re.sub(r'(\*{0,2}作者[:：]\*{0,2}.*?\n)', '', content)
        content = re.sub(r'(\*{0,2}(Author|链接|Link|Published|Updated)[:：]\*{0,2}.*?\n)', '', content, flags=re.IGNORECASE)
        # 移除纯 URL 行
        content = re.sub(r'^https?://\S+$', '', content, flags=re.MULTILINE)
        # 移除行内裸 URL（链接文字本身就是 URL 的情况）
        content = re.sub(r'https?://\S+', '', content)
        # 移除水平分隔线（--- 或 ***）
        content = re.sub(r'^\s*[-*]{3,}\s*$', '', content, flags=re.MULTILINE)
        # 将 Markdown 表格转换为简洁列表
        def convert_table(m):
            lines = [l.strip() for l in m.group(0).strip().split('\n')]
            # 过滤掉分隔行（只有 | - : 的行）
            data_lines = [l for l in lines if l and not re.match(r'^[|\s\-:]+$', l)]
            result = []
            headers = None
            for i, line in enumerate(data_lines):
                cells = [c.strip() for c in line.strip('|').split('|')]
                cells = [c for c in cells if c]
                if i == 0:
                    headers = cells
                else:
                    if headers and len(cells) == len(headers):
                        result.append(' | '.join(f'{headers[j]}: {cells[j]}' for j in range(len(cells))))
                    else:
                        result.append(' | '.join(cells))
            return '\n'.join(result)
        content = re.sub(r'(\|[^\n]+\|\n)+', convert_table, content)
        # 移除多余的空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()

    def split_content(self, content: str, num_parts: int = None, handle_images: bool = False, language: str = "zh", base_capacity: int = 310) -> List[str]:
        """
        按段落智能分割内容（参考小红书卡片风格）

        卡片容量规划：
        - 卡片 1（封面）：标题 + AI图片 + 引言（约30-50字）
        - 卡片 2-N（内容）：每张 250-300 字

        动态计算卡片数量：
        - 根据总字数自动计算需要的卡片数量
        - 每张卡片目标 280 字（250-300 字范围）
        - 最少 1 张，最多 5 张内容卡片

        参数：
        - content: 内容文本
        - num_parts: 指定卡片数量（None 则自动计算）
        - handle_images: 是否处理内容中的图片（默认 False）
        - language: 语言（"zh" 或 "en"）
        - base_capacity: 每张卡片的基础容量（字节）
        """
        # 如果需要处理图片，使用 ImageHandler
        if handle_images:
            return self._split_content_with_images(content, num_parts, language, base_capacity)

        # 原有的纯文字分割逻辑
        # 先清理Markdown格式
        content = self._clean_markdown_content(content)

        # 先按段落分割，保留段落结构
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if not paragraphs:
            paragraphs = [content.strip()]

        # 计算总字数
        total_chars = sum(len(p) for p in paragraphs)

        print(f"📊 内容分析: 总字数 {total_chars} 字，共 {len(paragraphs)} 个段落")

        # 动态计算卡片数量（如果未指定）
        if num_parts is None:
            chars_per_card = 250  # 目标每张卡片 250 字（避免溢出）
            # 向上取整，确保所有内容都能放入
            calculated_parts = (total_chars + chars_per_card - 1) // chars_per_card
            # 限制在 1-5 张之间
            num_parts = max(1, min(5, calculated_parts))
            print(f"💡 根据内容长度，自动计算需要 {num_parts} 张内容卡片")

        # 定义每张卡片的目标字数（降低到230避免溢出）
        target_chars_per_card = 230

        # 平均分配，所有卡片字数相近
        avg_chars = total_chars // num_parts
        target_chars = [avg_chars] * num_parts

        print(f"📋 目标字数分配: {target_chars}")

        # 按目标字数分配段落
        parts = []
        current_part = []
        current_chars = 0
        part_idx = 0

        for para in paragraphs:
            para_chars = len(para)

            # 如果当前部分已经达到目标字数的 90%，且还有剩余部分
            if current_chars > 0 and current_chars >= target_chars[part_idx] * 0.9 and part_idx < num_parts - 1:
                # 保存当前部分
                parts.append('\n\n'.join(current_part))
                print(f"   卡片 {part_idx + 2}: {current_chars} 字")
                current_part = [para]
                current_chars = para_chars
                part_idx += 1
            else:
                # 继续添加到当前部分
                current_part.append(para)
                current_chars += para_chars

        # 保存最后一部分
        if current_part:
            parts.append('\n\n'.join(current_part))
            print(f"   卡片 {part_idx + 2}: {current_chars} 字")

        # 补齐到 num_parts
        while len(parts) < num_parts:
            parts.append("")

        # 如果超过 num_parts，合并最后几部分
        if len(parts) > num_parts:
            last_parts = parts[num_parts-1:]
            parts = parts[:num_parts-1] + [' '.join(last_parts)]

        # 验证每部分字数，超限时自动截断（按段落截断，保持语义完整）
        max_chars_per_card = 200 if language != "en" else 500
        for i, part in enumerate(parts):
            char_count = len(part)
            if char_count > max_chars_per_card:
                print(f"✂️  卡片 {i+2} 字数过多 ({char_count} 字)，自动截断至 {max_chars_per_card} 字")
                # 按段落截断，保持语义完整
                paras = part.split('\n\n')
                truncated = []
                cur_len = 0
                for p in paras:
                    if cur_len + len(p) > max_chars_per_card:
                        break
                    truncated.append(p)
                    cur_len += len(p)
                parts[i] = '\n\n'.join(truncated) if truncated else part[:max_chars_per_card]
            elif char_count < 50 and i < num_parts - 1:
                print(f"⚠️  卡片 {i+2} 字数偏少 ({char_count} 字)")

        return parts

    def _split_content_with_images(self, content: str, num_parts: int = None, language: str = "zh", base_capacity: int = 310) -> List[str]:
        """
        智能分割内容，考虑图片占用的空间

        Args:
            content: 要分割的内容
            num_parts: 卡片数量
            language: 语言（"zh" 或 "en"）
            base_capacity: 每张卡片的基础容量（字节）

        返回：List[str] - 每张卡片的内容（包含图片标记）
        """
        from image_handler import ImageHandler

        print("🖼️  检测到内容中包含图片，移除图片后分割纯文字内容...")

        handler = ImageHandler()

        # 移除图片，只保留纯文字，并额外清理残余 URL 锚点
        text_only = handler.remove_images_from_content(content)
        # 清理空锚点 [](url) 和带标题的锚点 [](url "title")
        text_only = re.sub(r'\[\]\([^)]*\)', '', text_only)
        # 移除标题标记（## 等）
        text_only = re.sub(r'^#{1,6}\s+', '', text_only, flags=re.MULTILINE)
        # 清理空行
        text_only = re.sub(r'\n{3,}', '\n\n', text_only).strip()

        # 使用纯文字分割（不考虑图片占用）
        if num_parts is None:
            num_parts = 5  # 默认5张内容卡片

        cards = handler._split_text_only(text_only, num_parts, base_capacity)

        print(f"📊 内容分割结果:")
        for i, card in enumerate(cards, 1):
            print(f"   卡片 {i+1}: 文字 {len(card['text'])} 字节")

        # 转换为字符串列表
        result = []
        for card in cards:
            result.append(card['text'])

        # 确保只返回指定数量的卡片
        # 策略：智能合并，确保每张卡片都有足够的内容
        if len(result) > num_parts:
            # 第一步：合并文字太少的卡片（< 200 字节）
            merged_result = []
            i = 0
            while i < len(result):
                current = result[i]
                current_len = len(current.strip())

                # 如果当前卡片文字太少，合并到下一张
                if current_len < 200 and i < len(result) - 1:
                    result[i + 1] = current + '\n\n' + result[i + 1]
                    i += 1
                    continue

                merged_result.append(current)
                i += 1

            result = merged_result

            # 第二步：如果还是太多，均匀合并
            while len(result) > num_parts:
                # 找到最短的两张相邻卡片，合并它们
                min_total = float('inf')
                min_idx = 0
                for i in range(len(result) - 1):
                    total = len(result[i]) + len(result[i + 1])
                    if total < min_total:
                        min_total = total
                        min_idx = i

                # 合并 min_idx 和 min_idx+1
                result[min_idx] = result[min_idx] + '\n\n' + result[min_idx + 1]
                result.pop(min_idx + 1)

        # 如果卡片太少，补充空卡片
        while len(result) < num_parts:
            result.append("")

        # 截断超长内容，防止溢出
        max_chars = 200 if language != "en" else 500
        for i in range(len(result)):
            if len(result[i]) > max_chars:
                print(f"✂️  卡片 {i+2} 字数过多 ({len(result[i])} 字)，自动截断至 {max_chars} 字")
                paras = result[i].split('\n\n')
                truncated = []
                cur_len = 0
                for p in paras:
                    if cur_len + len(p) > max_chars:
                        break
                    truncated.append(p)
                    cur_len += len(p)
                result[i] = '\n\n'.join(truncated) if truncated else result[i][:max_chars]

        return result

    def _generate_cover_title(self, raw_title: str, content: str, language: str = "zh") -> str:
        """用 Groq 生成吸引人的封面标题（去掉 #，简洁有力）"""
        import requests as _req
        _GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
        try:
            if language == "en":
                prompt = f"""Rewrite this article title to be more catchy and engaging for social media (Xiaohongshu/X). Under 20 characters. No hashtags, no markdown. Just the title text.

Original: {raw_title}

Content preview: {content[:200]}

Output ONLY the new title, nothing else."""
            else:
                prompt = f"""将以下文章标题改写得更吸引眼球，适合小红书/X 封面。要求：20字以内，不用 # 符号，不用 Markdown，直接输出标题文字，不要加任何解释。

原标题：{raw_title}

内容摘要：{content[:200]}

只输出新标题，不要有其他内容。"""
            resp = _req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {_GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 100, "temperature": 0.8},
                timeout=15
            )
            resp.raise_for_status()
            new_title = resp.json()["choices"][0]["message"]["content"].strip().strip('"').strip()
            # 去掉可能残留的 # 和 markdown
            import re
            new_title = re.sub(r'^#+\s*', '', new_title).strip()
            if new_title:
                return new_title
        except Exception as e:
            print(f"⚠️  封面标题生成失败: {e}")
        return raw_title

    def _extract_title(self, content: str) -> str:
        """提取标题"""
        lines = content.strip().split('\n')
        if lines:
            first_line = lines[0].strip().lstrip('#').strip()
            if len(first_line) < 50 and not first_line.endswith(('。', '！', '？', '.', '!', '?')):
                return first_line
        return content[:20].lstrip('#').strip() + "..."

    def _extract_key_quote(self, content: str) -> str:
        """提取核心观点作为封面引言（跳过标题行）"""
        lines = content.strip().split('\n')
        # 跳过标题行（# 开头），找第一段正文
        body_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        body = '\n'.join(body_lines)
        sentences = re.split(r'[。！？.!?]', body)
        for s in sentences:
            s = s.strip().lstrip('#').strip()
            if len(s) > 5:
                return s
        return body[:50].strip()

    def _convert_markdown_images_to_html(self, text: str) -> str:
        """将 Markdown 图片语法转换为 HTML img 标签"""
        # 匹配 Markdown 图片：![alt](url)
        pattern = r'!\[(.*?)\]\((.*?)\)'

        def replace_image(match):
            alt = match.group(1)
            url = match.group(2)
            # 生成 HTML img 标签，设置合适的样式
            return f'<p class="text-align-center"><img src="{url}" alt="{alt}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;"></p>'

        return re.sub(pattern, replace_image, text)

    def format_html(self, text: str, is_title: bool = False, is_cover: bool = False, language: str = "zh") -> str:
        """
        格式化为 HTML（参考小红书卡片风格）

        格式规则：
        1. 问号结尾的句子：居中加粗（如"任务简单吗？"）
        2. 小标题（短句，如"用 Microlink"）：居中加粗
        3. 重点句子（包含"是"、"要"等关键词）：斜体
        4. 普通段落：左对齐，自然分段
        5. 段落之间空行
        6. 图片：转换为 HTML img 标签
        """
        if not text:
            return ""

        # 先处理 Markdown 图片语法：![alt](url) -> <img>
        text = self._convert_markdown_images_to_html(text)

        # 修复 LLM 生成的错误 Markdown：*_text_* → *text*
        text = re.sub(r'\*_(.+?)_\*', r'*\1*', text)
        # 修复 **_text_** → **text**
        text = re.sub(r'\*\*_(.+?)_\*\*', r'**\1**', text)

        if is_title:
            # 标题：加粗 + blockquote
            return f'<blockquote><p><strong>{text}</strong></p></blockquote>'

        if is_cover:
            # 封面内容：只有第一行（核心观点）居中加粗
            lines = text.split('\n')
            html_parts = []

            for idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # 只有第一行居中加粗（核心观点）
                if idx == 0:
                    html_parts.append(f'<p class="text-align-center"><strong>{line}</strong></p>')
                else:
                    # 其他内容左对齐，不加粗
                    html_parts.append(f'<p>{line}</p>')

            return ''.join(html_parts)
        else:
            # 内容卡片：先预处理文本（断行、防溢出）
            # 移除 LLM 生成的分隔线 ---，它们不贡献内容但占行数
            text = re.sub(r'\n[-_]{3,}\n', '\n\n', text)
            text = re.sub(r'^[-_]{3,}\n', '', text)
            text = re.sub(r'\n[-_]{3,}$', '', text)
            # 保护 ***...*** / **...** / *...* 跨行不被断开
            md_spans = []
            def _protect_span(m):
                placeholder = f'\uE000{len(md_spans)}\uE001'
                md_spans.append(m.group(0))
                return placeholder
            # 按长到短匹配，避免 *** 被 ** 或 * 误匹配
            text = re.sub(r'\*\*\*[^*]+?\*\*\*', _protect_span, text, flags=re.DOTALL)
            text = re.sub(r'\*\*[^*]+?\*\*', _protect_span, text, flags=re.DOTALL)
            text = re.sub(r'(?<![*])\*[^*\n]+?\*(?![*])', _protect_span, text)
            text = preprocess_card_text(text, language=language, max_chars_per_line_zh=40, max_words_per_line_en=12, max_lines=24)
            for idx, span in enumerate(md_spans):
                text = text.replace(f'\uE000{idx}\uE001', span)
            # 处理 Markdown 格式
            html_parts = []
            lines = text.split('\n')
            i = 0

            def process_inline_markdown(text):
                """处理行内 Markdown 格式（加粗+斜体、加粗、斜体）"""
                # 先处理加粗+斜体（***text***），必须在加粗和斜体之前处理
                text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<strong><em>\1</em></strong>', text)
                # 再处理加粗（**text**）
                text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
                # 最后处理斜体（*text*），但要避免处理列表符号
                text = re.sub(r'(?<!\*)\*(?!\*)([^\*]+?)\*(?!\*)', r'<em>\1</em>', text)
                return text

            while i < len(lines):
                line = lines[i].strip()

                if not line:
                    i += 1
                    continue

                # 处理分隔线 --- 或 ___：跳过，不渲染
                if re.match(r'^[-_]{3,}$', line):
                    i += 1
                    continue

                # 处理标题
                if line.startswith('###'):
                    title = line.replace('###', '').strip()
                    title = process_inline_markdown(title)
                    html_parts.append(f'<p class="text-align-center"><strong>{title}</strong></p>')
                    i += 1
                elif line.startswith('##'):
                    title = line.replace('##', '').strip()
                    title = process_inline_markdown(title)
                    html_parts.append(f'<p class="text-align-center"><strong>{title}</strong></p>')
                    i += 1
                elif line.startswith('#'):
                    title = line.replace('#', '').strip()
                    title = process_inline_markdown(title)
                    html_parts.append(f'<p class="text-align-center"><strong>{title}</strong></p>')
                    i += 1
                # 处理列表项
                elif re.match(r'^[*\-]\s+', line) and not re.match(r'^\*{2,}', line):
                    item = re.sub(r'^[*\-]\s+', '', line).strip()
                    item = process_inline_markdown(item)
                    p_class = 'class="text-align-center"' if language == 'en' else ''
                    html_parts.append(f'<p {p_class}>• {item}</p>' if p_class else f'<p>• {item}</p>')
                    i += 1
                elif line.startswith('✅'):
                    line = process_inline_markdown(line)
                    p_class = 'class="text-align-center"' if language == 'en' else ''
                    html_parts.append(f'<p {p_class}>{line}</p>' if p_class else f'<p>{line}</p>')
                    i += 1
                # 处理代码块
                elif line.startswith('```'):
                    # 跳过代码块
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('```'):
                        i += 1
                    i += 1
                # 处理引用
                elif line.startswith('>'):
                    quote = line.replace('>', '').strip()
                    quote = process_inline_markdown(quote)
                    html_parts.append(f'<blockquote><p><em>{quote}</em></p></blockquote>')
                    i += 1
                # 处理数字列表
                elif re.match(r'^\d+\.\s', line):
                    # 数字序号作为小节标题（加粗居左）
                    item = re.sub(r'^\d+\.\s+', '', line)
                    num = re.match(r'^(\d+)\.', line).group(1)
                    item = process_inline_markdown(item)
                    if language == 'en':
                        html_parts.append(f'<p><strong>{num}. {item}</strong></p>')
                    else:
                        html_parts.append(f'<p><strong>{num}. {item}</strong></p>')
                    i += 1
                # 处理中文序号（一、二、三、四、五、六、七、八、九、十）
                elif re.match(r'^[一二三四五六七八九十]+[、．.]', line):
                    header = process_inline_markdown(line)
                    html_parts.append(f'<p><strong>{header}</strong></p>')
                    i += 1
                # 处理普通段落
                else:
                    line = process_inline_markdown(line)

                    # 判断是否是问句
                    if line.endswith('？') or line.endswith('?'):
                        html_parts.append(f'<p class="text-align-center"><strong>{line}</strong></p>')
                    elif language == 'en':
                        html_parts.append(f'<p class="text-align-center">{line}</p>')
                    else:
                        html_parts.append(f'<p>{line}</p>')
                    i += 1

            html = ''.join(html_parts)
            if language == 'en':
                # EN: 居中对齐，防止单词拆行
                html = f'<div style="text-align:center;word-break:keep-all;overflow-wrap:normal;hyphens:none">{html}</div>'
            else:
                html = f'<div style="word-break:keep-all;overflow-wrap:normal;hyphens:none">{html}</div>'
            return html

    def generate_card(self, card: Card, save_dir: str = "/tmp/cards", is_cover: bool = False, is_last: bool = False, language: str = "zh") -> Optional[str]:
        """生成单张卡片"""
        import os

        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)

        # 准备完整的 form 数据
        from datetime import datetime

        # 封面卡片和内容卡片使用不同的格式
        if is_cover:
            # 封面：显示标题，内容使用特殊格式
            form_data = {
                "title": self.format_html(card.title, is_title=True),
                "content": self.format_html(card.content, is_cover=True),
                "pagination": card.pagination,
            }
            # 封面才显示 icon（AI 生成的图片）
            if card.icon:
                form_data["icon"] = card.icon
        else:
            # 内容卡片：从内容中提取标题
            title = ""
            content_without_title = card.content

            # 尝试从内容第一行提取标题
            lines = card.content.split('\n')
            if lines:
                first_line = lines[0].strip()

                # 检查是否是 Markdown 标题
                if first_line.startswith('#'):
                    # 提取标题文字
                    title = first_line.lstrip('#').strip()
                    # 移除标题行，剩余内容
                    content_without_title = '\n'.join(lines[1:]).strip()
                # 检查是否是加粗文字（可能是标题）
                elif first_line.startswith('**') and first_line.endswith('**'):
                    title = first_line.strip('*').strip()
                    content_without_title = '\n'.join(lines[1:]).strip()

            form_data = {
                "title": self.format_html(title, is_title=True) if title else "",
                "content": self.format_html(content_without_title, language=language),
                "pagination": card.pagination,
            }

            # 最后一张卡片添加作者信息
            if is_last:
                form_data["author"] = "AI博士Charlii"
                form_data["authorDesc"] = "分享AIGC与实用技能"
                form_data["qrcodeText"] = "AI博士Charlii"  # 替换"扫描二维码"文字
                form_data["qrcodeDesc"] = "分享AIGC与实用技能"  # 二维码描述

        style_data = {
            "align": self.style.align,
            "backgroundName": self.style.backgroundName,
            "font": self.style.font,
            "width": self.style.width,
            "height": self.style.height,
            "ratio": "3:4",
            "fontScale": 1,
            "padding": "30px",
            "borderRadius": "15px",
            "color": "#000000",
            "opacity": 1
        }

        print(f"📝 生成卡片 {card.pagination}...")
        print(f"   Title: {card.title[:50] if card.title else '(空)'}...")
        print(f"   Content: {card.content[:80]}...")

        # 创建 switchConfig 来控制显示/隐藏元素
        # 按照用户提供的 JSON 示例配置
        if is_cover:
            # 第1张封面卡片 - 显示 AI 生成的封面图片
            switch_config = {
                "showIcon": True,  # 显示 AI 生成的封面图片
                "showDate": False,  # 隐藏日期
                "showTitle": True,  # 显示标题
                "showContent": True,  # 显示内容（核心观点）
                "showAuthor": False,  # 不显示作者
                "showTextCount": False,  # 隐藏字数统计
                "showQrcode": False,  # 不显示二维码（lowercase）
                "showQRCode": False,  # 不显示二维码（uppercase）
                "showPageNum": True,  # 显示页码
                "showWatermark": False,  # 不显示水印
                "showIcon2": False  # 不显示第二个图标
            }
        elif is_last:
            # 最后一张卡片（只显示作者信息，不显示二维码）
            switch_config = {
                "showIcon": False,
                "showDate": False,
                "showTitle": False,
                "showContent": True,
                "showAuthor": True,  # 显示作者信息
                "showTextCount": True,  # 显示字数统计
                "showQrcode": False,  # 关闭二维码（lowercase）
                "showQRCode": False,  # 关闭二维码（uppercase）
                "showPageNum": True,
                "showWatermark": False,
                "showIcon2": False
            }
        else:
            # 中间内容卡片（2-4张）
            switch_config = {
                "showIcon": False,
                "showDate": False,
                "showTitle": False,
                "showContent": True,
                "showAuthor": False,
                "showTextCount": False,
                "showQrcode": False,  # 隐藏二维码（lowercase）
                "showQRCode": False,  # 隐藏二维码（uppercase）
                "showPageNum": True,
                "showWatermark": False,
                "showIcon2": False
            }

        try:
            payload = {
                "form": form_data,
                "style": style_data,
                "switchConfig": switch_config,  # 添加 switchConfig
                "temp": self.template
            }

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            # API 直接返回 PNG 图片数据，不是 JSON
            if response.headers.get('content-type', '').startswith('image/'):
                # 保存图片到本地
                filename = f"card_{card.pagination}.png"
                filepath = os.path.join(save_dir, filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"✅ 卡片 {card.pagination} 生成成功: {filepath}")
                return filepath
            else:
                # 尝试解析 JSON（以防 API 有时返回 JSON）
                try:
                    result = response.json()
                    if result.get("success") or result.get("code") == 200:
                        if "data" in result:
                            if isinstance(result["data"], dict) and "url" in result["data"]:
                                url = result["data"]["url"]
                            elif isinstance(result["data"], str):
                                url = result["data"]
                            else:
                                url = str(result["data"])
                        else:
                            url = result.get("url", "")

                        print(f"✅ 卡片 {card.pagination} 生成成功: {url}")
                        return url
                    else:
                        print(f"❌ 卡片 {card.pagination} 生成失败: {result}")
                        return None
                except:
                    print(f"❌ 卡片 {card.pagination} 返回了未知格式")
                    return None

        except Exception as e:
            print(f"❌ 卡片 {card.pagination} 生成失败: {e}")
            return None

    def visual_check_card(self, card_path: str) -> dict:
        """视觉检查卡片质量"""
        import subprocess

        print(f"👁️  视觉检查: {card_path}")

        # 使用 Claude Code 的 Read 工具读取图片
        # 这里返回检查结果的结构
        return {
            "path": card_path,
            "status": "pending_review",  # 需要人工确认
            "issues": []
        }

    def _generate_modern_cover(self, title: str, content: str, ai_image_path: str,
                               output_path: str, pagination: str = "01",
                               author: str = "小红书号：charlii", date: str = "",
                               icon_path: str = "") -> str:
        """使用现代风格生成封面卡片"""
        import subprocess
        import os
        from datetime import datetime

        # 获取当前日期
        if not date:
            date = datetime.now().strftime("%Y年%m月%d日")

        script_path = os.path.join(os.path.dirname(__file__), "create_modern_cover.py")

        try:
            result = subprocess.run(
                ["python3", script_path, title, content, ai_image_path, output_path,
                 pagination, author, date, icon_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return output_path
            else:
                print(f"⚠️  现代封面生成失败: {result.stderr}")
                return None

        except Exception as e:
            print(f"⚠️  现代封面生成失败: {e}")
            return None

    def _overlay_cover_image(self, card_path: str, ai_image_path: str) -> str:
        """叠加 AI 图片到封面卡片上"""
        import subprocess
        import os

        overlay_script = os.path.join(os.path.dirname(__file__), "overlay_blog_cover.py")
        output_path = card_path  # 直接覆盖原卡片

        try:
            result = subprocess.run(
                ["python3", overlay_script, card_path, ai_image_path, output_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return output_path
            else:
                print(f"⚠️  叠加失败: {result.stderr}")
                return None

        except Exception as e:
            print(f"⚠️  叠加失败: {e}")
            return None

    def _upload_single_image(self, image_path: str) -> str:
        """上传单张图片到图床，返回 URL"""
        import subprocess
        import os
        import json

        helper_script = os.path.join(os.path.dirname(__file__), "helper.py")

        try:
            result = subprocess.run(
                ["python3", helper_script, "upload", image_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # 从输出中提取 URL
                output = result.stdout
                # 查找 https:// 开头的 URL
                import re
                urls = re.findall(r'https://[^\s]+', output)
                if urls:
                    return urls[0]  # 返回第一个 URL

            return ""

        except Exception as e:
            print(f"⚠️  上传图片失败: {e}")
            return ""

    def upload_to_image_host(self, card_paths: List[str]) -> List[str]:
        """上传卡片到图床"""
        import subprocess
        import os

        print("")
        print("📤 上传卡片到图床...")

        # 调用 helper.py 进行批量上传
        helper_script = os.path.join(os.path.dirname(__file__), "helper.py")

        try:
            result = subprocess.run(
                ["python3", helper_script, "upload"] + card_paths,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                # 解析输出获取 URLs
                # 这里简化处理，实际应该解析 JSON 输出
                print(result.stdout)
                return card_paths  # 暂时返回本地路径
            else:
                print(f"❌ 上传失败: {result.stderr}")
                return card_paths

        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return card_paths

    def _generate_single_language(self, content: str, title: str = "", language: str = "zh",
                                 with_cover_image: bool = True,
                                 visual_check: bool = True, upload_to_host: bool = True,
                                 author_name: str = "", author_bio: str = "",
                                 author_icon: str = "https://cdn.jsdelivr.net/gh/kenchikuliu/picx-images@main/icons/icon.jpg") -> dict:
        """生成单语言的 6 张卡片"""
        import os
        import requests

        # 如果 author_icon 是 URL，下载到本地
        local_icon_path = ""
        if author_icon and author_icon.startswith('http'):
            try:
                local_icon_path = "/tmp/author_icon.jpg"
                if not os.path.exists(local_icon_path):
                    import subprocess as _sp
                    dl = _sp.run(
                        ["curl", "-sL", "--max-time", "5", "-o", local_icon_path, author_icon],
                        capture_output=True, timeout=8
                    )
                    if dl.returncode != 0 or os.path.getsize(local_icon_path) == 0:
                        os.remove(local_icon_path) if os.path.exists(local_icon_path) else None
                        local_icon_path = ""
                        print(f"⚠️  下载 icon 失败，跳过")
                    else:
                        print(f"✅ 已下载 icon: {local_icon_path}")
            except Exception as e:
                print(f"⚠️  下载 icon 失败: {e}")
                local_icon_path = ""
        elif author_icon and os.path.exists(author_icon):
            local_icon_path = author_icon

        print("=" * 60)
        print(f"🎴 开始生成流光卡片（共 6 张）- {language.upper()}")
        print("=" * 60)

        # 根据语言调整容量
        base_capacity = 220 if language == "en" else 310

        # 检查内容长度（清理后的纯文本）
        cleaned_content = self._clean_markdown_content(content)
        total_chars = len(cleaned_content)
        # 只在极端过长时截断（让 Groq 看到完整文章）
        max_chars = 6000

        if total_chars > max_chars:
            print(f"⚠️  内容过长 ({total_chars} 字)，自动压缩至约 {max_chars} 字...")
            cleaned_content = self._summarize_content(cleaned_content, max_chars, language)
            total_chars = len(cleaned_content)
            print(f"✅ 压缩完成: {total_chars} 字")

        cards_data = []

        # 1. 提取标题和核心观点，用 AI 生成吸引人的封面标题
        raw_title = title or self._extract_title(content)
        cover_title = self._generate_cover_title(raw_title, cleaned_content, language)
        # 最多26个字（两行）
        if len(cover_title) > 26:
            cover_title = cover_title[:26]
        key_quote = self._extract_key_quote(content)

        # 2. 生成封面图片（如果需要，传入标题和核心观点）
        cover_image_path = ""
        if with_cover_image:
            cover_image_path = self.generate_cover_image(content, cover_title, key_quote)

        # 3. 创建封面卡片（标题+核心观点，暂时不传 icon）
        cards_data.append(Card(
            title=cover_title,
            content=key_quote,  # 封面显示核心观点/引言
            pagination="01",
            icon=""  # 先不传 icon，后面用 overlay 叠加
        ))

        # 3. 用 AI 按逻辑分割内容为 5 个主题部分
        logic_parts = self._split_content_by_logic(cleaned_content, language=language, base_capacity=base_capacity)

        # 4. 创建内容卡片（第 2-6 张）
        for i in range(5):
            part_data = logic_parts[i] if i < len(logic_parts) else {"title": "", "content": ""}
            card_title = part_data.get("title", "")
            part = part_data.get("content", "")

            # 最后一张卡片添加结尾语
            if i == 4:  # 第6张卡片
                ending = "Thanks for reading!" if language == "en" else "感谢阅读！"
                if part:
                    part = part + f"\n\n{ending}"
                else:
                    part = ending

            cards_data.append(Card(
                title=card_title,
                content=part,
                pagination=f"{i+2:02d}"  # 02, 03, 04, 05, 06
            ))

        # 6. 生成所有卡片
        card_paths = []
        save_dir = f"/tmp/cards/{language}"  # 语言特定目录
        os.makedirs(save_dir, exist_ok=True)
        total_cards = len(cards_data)

        # 封面单独生成（依赖 cover_image_path）
        cover_card = cards_data[0]
        print(f"🎨 生成现代风格封面...")
        cover_path = os.path.join(save_dir, "card_01.png")
        path = self._generate_modern_cover(
            title=cover_card.title,
            content=cover_card.content,
            ai_image_path=cover_image_path,
            output_path=cover_path,
            pagination=cover_card.pagination,
            author=author_name or "小红书号：charlii",
            date="",
            icon_path=author_icon if author_icon.startswith('/') else ""
        )
        if path:
            print(f"✅ 现代封面生成成功: {path}")
            card_paths.append(path)
        else:
            print(f"⚠️  现代封面生成失败，使用备用方案")
            path = self.generate_card(cover_card, save_dir=save_dir, is_cover=True, is_last=False)
            if path and cover_image_path:
                overlay_path = self._overlay_cover_image(path, cover_image_path)
                if overlay_path:
                    path = overlay_path
            if path:
                card_paths.append(path)

        # 内容卡片 02-06 并行生成
        from concurrent.futures import ThreadPoolExecutor, as_completed
        content_cards = cards_data[1:]

        def _gen_content_card(args):
            idx, card = args
            is_last = (idx == total_cards - 1)
            p = self.generate_card(card, save_dir=save_dir, is_cover=False, is_last=is_last, language=language)
            return idx, p

        results = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(_gen_content_card, (i + 1, card)): i + 1
                       for i, card in enumerate(content_cards)}
            for future in as_completed(futures):
                idx, p = future.result()
                results[idx] = p

        # 按顺序追加（保证卡片顺序）
        for i in range(1, total_cards):
            p = results.get(i)
            if p:
                card_paths.append(p)

        print("=" * 60)
        print(f"✅ 完成！共生成 {len(card_paths)} 张卡片")
        print(f"💾 保存位置: {save_dir}")
        print("=" * 60)

        # 6. 视觉检查（如果启用）
        check_results = []
        if visual_check and card_paths:
            print("")
            print("=" * 60)
            print("👁️  开始视觉检查")
            print("=" * 60)
            for path in card_paths:
                result = self.visual_check_card(path)
                check_results.append(result)
            print("=" * 60)
            print("✅ 视觉检查完成")
            print("=" * 60)

        # 7. 上传到图床（如果启用）
        uploaded_urls = []
        if upload_to_host and card_paths:
            uploaded_urls = self.upload_to_image_host(card_paths)

        # 返回完整结果
        return {
            "local_paths": card_paths,
            "uploaded_urls": uploaded_urls if uploaded_urls else card_paths,
            "visual_check": check_results if check_results else None,
            "save_dir": save_dir
        }

    def generate_cards(self, content: str, title: str = "",
                      dual_language: bool = True,
                      source_language: str = "auto",
                      with_cover_image: bool = True,
                      visual_check: bool = False,  # 默认关闭视觉检查以加快速度
                      upload_to_host: bool = False,  # 默认关闭上传以加快速度
                      generate_social_copy: bool = True) -> dict:
        """
        生成双语卡片（v1.3 新功能）

        Args:
            content: 文章内容
            title: 文章标题
            dual_language: 是否生成双语版本（默认 True）
            source_language: 源语言（"zh", "en", "auto"）
            with_cover_image: 是否生成封面图片
            visual_check: 是否进行视觉检查
            upload_to_host: 是否上传到图床
            generate_social_copy: 是否生成社交媒体文案

        Returns:
            {
                "zh": {
                    "cards": [...],
                    "social_copy": {...},
                    "save_dir": "..."
                },
                "en": {
                    "cards": [...],
                    "social_copy": {...},
                    "save_dir": "..."
                }
            }
        """
        import os
        import json
        from translator import Translator
        from social_copy_generator import SocialCopyGenerator

        print("")
        print("=" * 70)
        print("🌍 流光卡片生成器 v1.3 - 双语版本")
        print("=" * 70)

        # 1. 检测语言
        translator = Translator()
        if source_language == "auto":
            detected_lang = translator.detect_language(content)
            print(f"🌐 检测到语言: {detected_lang.upper()}")
        else:
            detected_lang = source_language
            print(f"🌐 源语言: {detected_lang.upper()}")

        target_lang = "en" if detected_lang == "zh" else "zh"

        # 2. 生成源语言版本
        print("")
        print(f"📝 生成 {detected_lang.upper()} 版本...")
        source_result = self._generate_single_language(
            content=content,
            title=title,
            language=detected_lang,
            with_cover_image=with_cover_image,
            visual_check=visual_check,
            upload_to_host=upload_to_host
        )

        result = {detected_lang: source_result}

        # 3. 翻译并生成目标语言版本
        if dual_language:
            try:
                print("")
                print(f"🌐 翻译为 {target_lang.upper()}...")
                # 先压缩内容再翻译，减少 token 消耗
                max_chars = 400 * 5 if target_lang == "en" else 310 * 5
                translate_source = self._clean_markdown_content(content)
                if len(translate_source) > max_chars:
                    translate_source = self._summarize_content(translate_source, max_chars, detected_lang)
                # 分块翻译，每块不超过 400 字
                paragraphs = [p for p in translate_source.split('\n\n') if p.strip()]
                translated_chunks = []
                chunk = ""
                for para in paragraphs:
                    if len(chunk) + len(para) > 400:
                        if chunk:
                            translated_chunks.append(translator.translate_text(chunk.strip(), detected_lang, target_lang))
                            print(f"   ✅ 已翻译 {len(chunk)} 字")
                        chunk = para
                    else:
                        chunk = chunk + "\n\n" + para if chunk else para
                if chunk:
                    translated_chunks.append(translator.translate_text(chunk.strip(), detected_lang, target_lang))
                    print(f"   ✅ 已翻译 {len(chunk)} 字")
                translated_content = "\n\n".join(translated_chunks)

                translated_title = ""
                if title:
                    translated_title = translator.translate_title(title, detected_lang, target_lang)
                    print(f"   标题: {translated_title}")

                print("")
                print(f"📝 生成 {target_lang.upper()} 版本...")
                target_result = self._generate_single_language(
                    content=translated_content,
                    title=translated_title,
                    language=target_lang,
                    with_cover_image=with_cover_image,
                    visual_check=visual_check,
                    upload_to_host=upload_to_host
                )

                result[target_lang] = target_result

            except Exception as e:
                print(f"❌ 目标语言生成失败: {e}")
                print(f"✅ 已生成源语言版本")

        # 4. 生成社交媒体文案
        if generate_social_copy:
            try:
                print("")
                print("📱 生成社交媒体文案...")

                social_gen = SocialCopyGenerator()

                # 源语言文案
                print(f"   {detected_lang.upper()} 平台...")
                source_social = social_gen.generate_all_platforms(content, title, detected_lang)
                result[detected_lang]["social_copy"] = source_social

                # 保存源语言社交文案
                social_copy_file = os.path.join(result[detected_lang]["save_dir"], "social_copy.json")
                with open(social_copy_file, 'w', encoding='utf-8') as f:
                    json.dump(source_social, f, ensure_ascii=False, indent=2)
                print(f"   ✅ 已保存: {social_copy_file}")

                # 目标语言文案
                if dual_language and target_lang in result:
                    print(f"   {target_lang.upper()} 平台...")
                    target_social = social_gen.generate_all_platforms(
                        translated_content, translated_title, target_lang
                    )
                    result[target_lang]["social_copy"] = target_social

                    # 保存目标语言社交文案
                    social_copy_file = os.path.join(result[target_lang]["save_dir"], "social_copy.json")
                    with open(social_copy_file, 'w', encoding='utf-8') as f:
                        json.dump(target_social, f, ensure_ascii=False, indent=2)
                    print(f"   ✅ 已保存: {social_copy_file}")

            except Exception as e:
                print(f"⚠️  社交文案生成失败: {e}")

        # 5. 打印总结
        print("")
        print("=" * 70)
        print("🎉 完成！")
        print("=" * 70)

        total_cards = 0
        for lang, lang_result in result.items():
            if "local_paths" in lang_result:
                card_count = len(lang_result["local_paths"])
                total_cards += card_count
                print(f"   {lang.upper()}: {card_count} 张卡片 → {lang_result['save_dir']}")

        print(f"   总计: {total_cards} 张卡片")
        print("=" * 70)

        return result


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("用法: python generator.py <内容文件> [选项]")
        print("")
        print("选项:")
        print("  --title <标题>           指定标题")
        print("  --no-dual-language       只生成单语言版本")
        print("  --source-language <语言>  指定源语言 (zh/en/auto，默认 auto)")
        print("  --no-cover-image         不生成封面图片")
        print("  --no-social-copy         不生成社交媒体文案")
        print("")
        print("示例:")
        print("  python generator.py content.txt")
        print("  python generator.py content.txt --title '我的标题'")
        print("  python generator.py content.txt --no-dual-language")
        print("  python generator.py content.txt --source-language zh")
        sys.exit(1)

    content_file = sys.argv[1]
    title = ""
    dual_language = True
    source_language = "auto"
    with_cover_image = True
    generate_social_copy = True

    # 解析参数
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--title" and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--no-dual-language":
            dual_language = False
            i += 1
        elif sys.argv[i] == "--source-language" and i + 1 < len(sys.argv):
            source_language = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--no-cover-image":
            with_cover_image = False
            i += 1
        elif sys.argv[i] == "--no-social-copy":
            generate_social_copy = False
            i += 1
        else:
            i += 1

    # 读取内容
    if content_file == "-":
        content = sys.stdin.read()
    else:
        with open(content_file, 'r', encoding='utf-8') as f:
            content = f.read()

    # 生成卡片
    generator = CardGenerator()
    result = generator.generate_cards(
        content,
        title=title,
        dual_language=dual_language,
        source_language=source_language,
        with_cover_image=with_cover_image,
        generate_social_copy=generate_social_copy
    )

    # 输出结果
    print("")
    print("📍 生成结果:")
    for lang, lang_result in result.items():
        print(f"\n{lang.upper()} 版本:")
        if "local_paths" in lang_result:
            for i, path in enumerate(lang_result["local_paths"], start=1):
                print(f"   {i}. {path}")

        if "social_copy" in lang_result:
            social_file = f"{lang_result['save_dir']}/social_copy.json"
            print(f"   社交文案: {social_file}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Charlii 卡片文本预处理引擎（Python 版）
移植自 JS formatCardText，用于在 format_html() 前预处理内容卡片文本
"""
import re
import unicodedata


def preprocess_card_text(text: str, language: str = 'zh',
                         max_chars_per_line_zh: int = 20,
                         max_words_per_line_en: int = 8,
                         max_lines: int = 10) -> str:
    """
    Charlii 卡片文本预处理：
    - 长句拆成短行
    - 英文单词不断词
    - 并列项自动列表化
    - 超过 max_lines 行时压缩废话
    返回处理后的文本（供 format_html 继续处理）
    """
    FILLER_PATTERNS = [
        r'比如说',
        r'某种程度上',
        r'可以帮助你',
        r'这可以',
        r'让你能够',
        r'通过.{1,8}来',
        r'总的来说',
        r'总而言之',
        r'综上所述',
        r'需要注意的是',
        r'值得一提的是',
        r'不用说',
        # English filler
        r'(?i)in many cases[,]?\s*',
        r'(?i)it is important to note that\s*',
        r'(?i)you need to understand that\s*',
        r'(?i)in order to\s+',
        r'(?i)this can help you\s*',
        r'(?i)one of the key things is\s*',
        r'(?i)in other words[,]?\s*',
        r'(?i)it is worth noting that\s*',
        r'(?i)needless to say[,]?\s*',
    ]
    LOW_PRIORITY_PATTERNS = [
        r'^比如[:：]?$',
        r'^让我们来看看[:：]?$',
        r'^并且[，,]',
        r'^另外[，,]',
        r'^可以帮助',
        r'^这可以',
        # English low priority
        r'(?i)^for example[,:]?$',
        r'(?i)^in addition[,]',
        r'(?i)^furthermore[,]',
        r'(?i)^additionally[,]',
        r'(?i)^this can help',
    ]

    def normalize(t):
        t = t.replace('\r\n', '\n').replace('\r', '\n')
        t = re.sub(r'[ \t]+', ' ', t)
        t = re.sub(r'\n{3,}', '\n\n', t)
        for p in FILLER_PATTERNS:
            t = re.sub(p, '', t)
        return t.strip()

    def estimate_visual_len(t):
        length = 0
        for ch in t:
            if '\u4e00' <= ch <= '\u9fff':
                length += 1
            elif ch.isalnum():
                length += 0.55
            else:
                length += 0.5
        return length

    def is_mostly_english(t):
        en = sum(1 for c in t if c.isalpha() and ord(c) < 128)
        zh = sum(1 for c in t if '\u4e00' <= c <= '\u9fff')
        return en > zh

    def wrap_chinese(t, max_chars):
        lines = []
        current = ''
        # 在标点处分割
        tokens = re.split(r'(?<=[，。！？；：、])', t)
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            if estimate_visual_len(current + token) <= max_chars:
                current += token
            else:
                if current:
                    lines.append(current.strip())
                if estimate_visual_len(token) <= max_chars:
                    current = token
                else:
                    # 强制截断
                    rest = token
                    while estimate_visual_len(rest) > max_chars:
                        cut = 0
                        vlen = 0
                        for ch in rest:
                            if vlen + (1 if '\u4e00' <= ch <= '\u9fff' else 0.55) > max_chars:
                                break
                            vlen += 1 if '\u4e00' <= ch <= '\u9fff' else 0.55
                            cut += 1
                        lines.append(rest[:cut].strip())
                        rest = rest[cut:]
                    current = rest
        if current:
            lines.append(current.strip())
        return [l for l in lines if l]

    def wrap_english(t, max_words):
        words = t.split()
        lines = []
        current = []
        for word in words:
            if len(current) < max_words:
                current.append(word)
            else:
                lines.append(' '.join(current))
                current = [word]
        if current:
            lines.append(' '.join(current))
        return lines

    def wrap_mixed(t, max_chars):
        """中英混排：保护英文单词不断行"""
        # 把英文单词和中文分开处理
        parts = re.split(r'([A-Za-z0-9][A-Za-z0-9\-_/+.]*(?:\s+[A-Za-z0-9][A-Za-z0-9\-_/+.]*)*)', t)
        lines = []
        current = ''
        for part in parts:
            if not part:
                continue
            test = current + part
            if estimate_visual_len(test) <= max_chars:
                current = test
            else:
                if current.strip():
                    lines.append(current.strip())
                if estimate_visual_len(part) <= max_chars:
                    current = part.lstrip()
                else:
                    # 英文块太长，按空格换行
                    words = part.split()
                    for word in words:
                        if estimate_visual_len(current + ' ' + word) <= max_chars:
                            current = (current + ' ' + word).strip()
                        else:
                            if current:
                                lines.append(current.strip())
                            current = word
        if current.strip():
            lines.append(current.strip())
        return [l for l in lines if l]

    def is_list_like(sentence):
        s = sentence.rstrip('.。')
        if '、' in s and len(s) > 10:
            if '——' in s or '--' in s:
                return False
            return True
        if re.search(r'包括[:：]?\s*$', s):
            return True
        # English: "X, Y, Z, and W" pattern (3+ comma-separated items)
        if re.search(r'[a-zA-Z]', s):
            commas = s.count(',')
            if commas >= 2 and re.search(r',\s*(?:and|or)\s+\w', s):
                if not re.search(r'(?i)\b(however|but|although|because)\b', s):
                    return True
            if re.search(r'(?i)(can|support|include|allows?|enables?)s?[:：]?\s*$', s):
                return True
        return False

    def convert_list(sentence):
        clean = re.sub(r'包括[:：]?\s*$', '', sentence).strip()
        # English: strip trailing intro phrase
        clean = re.sub(r'(?i)^.*(?:can|support|include|allows?|enables?)[s]?:\s*', '', clean).strip()
        if '、' in clean:
            parts = [p.strip().rstrip('，。') for p in clean.split('、') if p.strip()]
            return ['* ' + p for p in parts]
        # English comma list: "X, Y, Z, and W"
        if re.search(r'[a-zA-Z]', clean) and ',' in clean:
            # Remove trailing "and X" or "or X" then split
            clean_no_conj = re.sub(r',?\s*(?:and|or)\s+([^,]+)$', r', \1', clean)
            parts = [p.strip().rstrip('.') for p in clean_no_conj.split(',') if p.strip()]
            if len(parts) >= 3:
                return ['* ' + p for p in parts]
        return [sentence]

    def split_into_blocks(t):
        raw_paras = [p.strip() for p in t.split('\n') if p.strip()]
        blocks = []
        for para in raw_paras:
            # 按句末标点分句（中文 + 英文句号）
            sentences = re.split(r'(?<=[。！？!?；;])\s*|(?<=[.])\s+(?=[A-Z])', para)
            for s in sentences:
                s = s.strip()
                if not s:
                    continue
                if is_list_like(s):
                    blocks.extend(convert_list(s))
                else:
                    blocks.append(s)
        return blocks

    def wrap_block(block, language):
        if block.startswith('* ') or block.startswith('- '):
            prefix = block[:2]
            content = block[2:].strip()
            if is_mostly_english(content):
                wrapped = wrap_english(content, max_words_per_line_en - 1)
            elif re.search(r'[A-Za-z]', content):
                wrapped = wrap_mixed(content, max_chars_per_line_zh - 2)
            else:
                wrapped = wrap_chinese(content, max_chars_per_line_zh - 2)
            if not wrapped:
                return []
            result = [prefix + wrapped[0]]
            result.extend('  ' + l for l in wrapped[1:])
            return result

        if language == 'en' or is_mostly_english(block):
            return wrap_english(block, max_words_per_line_en)
        elif re.search(r'[A-Za-z]', block):
            return wrap_mixed(block, max_chars_per_line_zh)
        else:
            return wrap_chinese(block, max_chars_per_line_zh)

    def compress_blocks(blocks):
        return [b for b in blocks
                if not any(re.match(p, b) for p in LOW_PRIORITY_PATTERNS)]

    def render(blocks, language):
        lines = []
        for i, block in enumerate(blocks):
            wrapped = wrap_block(block, language)
            if not wrapped:
                continue
            lines.extend(wrapped)
            # 每个块后加空行（除最后一个），但连续列表项之间不加
            if i < len(blocks) - 1 and len(lines) < max_lines:
                next_block = blocks[i + 1] if i + 1 < len(blocks) else ''
                is_list_item = block.startswith('* ') or block.startswith('- ')
                next_is_list = next_block.startswith('* ') or next_block.startswith('- ')
                if not (is_list_item and next_is_list):
                    lines.append('')
        return lines

    def trim_to_max(lines):
        if len(lines) <= max_lines:
            return lines
        trimmed = lines[:max_lines]
        while trimmed and trimmed[-1] == '':
            trimmed.pop()
        if trimmed:
            trimmed[-1] = trimmed[-1].rstrip('，、：;,.').strip()
        return trimmed

    # 主流程
    normalized = normalize(text)
    blocks = split_into_blocks(normalized)

    lines = render(blocks, language)

    if len(lines) > max_lines:
        blocks = compress_blocks(blocks)
        lines = render(blocks, language)

    if len(lines) > max_lines:
        lines = trim_to_max(lines)

    return '\n'.join(lines)


if __name__ == '__main__':
    test = """
自动化是提高社交媒体使用效率的关键。
社交媒体已经成为我们生活中不可或缺的一部分，但过度使用会导致时间浪费。
每天刷社交媒体可能会让你感到信息获取效率低。
低效率的原因包括：信息过载、无关紧要的内容。
自动化可以帮助你解决这个问题。
通过智能筛选和内容聚合，让你更高效地获取有价值的信息。
"""
    result = preprocess_card_text(test)
    print(result)
    print('---')
    print('Lines:', len([l for l in result.split('\n') if l]))

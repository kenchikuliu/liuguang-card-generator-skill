# 🧠 charlii English Card Spec v1.0

**(Production-Level Standard for AI Card Generation)**

---

# 0. Design Goal

This system is designed to generate:

👉 **high-clarity, high-impact English carousel cards**

Not:

* translated content ❌
* paragraph summaries ❌
* blog-style writing ❌

---

## Core Output Standard

Each card must feel like:

👉 a mix of:

* tweet
* slide
* punchline

---

# 1. Card Structure (Fixed)

## Total: 6 Cards

| Card   | Purpose      |
| ------ | ------------ |
| Card 1 | Hook         |
| Card 2 | Relatability |
| Card 3 | Core Insight |
| Card 4 | Path A       |
| Card 5 | Path B       |
| Card 6 | Summary      |

---

# 2. Global Constraints (Hard Rules)

## 2.1 Line Constraints

```text
MAX_LINES = 10
IDEAL_LINES = 6–9
```

---

## 2.2 Words per Line

```text
MIN_WORDS = 2
MAX_WORDS = 8
IDEAL = 4–6
```

---

## 2.3 Blocks per Card

```text
MIN_BLOCKS = 3
MAX_BLOCKS = 6
```

Each block:

* 1–2 lines max
* must be visually separable

---

## 2.4 Word Break Rules (Critical)

❌ Never allowed:

* auto / mation
* work / flow
* produc / tivity

✅ Must:

* keep full words intact
* wrap by word, not character

---

# 3. Writing Style Rules

## 3.1 Not Translation — Rewriting Required

All English output must be:

👉 rewritten, not translated

---

## 3.2 Sentence Rules

Each sentence must:

* express only ONE idea
* be ≤ 12 words
* avoid nested clauses

---

## 3.3 Tone

Use:

* direct
* confident
* minimal
* conversational

Avoid:

* academic tone
* passive voice
* filler phrases

---

## 3.4 Forbidden Patterns

Remove:

* "Many people think that"
* "It is important to note that"
* "In order to"
* "This can help you"
* "One of the key things is"

---

# 4. Rhythm Rules (MOST IMPORTANT)

English cards must follow:

## 4.1 Break Rhythm

Every card must include:

* frequent line breaks
* visible spacing
* no paragraph blocks

---

## 4.2 Contrast Structure

Preferred format:

```text
Not X

But Y
```

or

```text
X feels right

It isn't
```

---

## 4.3 Punchline Placement

Each card must include:

👉 at least ONE standalone punchline

Format:

```text
Short
Strong
Standalone
```

---

# 5. Structural Patterns

## 5.1 Hook Pattern (Card 1)

```text
More X
Less Y?

Something is off
```

or

```text
X should lead to Y

Right?

Wrong
```

---

## 5.2 Relatability Pattern (Card 2)

```text
You did X

You tried Y

Did it work?

Not really
```

---

## 5.3 Insight Pattern (Card 3)

```text
The problem is not X

It is Y
```

---

## 5.4 List Pattern

Max 3–4 items:

```text
- X
- Y
- Z
```

Each item: ≤ 6 words

---

## 5.5 Framework Pattern

```text
There are 3 ways

A → ...
B → ...
C → ...
```

---

## 5.6 Summary Pattern

```text
X is not the answer

Y is

Remember this
```

---

# 6. Compression Engine (Required for Overflow)

## Trigger

```text
IF line_count > MAX_LINES
```

## Compression Order

1. Remove filler phrases
2. Shorten sentences
3. Convert to list
4. Remove secondary ideas
5. Keep only core message

---

# 7. Layout Engine Rules

## 7.1 No Paragraph Mode

❌ Not allowed:

```text
This is a long paragraph that spans multiple lines...
```

## 7.2 Block Separation

Each block must be separated by at least one empty line.

## 7.3 Emphasis Rules

* max 2 emphasized lines per card
* emphasis = bold / caps / isolation

---

# 8. English-Specific Enhancements

## 8.1 Prefer Verbs Over Nouns

❌ Weak: efficiency improvement

✅ Better: work faster / waste less

---

## 8.2 Prefer Short Words

❌ utilize / leverage

✅ use / build

---

## 8.3 Prefer Spoken English

Cards should sound like something you would say out loud.

---

# 9. Quality Validation Checklist

## Readability
* Can be scanned in <3 seconds
* No re-reading needed

## Structure
* No block > 2 lines
* No sentence > 12 words

## Impact
* At least 1 punchline
* At least 1 contrast

## Layout
* ≤ 10 lines
* ≥ 2 spacing breaks

---

# 10. Output Format (for API)

```json
{
  "cards": [
    {
      "type": "cover",
      "title": ["More tools", "Less efficiency?"],
      "subtitle": ["Something is off", "Let's fix it"]
    },
    {
      "type": "content",
      "blocks": [
        "You downloaded",
        "five AI tools",
        "",
        "Did it help?",
        "Not really"
      ]
    }
  ]
}
```

---

# 11. Prompt Template (Production Ready)

```text
SYSTEM PROMPT

Generate a 6-card English carousel using the charlii system.

Requirements:
- Rewrite, do not translate
- Opinion-led, not explanation-led
- Max 10 lines per card
- Max 8 words per line
- Break sentences into short blocks
- No paragraph-style writing
- No broken words
- Use natural spoken English
- Include contrast and punchlines
- Each card must be scannable in 3 seconds
```

---

# Core Principle

👉 **English cards are not written.
They are designed.**

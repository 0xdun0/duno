# Sierra - Filing Cabinet

**Status:** ✅ Complete

## Description

A collection of cryptography challenges stored in EverSec's digital filing cabinet. Five documents, each protected by a different encoding or cipher — increasing in difficulty. All solvable with CyberChef.

**Category:** Cryptography
**Difficulty:** Easy → Hard
**Total Points:** 1,400 (5 flags)

## Challenge Information

- **Type:** Static file analysis
- **Port:** 4013
- **Tools Needed:** CyberChef, jwt.io (or any JWT decoder)

## Files Overview

| File | Technique | Points |
|------|-----------|--------|
| crypto1.txt | Base64 | 100 |
| crypto2.txt | Hex + Reverse | 150 |
| crypto3.txt | Decimal → Binary → word substitution | 300 |
| crypto4.txt | ROT13 → JWT decode | 350 |
| crypto5.txt | ROT8000 | 400 |
| **Total** | | **1,300** |

## Setup

### Using Docker Compose (Recommended)

```bash
docker compose up -d sierra-filing-cabinet
```

### Using Docker Directly

```bash
docker build -t sierra-filing-cabinet .
docker run -p 4013:80 sierra-filing-cabinet
```

Files available at `http://localhost:4013/`

## Solution

<details>
<summary>Click to reveal solution</summary>

### crypto1.txt — Base64 (100 points)

**Cipher:** `Y3J5cHQwX3c0cnIxMHI=`

**CyberChef Recipe:** From Base64

```bash
echo "Y3J5cHQwX3c0cnIxMHI=" | base64 -d
```

**Flag:** `crypt0_w4rr10r`

---

### crypto2.txt — Hex + Reverse (150 points)

**Cipher:** `46 27 16 a7 13 77 f5 33 46 03 36`

**CyberChef Recipe:** Reverse → From Hex

The hex string is reversed character-by-character. Reverse it first, then decode from hex.

Reversed: `63 30 64 33 5f 77 31 7a 61 72 64`

**Flag:** `c0d3_w1zard`

---

### crypto3.txt — Decimal → Binary → Word substitution (300 points)

**Cipher:** 41 space-separated groups where each bit is spelled out as "zero" or "one"

**What's happening:**
1. Flag → ASCII decimal values: `116 51 99 104 110 48 109 97 110 99 51 114`
2. Each character of that decimal string → 8-bit binary
3. Every `0` bit → `zero`, every `1` bit → `one`
4. Each byte's bits joined into one word, bytes space-separated

**CyberChef Recipe (to solve):**
1. Find/Replace: `zero` → `0` (simple string, not regex)
2. Find/Replace: `one` → `1` (simple string, not regex)
3. From Binary (byte length 8, space as delimiter)
4. From Decimal (space as delimiter)

**Flag:** `t3chn0manc3r`

---

### crypto4.txt — ROT13 → JWT decode (350 points)

**Cipher:** `rlWuoTpvBvWVHmV1AvVfVaE5pPV6VxcKIPW9.rlWmqJVvBvVkZwZ0AGL3BQxjVvjvozSgMFV6VaDmL2usLKWwnQA0rKNmplVfVzSxoJyhVwc0paIyYPWcLKDvBwR1ZGLlZmxjZwW9.sKcIdoYblm4D-7ln7Rc6BklYI-l_OftdhgL0zB9NZoZ`

The three `.`-separated sections are a tell — this is a ROT13-encoded JWT.

**CyberChef Recipe:**
1. ROT13
2. JWT Decode (or paste the result into jwt.io)

After ROT13 you get a valid JWT. The flag is in the `flag` field of the decoded payload.

**Flag:** `t3ch_arch3typ3s`

---

### crypto5.txt — ROT8000 (500 points)

**Cipher:** `籶簽籪簾籴簼籭籨籭簽籷籬簼类`

ROT8000 is a Unicode rotation cipher — the Unicode equivalent of ROT13, rotating across Unicode character blocks including CJK characters.

**CyberChef Recipe:** ROT8000

Or use the ROT8000 tool directly: https://rot8000.com/

**Flag:** `m4a5k3d_d4nc3r`

</details>

## Hints

> Share progressively — start with Hint 1.

<details>
<summary>Hint 1 — crypto1</summary>
The `=` padding at the end is a strong hint about the encoding scheme. Every modern decoder supports it.
</details>

<details>
<summary>Hint 2 — crypto2</summary>
The output of "From Hex" on this file looks backwards. Try reversing the input string first.
</details>

<details>
<summary>Hint 3 — crypto3</summary>
Read the words literally — they spell out binary digits. Once you have the bits, what format are the decoded bytes in?
</details>

<details>
<summary>Hint 4 — crypto4</summary>
Notice the two dots in the file? That structure is familiar in web authentication. But you need one step before you can decode it.
</details>

<details>
<summary>Hint 5 — crypto5</summary>
ROT13 rotates through 26 Latin letters. What if you applied the same concept to the entire Unicode character space?
</details>

## Flag Summary

```
FLAG 1: crypt0_w4rr10r    (100 pts) — Base64
FLAG 2: c0d3_w1zard       (150 pts) — Hex + Reverse
FLAG 3: t3chn0manc3r      (300 pts) — Decimal → Binary → word substitution
FLAG 4: t3ch_arch3typ3s   (350 pts) — ROT13 → JWT decode
FLAG 5: m4a5k3d_d4nc3r    (400 pts) — ROT8000
```

Total: **1,300 points** across 5 flags

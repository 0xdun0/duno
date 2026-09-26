## Solution

<details>
<summary>Click to reveal solution</summary>

### crypto1.txt — Base64 (100 points)

**Cipher:** `Y3J5cHQwX3c0cnIxMHI=`

**CyberChef Recipe:** From Base64

```bash
echo "Y3J5cHQwX3c0cnIxMHI=" | base64 -d
```

**Flag:** `DUNO{a36d0716573744a292e6aaf889fd59ae}`

---

### crypto2.txt — Hex + Reverse (150 points)

**Cipher:** `46 27 16 a7 13 77 f5 33 46 03 36`

**CyberChef Recipe:** Reverse → From Hex

The hex string is reversed character-by-character. Reverse it first, then decode from hex.

Reversed: `63 30 64 33 5f 77 31 7a 61 72 64`

**Flag:** `DUNO{f04a41a356065a91ac2e3a525b9b0ce0}`

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

**Flag:** `DUNO{32380a271e4eeb502fa7227d548726c6}`

---

### crypto5.txt — ROT8000 (500 points)

**Cipher:** `籶簽籪簾籴簼籭籨籭簽籷籬簼类`

ROT8000 is a Unicode rotation cipher — the Unicode equivalent of ROT13, rotating across Unicode character blocks including CJK characters.

**CyberChef Recipe:** ROT8000

Or use the ROT8000 tool directly: https://rot8000.com/

**Flag:** `DUNO{a7c6105e24aba57b619f3da3cfec9d34}`

</details>
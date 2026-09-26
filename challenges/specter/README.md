# Quebec - Web Enumeration Challenge

**Status:** ✅ Complete

## Player Description

Welcome to EverSec Security Solutions' corporate website! Our web development team built this beautiful site in just one sprint (we're agile!). We left lots of helpful files around to make development easier - robots.txt so search engines know what to index, sitemap.xml for navigation, backup folders in case we need to roll back, and .git for version control right on production because that's where the code is! Our CTO said something about "attack surface" but we think he meant "helpful surface" for our users. We also expose our .env file because "environment" variables should be visible in the environment, right? That's just logical! Plus we have tons of admin panels, API documentation, and debug endpoints - all wide open because we believe in transparency and we trust our users!

## Technical Description

**Category:** Web Security / Reconnaissance
**Difficulty:** Medium
**Points:** 750 (15 flags × 50 points each)
**Port:** 4018

A comprehensive web enumeration challenge featuring 15 flags hidden in realistic locations that penetration testers commonly discover during reconnaissance. This challenge tests your ability to thoroughly enumerate web applications using various techniques and tools.

Can you find all 15 flags hidden across this corporate website?

## Learning Objectives

- Performing comprehensive web application enumeration
- Using common enumeration tools (gobuster, dirb, nikto, ffuf, etc.)
- Discovering sensitive files and directories
- Analyzing HTTP headers and responses
- Reading robots.txt and sitemap.xml
- Finding exposed version control systems (.git)
- Identifying backup files and directories
- Discovering administrative interfaces
- Analyzing HTML source code and comments
- Using timing attacks to identify hidden endpoints
- Understanding common misconfigurations

## Flags

All flags are worth **50 points each** (750 total):

1. **FLAG 1** (50 pts) - Found in robots.txt
2. **FLAG 2** (50 pts) - Found in sitemap.xml
3. **FLAG 3** (50 pts) - Exposed .git directory
4. **FLAG 4** (50 pts) - Backup directory with sensitive files
5. **FLAG 5** (50 pts) - Admin login panel discovery
6. **FLAG 6** (50 pts) - Environment configuration file
7. **FLAG 7** (50 pts) - API documentation endpoint
8. **FLAG 8** (50 pts) - Debug endpoint with system information
9. **FLAG 9** (50 pts) - Custom HTTP response header
10. **FLAG 10** (50 pts) - HTML source code comment
11. **FLAG 11** (50 pts) - crossdomain.xml policy file
12. **FLAG 12** (50 pts) - security.txt in .well-known
13. **FLAG 13** (50 pts) - PHP info page
14. **FLAG 14** (50 pts) - Server status page
15. **FLAG 15** (50 pts) - Timing-based endpoint discovery

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
docker compose up -d quebec-enumeration
docker compose logs -f quebec-enumeration
docker compose down quebec-enumeration
```

### Local Development

```bash
cd Challenges/quebec-enumeration
pip install -r requirements.txt
python app.py
```

Access at: http://localhost:4018

## Solution

### FLAG 1: robots.txt (50 points)

One of the first files to check on any web application:

```bash
curl http://localhost:4018/robots.txt
```

**Response:**
```
User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /api/
Disallow: /.git/

# r0b0ts_txt_t3lls_s3cr3ts
```

**FLAG 1:** `r0b0ts_txt_t3lls_s3cr3ts`

---

### FLAG 2: sitemap.xml (50 points)

Check for XML sitemap commonly used for SEO:

```bash
curl http://localhost:4018/sitemap.xml
```

**Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>http://eversec.com/</loc>
        <lastmod>2026-01-15</lastmod>
        <priority>1.0</priority>
    </url>
    <!-- s1t3m4p_sh0ws_structur3 -->
    <!-- More URLs... -->
</urlset>
```

**FLAG 2:** `s1t3m4p_sh0ws_structur3`

---

### FLAG 3: Exposed .git Directory (50 points)

Check if version control is exposed:

```bash
curl http://localhost:4018/.git/HEAD
```

**Response:**
```
ref: refs/heads/main
# This shouldn't be here!
# g1t_3xp0sur3_1s_b4d
```

**FLAG 3:** `g1t_3xp0sur3_1s_b4d`

---

### FLAG 4: Backup Directory (50 points)

Common backup locations:

```bash
curl http://localhost:4018/backup/
```

**Response:**
```html
<h1>Backup Files</h1>
<ul>
    <li><a href="database.sql.bak">database.sql.bak</a></li>
    <li><a href="config.php.bak">config.php.bak</a></li>
</ul>
<!-- Flag: b4ckup_f1l3s_l34k_d4t4 -->
```

**FLAG 4:** `b4ckup_f1l3s_l34k_d4t4`

---

### FLAG 5: Admin Login Panel (50 points)

Discover hidden admin panels:

```bash
curl http://localhost:4018/admin/login
```

**Response:**
```html
<h1>EverSec Admin Login</h1>
<form method="POST">
    <input type="text" name="username" placeholder="Username">
    <input type="password" name="password" placeholder="Password">
    <button type="submit">Login</button>
</form>
<!-- Flag: h1dd3n_4dm1n_p4n3ls -->
```

**FLAG 5:** `h1dd3n_4dm1n_p4n3ls`

---

### FLAG 6: Environment File (50 points)

Check for exposed .env files:

```bash
curl http://localhost:4018/.env
```

**Response:**
```
DATABASE_URL=postgresql://admin:password@localhost/eversec
SECRET_KEY=super-secret-key-12345
API_KEY=prod-api-key-67890

# Flag: 3nv_f1l3s_c0nt41n_s3cr3ts
```

**FLAG 6:** `3nv_f1l3s_c0nt41n_s3cr3ts`

---

### FLAG 7: API Documentation (50 points)

Find exposed API documentation:

```bash
curl http://localhost:4018/api/docs
```

**Response:**
```json
{
  "api_version": "v1.0",
  "endpoints": [
    "/api/users",
    "/api/products",
    "/api/orders"
  ],
  "flag": "4p1_d0cs_r3v34l_3ndp01nts"
}
```

**FLAG 7:** `4p1_d0cs_r3v34l_3ndp01nts`

---

### FLAG 8: Debug Endpoint (50 points)

Check for debug interfaces:

```bash
curl http://localhost:4018/debug
```

**Response:**
```json
{
  "debug_mode": true,
  "python_version": "3.11.0",
  "flask_version": "3.0.0",
  "environment": "production",
  "flag": "d3bug_m0d3_3xp0s3s_1nf0"
}
```

**FLAG 8:** `d3bug_m0d3_3xp0s3s_1nf0`

---

### FLAG 9: HTTP Headers (50 points)

Examine HTTP response headers:

```bash
curl -I http://localhost:4018/
```

**Look for custom headers:**
```
HTTP/1.1 200 OK
Server: nginx/1.21.0
X-EverSec-Version: http_h34d3rs_h1d3_d4t4
Content-Type: text/html; charset=utf-8
```

**FLAG 9:** `http_h34d3rs_h1d3_d4t4`

---

### FLAG 10: HTML Comments (50 points)

View page source and search for comments:

```bash
curl http://localhost:4018/ | grep -o "<!--.*-->"
```

**Response:**
```html
<!-- Developer TODO: Remove this before going live! -->
<!-- Flag: html_c0mm3nts_l34k -->
```

**FLAG 10:** `html_c0mm3nts_l34k`

---

### FLAG 11: crossdomain.xml (50 points)

Check for Flash crossdomain policy:

```bash
curl http://localhost:4018/crossdomain.xml
```

**Response:**
```xml
<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
    <allow-access-from domain="*" />
    <!-- Flag: cr0ssd0m41n_p0l1cy_f0und -->
</cross-domain-policy>
```

**FLAG 11:** `cr0ssd0m41n_p0l1cy_f0und`

---

### FLAG 12: security.txt (50 points)

Check for security contact information:

```bash
curl http://localhost:4018/.well-known/security.txt
```

**Response:**
```
Contact: security@eversec.com
Expires: 2027-12-31T23:59:59.000Z
Preferred-Languages: en
Canonical: https://eversec.com/.well-known/security.txt

# Flag: s3cur1ty_txt_c0nt4ct
```

**FLAG 12:** `s3cur1ty_txt_c0nt4ct`

---

### FLAG 13: PHP Info Page (50 points)

Check for information disclosure pages:

```bash
curl http://localhost:4018/phpinfo.php
```

**Response:**
```html
<h1>System Information</h1>
<pre>
Python Version: 3.11.0
Flask Version: 3.0.0
OS: Linux
Architecture: x86_64

Flag: 1nf0_d1scl0sur3_vuln
</pre>
```

**FLAG 13:** `1nf0_d1scl0sur3_vuln`

---

### FLAG 14: Server Status (50 points)

Check for server status pages:

```bash
curl http://localhost:4018/server-status
```

**Response:**
```html
<h1>Apache Server Status</h1>
<p>Server Version: Apache/2.4.41</p>
<p>Uptime: 42 days</p>
<p>Active Connections: 127</p>
<!-- Flag: s3rv3r_st4tus_l34ks -->
```

**FLAG 14:** `s3rv3r_st4tus_l34ks`

---

### FLAG 15: Timing Attack (50 points)

Some endpoints reveal themselves through response timing:

```bash
time curl http://localhost:4018/api/check
```

**Note:** This endpoint has an intentional 2+ second delay. When you access it, you'll notice the slow response time.

**Response:**
```json
{
  "status": "ok",
  "message": "You found the slow endpoint!",
  "flag": "t1m1ng_4tt4cks_w0rk"
}
```

**FLAG 15:** `t1m1ng_4tt4cks_w0rk`

---

## Automated Solution Script

```python
#!/usr/bin/env python3
"""
Automated solution for Quebec Web Enumeration Challenge
Finds all 15 flags using Python stdlib only
"""

import urllib.request
import re
import time

BASE_URL = "http://localhost:4018"

flags = {}

print("[*] Starting Quebec Enumeration Challenge\n")

# FLAG 1: robots.txt
print("[1/15] Checking robots.txt...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/robots.txt")
    content = response.read().decode()
    match = re.search(r'# (.+)', content)
    if match:
        flags[1] = match.group(1)
        print(f"    ✓ FLAG 1: {flags[1]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 2: sitemap.xml
print("[2/15] Checking sitemap.xml...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/sitemap.xml")
    content = response.read().decode()
    match = re.search(r'<!-- (.+) -->', content)
    if match:
        flags[2] = match.group(1)
        print(f"    ✓ FLAG 2: {flags[2]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 3: .git/HEAD
print("[3/15] Checking .git/HEAD...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/.git/HEAD")
    content = response.read().decode()
    match = re.search(r'# (.+)', content)
    if match:
        flags[3] = match.group(1)
        print(f"    ✓ FLAG 3: {flags[3]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 4: /backup/
print("[4/15] Checking /backup/...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/backup/")
    content = response.read().decode()
    match = re.search(r'<!-- Flag: (.+) -->', content)
    if match:
        flags[4] = match.group(1)
        print(f"    ✓ FLAG 4: {flags[4]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 5: /admin/login
print("[5/15] Checking /admin/login...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/admin/login")
    content = response.read().decode()
    match = re.search(r'<!-- Flag: (.+) -->', content)
    if match:
        flags[5] = match.group(1)
        print(f"    ✓ FLAG 5: {flags[5]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 6: /.env
print("[6/15] Checking /.env...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/.env")
    content = response.read().decode()
    match = re.search(r'# Flag: (.+)', content)
    if match:
        flags[6] = match.group(1)
        print(f"    ✓ FLAG 6: {flags[6]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 7: /api/docs
print("[7/15] Checking /api/docs...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/api/docs")
    content = response.read().decode()
    match = re.search(r'"flag": "(.+?)"', content)
    if match:
        flags[7] = match.group(1)
        print(f"    ✓ FLAG 7: {flags[7]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 8: /debug
print("[8/15] Checking /debug...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/debug")
    content = response.read().decode()
    match = re.search(r'"flag": "(.+?)"', content)
    if match:
        flags[8] = match.group(1)
        print(f"    ✓ FLAG 8: {flags[8]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 9: HTTP Header
print("[9/15] Checking HTTP headers...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/")
    header_value = response.headers.get('X-EverSec-Version')
    if header_value:
        flags[9] = header_value
        print(f"    ✓ FLAG 9: {flags[9]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 10: HTML Comment
print("[10/15] Checking HTML comments...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/")
    content = response.read().decode()
    match = re.search(r'<!-- Flag: (.+?) -->', content)
    if match:
        flags[10] = match.group(1)
        print(f"    ✓ FLAG 10: {flags[10]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 11: /crossdomain.xml
print("[11/15] Checking /crossdomain.xml...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/crossdomain.xml")
    content = response.read().decode()
    match = re.search(r'<!-- Flag: (.+) -->', content)
    if match:
        flags[11] = match.group(1)
        print(f"    ✓ FLAG 11: {flags[11]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 12: /.well-known/security.txt
print("[12/15] Checking /.well-known/security.txt...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/.well-known/security.txt")
    content = response.read().decode()
    match = re.search(r'# Flag: (.+)', content)
    if match:
        flags[12] = match.group(1)
        print(f"    ✓ FLAG 12: {flags[12]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 13: /phpinfo.php
print("[13/15] Checking /phpinfo.php...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/phpinfo.php")
    content = response.read().decode()
    match = re.search(r'Flag: (.+)', content)
    if match:
        flags[13] = match.group(1)
        print(f"    ✓ FLAG 13: {flags[13]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 14: /server-status
print("[14/15] Checking /server-status...")
try:
    response = urllib.request.urlopen(f"{BASE_URL}/server-status")
    content = response.read().decode()
    match = re.search(r'<!-- Flag: (.+) -->', content)
    if match:
        flags[14] = match.group(1)
        print(f"    ✓ FLAG 14: {flags[14]}")
except Exception as e:
    print(f"    ✗ Error: {e}")

# FLAG 15: /api/check (timing attack)
print("[15/15] Checking /api/check (timing attack)...")
try:
    start = time.time()
    response = urllib.request.urlopen(f"{BASE_URL}/api/check")
    elapsed = time.time() - start
    content = response.read().decode()
    match = re.search(r'"flag": "(.+?)"', content)
    if match:
        flags[15] = match.group(1)
        print(f"    ✓ FLAG 15: {flags[15]} (took {elapsed:.2f}s)")
except Exception as e:
    print(f"    ✗ Error: {e}")

# Summary
print(f"\n[*] Found {len(flags)}/15 flags")
print(f"[*] Total Points: {len(flags) * 50}/750\n")

if len(flags) == 15:
    print("🎉 Congratulations! You found all flags!")
else:
    print(f"⚠️  Missing {15 - len(flags)} flag(s)")
```

---

**Tip**: `curl | grep "FLAG"` works consistently to extract flag values from all 15 endpoints. For example:

```bash
curl -s http://localhost:4018/robots.txt | grep "FLAG"
curl -s http://localhost:4018/api/docs | grep "flag"
curl -sI http://localhost:4018/ | grep -i "eversec"
```

---

## Common Enumeration Tools

### Using gobuster
```bash
gobuster dir -u http://localhost:4018 -w /usr/share/wordlists/dirb/common.txt
```

### Using dirb
```bash
dirb http://localhost:4018
```

### Using nikto
```bash
nikto -h http://localhost:4018
```

### Using ffuf
```bash
ffuf -u http://localhost:4018/FUZZ -w /usr/share/wordlists/dirb/common.txt
```

---

## Learning Points

1. **Always start with robots.txt and sitemap.xml** - These files often reveal directory structure
2. **Check for exposed version control** - .git, .svn, .hg directories shouldn't be in production
3. **Look for backup files** - .bak, .old, .backup extensions
4. **Test common admin paths** - /admin, /administrator, /manager
5. **Read HTTP headers** - Custom headers can leak information
6. **View page source** - Comments often contain sensitive data
7. **Check standard files** - .env, crossdomain.xml, security.txt
8. **Test for info disclosure** - phpinfo.php, server-status
9. **Use timing attacks** - Response times can reveal hidden endpoints
10. **Be systematic** - Use wordlists and automation for complete coverage

---

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Start with the foundational recon files — `robots.txt` and `sitemap.xml`. Site owners sometimes put sensitive paths in these to ask crawlers to stay away, which inadvertently tells you exactly where to look.

</details>

<details>
<summary>Hint 2</summary>

Think about what developers sometimes accidentally leave on production servers: environment files, source control directories, backup archives, admin login pages, debugging endpoints. What does a good web enumeration wordlist include?

</details>

<details>
<summary>Hint 3</summary>

Not every flag lives in the response body. HTTP responses have multiple components — what else is worth examining beyond the HTML?

</details>

<details>
<summary>Hint 4</summary>

Some endpoints behave differently than others in their response timing. If one endpoint consistently takes much longer to respond, what might that behavioral difference indicate?

</details>

## Prevention

- Never commit .git directories to production
- Remove backup files and development artifacts
- Disable debug endpoints in production
- Remove verbose error messages and info pages
- Use security headers properly
- Don't include sensitive data in HTML comments
- Implement proper access controls on admin panels
- Use .gitignore to prevent sensitive file commits
- Regular security audits and enumeration testing

---

**Challenge:** Can you find all 15 flags? Happy hunting! 🎯

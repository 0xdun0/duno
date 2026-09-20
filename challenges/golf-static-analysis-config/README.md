# Golf - Static Analysis Config Exposure

**Status:** ✅ Complete

## Player Description

Check out EverSec's bleeding-edge Development Dashboard! We believe in radical transparency, so we include source maps with all our JavaScript (so helpful!). We also commit our `.git` folder to production because those files are part of our project's history and we're sentimental like that. As for the API keys in the code — our developers said "we'll change them before production" but production came up really fast and we got busy. The `.env` file? Totally fine where it is. And the backup folder? Nobody knows about that one anyway. Don't worry though, who reads source code anyway? Everyone knows security through obscurity works great when the obscurity is... optional.

## Technical Description

**Difficulty**: Medium
**Points**: 550 (5 flags)
**Port**: 4004

EverSec's development portal has shipped to production with several development artifacts still accessible. Use web reconnaissance techniques to discover and exploit five different information disclosure vulnerabilities.

## Learning Objectives

- Web application reconnaissance and information gathering
- Understanding source maps and their security implications
- Identifying hardcoded credentials in JavaScript
- Exploiting exposed `.git` directories and reading commit history
- Recognizing exposed environment configuration files
- Finding insecure backup directories

## Vulnerability Types

1. **Source Map Exposure** — JavaScript source maps reveal original source code
2. **Hardcoded Credentials** — API keys embedded in client-side JavaScript
3. **Git Directory Exposure** — `.git` directory accessible, commit history readable
4. **Environment File Exposure** — `.env` file with production secrets publicly accessible
5. **Backup Directory Exposure** — Infrastructure backup files accessible without authentication

## Setup Instructions

### Using Docker Compose (Recommended)

```bash
# From repository root
docker compose up -d golf-static-analysis-config

# View logs
docker compose logs -f golf-static-analysis-config

# Stop the challenge
docker compose down golf-static-analysis-config
```

### Using Docker

```bash
# Build the image
cd Challenges/golf-static-analysis-config
docker build -t ctf-golf-static-analysis .

# Run the container
docker run -d -p 4004:4004 --name ctf-golf-static-analysis ctf-golf-static-analysis

# Stop the container
docker stop ctf-golf-static-analysis
docker rm ctf-golf-static-analysis
```

## Challenge Access

Once running, access the challenge at: http://localhost:4004

## Starting Point

Start with `robots.txt` — it's a common location that reveals which directories the site owner wants to keep hidden. That list of disallowed paths is itself a roadmap of interesting locations to investigate.

---

## Solutions

### FLAG 1: Source Map Discovery (50 pts)

**Vulnerability**: JavaScript source maps exposed in production

**Discovery Path**:
1. View the page source (`Ctrl+U` or `View Page Source`)
2. Note the `<script src="app.js">` reference
3. Fetch `app.js` and look at the very last line — find the `sourceMappingURL` comment
4. Fetch the `.map` file directly
5. Parse the JSON structure — look at the `sourcesContent` field

**Retrieval**:
```bash
curl http://localhost:4004/app.js.map
```

The flag is embedded in the `sourcesContent` array as a comment in the original source.

**Flag**: `s0urc3_m4ps_t3ll_s3cr3ts`

---

### FLAG 2: Hardcoded API Key in JavaScript (100 pts)

**Vulnerability**: Production secret embedded directly in client-side JavaScript

**Discovery Path**:
1. Fetch `app.js` directly
2. Review the JavaScript source — look for variable declarations near the top
3. Find the `API_KEY` constant

**Retrieval**:
```bash
curl http://localhost:4004/app.js
```

The flag is the value of the `API_KEY` constant.

**Flag**: `4p1_k3y_1n_s0urc3_c0d3`

---

### FLAG 3: Git History Exposure (150 pts)

**Vulnerability**: `.git` directory deployed to production server

**Discovery Path**:
1. Check `robots.txt` — note `Disallow: /.git/`
2. Visit `/.git/` directly — directory listing is enabled
3. Navigate to `/.git/logs/HEAD` to view commit history
4. Read the commit messages carefully

**Retrieval**:
```bash
curl http://localhost:4004/.git/logs/HEAD
```

The flag appears in a commit message where a developer "removed" a sensitive key (but it's right there in the commit log).

**Flag**: `g1t_h1st0ry_r3v34ls_s3cr3ts`

---

### FLAG 4: Environment File Exposure (100 pts)

**Vulnerability**: `.env` configuration file publicly accessible

**Discovery Path**:
1. Check `robots.txt` — note `Disallow: /.env`
2. Fetch `/.env` directly

**Retrieval**:
```bash
curl http://localhost:4004/.env
```

The flag is the value of one of the environment variables.

**Flag**: `3nv_f1l3_s3cr3ts_3xp0s3d`

---

### FLAG 5: Backup Directory Exposure (150 pts)

**Vulnerability**: Insecure backup directory with production configuration file

**Discovery Path**:
1. Check `robots.txt` — note `Disallow: /backup/`
2. Visit `/backup/` — find an index page with a file listing
3. Download `config.bak`
4. Read through the configuration — find monitoring/observability credentials

**Retrieval**:
```bash
curl http://localhost:4004/backup/config.bak
```

The flag is a credential value inside the backup configuration file.

**Flag**: `b4ckup_c0nf1g_l34k3d`

---

## Common Pitfalls

1. **Skipping robots.txt**: This challenge rewards methodical enumeration — robots.txt maps the entire attack surface
2. **Not reading app.js source**: View the raw JS file, not just what the browser renders
3. **Missing the source map reference**: It's the very last line of `app.js`
4. **Assuming .env is blocked**: Many servers expose `.env` files due to misconfiguration
5. **Not reading commit messages**: Git history often contains sensitive data developers thought they "removed"

---

## Hints

> These hints are for CTF administrators helping stuck players. Share them progressively — start with Hint 1.

<details>
<summary>Hint 1</summary>

Production JavaScript is often minified, but the original source code may still be reachable. Check browser developer tools for artifacts that map minified code back to its original form.

</details>

<details>
<summary>Hint 2</summary>

Developers sometimes include sensitive values directly in source code. Now that you can read the original, what does it contain that shouldn't be there?

</details>

<details>
<summary>Hint 3</summary>

Version control systems record everything, including secrets that were added and later removed. If a `.git` directory is accessible on a web server, what historical information can you extract from it?

</details>

## Prevention and Remediation

### Source Map Security

Never deploy source maps to production. Configure your build tool:

```javascript
// webpack.config.js
module.exports = {
  devtool: false,  // No source maps in production
}
```

Or block them in nginx:
```nginx
location ~* \.map$ {
    deny all;
    return 404;
}
```

### Hardcoded Credentials Prevention

```javascript
// ❌ Never do this
const API_KEY = "secret-key-12345";

// ✅ Use environment variables
const API_KEY = process.env.API_KEY;
```

Use secret scanning tools to catch this before commit:
- **GitLeaks**: `gitleaks detect --source /path/to/repo`
- **TruffleHog**: `trufflehog filesystem /path/to/repo`

### Git Directory Protection

```nginx
# Block .git and all hidden directories
location ~ /\. {
    deny all;
    return 404;
}
```

Use `.dockerignore` to prevent deploying `.git`:
```
.git
```

### Environment File Protection

```nginx
# Block .env files
location ~ /\.env {
    deny all;
    return 404;
}
```

Never commit `.env` files. Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### Backup File Protection

- Never store backup files in the web root
- Store backups in separate, access-controlled storage
- Implement authentication for any backup access

---

## References

- [OWASP Sensitive Data Exposure](https://owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure)
- [OWASP Security Misconfiguration](https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration)
- [CWE-540: Inclusion of Sensitive Information in Source Code](https://cwe.mitre.org/data/definitions/540.html)
- [Exploiting Exposed .git Directories](https://en.internetwache.org/dont-publicly-expose-git-or-how-we-downloaded-your-websites-sourcecode-an-analysis-of-alexas-1m-28-07-2015/)

---

**Author**: EverSec CTF Team
**Event**: Cackalacky Con 2026
**Category**: Web / Reconnaissance
**Version**: 2.0

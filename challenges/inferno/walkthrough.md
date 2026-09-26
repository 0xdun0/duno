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

**Flag**: `DUNO{35c8761ee56e8e9be0e007372359c53b}`

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

**Flag**: `DUNO{585f55d476046e2baf410aec24e5f67c}`

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

**Flag**: `DUNO{43dc0ab5f66439fe1fdb95235d128c00}`

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

**Flag**: `DUNO{3db0237a88449d6e6a86e7313e622335}`

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

**Flag**: `DUNO{af292b8d8043bedf123a6c12e3a378c3}`

---
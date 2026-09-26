## Solution

### FLAG 1: robots.txt (50 points)

One of the first files to check on any web application:

```bash
curl http://localhost:4018/robots.txt
```

**Response:**
```
User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /api/
Disallow: /.git/

# r0b0ts_txt_t3lls_s3cr3ts
```

**FLAG 1:** `r0b0ts_txt_t3lls_s3cr3ts`

---

### FLAG 2: sitemap.xml (50 points)

Check for XML sitemap commonly used for SEO:

```bash
curl http://localhost:4018/sitemap.xml
```

**Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>http://eversec.com/</loc>
        <lastmod>2026-01-15</lastmod>
        <priority>1.0</priority>
    </url>
    <!-- s1t3m4p_sh0ws_structur3 -->
    <!-- More URLs... -->
</urlset>
```

**FLAG 2:** `s1t3m4p_sh0ws_structur3`

---

### FLAG 3: Exposed .git Directory (50 points)

Check if version control is exposed:

```bash
curl http://localhost:4018/.git/HEAD
```

**Response:**
```
ref: refs/heads/main
# This shouldn't be here!
# g1t_3xp0sur3_1s_b4d
```

**FLAG 3:** `g1t_3xp0sur3_1s_b4d`

---

### FLAG 4: Backup Directory (50 points)

Common backup locations:

```bash
curl http://localhost:4018/backup/
```

**Response:**
```html
<h1>Backup Files</h1>
<ul>
    <li><a href="database.sql.bak">database.sql.bak</a></li>
    <li><a href="config.php.bak">config.php.bak</a></li>
</ul>
<!-- Flag: b4ckup_f1l3s_l34k_d4t4 -->
```

**FLAG 4:** `b4ckup_f1l3s_l34k_d4t4`

---

### FLAG 5: Admin Login Panel (50 points)

Discover hidden admin panels:

```bash
curl http://localhost:4018/admin/login
```

**Response:**
```html
<h1>EverSec Admin Login</h1>
<form method="POST">
    <input type="text" name="username" placeholder="Username">
    <input type="password" name="password" placeholder="Password">
    <button type="submit">Login</button>
</form>
<!-- Flag: h1dd3n_4dm1n_p4n3ls -->
```

**FLAG 5:** `h1dd3n_4dm1n_p4n3ls`

---

### FLAG 6: Environment File (50 points)

Check for exposed .env files:

```bash
curl http://localhost:4018/.env
```

**Response:**
```
DATABASE_URL=postgresql://admin:password@localhost/eversec
SECRET_KEY=super-secret-key-12345
API_KEY=prod-api-key-67890

# Flag: 3nv_f1l3s_c0nt41n_s3cr3ts
```

**FLAG 6:** `3nv_f1l3s_c0nt41n_s3cr3ts`

---

### FLAG 7: API Documentation (50 points)

Find exposed API documentation:

```bash
curl http://localhost:4018/api/docs
```

**Response:**
```json
{
  "api_version": "v1.0",
  "endpoints": [
    "/api/users",
    "/api/products",
    "/api/orders"
  ],
  "flag": "4p1_d0cs_r3v34l_3ndp01nts"
}
```

**FLAG 7:** `4p1_d0cs_r3v34l_3ndp01nts`

---

### FLAG 8: Debug Endpoint (50 points)

Check for debug interfaces:

```bash
curl http://localhost:4018/debug
```

**Response:**
```json
{
  "debug_mode": true,
  "python_version": "3.11.0",
  "flask_version": "3.0.0",
  "environment": "production",
  "flag": "d3bug_m0d3_3xp0s3s_1nf0"
}
```

**FLAG 8:** `d3bug_m0d3_3xp0s3s_1nf0`

---

### FLAG 9: HTTP Headers (50 points)

Examine HTTP response headers:

```bash
curl -I http://localhost:4018/
```

**Look for custom headers:**
```
HTTP/1.1 200 OK
Server: nginx/1.21.0
X-EverSec-Version: http_h34d3rs_h1d3_d4t4
Content-Type: text/html; charset=utf-8
```

**FLAG 9:** `http_h34d3rs_h1d3_d4t4`

---

### FLAG 10: HTML Comments (50 points)

View page source and search for comments:

```bash
curl http://localhost:4018/ | grep -o "<!--.*-->"
```

**Response:**
```html
<!-- Developer TODO: Remove this before going live! -->
<!-- Flag: html_c0mm3nts_l34k -->
```

**FLAG 10:** `html_c0mm3nts_l34k`

---

### FLAG 11: crossdomain.xml (50 points)

Check for Flash crossdomain policy:

```bash
curl http://localhost:4018/crossdomain.xml
```

**Response:**
```xml
<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
    <allow-access-from domain="*" />
    <!-- Flag: cr0ssd0m41n_p0l1cy_f0und -->
</cross-domain-policy>
```

**FLAG 11:** `cr0ssd0m41n_p0l1cy_f0und`

---

### FLAG 12: security.txt (50 points)

Check for security contact information:

```bash
curl http://localhost:4018/.well-known/security.txt
```

**Response:**
```
Contact: security@eversec.com
Expires: 2027-12-31T23:59:59.000Z
Preferred-Languages: en
Canonical: https://eversec.com/.well-known/security.txt

# Flag: s3cur1ty_txt_c0nt4ct
```

**FLAG 12:** `s3cur1ty_txt_c0nt4ct`

---

### FLAG 13: PHP Info Page (50 points)

Check for information disclosure pages:

```bash
curl http://localhost:4018/phpinfo.php
```

**Response:**
```html
<h1>System Information</h1>
<pre>
Python Version: 3.11.0
Flask Version: 3.0.0
OS: Linux
Architecture: x86_64

Flag: 1nf0_d1scl0sur3_vuln
</pre>
```

**FLAG 13:** `1nf0_d1scl0sur3_vuln`

---

### FLAG 14: Server Status (50 points)

Check for server status pages:

```bash
curl http://localhost:4018/server-status
```

**Response:**
```html
<h1>Apache Server Status</h1>
<p>Server Version: Apache/2.4.41</p>
<p>Uptime: 42 days</p>
<p>Active Connections: 127</p>
<!-- Flag: s3rv3r_st4tus_l34ks -->
```

**FLAG 14:** `s3rv3r_st4tus_l34ks`

---

### FLAG 15: Timing Attack (50 points)

Some endpoints reveal themselves through response timing:

```bash
time curl http://localhost:4018/api/check
```

**Note:** This endpoint has an intentional 2+ second delay. When you access it, you'll notice the slow response time.

**Response:**
```json
{
  "status": "ok",
  "message": "You found the slow endpoint!",
  "flag": "t1m1ng_4tt4cks_w0rk"
}
```

**FLAG 15:** `t1m1ng_4tt4cks_w0rk`

---
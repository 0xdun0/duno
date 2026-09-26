"""
EverSec Corporate Website - Web Enumeration Challenge
A comprehensive web enumeration challenge with 15 flags hidden in realistic locations.

FLAGS (tiered points = 775 total):
Trivial (25 pts each):
1. robots.txt - Classic enumeration starting point
2. sitemap.xml - Standard SEO/crawling file
6. /.env - Environment variables file
9. HTTP headers - Custom header with flag
10. HTML comments - Flag in source code
Easy (50 pts each):
3. /.git/HEAD - Exposed git repository
4. /backup/ - Backup directory
5. /admin/login - Hidden admin panel
7. /api/docs - API documentation
8. /debug - Debug endpoint
Medium (75 pts each):
11. /crossdomain.xml - Flash crossdomain policy
12. /.well-known/security.txt - Security contact info
13. /phpinfo.php - Info disclosure (fake PHP)
14. /server-status - Apache server status
Hard (100 pts):
15. Response timing - Flag in slow endpoint
"""

from flask import Flask, render_template, send_from_directory, make_response, request
import os
import time

app = Flask(__name__)

# Flags
FLAGS = {
    'robots': 'r0b0ts_txt_t3lls_s3cr3ts',
    'sitemap': 's1t3m4p_sh0ws_structur3',
    'git': 'g1t_3xp0sur3_1s_b4d',
    'backup': 'b4ckup_f1l3s_l34k_d4t4',
    'admin': 'h1dd3n_4dm1n_p4n3ls',
    'env': '3nv_f1l3s_c0nt41n_s3cr3ts',
    'api': '4p1_d0cs_r3v34l_3ndp01nts',
    'debug': 'd3bug_m0d3_3xp0s3s_1nf0',
    'header': 'http_h34d3rs_h1d3_d4t4',
    'comment': 'html_c0mm3nts_l34k',
    'crossdomain': 'cr0ssd0m41n_p0l1cy_f0und',
    'security_txt': 's3cur1ty_txt_c0nt4ct',
    'phpinfo': '1nf0_d1scl0sur3_vuln',
    'server_status': 's3rv3r_st4tus_l34ks',
    'timing': 't1m1ng_4tt4cks_w0rk'
}

@app.route('/')
def index():
    """Main page with flag hidden in HTML comment"""
    response = make_response(render_template('index.html', flag_comment=FLAGS['comment']))
    # FLAG 9: Custom HTTP header
    response.headers['X-EverSec-Version'] = FLAGS['header']
    return response

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/services')
def services():
    """Services page"""
    return render_template('services.html')

# FLAG 1: robots.txt
@app.route('/robots.txt')
def robots():
    """Robots.txt with disallowed paths and flag"""
    return f"""User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /debug/
Disallow: /api/internal/
Disallow: /api/check
Disallow: /.git/

# FLAG 1: {FLAGS['robots']}
# Our intern said we should hide these paths in robots.txt for "security"
""", 200, {'Content-Type': 'text/plain'}

# FLAG 2: sitemap.xml
@app.route('/sitemap.xml')
def sitemap():
    """Sitemap with all URLs and flag"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>http://eversec.local/</loc>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>http://eversec.local/about</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://eversec.local/services</loc>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>http://eversec.local/contact</loc>
    <priority>0.7</priority>
  </url>
  <!-- FLAG 2: {FLAGS['sitemap']} -->
  <!-- Why would putting flags in comments be a problem? Comments are invisible! -->
</urlset>
""", 200, {'Content-Type': 'application/xml'}

# FLAG 3: .git directory exposure
@app.route('/.git/HEAD')
def git_head():
    """Exposed .git/HEAD file"""
    return f"""ref: refs/heads/main
# FLAG 3: {FLAGS['git']}
# We deployed our .git folder to production because it's part of version control!
""", 200, {'Content-Type': 'text/plain'}

@app.route('/.git/config')
def git_config():
    """Git config file"""
    return """[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = https://github.com/eversec/production-website.git
	fetch = +refs/heads/*:refs/remotes/origin/*
""", 200, {'Content-Type': 'text/plain'}

@app.route('/.git/logs/HEAD')
def git_log():
    """Git log showing commits"""
    return """0000000000000000000000000000000000000000 abc123def456 EverSec Dev <dev@eversec.local> 1640000000 -0500	commit (initial): Initial commit
abc123def456 def789abc012 EverSec Dev <dev@eversec.local> 1640000100 -0500	commit: Add admin panel
def789abc012 fed456cba789 EverSec Dev <dev@eversec.local> 1640000200 -0500	commit: Remove API keys (oops!)
""", 200, {'Content-Type': 'text/plain'}

# FLAG 4: Backup directory
@app.route('/backup/')
def backup_index():
    """Backup directory listing"""
    return f"""<html>
<head><title>Index of /backup/</title></head>
<body>
<h1>Index of /backup/</h1>
<pre>
<a href="../">../</a>
<a href="database_backup_2025.sql">database_backup_2025.sql</a>     15-Jan-2025 03:00  2.5M
<a href="website_backup.tar.gz">website_backup.tar.gz</a>         14-Jan-2025 23:00  15M
<a href="config_backup.zip">config_backup.zip</a>              10-Jan-2025 12:00  1.2M
<a href="flag.txt">flag.txt</a>                           01-Jan-2025 00:00  45
</pre>
<!-- FLAG 4: {FLAGS['backup']} -->
<hr>
<address>Apache/2.4.41 (Ubuntu) Server at eversec.local Port 80</address>
</body>
</html>""", 200, {'Content-Type': 'text/html'}

# FLAG 5: Admin login page
@app.route('/admin/login')
@app.route('/admin')
def admin_login():
    """Hidden admin login panel"""
    return f"""<html>
<head>
    <title>EverSec Admin Portal</title>
    <style>
        body {{ font-family: Arial; background: #1a1a2e; color: #fff; padding: 50px; }}
        .login-box {{ max-width: 400px; margin: 0 auto; background: #16213e; padding: 30px; border-radius: 10px; }}
        input {{ width: 100%; padding: 10px; margin: 10px 0; background: #0f3460; border: 1px solid #e94560; color: #fff; }}
        button {{ width: 100%; padding: 10px; background: #e94560; color: #fff; border: none; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔒 EverSec Admin Portal</h2>
        <p>Authorized Personnel Only</p>
        <form>
            <input type="text" placeholder="Username" />
            <input type="password" placeholder="Password" />
            <button type="submit">Login</button>
        </form>
        <p style="font-size: 12px; color: #888; margin-top: 20px;">
            FLAG 5: {FLAGS['admin']}
        </p>
        <p style="font-size: 10px; color: #666;">
            Note: Admin login is disabled in production. This page shouldn't even be accessible!
        </p>
    </div>
</body>
</html>""", 200, {'Content-Type': 'text/html'}

# FLAG 6: .env file exposure
@app.route('/.env')
def env_file():
    """Exposed environment variables"""
    return f"""# EverSec Production Environment Variables
# DO NOT COMMIT TO GIT (oops, we did anyway)

APP_ENV=production
APP_DEBUG=true
APP_KEY=base64:ThisIsNotSecureAtAll123456789

DB_CONNECTION=mysql
DB_HOST=db.eversec.local
DB_PORT=3306
DB_DATABASE=eversec_prod
DB_USERNAME=root
DB_PASSWORD=SuperSecretPassword123!

AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# FLAG 6: {FLAGS['env']}
# Our DevOps team said .env files should be "git ignored" but we ignored that advice

STRIPE_KEY=sk_live_definitely_not_a_real_key
OPENAI_API_KEY=sk-proj-fake_key_for_demo_purposes

ADMIN_EMAIL=admin@eversec.local
ADMIN_PASSWORD=admin123
""", 200, {'Content-Type': 'text/plain'}

# FLAG 7: API documentation
@app.route('/api/docs')
@app.route('/api/swagger')
def api_docs():
    """API documentation endpoint"""
    return f"""<html>
<head><title>EverSec API Documentation</title></head>
<body style="font-family: Arial; padding: 40px; background: #f5f5f5;">
    <h1>🔌 EverSec API Documentation</h1>
    <p>Version 2.0 - Internal Use Only</p>

    <h2>Endpoints</h2>
    <ul>
        <li><code>GET /api/users</code> - List all users</li>
        <li><code>GET /api/users/:id</code> - Get user details</li>
        <li><code>POST /api/auth/login</code> - Authenticate user</li>
        <li><code>GET /api/admin/stats</code> - Admin statistics</li>
        <li><code>GET /api/internal/config</code> - Internal configuration</li>
    </ul>

    <h2>Authentication</h2>
    <p>All requests require an API key in the <code>X-API-Key</code> header.</p>
    <p>Example: <code>X-API-Key: eversec_api_key_12345</code></p>

    <h2>Rate Limiting</h2>
    <p>Limited to 1000 requests per hour per IP address.</p>

    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 20px;">
        <strong>⚠️ FLAG 7:</strong> {FLAGS['api']}<br>
        <small>Why is API documentation public? Our CEO wanted "API-first development" visibility!</small>
    </div>
</body>
</html>""", 200, {'Content-Type': 'text/html'}

# FLAG 8: Debug endpoint
@app.route('/debug')
@app.route('/debug/')
def debug():
    """Debug information page"""
    return f"""<html>
<head><title>Debug Information</title></head>
<body style="font-family: monospace; padding: 20px; background: #000; color: #0f0;">
    <h1>🐛 EverSec Debug Panel</h1>
    <p style="color: #ff0;">WARNING: Debug mode is ENABLED in production!</p>

    <h2>Environment Variables:</h2>
    <pre>
APP_ENV=production
DEBUG=true
SECRET_KEY=not-so-secret-key
DATABASE_URL=postgresql://admin:password@localhost/eversec
    </pre>

    <h2>System Information:</h2>
    <pre>
Python Version: 3.11.0
Flask Version: 3.0.0
Platform: Linux-5.15.0-91-generic-x86_64
Hostname: eversec-prod-01
    </pre>

    <h2>Recent Errors:</h2>
    <pre>
[2025-01-19 15:23:41] ERROR: Failed login attempt for 'admin'
[2025-01-19 15:23:42] ERROR: SQL injection attempt detected
[2025-01-19 15:24:00] ERROR: Unauthorized API access from 192.168.1.100
    </pre>

    <h2>FLAG 8: {FLAGS['debug']}</h2>
    <pre style="color: #ff0;">{FLAGS['debug']}</pre>
    <p style="color: #888; font-size: 12px;">
        Debug mode exposes way too much information. But it's so convenient for troubleshooting!
    </p>
</body>
</html>""", 200, {'Content-Type': 'text/html'}

# FLAG 11: crossdomain.xml
@app.route('/crossdomain.xml')
def crossdomain():
    """Flash crossdomain policy (legacy)"""
    return f"""<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
    <allow-access-from domain="*" />
    <allow-http-request-headers-from domain="*" headers="*" />
    <!-- FLAG 11: {FLAGS['crossdomain']} -->
    <!-- We allow all domains because we're friendly! Security through hospitality! -->
</cross-domain-policy>
""", 200, {'Content-Type': 'application/xml'}

# FLAG 12: security.txt
@app.route('/.well-known/security.txt')
def security_txt():
    """Security contact information (RFC 9116)"""
    return f"""Contact: security@eversec.local
Contact: https://eversec.local/security
Expires: 2026-12-31T23:59:59z
Encryption: https://eversec.local/pgp-key.txt
Acknowledgments: https://eversec.local/security/hall-of-fame
Preferred-Languages: en
Canonical: https://eversec.local/.well-known/security.txt

# FLAG 12: {FLAGS['security_txt']}
# At least we got THIS security best practice right! (sort of)

Hiring: https://eversec.local/careers
""", 200, {'Content-Type': 'text/plain'}

# FLAG 13: phpinfo.php (fake)
@app.route('/phpinfo.php')
@app.route('/info.php')
def phpinfo():
    """Fake PHP info page"""
    return f"""<html>
<head><title>phpinfo() - EverSec Production</title></head>
<body style="font-family: sans-serif; background: #fff;">
    <table border="1" cellpadding="3" width="100%">
        <tr><td colspan="2" style="background: #9999cc; color: #fff; font-weight: bold;">PHP Version 8.2.0</td></tr>
        <tr><td>System</td><td>Linux eversec-prod 5.15.0-91-generic</td></tr>
        <tr><td>Server API</td><td>Apache 2.0 Handler</td></tr>
        <tr><td>Loaded Configuration File</td><td>/etc/php/8.2/apache2/php.ini</td></tr>
        <tr><td>display_errors</td><td>On</td></tr>
        <tr><td>expose_php</td><td>On</td></tr>
    </table>

    <h2>FLAG 13: {FLAGS['phpinfo']}</h2>
    <p style="color: #666; font-size: 14px;">
        phpinfo() pages expose tons of server configuration details.
        Probably should delete this file... but it's so useful for debugging!
    </p>
</body>
</html>""", 200, {'Content-Type': 'text/html'}

# FLAG 14: server-status
@app.route('/server-status')
def server_status():
    """Apache server status page"""
    return f"""<html>
<head><title>Apache Server Status for eversec.local</title></head>
<body>
<h1>Apache Server Status for eversec.local (via localhost)</h1>

<dl>
<dt>Server Version: Apache/2.4.41 (Ubuntu) OpenSSL/1.1.1f</dt>
<dt>Server MPM: event</dt>
<dt>Server Built: 2024-03-15T10:22:47</dt>
</dl>

<dl>
<dt>Current Time: Monday, 20-Jan-2025 18:30:00 EST</dt>
<dt>Restart Time: Monday, 20-Jan-2025 00:00:05 EST</dt>
<dt>Parent Server Config. Generation: 1</dt>
<dt>Parent Server MPM Generation: 0</dt>
<dt>Server uptime: 18 hours 29 minutes 55 seconds</dt>
<dt>Server load: 0.15 0.10 0.08</dt>
<dt>Total accesses: 15234 - Total Traffic: 142.3 MB</dt>
<dt>CPU Usage: u12.35 s3.21 cu0 cs0 - .024% CPU load</dt>
<dt>0.228 requests/sec - 2195 B/second - 9784 B/request</dt>
<dt>3 requests currently being processed, 7 idle workers</dt>
</dl>

<pre>
Scoreboard Key:
"_" Waiting for Connection, "S" Starting up, "R" Reading Request,
"W" Sending Reply, "K" Keepalive (read), "D" DNS Lookup,
"C" Closing connection, "L" Logging, "G" Gracefully finishing,
"I" Idle cleanup of worker, "." Open slot with no current process
</pre>

<p style="background: #ffeb3b; padding: 10px; border-radius: 5px;">
    <strong>FLAG 14:</strong> {FLAGS['server_status']}<br>
    <small>server-status pages reveal server configuration and active connections. Very helpful for monitoring... and reconnaissance!</small>
</p>

<hr>
<address>Apache/2.4.41 (Ubuntu) Server at eversec.local Port 80</address>
</body>
</html>""", 200, {'Content-Type': 'text/html'}

# FLAG 15: Timing-based discovery
@app.route('/api/check')
def api_check():
    """Endpoint with timing side-channel"""
    # Introduce delay to simulate database query
    time.sleep(2)
    return f"""{{
    "status": "ok",
    "message": "System operational",
    "flag": "{FLAGS['timing']}",
    "note": "This endpoint takes 2 seconds to respond. Timing differences can leak information!"
}}""", 200, {'Content-Type': 'application/json'}

# Additional realistic endpoints
@app.route('/favicon.ico')
def favicon():
    """Favicon"""
    return '', 404

@app.route('/humans.txt')
def humans():
    """humans.txt file"""
    return """/* TEAM */
Developer: EverSec Dev Team
Site: https://eversec.local
Twitter: @eversec_official
Location: Everywhere and Nowhere

/* THANKS */
Tools: Flask, Python, Coffee

/* SITE */
Last update: 2025/01/20
Standards: HTML5, CSS3
Components: Flask, SQLite
Software: VS Code, Git
""", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4018, debug=False)

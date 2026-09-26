"""EverSec Employee Portal - Internal web application"""

from flask import Flask, render_template_string, request, redirect, url_for, session, make_response
import sqlite3
import subprocess
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')
FLAG3 = os.environ.get('FLAG3', '')
FLAG4 = os.environ.get('FLAG4', '')
FLAG5 = os.environ.get('FLAG5', '')

BASE_STYLE = """
<style>
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #eee;
        margin: 0;
        min-height: 100vh;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 40px 20px;
    }
    .card {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    h1, h2 {
        color: #00d4ff;
        margin-top: 0;
    }
    .logo {
        font-size: 28px;
        font-weight: bold;
        color: #00d4ff;
        margin-bottom: 20px;
    }
    input[type="text"], input[type="password"] {
        width: 100%;
        padding: 12px;
        margin: 8px 0 16px 0;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 6px;
        background: rgba(0,0,0,0.3);
        color: #fff;
        font-size: 16px;
        box-sizing: border-box;
    }
    input[type="submit"], .btn {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
        color: #000;
        padding: 12px 24px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: bold;
        font-size: 16px;
        text-decoration: none;
        display: inline-block;
    }
    input[type="submit"]:hover, .btn:hover {
        background: linear-gradient(135deg, #33ddff 0%, #00aadd 100%);
    }
    .error {
        background: rgba(255,0,0,0.2);
        border: 1px solid #ff4444;
        color: #ff6666;
        padding: 12px;
        border-radius: 6px;
        margin: 10px 0;
    }
    .success {
        background: rgba(0,255,0,0.2);
        border: 1px solid #44ff44;
        color: #66ff66;
        padding: 12px;
        border-radius: 6px;
        margin: 10px 0;
    }
    .flag {
        background: rgba(255,215,0,0.2);
        border: 1px solid #ffd700;
        color: #ffd700;
        padding: 15px;
        border-radius: 6px;
        margin: 15px 0;
        font-family: monospace;
        font-size: 18px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    th {
        background: rgba(0,212,255,0.2);
        color: #00d4ff;
    }
    pre {
        background: #000;
        padding: 15px;
        border-radius: 6px;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        color: #0f0;
    }
    .nav {
        background: rgba(0,0,0,0.3);
        padding: 15px 20px;
        margin-bottom: 20px;
        border-radius: 8px;
    }
    .nav a {
        color: #00d4ff;
        text-decoration: none;
        margin-right: 20px;
    }
    .nav a:hover {
        text-decoration: underline;
    }
    .hint {
        background: rgba(255,165,0,0.1);
        border-left: 4px solid #ffa500;
        padding: 10px 15px;
        margin: 15px 0;
        font-style: italic;
        color: #ffcc66;
    }
</style>
"""

LOGIN_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>[Alpha] EverSec Portal - Login</title>
    {BASE_STYLE}
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">🔐 EverSec Security Portal</div>
            <h2>Employee Login</h2>
            <p>Welcome to the EverSec internal portal. Please authenticate to continue.</p>

            <form method="POST">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" placeholder="Enter your username" required>

                <label for="password">Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter your password" required>

                <input type="submit" value="Login">
            </form>

            {{% if message %}}
                <p class="{{{{ message_type }}}}">{{{{ message }}}}</p>
            {{% endif %}}
        </div>

    </div>
</body>
</html>
"""

USER_DASHBOARD_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>[Alpha] EverSec Portal - User Dashboard</title>
    {BASE_STYLE}
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/logout">Logout</a>
            <span style="color: #666;">|</span>
            <span style="color: #888;">Logged in as: {{{{ username }}}}</span>
        </div>

        <div class="card">
            <div class="logo">🔐 EverSec Security Portal</div>
            <h2>Welcome, {{{{ username }}}}!</h2>

            <div class="flag">
                🚩 FLAG 1: {{{{ flag1 }}}}
            </div>

            <p>You've successfully authenticated to the EverSec portal.</p>

            <h3>Available Actions:</h3>
            <ul>
                <li>View your profile</li>
                <li>Check system status</li>
                <li>Submit support tickets</li>
            </ul>

            <p style="color: #888; font-size: 14px;">
                Note: Administrative functions require admin-level access.
                <a href="/admin" style="color: #ff6666;">Admin Panel</a> (restricted)
            </p>
        </div>

        <div class="card">
            <h3>🔍 User Search</h3>
            <p>Search for other employees in the system:</p>
            <form method="POST" action="/search">
                <input type="text" name="search" placeholder="Search by username...">
                <input type="submit" value="Search">
            </form>
            {{% if search_results %}}
                <h4>Search Results:</h4>
                <table>
                    <tr><th>ID</th><th>Username</th><th>Role</th></tr>
                    {{% for row in search_results %}}
                        <tr><td>{{{{ row[0] }}}}</td><td>{{{{ row[1] }}}}</td><td>{{{{ row[2] if row|length > 2 else 'user' }}}}</td></tr>
                    {{% endfor %}}
                </table>
            {{% endif %}}
            {{% if search_error %}}
                <p class="error">{{{{ search_error }}}}</p>
            {{% endif %}}
        </div>

    </div>
</body>
</html>
"""

ADMIN_LOGIN_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>[Alpha] EverSec Portal - Admin Login</title>
    {BASE_STYLE}
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">🛡️ EverSec Admin Portal</div>
            <h2>Administrator Authentication</h2>
            <p>This area is restricted to administrators only. Please provide valid admin credentials.</p>

            <form method="POST">
                <label for="username">Admin Username:</label>
                <input type="text" id="username" name="username" placeholder="admin" required>

                <label for="password">Admin Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter admin password" required>

                <input type="submit" value="Authenticate">
            </form>

            {{% if message %}}
                <p class="{{{{ message_type }}}}">{{{{ message }}}}</p>
            {{% endif %}}

            <p style="margin-top: 20px;"><a href="/" style="color: #00d4ff;">← Back to main login</a></p>
        </div>
    </div>
</body>
</html>
"""

ADMIN_PANEL_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>[Alpha] EverSec Portal - Admin Panel</title>
    {BASE_STYLE}
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/admin/logout">Logout</a>
            <span style="color: #666;">|</span>
            <span style="color: #ff6666;">⚡ ADMIN MODE</span>
        </div>

        <div class="card">
            <div class="logo">🛡️ EverSec Admin Panel</div>
            <h2>Administrator Dashboard</h2>

            <div class="flag">
                🚩 FLAG 3: {{{{ flag3 }}}}
            </div>

            <p>Welcome, Administrator. You have full access to system management tools.</p>
        </div>

        <div class="card">
            <h3>🌐 Network Diagnostics</h3>
            <p>Use this tool to check network connectivity to internal and external hosts:</p>
            <form method="POST" action="/admin/ping">
                <label for="host">Host to ping:</label>
                <input type="text" name="host" id="host" placeholder="e.g., 8.8.8.8 or google.com">
                <input type="submit" value="Run Ping">
            </form>

            {{% if ping_result %}}
                <h4>Ping Results:</h4>
                <pre>{{{{ ping_result }}}}</pre>
            {{% endif %}}

            {{% if ping_error %}}
                <p class="error">{{{{ ping_error }}}}</p>
            {{% endif %}}
        </div>

        <div class="card">
            <h3>📊 System Information</h3>
            <ul>
                <li>Server: EverSec-PROD-01</li>
                <li>OS: Alpine Linux</li>
                <li>Uptime: 47 days</li>
                <li>Connected Users: 3</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

def init_db():
    db_path = '/tmp/challenge.db'

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE admins (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute("INSERT INTO users (username, role) VALUES ('john.doe', 'user')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('jane.smith', 'user')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('bob.wilson', 'manager')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('alice.chen', 'user')")
    cursor.execute("INSERT INTO users (username, role) VALUES ('admin', 'administrator')")

    cursor.execute("INSERT INTO admins (username, password) VALUES ('admin', ?)", (FLAG2,))

    conn.commit()
    conn.close()

    os.makedirs('/home/ctfuser', exist_ok=True)
    with open('/home/ctfuser/flag4.txt', 'w') as f:
        f.write(FLAG4)

    print("Application initialized")


@app.route('/', methods=['GET', 'POST'])
def login():
    message = None
    message_type = None

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        query = f"SELECT * FROM users WHERE username = '{username}'"

        try:
            conn = sqlite3.connect('/tmp/challenge.db')
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()

            if result:
                # User found - set session and redirect to dashboard
                session['logged_in'] = True
                session['username'] = result[1]  # username from db
                session['role'] = result[2] if len(result) > 2 else 'user'
                return redirect(url_for('dashboard'))
            else:
                message = "Invalid username or password."
                message_type = "error"

        except sqlite3.Error as e:
            message = f"Database error: {str(e)}"
            message_type = "error"

    return render_template_string(LOGIN_TEMPLATE, message=message, message_type=message_type)


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template_string(
        USER_DASHBOARD_TEMPLATE,
        username=session.get('username', 'user'),
        flag1=FLAG1,
        search_results=None,
        search_error=None
    )


@app.route('/search', methods=['POST'])
def search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    search_term = request.form.get('search', '')
    search_results = None
    search_error = None

    query = f"SELECT id, username, role FROM users WHERE username LIKE '%{search_term}%'"

    try:
        conn = sqlite3.connect('/tmp/challenge.db')
        cursor = conn.cursor()
        cursor.execute(query)
        search_results = cursor.fetchall()
        conn.close()
    except sqlite3.Error as e:
        search_error = f"Search error: {str(e)}"

    return render_template_string(
        USER_DASHBOARD_TEMPLATE,
        username=session.get('username', 'user'),
        flag1=FLAG1,
        search_results=search_results,
        search_error=search_error
    )


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    message = None
    message_type = None

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = sqlite3.connect('/tmp/challenge.db')
        cursor = conn.cursor()
        # VULNERABLE: String concatenation allows SQL injection
        query = f"SELECT * FROM admins WHERE username = '{username}' AND password = '{password}'"
        cursor.execute(query)
        result = cursor.fetchone()
        conn.close()

        if result:
            session['admin_logged_in'] = True
            session['admin_username'] = result[1]
            return redirect(url_for('admin_panel'))
        else:
            message = "Invalid admin credentials."
            message_type = "error"

    return render_template_string(ADMIN_LOGIN_TEMPLATE, message=message, message_type=message_type)


@app.route('/admin/panel', methods=['GET'])
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    return render_template_string(
        ADMIN_PANEL_TEMPLATE,
        flag3=FLAG3,
        ping_result=None,
        ping_error=None
    )


@app.route('/admin/ping', methods=['POST'])
def admin_ping():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    host = request.form.get('host', '')
    ping_result = None
    ping_error = None

    if not host:
        ping_error = "Please enter a host to ping."
    else:
        try:
            command = f"ping -c 2 {host}"
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=10)
            ping_result = result.decode('utf-8')
        except subprocess.CalledProcessError as e:
            ping_result = e.output.decode('utf-8') if e.output else "Command failed"
        except subprocess.TimeoutExpired:
            ping_error = "Ping timed out"
        except Exception as e:
            ping_error = f"Error: {str(e)}"

    return render_template_string(
        ADMIN_PANEL_TEMPLATE,
        flag3=FLAG3,
        ping_result=ping_result,
        ping_error=ping_error
    )


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)

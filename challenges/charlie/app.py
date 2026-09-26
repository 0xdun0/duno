from flask import Flask, render_template, request, redirect, url_for, make_response, Response
import base64
import json
import os

app = Flask(__name__)

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')
FLAG3 = os.environ.get('FLAG3', '')
FLAG4 = os.environ.get('FLAG4', '')
FLAG5 = os.environ.get('FLAG5', '')

USERS = {
    'employee': {'password': 'welcome123', 'role': 'employee', 'name': 'John Employee'},
    'manager': {'password': 'mgr456', 'role': 'manager', 'name': 'Jane Manager'},
    'admin': {'password': 'admin789', 'role': 'admin', 'name': 'Admin User'}
}

EMPLOYEE_RECORDS = [
    {'id': 1, 'name': 'John Employee', 'salary': '$45,000', 'department': 'Engineering', 'email': 'jemployee@eversec.local'},
    {'id': 2, 'name': 'Alice Smith', 'salary': '$48,000', 'department': 'Marketing', 'email': 'asmith@eversec.local'},
    {'id': 3, 'name': 'Bob Johnson', 'salary': '$52,000', 'department': 'Sales', 'email': 'bjohnson@eversec.local'},
    {'id': 4, 'name': 'Carol White', 'salary': '$50,000', 'department': 'Engineering', 'email': 'cwhite@eversec.local'},
    {'id': 5, 'name': 'Dave Brown', 'salary': '$46,000', 'department': 'Support', 'email': 'dbrown@eversec.local'},
]

DATA_DIR = '/app/data'

EXPORT_FILES = [
    {'name': 'employees.csv', 'description': 'Employee records export'},
    {'name': 'departments.csv', 'description': 'Department summary'},
    {'name': 'quarterly_report.txt', 'description': 'Q4 2025 quarterly report'},
]


def create_session_cookie(username, role):
    session_data = {
        'username': username,
        'role': role,
        'authenticated': True
    }
    cookie_value = base64.b64encode(json.dumps(session_data).encode()).decode()
    return cookie_value


def parse_session_cookie(cookie_value):
    try:
        # Add padding if missing (browsers sometimes strip trailing =)
        padded = cookie_value + '=' * (-len(cookie_value) % 4)
        decoded = base64.b64decode(padded.encode()).decode()
        session_data = json.loads(decoded)
        if 'username' in session_data and 'role' in session_data:
            return session_data
    except Exception:
        pass
    return None


def get_session():
    cookie = request.cookies.get('session')
    if not cookie:
        return None
    return parse_session_cookie(cookie)


@app.route('/')
def index():
    session_data = get_session()
    if session_data:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username in USERS and USERS[username]['password'] == password:
            cookie_value = create_session_cookie(username, USERS[username]['role'])
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('session', cookie_value, httponly=False)
            return response
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('session', '', expires=0)
    return response


@app.route('/dashboard')
def dashboard():
    session_data = get_session()
    if not session_data:
        return redirect(url_for('login'))

    username = session_data.get('username')
    role = session_data.get('role')

    return render_template('dashboard.html', username=username, role=role)


@app.route('/profile')
def profile():
    session_data = get_session()
    if not session_data:
        return redirect(url_for('login'))

    username = session_data.get('username')
    role = session_data.get('role')
    user_info = USERS.get(username, {'name': 'Unknown', 'role': role})

    return render_template('profile.html',
                           username=username,
                           role=role,
                           name=user_info.get('name', username))


@app.route('/admin')
def admin_panel():
    session_data = get_session()
    if not session_data:
        return redirect(url_for('login'))

    role = session_data.get('role')
    username = session_data.get('username')

    if role != 'admin':
        return render_template('error.html',
                               error='Access Denied: Admin role required',
                               username=username,
                               role=role)

    return render_template('admin.html',
                           username=username,
                           role=role,
                           flag1=FLAG1,
                           employees=EMPLOYEE_RECORDS,
                           export_files=EXPORT_FILES)


@app.route('/admin/export')
def admin_export():
    session_data = get_session()
    if not session_data:
        return redirect(url_for('login'))

    role = session_data.get('role')
    if role != 'admin':
        return 'Access Denied', 403

    filename = request.args.get('file', '')
    if not filename:
        return 'No file specified', 400

    # VULNERABLE: No path sanitization - allows directory traversal via ../
    filepath = os.path.join(DATA_DIR, filename)

    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return Response(content,
                        mimetype='text/plain',
                        headers={'Content-Disposition': f'attachment; filename={os.path.basename(filename)}'})
    except FileNotFoundError:
        return 'File not found', 404
    except Exception:
        return 'Error reading file', 500


def write_flag_files():
    """Write flag files to filesystem at startup."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # FLAG3: readable via path traversal
    flag3_path = '/app/flag3.txt'
    try:
        with open(flag3_path, 'w') as f:
            f.write(FLAG3)
    except Exception:
        pass

    # FLAG4: in ctfuser home directory (readable after SSH)
    flag4_path = os.path.expanduser('~/flag4.txt')
    try:
        with open(flag4_path, 'w') as f:
            f.write(FLAG4)
    except Exception:
        pass


if __name__ == '__main__':
    write_flag_files()
    app.run(host='0.0.0.0', port=4000, debug=False)

from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import json
import os
import threading
import time
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)

DATABASE = '/tmp/tickets.db'
WEBHOOK_LOG = '/tmp/webhook_log.txt'
WEBHOOK_METADATA = '/tmp/webhook_last_clear.txt'

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')

def init_db():
    """Initialize the database with tickets table"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS tickets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  description TEXT,
                  status TEXT,
                  reporter TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    sample_tickets = [
        ('Password Reset Issue', 'I cannot reset my password', 'Open', 'user1'),
        ('Bug in Dashboard', 'The dashboard shows wrong data', 'In Progress', 'user2'),
        ('Feature Request', 'Please add dark mode', 'Open', 'user3'),
    ]

    c.execute('DELETE FROM tickets')
    c.executemany('INSERT INTO tickets (title, description, status, reporter) VALUES (?, ?, ?, ?)',
                  sample_tickets)

    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Home page - list all tickets"""
    conn = get_db()
    tickets = conn.execute('SELECT * FROM tickets ORDER BY timestamp DESC').fetchall()
    conn.close()

    return render_template('index.html', tickets=tickets)

@app.route('/ticket/<int:ticket_id>')
def view_ticket(ticket_id):
    """View a specific ticket"""
    conn = get_db()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if not ticket:
        return "Ticket not found", 404

    return render_template('ticket.html', ticket=ticket)

@app.route('/submit', methods=['GET', 'POST'])
def submit_ticket():
    """Submit a new support ticket"""
    if request.method == 'POST':
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        reporter = request.form.get('reporter', 'Anonymous')

        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO tickets (title, description, status, reporter) VALUES (?, ?, ?, ?)',
                 (title, description, 'Open', reporter))
        ticket_id = c.lastrowid
        conn.commit()
        conn.close()

        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    return render_template('submit.html')

@app.route('/search')
def search():
    """Search tickets"""
    query = request.args.get('q', '')

    if query:
        conn = get_db()
        tickets = conn.execute(
            'SELECT * FROM tickets WHERE title LIKE ? OR description LIKE ?',
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        conn.close()
    else:
        tickets = []

    return render_template('search.html', query=query, tickets=tickets, flag1=FLAG1)

@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
def delete_ticket(ticket_id):
    """Delete a ticket"""
    conn = get_db()
    conn.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/report/<int:ticket_id>', methods=['POST'])
def report_to_admin(ticket_id):
    """Report ticket to admin"""
    conn = get_db()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if not ticket:
        return "Ticket not found", 404

    # Launch admin bot in background thread
    threading.Thread(target=admin_bot_visit, args=(ticket_id,), daemon=True).start()

    return render_template('reported.html', ticket_id=ticket_id)

def admin_bot_visit(ticket_id):
    """Real Selenium-based admin bot that visits ticket with FLAG2 cookie"""
    time.sleep(2)  # Small delay before admin "responds"

    try:
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # Create Chrome driver
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Navigate to the ticket URL
        ticket_url = f'http://localhost:4002/ticket/{ticket_id}'
        driver.get(ticket_url)

        # Add admin cookie with FLAG2
        driver.add_cookie({
            'name': 'admin_session',
            'value': FLAG2,
            'domain': 'localhost',
            'path': '/'
        })

        # Refresh to apply cookie
        driver.get(ticket_url)

        # Wait for XSS payload to execute
        time.sleep(3)

        # Close browser
        driver.quit()

    except Exception as e:
        # Log error but don't crash
        print(f"Admin bot error: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook for receiving exfiltrated data"""
    data = request.get_json() or {}
    logged_data = json.dumps(data) if data else 'No data provided'

    # Get current timestamp and next clear time
    now = datetime.now()
    next_clear = get_next_clear_time()

    with open(WEBHOOK_LOG, 'a') as f:
        f.write(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] {logged_data}\n")

    return {
        'status': 'received',
        'message': f'Data logged. Logs auto-clear every 3 minutes. Next clear: {next_clear}'
    }, 200

@app.route('/webhook/log')
def webhook_log():
    """View webhook logs with auto-clear notice"""
    last_clear = get_last_clear_time()
    next_clear = get_next_clear_time()

    try:
        with open(WEBHOOK_LOG, 'r') as f:
            logs = f.read().strip()
    except FileNotFoundError:
        logs = ''

    header = f"""╔══════════════════════════════════════════════════════════════════════╗
║  EverSec Webhook Log Viewer                                          ║
║  🕐 Auto-clear: Every 3 minutes                                      ║
║  📅 Last cleared: {last_clear:<51} ║
║  ⏱️  Next clear: {next_clear:<53} ║
╚══════════════════════════════════════════════════════════════════════╝

{logs if logs else '[No webhook data received yet]'}
"""

    return f"<pre>{header}</pre>"

@app.route('/admin/cmd', methods=['GET'])
def admin_execute():
    """Admin command execution endpoint (FLAG 3)"""
    if request.remote_addr not in ['127.0.0.1', 'localhost', '::1']:
        return jsonify({'error': 'Access denied: Admin panel only accessible from localhost'}), 403

    command = request.args.get('cmd', '')

    if not command:
        return jsonify({'error': 'No command provided', 'usage': '/admin/cmd?cmd=<command>'}), 400

    try:
        result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        return jsonify({'output': result, 'success': True})
    except subprocess.CalledProcessError as e:
        return jsonify({'output': e.output, 'error': str(e), 'success': False}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

def get_last_clear_time():
    """Get timestamp of last webhook log clear"""
    try:
        with open(WEBHOOK_METADATA, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'Never'

def get_next_clear_time():
    """Calculate next clear time (3 minutes from last clear)"""
    try:
        with open(WEBHOOK_METADATA, 'r') as f:
            last_clear_str = f.read().strip()
            last_clear = datetime.strptime(last_clear_str, '%Y-%m-%d %H:%M:%S')
            next_clear = last_clear.timestamp() + 180  # 3 minutes
            time_until = int(next_clear - time.time())

            if time_until <= 0:
                return 'Soon (overdue)'

            mins, secs = divmod(time_until, 60)
            return f'in {mins}m {secs}s'
    except Exception:
        return 'in 3m 0s'

def auto_clear_webhook_logs():
    """Background thread that clears webhook logs every 3 minutes"""
    while True:
        time.sleep(180)  # 3 minutes
        try:
            # Clear the log file
            with open(WEBHOOK_LOG, 'w') as f:
                f.write('')

            # Update last clear timestamp
            with open(WEBHOOK_METADATA, 'w') as f:
                f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Webhook logs cleared")
        except Exception as e:
            print(f"Error clearing webhook logs: {e}")

if __name__ == '__main__':
    # Initialize database
    if not os.path.exists(DATABASE):
        init_db()
    else:
        os.remove(DATABASE)
        init_db()

    # Initialize webhook log and metadata files
    with open(WEBHOOK_LOG, 'w') as f:
        f.write('')
    with open(WEBHOOK_METADATA, 'w') as f:
        f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # Write FLAG3 to file for RCE challenge
    FLAG3 = os.environ.get('FLAG3', '')
    try:
        with open('/home/ctfuser/flag3.txt', 'w') as f:
            f.write(f"{FLAG3}\n")
    except Exception:
        pass

    # Start auto-clear background thread
    clear_thread = threading.Thread(target=auto_clear_webhook_logs, daemon=True)
    clear_thread.start()
    print("🕐 Webhook log auto-clear enabled (every 3 minutes)")

    # Start Flask app
    app.run(host='0.0.0.0', port=4002, debug=False)

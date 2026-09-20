from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import os
import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

app = Flask(__name__)

DATABASE = '/tmp/tickets.db'
FLAG1 = os.environ.get('FLAG1', 'xss_st0l3_my_c00k13')
FLAG2 = os.environ.get('FLAG2', '4dm1n_c00k13_c4ptur3d')

# Admin bot will have this special cookie
ADMIN_COOKIE_VALUE = f'admin_session={FLAG2}'

def init_db():
    """Initialize the database with tickets table"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Create tickets table
    c.execute('''CREATE TABLE IF NOT EXISTS tickets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  description TEXT,
                  status TEXT,
                  reporter TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # Insert some sample tickets
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
    """
    Search tickets by query parameter.
    VULNERABILITY: Reflects search query directly into HTML without sanitization!
    """
    query = request.args.get('q', '')

    if query:
        conn = get_db()
        # Use LIKE for search
        tickets = conn.execute(
            'SELECT * FROM tickets WHERE title LIKE ? OR description LIKE ?',
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        conn.close()
    else:
        tickets = []

    # VULNERABLE: Render template with unsanitized query
    return render_template('search.html', query=query, tickets=tickets, flag1=FLAG1)

@app.route('/report/<int:ticket_id>', methods=['POST'])
def report_to_admin(ticket_id):
    """
    Report a ticket to admin for review.
    This triggers the admin bot to visit the ticket.
    """
    conn = get_db()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if not ticket:
        return "Ticket not found", 404

    # Construct the URL the admin bot will visit
    ticket_url = f"http://localhost:4002/ticket/{ticket_id}"

    # Trigger admin bot in a background thread
    threading.Thread(target=admin_bot_visit, args=(ticket_url,), daemon=True).start()

    return render_template('reported.html', ticket_id=ticket_id)

def admin_bot_visit(url):
    """
    Simulated admin bot that visits a URL with special admin cookies.
    This bot has a cookie containing FLAG2.
    If an attacker can steal this cookie via XSS, they get the flag.
    """
    try:
        # Wait a moment to simulate processing time
        time.sleep(2)

        print(f"[BOT] Admin bot visiting: {url}")

        # Set up headless Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # Use ChromeDriver
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # First visit the homepage to set the domain
            driver.get('http://localhost:4002/')

            # Set admin cookie with FLAG2
            driver.add_cookie({
                'name': 'admin_session',
                'value': FLAG2,
                'domain': 'localhost',
                'path': '/'
            })

            print(f"[BOT] Admin cookie set: {FLAG2[:30]}...")

            # Now visit the reported ticket URL
            driver.get(url)

            # Wait a bit for any JavaScript to execute
            time.sleep(3)

            print(f"[BOT] Admin bot finished visiting {url}")

        finally:
            driver.quit()

    except Exception as e:
        print(f"[BOT] Error in admin bot: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint for receiving exfiltrated data.
    Attackers can use this to receive stolen cookies.
    """
    data = request.get_json() or {}
    cookie = data.get('cookie', 'No cookie provided')

    print(f"[WEBHOOK] Received data: {cookie}")

    # Store in a simple file for participants to check
    with open('/tmp/webhook_log.txt', 'a') as f:
        f.write(f"{cookie}\n")

    return {'status': 'received'}, 200

@app.route('/webhook/log')
def webhook_log():
    """View webhook logs (for participants to verify their exfiltration worked)"""
    try:
        with open('/tmp/webhook_log.txt', 'r') as f:
            logs = f.read()
        return f"<pre>{logs}</pre>"
    except FileNotFoundError:
        return "<pre>No logs yet</pre>"

if __name__ == '__main__':
    # Initialize database on startup
    if not os.path.exists(DATABASE):
        init_db()
    else:
        os.remove(DATABASE)
        init_db()

    # Create webhook log file
    open('/tmp/webhook_log.txt', 'w').close()

    app.run(host='0.0.0.0', port=4002, debug=False)

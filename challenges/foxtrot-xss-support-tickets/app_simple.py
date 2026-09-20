from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import threading
import time

app = Flask(__name__)

DATABASE = '/tmp/tickets.db'
FLAG1 = os.environ.get('FLAG1', 'xss_st0l3_my_c00k13')
FLAG2 = os.environ.get('FLAG2', '4dm1n_c00k13_c4ptur3d')

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
    """Search tickets - VULNERABLE to reflected XSS"""
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

@app.route('/report/<int:ticket_id>', methods=['POST'])
def report_to_admin(ticket_id):
    """Report ticket to admin - simulated admin bot"""
    conn = get_db()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()
    conn.close()

    if not ticket:
        return "Ticket not found", 404

    # Simulate admin bot visiting (without actual Selenium)
    threading.Thread(target=simulate_admin_visit, args=(ticket_id,), daemon=True).start()

    return render_template('reported.html', ticket_id=ticket_id)

def simulate_admin_visit(ticket_id):
    """Simulated admin bot - logs that admin visited"""
    time.sleep(2)
    print(f"[BOT] Simulated admin bot visiting ticket #{ticket_id}")
    print(f"[BOT] Admin cookie would be: admin_session={FLAG2}")

    # Log to webhook file
    with open('/tmp/webhook_log.txt', 'a') as f:
        f.write(f"admin_session={FLAG2}\n")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook for receiving exfiltrated data"""
    data = request.get_json() or {}
    cookie = data.get('cookie', 'No cookie provided')

    print(f"[WEBHOOK] Received data: {cookie}")

    with open('/tmp/webhook_log.txt', 'a') as f:
        f.write(f"{cookie}\n")

    return {'status': 'received'}, 200

@app.route('/webhook/log')
def webhook_log():
    """View webhook logs"""
    try:
        with open('/tmp/webhook_log.txt', 'r') as f:
            logs = f.read()
        return f"<pre>{logs}</pre>"
    except FileNotFoundError:
        return "<pre>No logs yet</pre>"

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        os.remove(DATABASE)
        init_db()

    open('/tmp/webhook_log.txt', 'w').close()

    app.run(host='0.0.0.0', port=4002, debug=False)

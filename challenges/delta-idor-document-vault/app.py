from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = '/tmp/documents.db'
FLAG1 = os.environ.get('FLAG1', '1d0r_bur1ed_tr34sur3')
FLAG2 = os.environ.get('FLAG2', '3num3r4t3_4ll_th3_th1ngs')
FLAG3 = os.environ.get('FLAG3', 'd3l3t3d_but_n0t_g0n3')
FLAG4 = os.environ.get('FLAG4', '1d0r_us3r_pr0f1l3_pwn3d')


def init_db():
    """Initialize the database with users and documents"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT,
                  department TEXT, email TEXT, internal_notes TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT, owner_id INTEGER,
                  confidential INTEGER, is_deleted INTEGER DEFAULT 0)''')

    c.execute('DELETE FROM users')
    c.execute('DELETE FROM documents')

    # Users with extra profile fields for FLAG4
    users = [
        (1, 'employee', 'password123', 'employee', 'Engineering',
         'jsmith@eversec.io', 'Standard user. Onboarded 2025-03-15.'),
        (2, 'manager', 'manager456', 'manager', 'Engineering',
         'klee@eversec.io', 'Team lead. Access to budget docs approved by CTO.'),
        (3, 'admin', 'admin789', 'admin', 'IT Security',
         'root@eversec.io', f'System administrator. Backup codes: {FLAG4}'),
    ]
    c.executemany(
        'INSERT INTO users (id, username, password, role, department, email, internal_notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
        users
    )

    documents = [
        # Admin documents (low IDs)
        (1000, 'Executive Compensation Review - Q4 2026',
         'CONFIDENTIAL - BOARD EYES ONLY\n\n'
         'Executive compensation adjustments for fiscal year 2026:\n\n'
         'CEO - Marcus Webb: Base $485,000 + 30% bonus target\n'
         'CTO - Diana Chen: Base $410,000 + 25% bonus target\n'
         'CFO - Robert Park: Base $395,000 + 25% bonus target\n'
         'VP Engineering - Sarah Kim: Base $340,000 + 20% bonus target\n\n'
         'NOTE: Do NOT share externally. Glassdoor incident in 2024 caused\n'
         'significant retention issues when compensation data leaked.\n\n'
         'Board approval pending for Q1 2027 adjustments.',
         3, 1, 0),

        (1001, 'Incident Response Playbook',
         'EverSec IR Playbook v3.2\n\n'
         'Step 1: Contain the breach (isolate affected systems)\n'
         'Step 2: Preserve evidence (do NOT reboot servers)\n'
         'Step 3: Notify legal (compliance@eversec.io) within 1 hour\n'
         'Step 4: Engage forensics team\n'
         'Step 5: Draft customer notification (if PII affected)\n\n'
         'Emergency contacts:\n'
         '  SOC Lead: ext. 4401\n'
         '  Legal: ext. 2200\n'
         '  PR/Comms: ext. 3100\n\n'
         'Remember: assume breach, verify containment, then investigate.',
         3, 1, 0),

        (1002, 'Vendor Security Assessment - CloudPipe Inc.',
         'ASSESSMENT: CloudPipe Inc. (SaaS data pipeline vendor)\n'
         'Date: 2026-09-14\n'
         'Assessor: J. Torres, Security Engineering\n\n'
         'FINDINGS:\n'
         '  [CRITICAL] No encryption at rest for customer data\n'
         '  [HIGH] API keys transmitted via query parameters\n'
         '  [MEDIUM] SOC 2 Type II report expired (last audit: 2024)\n'
         '  [LOW] Password policy allows 6-character passwords\n\n'
         'RECOMMENDATION: Do NOT onboard until critical findings resolved.\n'
         'Scheduling follow-up review for Q1 2027.',
         3, 1, 0),

        # Manager documents
        (2000, 'Q4 2026 Engineering Budget',
         'ENGINEERING BUDGET - Q4 2026\n\n'
         'Infrastructure:\n'
         '  AWS hosting:      $47,200/mo\n'
         '  Datadog:          $8,400/mo\n'
         '  GitHub Enterprise: $2,100/mo\n\n'
         'Headcount:\n'
         '  2x Senior Engineers (backfill): $180k each\n'
         '  1x DevOps Engineer: $155k\n\n'
         'Total Q4 Budget: $1,208,100\n'
         'Remaining from Q3 rollover: $42,300\n\n'
         'STATUS: Approved by CFO 2026-10-01',
         2, 0, 0),

        (2001, 'Performance Review Notes - Engineering Team',
         'PERFORMANCE REVIEWS - Q3 2026\n\n'
         'J. Smith (employee): Meets expectations. Good work on the\n'
         'Document Vault migration. Needs improvement on documentation.\n'
         'Recommended: no promotion this cycle, revisit Q1.\n\n'
         'A. Patel: Exceeds expectations. Led the API redesign project.\n'
         'Recommended: promotion to Senior Engineer.\n\n'
         'M. Garcia: Below expectations. Missed 3 sprint commitments.\n'
         'Recommended: PIP if no improvement by EOY.\n\n'
         'NOTE: Do not share with direct reports until reviews finalized.',
         2, 0, 0),

        # Employee documents (assigned to employee user)
        (1042, 'Meeting Notes - Sprint Retrospective',
         'SPRINT 47 RETROSPECTIVE - 2026-10-18\n\n'
         'What went well:\n'
         '  - Document Vault v2.1 shipped on time\n'
         '  - Zero P1 incidents this sprint\n'
         '  - New hire onboarding went smoothly\n\n'
         'What could improve:\n'
         '  - API documentation still outdated\n'
         '  - Mobile app performance on iOS needs work\n'
         '  - Better error messages for end users\n\n'
         'Action items:\n'
         '  - J. Smith: Update API docs by EOW\n'
         '  - A. Patel: Investigate iOS scroll lag\n'
         '  - K. Lee: Draft new error message templates',
         1, 0, 0),

        (1043, 'Project Proposal - Mobile App Redesign',
         'PROJECT PROPOSAL: Document Vault Mobile v3.0\n'
         'Author: J. Smith\n'
         'Date: 2026-10-20\n\n'
         'OBJECTIVE: Modernize mobile experience and improve UX.\n\n'
         'Proposed Changes:\n'
         '  1. Redesign document browser with card-based UI\n'
         '  2. Add offline caching for recently viewed documents\n'
         '  3. Implement biometric authentication (Face ID/Touch ID)\n'
         '  4. Add dark mode support\n\n'
         'TIMELINE: 6 weeks (2 sprints)\n'
         'RESOURCES: 2 engineers + 1 UX designer\n\n'
         'STATUS: Pending manager approval\n\n'
         'NOTE: Current mobile app has 3.2-star rating on App Store.\n'
         'iOS users consistently request dark mode.',
         1, 0, 0),

        # FLAG1 - one ID away from employee's last document
        (1044, 'Annual Security Audit - Infrastructure Review',
         f'CONFIDENTIAL - INTERNAL USE ONLY\n\n'
         f'EverSec Annual Security Audit Report\n'
         f'Audit Period: Q3 2026\n'
         f'Auditor: TrustedSec Partners LLP\n'
         f'Date: 2026-09-28\n\n'
         f'EXECUTIVE SUMMARY:\n'
         f'Overall security posture is adequate with room for improvement.\n'
         f'Notable strengths in incident response and patch management.\n'
         f'Recommendations focus on access logging and monitoring.\n\n'
         f'KEY FINDINGS:\n'
         f'  [HIGH] Insufficient audit logging on production systems\n'
         f'  [MEDIUM] MFA not enforced for all administrative accounts\n'
         f'  [MEDIUM] Backup encryption keys stored alongside backups\n'
         f'  [LOW] Certificate expiration monitoring could be improved\n\n'
         f'Audit completion token: {FLAG1}\n\n'
         f'RECOMMENDATIONS:\n'
         f'Implement centralized log aggregation (Splunk/ELK) and enforce\n'
         f'MFA for all accounts with elevated privileges.\n\n'
         f'Next audit scheduled: Q3 2027',
         3, 1, 0),

        # Hidden admin document (high ID, requires enumeration)
        (9999, 'Master Recovery Keys',
         f'EMERGENCY USE ONLY\n\n'
         f'EverSec Infrastructure Master Recovery Keys\n'
         f'Generated: 2026-01-15\n'
         f'Custodian: Systems Administrator\n\n'
         f'These keys provide full administrative access to all EverSec\n'
         f'systems in the event of a catastrophic failure.\n\n'
         f'Recovery Token: {FLAG2}\n\n'
         f'STORAGE NOTICE: This document should be stored in a hardware\n'
         f'security module, not in the Document Vault. Migration pending.\n\n'
         f'If you are reading this and you are not the Systems Administrator,\n'
         f'please report this access to security@eversec.io immediately.',
         3, 1, 0),

        # Scattered documents to make enumeration more interesting
        (3500, 'Office Snack Budget Proposal',
         'TO: Finance Department\n'
         'FROM: Office Culture Committee\n'
         'RE: Emergency Snack Budget Increase\n\n'
         'We are formally requesting a 200% increase to the monthly\n'
         'snack budget ($400 -> $1,200). Justification:\n\n'
         '  1. The LaCroix situation is critical. We have been out of\n'
         '     Pamplemousse for 3 weeks. Morale is at an all-time low.\n'
         '  2. Someone keeps stealing the good granola bars and replacing\n'
         '     them with rice cakes. This is unacceptable.\n'
         '  3. The engineering team has threatened to mass-resign if we\n'
         '     switch from Kirkland cold brew to Folgers again.\n\n'
         'This is a P0 issue. Please treat with appropriate urgency.\n\n'
         'Respectfully,\n'
         'The Snack Committee',
         2, 0, 0),

        (5000, 'All-Hands Meeting Notes - October 2026',
         'ALL-HANDS MEETING - 2026-10-01\n\n'
         'CEO Update (Marcus Webb):\n'
         '  - Revenue up 23% YoY. Nice.\n'
         '  - New office in Austin opening Q1 2027\n'
         '  - Holiday party confirmed for Dec 13 at The Fillmore\n\n'
         'CTO Update (Diana Chen):\n'
         '  - Platform reliability at 99.97% uptime\n'
         '  - Document Vault v2.1 launch went well\n'
         '  - "Please stop putting credentials in Slack" - direct quote\n\n'
         'HR Update:\n'
         '  - Open enrollment starts Nov 1\n'
         '  - New PTO policy: unlimited (with manager approval)\n'
         '  - Reminder: the parking garage code is NOT a shared secret',
         3, 0, 0),

        (6200, 'Cafeteria Menu - Week of Oct 21',
         'EVERSEC CAFETERIA - WEEKLY MENU\n\n'
         'Monday:    Grilled chicken, quinoa bowl, sad salad bar\n'
         'Tuesday:   Taco Tuesday (the one day worth showing up for)\n'
         'Wednesday: "Mediterranean Fusion" (last week this was just hummus)\n'
         'Thursday:  Sushi day (decent, bring your own soy sauce)\n'
         'Friday:    Pizza party because we hit our sprint goals\n\n'
         'ALLERGEN NOTICE: Everything may contain everything.\n'
         'The kitchen staff asked us to stop microwaving fish.\n'
         'You know who you are.\n\n'
         'Vegan options available daily (it\'s always the sad salad bar).',
         1, 0, 0),

        # Soft-deleted document
        (7777, 'INCIDENT REPORT #2026-0041',
         f'SECURITY INCIDENT REPORT\n'
         f'ID: INC-2026-0041\n'
         f'Severity: CRITICAL\n'
         f'Status: CLOSED (record marked for deletion)\n\n'
         f'SUMMARY:\n'
         f'On 2026-08-12, production database credentials were found\n'
         f'committed to a public GitHub repository. The credentials\n'
         f'provided read/write access to the customer database.\n\n'
         f'IMPACT:\n'
         f'  - 12,400 customer records potentially exposed\n'
         f'  - Credentials active for approximately 6 days before rotation\n'
         f'  - No evidence of unauthorized access (per CloudTrail audit)\n\n'
         f'ROOT CAUSE:\n'
         f'Developer committed .env file to repo. Pre-commit hooks were\n'
         f'disabled because "they were slowing down my workflow."\n\n'
         f'Forensic tracking token: {FLAG3}\n\n'
         f'REMEDIATION:\n'
         f'  - Credentials rotated immediately\n'
         f'  - Pre-commit hooks made mandatory (cannot be bypassed)\n'
         f'  - Mandatory security training for all engineering staff\n\n'
         f'NOTE: This report was soft-deleted per legal request.\n'
         f'Do not distribute.',
         3, 1, 1),
    ]

    c.executemany(
        'INSERT INTO documents (id, title, content, owner_id, confidential, is_deleted) VALUES (?, ?, ?, ?, ?, ?)',
        documents
    )

    conn.commit()
    conn.close()


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard showing user's assigned documents"""
    conn = get_db()

    if session['role'] == 'admin':
        docs = conn.execute('SELECT id, title, confidential FROM documents WHERE owner_id = 3 AND is_deleted = 0 ORDER BY id').fetchall()
    elif session['role'] == 'manager':
        docs = conn.execute('SELECT id, title, confidential FROM documents WHERE owner_id = 2 AND is_deleted = 0 ORDER BY id').fetchall()
    else:
        docs = conn.execute('SELECT id, title, confidential FROM documents WHERE owner_id = 1 AND is_deleted = 0 ORDER BY id').fetchall()

    conn.close()

    return render_template('dashboard.html', username=session['username'],
                           role=session['role'], documents=docs)


@app.route('/document/<int:doc_id>')
@login_required
def view_document(doc_id):
    """
    VULNERABILITY: No authorization check!
    Any logged-in user can view any document by knowing the ID.
    Soft-deleted documents are also accessible via direct ID.
    """
    conn = get_db()
    # No ownership check, no is_deleted check
    document = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
    conn.close()

    if not document:
        return render_template('error.html', error='Document not found'), 404

    return render_template('document.html', document=document, username=session['username'])


@app.route('/api')
@login_required
def api_docs():
    """API documentation page"""
    return render_template('api_docs.html', username=session['username'])


@app.route('/api/documents')
@login_required
def api_documents():
    """
    VULNERABILITY: Returns all non-deleted documents without access control.
    Soft-deleted documents are excluded from listing but still in the DB.
    """
    conn = get_db()
    documents = conn.execute(
        'SELECT id, title, confidential FROM documents WHERE is_deleted = 0 ORDER BY id'
    ).fetchall()
    conn.close()

    doc_list = [{'id': doc['id'], 'title': doc['title'],
                 'confidential': bool(doc['confidential'])} for doc in documents]

    return jsonify({'documents': doc_list, 'total': len(doc_list)})


@app.route('/api/users/<int:user_id>')
@login_required
def api_user_profile(user_id):
    """
    VULNERABILITY: No authorization check on user profiles!
    Any authenticated user can view any user's profile by changing the ID.
    Internal notes field contains sensitive data.
    """
    conn = get_db()
    user = conn.execute(
        'SELECT id, username, role, department, email, internal_notes FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'department': user['department'],
        'email': user['email'],
        'internal_notes': user['internal_notes']
    })


if __name__ == '__main__':
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    init_db()

    print("Delta - IDOR Document Vault")
    print("Port: 4001")
    print("Flags: 4")
    app.run(host='0.0.0.0', port=4001, debug=False)

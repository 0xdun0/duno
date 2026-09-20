"""
EverSec Gift Card System - Race Condition Challenge
A gift card redemption system vulnerable to race conditions.

FLAGS:
- FLAG 1: Redeem the same coupon multiple times using race condition
- FLAG 2: Exploit race condition to get negative balance (underflow)
- FLAG 3: Chain race conditions to achieve maximum balance

The vulnerability:
1. Check-then-act pattern without proper locking (TOCTOU)
2. No database transaction isolation
3. No request deduplication
4. Allows concurrent redemptions of same coupon
"""

from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
import time
import threading
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Flags (no wrappers)
FLAG1 = os.environ.get('FLAG1', 'r4c3_c0nd1t10n_pwn3d')
FLAG2 = os.environ.get('FLAG2', 'n3g4t1v3_b4l4nc3_h4ck')
FLAG3 = os.environ.get('FLAG3', 'r4c3_t0_th3_t0p')
FLAG4 = os.environ.get('FLAG4', '')

DATABASE = '/tmp/giftcards.db'

# Database lock (intentionally not used in vulnerable code)
db_lock = threading.Lock()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema and test data"""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Coupons table
    c.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            value INTEGER NOT NULL,
            max_redemptions INTEGER DEFAULT 1,
            current_redemptions INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Redemptions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            coupon_id INTEGER,
            amount INTEGER,
            redeemed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (coupon_id) REFERENCES coupons (id)
        )
    ''')

    # Create test user
    c.execute('INSERT OR IGNORE INTO users (username, balance) VALUES (?, ?)',
              ('player', 0))

    # Create test coupons
    test_coupons = [
        ('WELCOME100', 100, 1),      # Single use coupon - FLAG 1 target
        ('BONUS50', 50, 1),           # Single use coupon
        ('SPECIAL200', 200, 1),       # High value single use - FLAG 2 target
        ('PREMIUM500', 500, 1),       # Very high value - FLAG 3 target
        ('LOYALTY25', 25, 5),         # Multi-use coupon
    ]

    for code, value, max_red in test_coupons:
        c.execute('''
            INSERT OR IGNORE INTO coupons (code, value, max_redemptions, current_redemptions, active)
            VALUES (?, ?, ?, 0, 1)
        ''', (code, value, max_red))

    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main page"""
    if 'user_id' not in session:
        # Auto-login as player for simplicity
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', ('player',)).fetchone()
        session['user_id'] = user['id']
        session['username'] = user['username']
        conn.close()

    return render_template('index.html')

@app.route('/balance')
def get_balance():
    """Get current user balance"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()
    user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    balance = user['balance'] if user else 0

    # Check for flag achievements
    flags = []
    if balance >= 200:
        flags.append({'flag': FLAG1, 'message': 'You exploited the race condition!'})
    if balance >= 500:
        flags.append({'flag': FLAG2, 'message': 'You achieved a massive balance!'})
    if balance >= 1000:
        flags.append({'flag': FLAG3, 'message': 'You are the race condition master!'})

    return jsonify({
        'balance': balance,
        'flags': flags
    })

@app.route('/coupons')
def list_coupons():
    """List available coupons"""
    conn = get_db()
    coupons = conn.execute('''
        SELECT code, value, max_redemptions, current_redemptions, active
        FROM coupons
        WHERE active = 1
        ORDER BY value DESC
    ''').fetchall()
    conn.close()

    coupon_list = []
    for c in coupons:
        coupon_list.append({
            'code': c['code'],
            'value': c['value'],
            'max_redemptions': c['max_redemptions'],
            'current_redemptions': c['current_redemptions'],
            'remaining': c['max_redemptions'] - c['current_redemptions']
        })

    return jsonify({'coupons': coupon_list})

def _run_fraud_check(user_id, coupon_code, amount):
    """Simulate external fraud detection API call.
    In production this contacts the EverSec FraudGuard service to verify
    the redemption isn't suspicious. The network round-trip takes ~100ms."""
    time.sleep(0.1)

@app.route('/redeem', methods=['POST'])
def redeem_coupon():
    """
    VULNERABLE: Redeem a coupon without proper synchronization

    This endpoint has a classic race condition (Time-of-Check-Time-of-Use):
    1. Check if coupon is valid and available
    2. [GAP - another request can squeeze in here]
    3. Add balance and update coupon

    Multiple concurrent requests can all pass the check before any update occurs,
    allowing the same coupon to be redeemed multiple times.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    data = request.get_json()
    coupon_code = data.get('code', '').strip().upper()

    if not coupon_code:
        return jsonify({'error': 'Coupon code is required'}), 400

    conn = get_db()

    try:
        # STEP 1: Check if coupon exists and is valid
        # VULNERABLE: No lock or transaction isolation
        coupon = conn.execute('''
            SELECT id, code, value, max_redemptions, current_redemptions, active
            FROM coupons
            WHERE code = ? AND active = 1
        ''', (coupon_code,)).fetchone()

        if not coupon:
            conn.close()
            return jsonify({'error': 'Invalid or inactive coupon'}), 400

        # STEP 2: Check if coupon has redemptions remaining
        # VULNERABLE: This check happens outside of a transaction
        if coupon['current_redemptions'] >= coupon['max_redemptions']:
            conn.close()
            return jsonify({'error': 'Coupon has been fully redeemed'}), 400

        # Simulate fraud check - in production this calls an external API
        # The latency from this check creates the race condition window
        _run_fraud_check(user_id, coupon_code, coupon['value'])

        # STEP 3: Update user balance
        # VULNERABLE: No transaction, no lock
        conn.execute('''
            UPDATE users
            SET balance = balance + ?
            WHERE id = ?
        ''', (coupon['value'], user_id))

        # STEP 4: Increment coupon redemption count
        # VULNERABLE: Increment happens separately
        conn.execute('''
            UPDATE coupons
            SET current_redemptions = current_redemptions + 1
            WHERE id = ?
        ''', (coupon['id'],))

        # STEP 5: Record redemption
        conn.execute('''
            INSERT INTO redemptions (user_id, coupon_id, amount)
            VALUES (?, ?, ?)
        ''', (user_id, coupon['id'], coupon['value']))

        conn.commit()

        # Get updated balance
        user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
        new_balance = user['balance']

        conn.close()

        return jsonify({
            'success': True,
            'message': f'Redeemed {coupon["code"]} for ${coupon["value"]}',
            'new_balance': new_balance
        })

    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/redemptions')
def list_redemptions():
    """List user's redemption history"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()
    redemptions = conn.execute('''
        SELECT r.amount, r.redeemed_at, c.code
        FROM redemptions r
        JOIN coupons c ON r.coupon_id = c.id
        WHERE r.user_id = ?
        ORDER BY r.redeemed_at DESC
    ''').fetchall()
    conn.close()

    history = []
    for r in redemptions:
        history.append({
            'code': r['code'],
            'amount': r['amount'],
            'redeemed_at': r['redeemed_at']
        })

    return jsonify({'redemptions': history})

@app.route('/reset', methods=['POST'])
def reset_account():
    """Reset user balance and coupons"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()

    # Reset user balance
    conn.execute('UPDATE users SET balance = 0 WHERE id = ?', (user_id,))

    # Reset all coupons
    conn.execute('UPDATE coupons SET current_redemptions = 0, active = 1')

    # Clear redemption history
    conn.execute('DELETE FROM redemptions WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Account reset successfully'})

@app.route('/admin/transactions')
def admin_transactions():
    """Hidden admin endpoint - requires $1000+ balance"""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', ('player',)).fetchone()
    if not user or user['balance'] < 1000:
        conn.close()
        return jsonify({'error': 'Insufficient privileges'}), 403

    redemptions = conn.execute('''
        SELECT r.id, r.amount, r.redeemed_at, c.code
        FROM redemptions r
        JOIN coupons c ON r.coupon_id = c.id
        WHERE r.user_id = ?
        ORDER BY r.redeemed_at DESC
    ''', (user['id'],)).fetchall()
    conn.close()

    export = {
        'export_type': 'transaction_audit',
        'generated_by': 'EverSec Financial Systems',
        'total_transactions': len(redemptions),
        'audit_flag': FLAG4,
        'transactions': [{'id': r['id'], 'code': r['code'], 'amount': r['amount'], 'redeemed_at': r['redeemed_at']} for r in redemptions]
    }
    return jsonify(export)

if __name__ == '__main__':
    print("="*60)
    print("🎁 EverSec Gift Card System Starting...")
    print("="*60)
    print("Initializing database...")

    init_db()

    print("Database initialized!")
    print("="*60)
    print("Service running on: http://0.0.0.0:4011")
    print("="*60)

    app.run(host='0.0.0.0', port=4011, debug=False, threaded=True)

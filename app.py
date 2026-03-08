"""Flask backend with SQLite database."""
import os
import secrets
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, get_db, db_cursor
from security import is_sql_injection, is_xss_attempt, log_security_event

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)

# Initialize database on startup
init_db()


def get_user_from_token():
    """Get user from Authorization header token."""
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT u.id, u.email, u.name FROM users u JOIN sessions s ON u.id = s.user_id WHERE s.token = ?',
            (token,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def is_owner(user):
    """Check if user is owner/admin (dashboard access)."""
    if not user:
        return False
    admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
    if admin_email:
        return (user.get('email') or '').lower() == admin_email
    return user.get('id') == 1


# --- API Routes (must be before catch-all) ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    name = (data.get('name') or email.split('@')[0]).strip()

    if not email or not password:
        return jsonify({'ok': False, 'message': 'Email and password required'}), 400
    if len(password) < 4:
        return jsonify({'ok': False, 'message': 'Password must be at least 4 characters'}), 400

    # Detect and log SQL injection / XSS in registration
    if is_sql_injection(email) or is_sql_injection(password) or is_sql_injection(name):
        log_security_event(
            'sql_injection',
            attacker_name=email[:50] if email else 'Unknown',
            fixed=True,
            message='SQL injection attempt blocked. Registration denied.',
            details=f'Email: {email[:80]!r}'
        )
        return jsonify({'ok': False, 'message': 'Invalid input. Suspicious characters detected.'}), 400
    if is_xss_attempt(name) or is_xss_attempt(email):
        log_security_event(
            'xss_attempt',
            attacker_name=email[:50] if email else 'Unknown',
            fixed=True,
            message='XSS attempt blocked. Registration denied.',
            details=f'Name: {name[:80]!r}'
        )
        return jsonify({'ok': False, 'message': 'Invalid input. Suspicious characters detected.'}), 400

    pw_hash = generate_password_hash(password)
    try:
        with db_cursor() as cur:
            cur.execute(
                'INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)',
                (email, pw_hash, name)
            )
            user_id = cur.lastrowid
            token = secrets.token_urlsafe(32)
            cur.execute('INSERT INTO sessions (user_id, token) VALUES (?, ?)', (user_id, token))
    except Exception as e:
        if 'UNIQUE' in str(e):
            return jsonify({'ok': False, 'message': 'Email already registered'}), 400
        raise

    return jsonify({
        'ok': True,
        'token': token,
        'user': {'id': user_id, 'email': email, 'name': name}
    })


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({'ok': False, 'message': 'Email and password required'}), 400

    # Detect and log SQL injection attempts (auto-fixed by parameterized queries)
    if is_sql_injection(email) or is_sql_injection(password):
        log_security_event(
            'sql_injection',
            attacker_name=email[:50] if email else 'Unknown',
            fixed=True,
            message='SQL injection attempt blocked. Login denied.',
            details=f'Email field: {email[:100]!r}'
        )
        return jsonify({'ok': False, 'message': 'Invalid credentials. Suspicious input detected.'}), 401

    with db_cursor() as cur:
        cur.execute('SELECT id, email, name, password_hash FROM users WHERE email = ?', (email,))
        row = cur.fetchone()
        if not row:
            return jsonify({'ok': False, 'message': 'No account with this email. Create an account first.'}), 401
        if not check_password_hash(str(row['password_hash']), password):
            return jsonify({'ok': False, 'message': 'Invalid password.'}), 401

        user_id = row['id']
        email_val = row['email']
        name = row['name']
        token = secrets.token_urlsafe(32)
        cur.execute('INSERT INTO sessions (user_id, token) VALUES (?, ?)', (user_id, token))

    return jsonify({
        'ok': True,
        'token': token,
        'user': {'id': user_id, 'email': email_val, 'name': name or email_val.split('@')[0]}
    })


@app.route('/api/me', methods=['GET'])
def me():
    """Get current user info (includes is_owner for dashboard access)."""
    user = get_user_from_token()
    if not user:
        return jsonify({'ok': False, 'user': None}), 401
    return jsonify({
        'ok': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'is_owner': is_owner(user)
        }
    })


@app.route('/api/security/events', methods=['GET'])
def security_events():
    """Get security events for owner dashboard."""
    user = get_user_from_token()
    if not user or not is_owner(user):
        return jsonify({'ok': False, 'message': 'Access denied'}), 403

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, created_at, event_type, attacker_name, ip_address, location, fixed, message, details
            FROM security_events
            ORDER BY id DESC
            LIMIT 200
        ''')
        rows = cur.fetchall()
        events = [{
            'id': r['id'],
            'created_at': r['created_at'],
            'event_type': r['event_type'],
            'attacker_name': r['attacker_name'],
            'ip_address': r['ip_address'],
            'location': r['location'],
            'fixed': bool(r['fixed']),
            'message': r['message'],
            'details': r['details']
        } for r in rows]
        return jsonify({'ok': True, 'events': events})
    finally:
        conn.close()


@app.route('/api/products', methods=['GET'])
def products():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, name, price, image FROM products ORDER BY id')
        rows = cur.fetchall()
        return jsonify([{k: r[k] for k in r.keys()} for r in rows])
    finally:
        conn.close()


@app.route('/api/orders', methods=['POST'])
def create_order():
    user = get_user_from_token()
    if not user:
        return jsonify({'ok': False, 'message': 'Unauthorized'}), 401

    data = request.get_json() or {}
    items = data.get('items') or []
    shipping_name = (data.get('shipping_name') or '').strip()
    shipping_address = (data.get('shipping_address') or '').strip()

    if not items:
        return jsonify({'ok': False, 'message': 'Cart is empty'}), 400
    if not shipping_name or not shipping_address:
        return jsonify({'ok': False, 'message': 'Shipping name and address required'}), 400

    # Detect and log XSS in shipping fields (auto-fixed by output encoding)
    if is_xss_attempt(shipping_name) or is_xss_attempt(shipping_address):
        log_security_event(
            'xss_attempt',
            attacker_name=user.get('email', 'Unknown'),
            fixed=True,
            message='XSS attempt in shipping fields blocked. Order not placed.',
            details=f'Name: {shipping_name[:80]!r}'
        )
        return jsonify({'ok': False, 'message': 'Invalid characters in shipping details. Please use plain text only.'}), 400

    total = 0.0
    with db_cursor() as cur:
        cur.execute(
            'INSERT INTO orders (user_id, total, shipping_name, shipping_address) VALUES (?, 0, ?, ?)',
            (user['id'], shipping_name, shipping_address)
        )
        order_id = cur.lastrowid

        for item in items:
            pid = item.get('product_id') or item.get('id')
            qty = int(item.get('quantity') or 1)
            cur.execute('SELECT id, name, price FROM products WHERE id = ?', (pid,))
            prod = cur.fetchone()
            if prod:
                price = float(prod['price'])
                total += price * qty
                cur.execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                    (order_id, prod['id'], qty, price)
                )

        cur.execute('UPDATE orders SET total = ? WHERE id = ?', (total, order_id))

    return jsonify({'ok': True, 'order_id': order_id, 'total': total})


@app.route('/api/orders/recent', methods=['GET'])
def recent_orders():
    user = get_user_from_token()
    if not user:
        return jsonify({'ok': False, 'message': 'Unauthorized'}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT id, total, created_at, shipping_name
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 5
            ''',
            (user['id'],)
        )
        rows = cur.fetchall()
        return jsonify([{'id': r['id'], 'total': r['total'], 'created_at': r['created_at'], 'shipping_name': r['shipping_name']} for r in rows])
    finally:
        conn.close()


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id: int):
    user = get_user_from_token()
    if not user:
        return jsonify({'ok': False, 'message': 'Unauthorized'}), 401

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT id, user_id, total, shipping_name, shipping_address, created_at
            FROM orders
            WHERE id = ? AND user_id = ?
            ''',
            (order_id, user['id'])
        )
        order = cur.fetchone()
        if not order:
            return jsonify({'ok': False, 'message': 'Order not found'}), 404

        cur.execute(
            '''
            SELECT oi.product_id, p.name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.id
            ''',
            (order_id,)
        )
        items = cur.fetchall()

        return jsonify({
            'ok': True,
            'order': {
                'id': order['id'],
                'total': order['total'],
                'shipping_name': order['shipping_name'],
                'shipping_address': order['shipping_address'],
                'created_at': order['created_at'],
            },
            'items': [{'product_id': i['product_id'], 'name': i['name'], 'quantity': i['quantity'], 'price': i['price']} for i in items]
        })
    finally:
        conn.close()


# --- Static file serving ---

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve(path):
    if os.path.exists(path) and os.path.isfile(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')


def get_local_ip():
    """Get this machine's local IP so others on the same network can connect."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'
    return ip


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    if not os.environ.get('PORT'):
        local_ip = get_local_ip()
        print('')
        print('  Purchase server running.')
        print('  On this PC:     http://127.0.0.1:{}/'.format(port))
        print('  On same WiFi:  http://{}:{}/'.format(local_ip, port))
        print('  Share the second link with other PCs and phones on your network.')
        print('')
    app.run(host='0.0.0.0', port=port, debug=not os.environ.get('PORT'))

from flask import Flask, request, jsonify, session, abort, send_file

import re
import os
import sqlite3
import uuid

app = Flask(__name__, static_folder='.', static_url_path='')
app.url_map.strict_slashes = False


app.secret_key = 'change-me-in-production'

DB_PATH = os.path.join(os.path.dirname(__file__), 'bins.db')

BIN_SEED = [
    {'name': 'Beirut Central', 'lat': 33.8938, 'lng': 35.5018, 'status': 'normal'},
    {'name': 'Beirut South', 'lat': 33.8547, 'lng': 35.8623, 'status': 'full'},
    {'name': 'Jounieh', 'lat': 33.9677, 'lng': 35.7441, 'status': 'maintenance'},
    {'name': 'Tripoli', 'lat': 34.4358, 'lng': 35.8346, 'status': 'normal'},
    {'name': 'Sidon', 'lat': 33.5688, 'lng': 35.3835, 'status': 'full'},
    {'name': 'Tyre', 'lat': 33.2715, 'lng': 35.1983, 'status': 'normal'},
    {'name': 'Baabda', 'lat': 33.7490, 'lng': 35.7076, 'status': 'maintenance'}
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_bins_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bins (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cur.execute('SELECT COUNT(*) AS c FROM bins')
    if (cur.fetchone()['c'] if cur.rowcount is None else cur.fetchone()):
        pass

    # Seed only if empty
    cur.execute('SELECT COUNT(*) AS c FROM bins')
    c = cur.fetchone()['c']
    if c == 0:
        for b in BIN_SEED:
            cur.execute(
                'INSERT INTO bins (id, name, lat, lng, status) VALUES (?, ?, ?, ?, ?)',
                (str(uuid.uuid4()), b['name'], b['lat'], b['lng'], b['status'])
            )
        conn.commit()


    conn.close()

def bins_for_ai():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT name, lat, lng, status FROM bins')
    rows = cur.fetchall()
    conn.close()
    return [{'name': r['name'], 'lat': r['lat'], 'lng': r['lng'], 'status': r['status']} for r in rows]


def admin_is_logged_in():
    return bool(session.get('admin_logged_in'))


# AI Response logic
def get_ai_response(query, name):
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['hello', 'hi', 'hey']):
        return f"Hello {name}! 👋 Welcome to LebRecycle AI Support. Ask me about recycling bins, locations, statistics, or how our smart bins work!"
    
    elif any(word in query_lower for word in ['bin', 'location', 'near', 'find', 'where']):
        # Query bins from DB so AI stays in sync with admin edits
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT name, status FROM bins')
        rows = cur.fetchall()
        conn.close()
        normal_bins = [ {'name': r['name'], 'status': r['status']} for r in rows if r['status'] == 'normal' ]
        if normal_bins:
            locations = ', '.join([b['name'] for b in normal_bins[:3]])
            return f"Nearest available bins (Normal status): {locations}. Check the interactive map on the main page! 🗺️"
        return "All bins currently full or in maintenance. Please check back later!"
    
    elif any(word in query_lower for word in ['full', 'status']):
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT name, status FROM bins')
        rows = cur.fetchall()
        conn.close()
        full_bins = [r['name'] for r in rows if r['status'] == 'full']
        return f"Currently full bins: {', '.join(full_bins)}. Our collectors will empty them soon! 🚛"
    

    
    elif any(word in query_lower for word in ['stats', 'statistics', 'impact']):
        return "📊 Our Impact: 1,200+ smart bins deployed, 450 tons recycled YTD, 2,500 trees saved, 1,200t CO2 reduced!"
    
    elif any(word in query_lower for word in ['sort', 'recycle', 'recycled', 'recycling', 'plastic', 'paper', 'glass', 'materials']):
        return "Our AI smart bins automatically sort recycled materials: 🟢 Plastic, 📄 Paper, 🔹 Glass, 🪙 Metals using computer vision technology!"
    
    elif any(word in query_lower for word in ['lebanon', 'waste', 'crisis']):
        return "Lebanon produces 7,000 tons waste daily, only 15% recycled. Our mission: 50% recycling by 2030! 🌍"
    
    elif any(word in query_lower for word in ['contact', 'team', 'about']):
        return "Team: Mikael Moussa & Ali Hamieh (LIU). Email: mikaelsmoussa@gmail.com | alihamieh119@gmail.com 📧"
    
    else:
        return f"Thanks for your question, {name}! 😊 I can help with recycling bins locations, statuses, statistics, sorting info, or Lebanon waste facts. What would you like to know?"

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return app.send_static_file(f"static/{path}")

@app.route('/admin')
def admin_index():
    ensure_bins_table()
    # Serve the main admin dashboard page (bins UI)
    return send_file(os.path.join(app.root_path, 'static', 'admin_bins.html'))











@app.route('/admin/')
def admin_index_slash():
    return admin_index()


@app.route('/admin/bins')
def admin_bins_page():
    return send_file(os.path.join(app.root_path, 'static', 'admin_bins.html'))


@app.route('/admin/users')
def admin_users_page():
    ensure_user_tables()
    return send_file(os.path.join(app.root_path, 'static', 'admin_users.html'))



# -----------------
# User auth / points
# -----------------

def ensure_user_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recycling_entries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            amount_kg REAL NOT NULL,
            points_awarded INTEGER NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    conn.commit()

    # Seed demo user: demo / demo
    cur.execute('SELECT id FROM users WHERE username = ?', ('demo',))
    if cur.fetchone() is None:
        import hashlib
        import datetime

        demo_id = str(uuid.uuid4())
        pwd_hash = hashlib.sha256('demo'.encode('utf-8')).hexdigest()
        cur.execute(
            'INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)',
            (demo_id, 'demo', pwd_hash, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()

    conn.close()


def user_is_logged_in():
    return bool(session.get('user_logged_in') and session.get('user_id'))


def points_for_items(items: int) -> int:
    # Demo rule: 1 item = 1 point
    if items <= 0:
        raise ValueError('items must be greater than 0')
    return int(items)



@app.route('/admin/login', methods=['POST'])
def admin_login():

    # Admin login is hardcoded for demo purposes
    ensure_bins_table()

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    if username == 'admin' and password == 'admin':
        session['admin_logged_in'] = True
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 401

@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({'ok': True})


@app.route('/admin/session', methods=['GET'])
def admin_session():
    logged_in = admin_is_logged_in()
    return jsonify({'loggedIn': logged_in})


@app.route('/api/bins', methods=['GET'])
def api_get_bins():
    # Admin-only: full access to bins list
    if not admin_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    ensure_bins_table()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, lat, lng, status FROM bins')
    rows = cur.fetchall()
    conn.close()
    bins_out = []
    for r in rows:
        bins_out.append({
            'id': r['id'],
            'name': r['name'],
            'lat': r['lat'],
            'lng': r['lng'],
            'status': r['status']
        })
    return jsonify(bins_out)


@app.route('/api/bins/public', methods=['GET'])
def api_get_bins_public():
    # Public: used by the home page map to show live DB data.
    ensure_bins_table()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, lat, lng, status FROM bins')
    rows = cur.fetchall()
    conn.close()

    bins_out = []
    for r in rows:
        bins_out.append({
            'id': r['id'],
            'name': r['name'],
            'lat': r['lat'],
            'lng': r['lng'],
            'status': r['status']
        })
    return jsonify(bins_out)


@app.route('/api/users', methods=['GET'])
def api_list_users():
    if not admin_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    ensure_user_tables()

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, created_at FROM users ORDER BY created_at DESC')
    rows = cur.fetchall()

    users_out = []
    for r in rows:
        user_id = r['id']
        cur.execute(
            'SELECT COALESCE(SUM(points_awarded), 0) AS totalPoints FROM recycling_entries WHERE user_id = ?',
            (user_id,)
        )
        total_points = cur.fetchone()['totalPoints']

        cur.execute(
            'SELECT COUNT(*) AS c FROM recycling_entries WHERE user_id = ?',
            (user_id,)
        )
        recent_entries = cur.fetchone()['c']

        users_out.append({
            'id': user_id,
            'username': r['username'],
            'totalPoints': total_points,
            # Keep the property name aligned with frontend usage
            'recentEntries': recent_entries,
        })

    conn.close()
    return jsonify(users_out)


@app.route('/api/users/<user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    if not admin_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    ensure_user_tables()

    try:
        user_id = str(user_id)
    except Exception:
        return jsonify({'error': 'invalid user id'}), 400

    conn = get_db()
    cur = conn.cursor()

    # Check user exists
    cur.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    exists = cur.fetchone() is not None
    if not exists:
        conn.close()
        return jsonify({'error': 'not found'}), 404

    data = request.get_json(silent=True) or {}
    delete_history = bool(data.get('deleteHistory'))

    if delete_history:
        cur.execute('DELETE FROM recycling_entries WHERE user_id = ?', (user_id,))

    cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/bins', methods=['POST'])
def api_add_bin():

    if not admin_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    ensure_bins_table()
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    lat = float(data.get('lat'))
    lng = float(data.get('lng'))
    status = (data.get('status') or '').strip()
    if status not in {'normal', 'full', 'maintenance'}:
        return jsonify({'error': 'invalid status'}), 400
    if not name:
        return jsonify({'error': 'name required'}), 400
    bin_id = str(uuid.uuid4())
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO bins (id, name, lat, lng, status) VALUES (?, ?, ?, ?, ?)', (bin_id, name, lat, lng, status))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'id': bin_id})

@app.route('/api/bins/<bin_id>', methods=['PUT'])
def api_update_bin(bin_id):
    if not admin_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    ensure_bins_table()
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    lat = float(data.get('lat'))
    lng = float(data.get('lng'))
    status = (data.get('status') or '').strip()
    if status not in {'normal', 'full', 'maintenance'}:
        return jsonify({'error': 'invalid status'}), 400
    if not name:
        return jsonify({'error': 'name required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE bins SET name = ?, lat = ?, lng = ?, status = ? WHERE id = ?', (name, lat, lng, status, bin_id))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    if not ok:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'ok': True})

@app.route('/api/bins/<bin_id>', methods=['DELETE'])
def api_delete_bin(bin_id):
    if not admin_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401
    ensure_bins_table()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM bins WHERE id = ?', (bin_id,))
    conn.commit()
    ok = cur.rowcount > 0
    conn.close()
    if not ok:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'ok': True})

@app.route('/get_answer')
def get_answer():

    # Admin-only gating: if user tries to use admin privileges from AI chat,
    # block access unless they are on /admin.
    # Since this app is single-process demo, we enforce by requiring a flag
    # that only /admin page loads (see admin.html).
    query = request.args.get('query', '').strip()
    name = request.args.get('name', 'User').strip()
    email = request.args.get('email', '').strip()
    
    if not query:
        return jsonify({'Answer': 'Please ask a question about recycling!'})
    
    response = get_ai_response(query, name)
    
    # Log query (optional)
    print(f"AI Query from {email} ({name}): {query}")
    print(f"Response: {response[:100]}...")
    
    return jsonify({'Answer': response})

@app.route('/user')
def user_page_redirect():
    return send_file(os.path.join(app.root_path, 'static', 'user.html'))


@app.route('/user/register', methods=['POST'])
def user_register():
    ensure_user_tables()
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not re.fullmatch(r'[A-Za-z0-9_]{3,20}', username):
        return jsonify({'error': 'invalid username'}), 400
    if len(password) < 4:
        return jsonify({'error': 'password too short'}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cur.fetchone() is not None:
        conn.close()
        return jsonify({'error': 'username taken'}), 400

    import hashlib
    import datetime

    user_id = str(uuid.uuid4())
    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    cur.execute(
        'INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)',
        (user_id, username, pwd_hash, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    session['user_logged_in'] = True
    session['user_id'] = user_id

    return jsonify({'ok': True})


@app.route('/user/login', methods=['POST'])
def user_login():
    ensure_user_tables()
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return jsonify({'error': 'missing credentials'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({'error': 'invalid username or password'}), 401

    import hashlib

    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    if pwd_hash != row['password_hash']:
        return jsonify({'error': 'invalid username or password'}), 401

    session['user_logged_in'] = True
    session['user_id'] = row['id']

    return jsonify({'ok': True})



@app.route('/user/logout', methods=['POST'])
def user_logout():
    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.route('/user/session', methods=['GET'])
def user_session():
    if not user_is_logged_in():
        return jsonify({'loggedIn': False})
    return jsonify({'loggedIn': True})


@app.route('/user/recycle', methods=['POST'])
def user_recycle():
    ensure_user_tables()
    if not user_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True) or {}

    material = (data.get('material') or '').strip().lower()
    quantity = data.get('quantity')
    notes = (data.get('notes') or '').strip()

    allowed = {'paper', 'glass', 'metal', 'plastic'}
    if material not in allowed:
        return jsonify({'error': 'invalid material'}), 400

    try:
        quantity = float(quantity)
    except Exception:
        return jsonify({'error': 'invalid quantity'}), 400

    if quantity <= 0:
        return jsonify({'error': 'quantity must be a positive number'}), 400

    # Keep existing “1 item = 1 point” rule, but apply it to quantity.
    points = points_for_items(int(quantity))

    import datetime
    today = datetime.datetime.utcnow().date().isoformat()

    user_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()

    entry_id = str(uuid.uuid4())
    cur.execute(
        'INSERT INTO recycling_entries (id, user_id, date, amount_kg, points_awarded, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (entry_id, user_id, today, float(quantity), points, notes if notes else f"{material.title()}", datetime.datetime.utcnow().isoformat())
    )

    cur.execute(
        'SELECT COALESCE(SUM(points_awarded), 0) AS totalPoints FROM recycling_entries WHERE user_id = ?',
        (user_id,)
    )
    total_points = cur.fetchone()['totalPoints']

    conn.commit()
    conn.close()

    return jsonify({
        'ok': True,
        'pointsAwarded': points,
        'totalPoints': total_points,
        'entry': {
            'id': entry_id,
            'date': today,
            'material': material,
            'quantity': quantity,
            'points': points,
            'notes': notes if notes else f"{material.title()}"
        }
    })


@app.route('/user/profile', methods=['GET'])
def user_profile():
    ensure_user_tables()
    if not user_is_logged_in():
        return jsonify({'error': 'unauthorized'}), 401

    user_id = session.get('user_id')

    conn = get_db()
    cur = conn.cursor()

    cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    u = cur.fetchone()
    username = u['username'] if u else ''

    cur.execute('SELECT COALESCE(SUM(points_awarded), 0) AS totalPoints FROM recycling_entries WHERE user_id = ?', (user_id,))
    total_points = cur.fetchone()['totalPoints']

    cur.execute(
        'SELECT date, amount_kg, points_awarded, notes FROM recycling_entries WHERE user_id = ? ORDER BY date DESC, created_at DESC LIMIT 10',
        (user_id,)
    )
    entries = cur.fetchall()
    conn.close()

    recent_entries = [
        {
            'date': r['date'],
            # DB column name stays amount_kg; UI shows items count
            'items': int(float(r['amount_kg'])),
            'points': r['points_awarded'],
            'notes': r['notes']
        }
        for r in entries
    ]


    # lastEntry format for the client
    last_entry = None
    if entries:
        first = entries[0]
        last_entry = {'date': first['date'], 'points': first['points_awarded']}

    return jsonify({'username': username, 'totalPoints': total_points, 'recentEntries': recent_entries, 'lastEntry': last_entry})



if __name__ == '__main__':
    print("🚀 Starting LebRecycle server on http://localhost:8000")
    print("📱 AI Chat fully functional at /static/recycling-chat.html")

    app.run(host='localhost', port=8000, debug=True, use_reloader=False)






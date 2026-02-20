from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import firebase_admin
from firebase_admin import credentials, db # Added db here to ensure reference() works
from firebase_config import get_db, get_portfolio_ref, DATABASE_URL
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-key')

def get_db_ref():
    try:
        ref = get_portfolio_ref()
        return ref
    except Exception:
        return None

# --- PUBLIC ROUTE ---
@app.route('/')
def index():
    try:
        # Use the imported get_portfolio_ref to stay consistent
        ref = get_portfolio_ref()
        portfolio_data = ref.get() or {}
    except Exception:
        portfolio_data = {}
    return render_template('index.html', data=portfolio_data)

# --- API ROUTES (Used by admin.html JavaScript) ---

@app.route('/api/data', methods=['GET'])
def api_get_data():
    ref = get_db_ref()
    if not ref:
        return jsonify({'error': 'firebase_unavailable'}), 503
    try:
        data = ref.get() or {}
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<category>', methods=['POST'])
def api_add_entry(category):
    if 'admin' not in session: return jsonify({'error': 'unauthorized'}), 401
    entry = request.get_json() or {}
    ref = get_portfolio_ref()
    
    try:
        # Match your logic: profile/socials overwrite, others push
        if category in ['profile', 'socials', 'description']:
            ref.child(category).set(entry)
            return jsonify({'success': True})
        else:
            new_ref = ref.child(category).push(entry)
            return jsonify({'success': True, 'id': new_ref.key})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<category>/<item_id>', methods=['PUT', 'POST'])
def api_update_entry(category, item_id):
    if 'admin' not in session: return jsonify({'error': 'unauthorized'}), 401
    entry = request.get_json() or {}
    ref = get_portfolio_ref()
    try:
        # Fixed pathing to use the specific item ID
        ref.child(category).child(item_id).update(entry)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/<category>/<item_id>', methods=['DELETE'])
def api_delete_entry(category, item_id):
    if 'admin' not in session: return jsonify({'error': 'unauthorized'}), 401
    ref = get_portfolio_ref()
    try:
        ref.child(category).child(item_id).delete()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ADMIN ROUTES ---

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        admin_creds = load_admin() or {}

        if not email or not password:
            error = 'All fields are required.'
        elif email != admin_creds.get('email'):
            error = 'Invalid credentials.'
        elif not check_password_hash(admin_creds.get('password_hash', ''), password):
            error = 'Invalid credentials.'
        else:
            session['admin'] = True
            return redirect(url_for('admin'))
    return render_template('login.html', error=error)

@app.route('/admin')
def admin():
    if 'admin' not in session: 
        return redirect(url_for('login'))
    
    ref = get_portfolio_ref()
    portfolio_data = ref.get() or {}
    # Passing 'data' ensures admin.html loops work
    return render_template('admin.html', data=portfolio_data)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# --- DIAGNOSTICS (Kept exactly as requested) ---

@app.route('/db_test')
def db_test():
    try:
        sample = db.reference('/').get()
        return {'connected': True, 'sample_preview': sample}
    except Exception as e:
        return {'connected': False, 'error': str(e)}, 500

@app.route('/firebase_status')
def firebase_status():
    info = {'database_url': DATABASE_URL}
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'serviceAccount.json')
    try:
        if os.path.exists(cred_path):
            with open(cred_path, 'r', encoding='utf-8') as f:
                sa = json.load(f)
            info['service_account_project_id'] = sa.get('project_id')
    except: pass

    ref = get_portfolio_ref()
    try:
        sample = ref.get()
        info['db_test'] = {'ok': True, 'sample_preview': sample}
    except Exception as e:
        info['db_test'] = {'ok': False, 'error': str(e)}
    return jsonify(info)

# --- HELPERS ---

ADMIN_CRED_FILE = os.path.join(os.path.dirname(__file__), 'admin_credentials.json')

def load_admin():
    try:
        if os.path.exists(ADMIN_CRED_FILE):
            with open(ADMIN_CRED_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: return None
    return None

if __name__ == '__main__':
    app.run(debug=True)

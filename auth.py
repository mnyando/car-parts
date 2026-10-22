"""Accounts, sessions and role-based access.

Users live in the "users" collection, keyed by lowercased email:
    {name, email, phone, password_hash, role: "admin" | "shopper", created_at}

Anyone can sign up as a shopper. Emails listed in ADMIN_EMAIL (comma separated)
become admins when they sign up or log in; admins can promote others later.
"""
import datetime
import functools
import hmac
import os
import re
import secrets

from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__)

MIN_PASSWORD_LENGTH = 8
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
# Checked when the email doesn't exist so response time doesn't reveal which emails have accounts
_DUMMY_HASH = generate_password_hash('not-a-real-password')

# Set by init_auth()
_db = None


def admin_emails():
    return {e.strip().lower() for e in os.getenv('ADMIN_EMAIL', '').split(',') if e.strip()}


def get_user(email):
    if not email:
        return None
    snap = _db.collection('users').document(email.lower()).get()
    if not snap.exists:
        return None
    user = snap.to_dict()
    user['id'] = snap.id
    return user


def is_admin(user=None):
    user = user if user is not None else g.get('user')
    return bool(user) and user.get('role') == 'admin'


def _wants_json():
    return request.is_json or request.path.startswith('/orders/') or request.path == '/checkout'


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not g.get('user'):
            if _wants_json():
                return jsonify({'error': 'Please log in to continue', 'login_url': url_for('auth.login')}), 401
            return redirect(url_for('auth.login', next=request.full_path.rstrip('?')))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @functools.wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not is_admin():
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_urlsafe(32)
    return session['_csrf']


def _safe_next(target):
    """Only allow redirects to paths on this site (no //evil.com or absolute URLs)."""
    if target and target.startswith('/') and not target.startswith('//') and '\\' not in target:
        return target
    return url_for('catalog')


def init_auth(app, db, csrf_exempt=()):
    """Register the blueprint and request hooks. csrf_exempt: endpoint names that skip CSRF."""
    global _db
    _db = db

    secret = os.getenv('SECRET_KEY')
    if not secret:
        secret = secrets.token_hex(32)
        print("SECRET_KEY not set: using a random key, so everyone is logged out on restart. "
              "Set SECRET_KEY in production.", flush=True)
    app.config.update(
        SECRET_KEY=secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        # Render serves over HTTPS and sets RENDER=true
        SESSION_COOKIE_SECURE=bool(os.getenv('RENDER')) or os.getenv('SESSION_COOKIE_SECURE') == '1',
        PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=14),
    )
    app.register_blueprint(bp)

    @app.before_request
    def load_user_and_check_csrf():
        if request.endpoint == 'static':
            return
        g.user = get_user(session.get('user_id'))
        if session.get('user_id') and not g.user:
            session.pop('user_id', None)  # account deleted

        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and request.endpoint not in csrf_exempt:
            sent = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token') or ''
            if not hmac.compare_digest(sent, session.get('_csrf', '')):
                if _wants_json():
                    return jsonify({'error': 'Your session expired, please refresh the page'}), 400
                abort(400, description='Your session expired, please go back and try again.')

    @app.context_processor
    def inject_auth():
        return {'current_user': g.get('user'), 'is_admin': is_admin(), 'csrf_token': csrf_token}


def _start_session(user):
    session.clear()  # new session id on login (prevents session fixation)
    session.permanent = True
    session['user_id'] = user['id']
    csrf_token()


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if g.user:
        return redirect(url_for('catalog'))
    form = {'name': '', 'email': '', 'phone': ''}
    if request.method == 'POST':
        form = {k: request.form.get(k, '').strip() for k in form}
        email = form['email'].lower()
        password = request.form.get('password', '')
        error = None
        if not form['name']:
            error = 'Please enter your name.'
        elif not EMAIL_RE.match(email):
            error = 'Please enter a valid email address.'
        elif len(password) < MIN_PASSWORD_LENGTH:
            error = f'Password must be at least {MIN_PASSWORD_LENGTH} characters.'
        elif password != request.form.get('confirm', ''):
            error = 'Passwords do not match.'
        elif get_user(email):
            error = 'An account with that email already exists. Please log in.'

        if error:
            flash(error, 'error')
        else:
            user = {
                'name': form['name'][:80],
                'email': email,
                'phone': form['phone'][:20],
                'password_hash': generate_password_hash(password),
                'role': 'admin' if email in admin_emails() else 'shopper',
                'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            _db.collection('users').document(email).set(user)
            user['id'] = email
            _start_session(user)
            return redirect(_safe_next(request.args.get('next')))
    return render_template('auth/signup.html', form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(_safe_next(request.args.get('next')))
    email = ''
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = get_user(email)
        password_ok = check_password_hash(user.get('password_hash', '') if user else _DUMMY_HASH,
                                          request.form.get('password', ''))
        if user and password_ok:
            if email in admin_emails() and user.get('role') != 'admin':
                _db.collection('users').document(email).update({'role': 'admin'})
                user['role'] = 'admin'
            _start_session(user)
            return redirect(_safe_next(request.args.get('next')))
        flash('Incorrect email or password.', 'error')
    return render_template('auth/login.html', email=email)


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

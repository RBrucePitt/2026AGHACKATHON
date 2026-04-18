import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Code for register blueprint
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        db = get_db()
        error = None

        required_fields = {
            'username': 'Username',
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'farm_name': 'Farm Name',
            'password': 'Password'
        }

        for field, friendly_name in required_fields.items():
            if not request.form.get(field):
                error = f"{friendly_name} is required."
                break  
        
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, email, first_name, last_name, farm_name, password)"
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        request.form['username'], 
                        request.form['email'], 
                        request.form['first_name'], 
                        request.form['last_name'], 
                        request.form['farm_name'], 
                        generate_password_hash(request.form['password'])
                     ),
                )
                db.commit()
            except db.IntegrityError:
                if db.execute("SELECT id FROM user WHERE username = ?", (request.form['username'],)).fetchone():
                    error = f"Username {request.form['username']} is already registered."
                elif db.execute("SELECT id FROM user WHERE email = ?", (request.form['email'],)).fetchone():
                    error = f"Email {request.form['email']} is already registered."
                else:
                    error = "A database error occurred."            
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    # Required fields
    form_fields = [
        ('username', 'Username', 'text'),
        ('email', 'Email Address', 'email'),
        ('first_name', 'First Name', 'text'),
        ('last_name', 'Last Name', 'text'),
        ('farm_name', 'Farm Name', 'text'),
        ('password', 'Password', 'password')
    ]

    return render_template('auth/register.html', fields=form_fields)

# Code for login blueprint
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            # Updates last login date!
            db.execute(
                'UPDATE user SET last_login_dtm = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            db.commit()

            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

# Checks if user is logged in
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

# Logout blueprint
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Enforces authenticiation
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
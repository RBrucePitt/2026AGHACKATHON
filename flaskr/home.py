from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from . import form

bp = Blueprint('home', __name__)

# Home
@bp.route('/')
def index():
# If they aren't logged in, show a generic landing page
    if g.user is None:
        return render_template('home/landing.html')

    db = get_db()
    # Get the count of existing forms for THIS user
    form_count = db.execute(
        'SELECT COUNT(id) FROM post WHERE author_id = ?', (g.user['id'],)
    ).fetchone()[0]

    return render_template('home/index.html', form_count=form_count)

# Creation!
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        year = request.form['year']
        farm_name = request.form['farm_name']
        db = get_db()
        error = None

        if not year:
            error = 'Crop Year is required.'

        if error is None:
            # Create the 'Header'
            cursor = db.execute(
                'INSERT INTO report (year, farm_name, author_id) VALUES (?, ?, ?)',
                (year, farm_name, g.user['id'])
            )
            db.commit()
            # Redirect to the page where they add the actual crops
            return redirect(url_for('home.add_item', id=cursor.lastrowid))

        flash(error)
    return render_template('blog/create.html')

# Update
def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

# Updating!

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

# Delete
@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
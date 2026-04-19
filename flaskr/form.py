from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('report', __name__, url_prefix='/report')

@bp.route('/start')
@login_required
def start():
    # Logic to initialize a new report in the DB
    return render_template('report/step1_farm_info.html')

@bp.route('/<int:id>/tracts')
@login_required
def tracts(id):
    # Logic for adding land parcels
    return render_template('report/step2_tracts.html')
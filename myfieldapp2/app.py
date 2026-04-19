import os
import zipfile
import io
import geopandas as gpd
from shapely.geometry import shape
from flask import jsonify, send_file
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError


# --- 1. APP CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-123456789' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 2. DATABASE INITIALIZATION ---
db = SQLAlchemy(app)

# --- 3. DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address_line1 = db.Column(db.String(150), nullable=False)
    address_line2 = db.Column(db.String(150))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    farm_name = db.Column(db.String(100), nullable=False)
    gov_farm_number = db.Column(db.String(50))
    address_line1 = db.Column(db.String(150))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    county = db.Column(db.String(100))
    farmland_type = db.Column(db.String(100))
    cropland_type = db.Column(db.String(100))
    operator_name = db.Column(db.String(100))
    operator_address = db.Column(db.String(255))
    operator_phone = db.Column(db.String(20))
    google_kml_name = db.Column(db.String(255))
    usda_shape_name = db.Column(db.String(255))
    usda_shape_guid = db.Column(db.String(100))
    system_guid = db.Column(db.String(100), default=lambda: str(uuid.uuid4()))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile = db.relationship('UserProfile', backref=db.backref('farms', lazy=True))

class Field(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    profile_id = db.Column(db.Integer, nullable=False)
    field_name = db.Column(db.String(100), nullable=False)
    field_shapefile_name = db.Column(db.String(255))
    field_usda_guid = db.Column(db.String(100))
    internal_guid = db.Column(db.String(100), default=lambda: str(uuid.uuid4()))
    google_kml_filename = db.Column(db.String(255))
    crops = db.relationship('Crop', backref='field', lazy=True)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    profile_id = db.Column(db.Integer, nullable=False)
    crop_name = db.Column(db.String(100), nullable=False)
    crop_usda_code = db.Column(db.String(20))
    subtype = db.Column(db.String(100))
    land_usage = db.Column(db.String(100))
    estimated_yield = db.Column(db.Float)

# --- 4. FORM CLASSES ---
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters.")
    ])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Account')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# --- 5. CREATE DATABASE TABLES ---
with app.app_context():
    db.create_all()

# --- 6. ROUTES ---

# HARDCODED USER FOR TESTING
TEST_USER_ID = 1

@app.route("/")
@app.route("/landing")
def landing():
    return render_template('index.html')

@app.route("/create-account", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            password=form.password.data 
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # FIX: Adding empty required fields to prevent DB crash on creation
            new_profile = UserProfile(
                user_id=new_user.id, 
                full_name=new_user.username, 
                phone=new_user.phone,
                address_line1="TBD",
                city="TBD",
                state="TBD",
                zip_code="00000"
            )
            db.session.add(new_profile)
            db.session.commit()

            flash(f'Account created! You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Email or Username may be taken.', 'danger')
            
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.password == form.password.data:
            # Session logic removed. Just redirects for testing.
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/logout")
def logout():
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/setup-profile", methods=['GET', 'POST'])
def setup_profile():
    user_id = TEST_USER_ID
    
    if request.method == 'POST':
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            
        profile.full_name = request.form.get('full_name')
        profile.company_name = request.form.get('company_name')
        profile.phone = request.form.get('phone')
        profile.address_line1 = request.form.get('address_line1')
        profile.address_line2 = request.form.get('address_line2') 
        profile.city = request.form.get('city')
        profile.state = request.form.get('state')
        profile.zip_code = request.form.get('zip_code')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('manage_farms'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
        
    return render_template('setup_profile.html')

@app.route("/farms", methods=['GET', 'POST'])
def manage_farms():
    profile = UserProfile.query.filter_by(user_id=TEST_USER_ID).first()
    
    if request.method == 'POST':
        new_farm = Farm(
            user_id=profile.user_id,
            profile_id=profile.id,
            farm_name=request.form.get('farm_name'), 
            gov_farm_number=request.form.get('gov_number'),
        )
        
        try:
            db.session.add(new_farm)
            db.session.commit()
            flash('Farm saved! Proceeding to mapping.', 'success')
            
            # CHANGE: Redirect directly to Step 3 with URL parameters
            return redirect(url_for('fsa_step3', 
                                    farm_no=new_farm.gov_farm_number, 
                                    program_yr=2026)) 
            
        except IntegrityError:
            db.session.rollback() 
            flash('Error: The Farm Name is required.', 'danger')
            return redirect(url_for('manage_farms'))
        except Exception as e:
            db.session.rollback()
            flash('An unexpected error occurred.', 'danger')
            return redirect(url_for('manage_farms'))

    farms = Farm.query.filter_by(profile_id=profile.id).all() if profile else []
    return render_template('farms.html', farms=farms)

@app.route("/farm/<int:farm_id>/fields", methods=['GET', 'POST'])
def manage_fields(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    
    if request.method == 'POST':
        new_field = Field(
            farm_id=farm.id,
            user_id=farm.user_id,
            profile_id=farm.profile_id,
            field_name=request.form.get('field_name'),
        )
        db.session.add(new_field)
        db.session.commit()
        flash('Field created successfully!', 'success')
        return redirect(url_for('fsa_step3', farm_id=farm.id))

    fields = Field.query.filter_by(farm_id=farm_id).all()
    return render_template('fields.html', farm=farm, fields=fields)

@app.route("/add-crop/<int:field_id>", methods=['POST'])
def add_crop(field_id):
    field = Field.query.get_or_404(field_id)
    new_crop = Crop(
        field_id=field.id,
        user_id=field.user_id,
        profile_id=field.profile_id,
        crop_name=request.form.get('crop_name'),
        crop_usda_code=request.form.get('crop_code'),
        subtype=request.form.get('subtype')
    )
    db.session.add(new_crop)
    db.session.commit()
    return redirect(url_for('manage_fields', farm_id=field.farm_id))


@app.route("/fsa-578/step1", methods=['GET', 'POST'])
def fsa_step1():
    if request.method == 'POST':
        # Grab the data from the form fields
        f_no = request.form.get('farm_no')
        p_yr = request.form.get('program_yr')
        
        # Pass them as URL parameters to step 2
        return redirect(url_for('fsa_step2', farm_no=f_no, program_yr=p_yr))
            
    prefill_operator = ""
    profile = UserProfile.query.filter_by(user_id=TEST_USER_ID).first()
    
    if profile:
        name = profile.company_name if profile.company_name else profile.full_name
        address1 = profile.address_line1 or ""
        address2 = f", {profile.address_line2}" if profile.address_line2 else ""
        city = profile.city or ""
        state = profile.state or ""
        zip_code = profile.zip_code or ""
        
        prefill_operator = f"{name}\n{address1}{address2}\n{city}, {state} {zip_code}".strip()

    return render_template('fsa_step1.html', prefill_operator=prefill_operator)

@app.route("/fsa-578/step2", methods=['GET', 'POST'])
def fsa_step2():
    if request.method == 'POST':
        # Grab the data from the form
        tract = request.form.get('tract_no')
        field = request.form.get('field_no')
        # Pass the data to the NEXT route via the URL
        return redirect(url_for('fsa_step3', tract=tract, field=field))
        
    return render_template('fsa_step2.html')

@app.route("/fsa-578/step3")
def fsa_step3():
    # Pull data from the URL parameters
    farm_no = request.args.get('farm_no', 'N/A')
    program_yr = request.args.get('program_yr', 'N/A')
    tract_no = request.args.get('tract', 'N/A')
    field_no = request.args.get('field', 'N/A')
    
    return render_template('fsa_step3.html', 
                           farm_no=farm_no, 
                           program_yr=program_yr,
                           tract_no=tract_no, 
                           field_no=field_no)

@app.route('/fsa-578/convert', methods=['POST'])
def convert_shapefile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        gdf = gpd.GeoDataFrame.from_features([data])
        gdf.set_crs(epsg=4326, inplace=True)

        zip_buffer = io.BytesIO()
        temp_folder = "temp_export"
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
            
        base_name = "field_boundary"
        shp_path = os.path.join(temp_folder, f"{base_name}.shp")
        
        gdf.to_file(shp_path)

        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                file_path = os.path.join(temp_folder, f"{base_name}{ext}")
                zf.write(file_path, arcname=f"{base_name}{ext}")
                os.remove(file_path) 

        zip_buffer.seek(0)
        
        # Session cleanup removed
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='fsa578_field_boundary.zip'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/fsa-578/finalize', methods=['POST'])
def fsa_finalize():
    data = request.get_json()
    acreage = data.get('acreage')
    
    # Session cleanup removed
    flash(f'FSA-578 submitted successfully! Total Acreage: {acreage}', 'success')
    return jsonify({"status": "success"})

@app.route("/simulator")
def simulator():
    # Renders the simulation page corresponding to the hackathon repository
    return render_template('simulation.html')

# --- 7. RUN THE APP ---
if __name__ == '__main__':
    app.run(debug=True)
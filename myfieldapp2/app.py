import os
import zipfile
import io
import geopandas as gpd
from shapely.geometry import shape
from flask import jsonify, send_file
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError


# --- 1. APP CONFIGURATION ---
app = Flask(__name__)
# The Secret Key is required for Flask-WTF forms to prevent CSRF errors
app.config['SECRET_KEY'] = 'dev-key-123456789' 
# SQLite initialization: 'users.db' will be created in your project folder
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
    # The 'ident' link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    
    # Profile Fields
    full_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Mailing Address Fields
    address_line1 = db.Column(db.String(150), nullable=False)
    address_line2 = db.Column(db.String(150))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)

    # Relationship to allow: user.profile
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    # Farm Identification
    farm_name = db.Column(db.String(100), nullable=False)
    gov_farm_number = db.Column(db.String(50))
    
    # Address & Location
    address_line1 = db.Column(db.String(150))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(10))
    county = db.Column(db.String(100))
    
    # Land Classification
    farmland_type = db.Column(db.String(100))
    cropland_type = db.Column(db.String(100))
    
    # Operator Info
    operator_name = db.Column(db.String(100))
    operator_address = db.Column(db.String(255))
    operator_phone = db.Column(db.String(20))
    
    # File References
    google_kml_name = db.Column(db.String(255))
    usda_shape_name = db.Column(db.String(255))
    usda_shape_guid = db.Column(db.String(100))
    system_guid = db.Column(db.String(100), default=lambda: str(uuid.uuid4()))
    
    # Timestamps
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to profile
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

    # Relationship to access crops easily
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
# This ensures users.db and the User table exist before the first request
with app.app_context():
    db.create_all()

# --- 6. ROUTES ---

@app.route("/")
@app.route("/landing")
def landing():
    # This represents your existing landing page
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
            
            # FIX: Create an empty profile so Step 1 doesn't crash or stay empty
            new_profile = UserProfile(user_id=new_user.id, full_name=new_user.username, phone=new_user.phone)
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
        # Search for the user by email
        user = User.query.filter_by(email=form.email.data).first()
        
        # Check if user exists and password matches plain text
        if user and user.password == form.password.data:
            session['user_id'] = user.id  # CRITICAL: This logs the user in
            session['username'] = user.username
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
    session.clear() # Removes user_id and logged-in status
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/setup-profile", methods=['GET', 'POST'])
def setup_profile():
    # 1. Make sure they are logged in
    if 'user_id' not in session:
        flash('Please login to edit your profile.', 'warning')
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    
    if request.method == 'POST':
        # 2. Check if a profile already exists so we UPDATE instead of creating duplicates
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            
        # 3. Pull data using the EXACT 'name' attributes from your HTML form
        profile.full_name = request.form.get('full_name')
        profile.company_name = request.form.get('company_name')
        profile.phone = request.form.get('phone')
        profile.address_line1 = request.form.get('address_line1')
        profile.address_line2 = request.form.get('address_line2') # Added this!
        profile.city = request.form.get('city')
        profile.state = request.form.get('state')
        profile.zip_code = request.form.get('zip_code')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
        
    return render_template('setup_profile.html')

@app.route("/farms", methods=['GET', 'POST'])
def manage_farms():
    profile = UserProfile.query.order_by(UserProfile.id.desc()).first()
    
    if request.method == 'POST':
        new_farm = Farm(
            user_id=profile.user_id,
            profile_id=profile.id,
            farm_name=request.form.get('farm_name'), # Mandatory field
            gov_farm_number=request.form.get('gov_number'),
            # ... other fields ...
        )
        
        try:
            db.session.add(new_farm)
            db.session.commit()
            flash('Farm added successfully!', 'success')
            return redirect(url_for('manage_farms'))
            
        except IntegrityError:
            # This happens if a NOT NULL constraint is hit
            db.session.rollback() # Important: undo the failed change
            flash('Error: The Farm Name is required. Please fill it in and try again.', 'danger')
            return redirect(url_for('manage_farms'))
            
        except Exception as e:
            # A catch-all for other unexpected database errors
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return redirect(url_for('manage_farms'))

    farms = Farm.query.filter_by(profile_id=profile.id).all() if profile else []
    return render_template('farms.html', farms=farms)

@app.route("/farm/<int:farm_id>/fields", methods=['GET', 'POST'])
def manage_fields(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    
    if request.method == 'POST':
        # Logic to add a new field
        new_field = Field(
            farm_id=farm.id,
            user_id=farm.user_id,
            profile_id=farm.profile_id,
            field_name=request.form.get('field_name'),
            # Shapefile/KML names would be populated by your mapping logic
        )
        db.session.add(new_field)
        db.session.commit()
        flash('Field created successfully!', 'success')
        return redirect(url_for('manage_fields', farm_id=farm.id))

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
    if 'user_id' not in session:
        flash('Please login to access forms.', 'warning')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        # Save Step 1 data to session temporarily
        session['fsa_farm_no'] = request.form.get('farm_no')
        session['fsa_program_yr'] = request.form.get('program_yr')
        session['fsa_operator_name'] = request.form.get('operator_name')
        return redirect(url_for('fsa_step2'))
        
    # --- AUTO-IMPORT PROFILE DATA ---
    prefill_operator = ""
    # Query the database for the current user's profile
    profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
    
    if profile:
        # Prefer Company Name, fallback to Full Name
        name = profile.company_name if profile.company_name else profile.full_name
        
        # Build the address string safely handling empty fields
        address1 = profile.address_line1 or ""
        address2 = f", {profile.address_line2}" if profile.address_line2 else ""
        city = profile.city or ""
        state = profile.state or ""
        zip_code = profile.zip_code or ""
        
        # Format it exactly how the FSA-578 textarea expects it
        prefill_operator = f"{name}\n{address1}{address2}\n{city}, {state} {zip_code}".strip()

    return render_template('fsa_step1.html', prefill_operator=prefill_operator)

@app.route("/fsa-578/step2", methods=['GET', 'POST'])
def fsa_step2():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        # Save the Tract and Field numbers to the session so Step 3 can use them!
        session['fsa_tract_no'] = request.form.get('tract_no')
        session['fsa_field_no'] = request.form.get('field_no')
        
        # REDIRECT TO STEP 3, NOT HOME!
        return redirect(url_for('fsa_step3'))
        
    return render_template('fsa_step2.html')
# Step 3
@app.route("/fsa-578/step3", methods=['GET'])
def fsa_step3():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('fsa_step3.html')

@app.route('/fsa-578/convert', methods=['POST'])
def convert_shapefile():
    try:
        # Get GeoJSON data from the frontend map
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features([data])
        
        # Set the coordinate system to WGS84 (Standard for GPS/USDA)
        gdf.set_crs(epsg=4326, inplace=True)

        # Create an in-memory zip file
        zip_buffer = io.BytesIO()
        temp_folder = "temp_export"
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
            
        base_name = "field_boundary"
        shp_path = os.path.join(temp_folder, f"{base_name}.shp")
        
        # Export to Shapefile
        gdf.to_file(shp_path)

        # Zip the .shp, .shx, .dbf, and .prj files
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for ext in ['.shp', '.shx', '.dbf', '.prj']:
                file_path = os.path.join(temp_folder, f"{base_name}{ext}")
                zf.write(file_path, arcname=f"{base_name}{ext}")
                os.remove(file_path) # Clean up temp files

        zip_buffer.seek(0)
        
        # Clear the temporary session data as the form is "complete"
        session.pop('fsa_farm_no', None)
        session.pop('fsa_program_yr', None)
        session.pop('fsa_operator_name', None)
        
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
    
    # Clear the session data now that the form is finished
    session.pop('fsa_farm_no', None)
    session.pop('fsa_program_yr', None)
    session.pop('fsa_operator_name', None)
    session.pop('fsa_tract_no', None)
    session.pop('fsa_field_no', None)
    
    flash(f'FSA-578 submitted successfully! Total Acreage: {acreage}', 'success')
    return jsonify({"status": "success"})

# --- 7. RUN THE APP ---
if __name__ == '__main__':
    app.run(debug=True)


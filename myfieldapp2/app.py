import os
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
# The Secret Key is required for Flask-WTF forms to prevent CSRF errors
app.config['SECRET_KEY'] = 'your_secret_key_here' 
# SQLite initialization: 'users.db' will be created in your project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///green5x5.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 2. DATABASE INITIALIZATION ---
db = SQLAlchemy(app)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(60), nullable=True)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # The 'ident' link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, unique=True)
    
    # Profile Fields
    full_name = db.Column(db.String(100), nullable=True)
    company_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Mailing Address Fields
    address_line1 = db.Column(db.String(150), nullable=True)
    address_line2 = db.Column(db.String(150), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)

    # Relationship to allow: user.profile
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=True)
    
    # Farm Identification
    farm_name = db.Column(db.String(100), nullable=True)
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
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=False)
    profile_id = db.Column(db.Integer, nullable=False)
    
    field_name = db.Column(db.String(100), nullable=True)
    field_shapefile_name = db.Column(db.String(255))
    field_usda_guid = db.Column(db.String(100))
    internal_guid = db.Column(db.String(100), default=lambda: str(uuid.uuid4()))
    google_kml_filename = db.Column(db.String(255))

    # Relationship to access crops easily
    crops = db.relationship('Crop', backref='field', lazy=True)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('field.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    profile_id = db.Column(db.Integer, nullable=True)
    
    crop_name = db.Column(db.String(100), nullable=True)
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
        # Create user instance
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            password=form.password.data # Note: In production, use hashing (bcrypt)
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            # Fake verification email message as requested
            flash(f'Account created! A verification email has been sent to {form.email.data}.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('That email or username is already taken.', 'danger')
            
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            flash('You have successfully logged in!', 'success')
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
    # Fetch the most recent user (or current_user if using Flask-Login)
    user = User.query.order_by(User.id.desc()).first()
    
    # Try to find an existing profile
    profile = UserProfile.query.filter_by(user_id=user.id).first()

    if request.method == 'POST':
        if not profile:
            # Create new profile if it doesn't exist
            profile = UserProfile(user_id=user.id)
            db.session.add(profile)
        
        # Populate fields from your HTML form 'name' attributes
        profile.full_name = request.form.get('full_name')
        profile.company_name = request.form.get('company_name')
        profile.phone = request.form.get('phone')
        profile.address_line1 = request.form.get('address_line1')
        profile.address_line2 = request.form.get('address_line2')
        profile.city = request.form.get('city')
        profile.state = request.form.get('state')
        profile.zip_code = request.form.get('zip_code')

        db.session.commit()
        flash('Profile saved successfully!', 'success')
        
        # REDIRECT to the farms page
        return redirect(url_for('manage_farms'))

    return render_template('setup_profile.html', profile=profile)

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

# --- 7. RUN THE APP ---
if __name__ == '__main__':
    app.run(debug=True)
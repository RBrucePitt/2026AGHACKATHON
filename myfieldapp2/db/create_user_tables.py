from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///green5x5.db'
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

# Initialize Database
with app.app_context():
    db.create_all()
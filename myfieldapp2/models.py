from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -- tblAccount
class Account(db.Model):
    __tablename__ = 'tblAccount'
    AccountID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.Text, unique=True, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    FirstName = db.Column(db.Text, nullable=False)
    LastName = db.Column(db.Text, nullable=False)
    FarmName = db.Column(db.Text, nullable=False)
    PasswordHash = db.Column(db.Text, nullable=False)
    AddDtm = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ModDtm = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    LastLoginDtm = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# -- tblFieldReport
class FieldReport(db.Model):
    __tablename__ = 'tblFieldReport'
    id = db.Column(db.Integer, primary_key=True) # Added PK for SQLAlchemy requirement
    TractNumber = db.Column(db.Integer)
    FieldNumber = db.Column(db.Integer)
    CropCode = db.Column(db.String(50))
    CropType = db.Column(db.String(50))
    IntendedUse = db.Column(db.String(50))
    PlantingDate = db.Column(db.String(50))
    IrrigationPracticeCode = db.Column(db.String(50))
    ReportedAcreage = db.Column(db.Numeric)

# -- tblLocationReference
class LocationReference(db.Model):
    __tablename__ = 'tblLocationReference'
    id = db.Column(db.Integer, primary_key=True)
    GMLReference = db.Column(db.String(50))

# -- tblProducer
class Producer(db.Model):
    __tablename__ = 'tblProducer'
    id = db.Column(db.Integer, primary_key=True)
    TaxID = db.Column(db.String(50))
    ProducerName = db.Column(db.String(50))
    ProducerSharePercentage = db.Column(db.Float)
    AccountID = db.Column(db.Integer, db.ForeignKey('tblAccount.AccountID'))

# -- tblReportHeader
class ReportHeader(db.Model):
    __tablename__ = 'tblReportHeader'
    id = db.Column(db.Integer, primary_key=True)
    ProgramYear = db.Column(db.Integer)
    StateCode = db.Column(db.String(2))
    CountyCode = db.Column(db.String(5))
    FarmNumber = db.Column(db.Integer)

# -- tlk Tables (Lookups)
class County(db.Model):
    __tablename__ = 'tlkCounty'
    CountyCode = db.Column(db.String(5), primary_key=True)
    County = db.Column(db.String(50))

class CropLookup(db.Model):
    __tablename__ = 'tlkCrop'
    id = db.Column(db.Integer, primary_key=True)
    CropCode = db.Column(db.String(5))
    CropTypeCode = db.Column(db.String(5))
    Crop = db.Column(db.String(50))
    CropType = db.Column(db.String(50))

class CropStatus(db.Model):
    __tablename__ = 'tlkCropStatus'
    CropStatusCode = db.Column(db.String(50), primary_key=True)
    CropStatus = db.Column(db.String(50))

class IntendedUse(db.Model):
    __tablename__ = 'tlkIntendedUse'
    IntendedUseCode = db.Column(db.String(50), primary_key=True)
    IntendedUse = db.Column(db.String(50))
    IntendedUseFSA578 = db.Column(db.String(50))

class IrrigationPractice(db.Model):
    __tablename__ = 'tlkIrrigationPractice'
    IrrigationPracticeCode = db.Column(db.String(50), primary_key=True)
    IrrigationPractice = db.Column(db.String(50))

class State(db.Model):
    __tablename__ = 'tlkState'
    StateFipsCode = db.Column(db.String(2), primary_key=True)
    State = db.Column(db.String(50))
    StateName = db.Column(db.String(50))
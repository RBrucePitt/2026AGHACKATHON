-- tblAccount definition

CREATE TABLE tblAccount (
    AccountID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT UNIQUE NOT NULL,
    Email TEXT UNIQUE NOT NULL,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    FarmName TEXT NOT NULL,
    PasswordHash TEXT NOT NULL, -- Never store passwords in plain text
    AddDtm DATETIME NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    ModDtm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    LastLoginDtm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- tblFieldReport definition

CREATE TABLE tblFieldReport (
	TractNumber INTEGER,
	FieldNumber INTEGER,
	CropCode VARCHAR(50),
	CropType VARCHAR(50),
	IntendedUse VARCHAR(50),
	PlantingDate NVARCHAR(50),
	IrrigationPracticeCode VARCHAR(50),
	ReportedAcreage NUMERIC
);

CREATE TABLE tblLocationReference (
	GMLReference VARCHAR(50)
);


CREATE TABLE tblProducer (
	TaxID VARCHAR(50),
	ProducerName VARCHAR(50),
	ProducerSharePercentage REAL
, AccountID INTEGER);


CREATE TABLE tblReportHeader (
	ProgramYear INTEGER,
	StateCode CHAR(2),
	CountyCode CHAR(5),
	FarmNumber INTEGER
);


CREATE TABLE tlkCounty (
	CountyCode char(5),
	County VARCHAR(50)
);

CREATE TABLE tlkCrop (
	CropCode varchar(5),
	CropTypeCode VARCHAR(5),
	Crop VARCHAR(50),
	CropType VARCHAR(50)
);

CREATE TABLE tlkCropStatus (
	CropStatusCode VARCHAR(50),
	CropStatus VARCHAR(50)
);

CREATE TABLE tlkIntendedUse (
	IntendedUseCode VARCHAR(50),
	IntendedUse VARCHAR(50),
	IntendedUseFSA578 VARCHAR(50)
);


CREATE TABLE tlkIrrigationPractice (
	IrrigationPracticeCode VARCHAR(50),
	IrrigationPractice VARCHAR(50)
);

CREATE TABLE tlkState (
	StateFipsCode char(2),
	State VARCHAR(50),
	StateName VARCHAR(50)
);

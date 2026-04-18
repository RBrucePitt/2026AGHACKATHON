PRAGMA foreign_keys = ON;

-- Table for authentication credentials
-- FOREIGN KEY (AccountID) REFERENCES tblAccount (AccountID) ON DELETE CASCADE
CREATE TABLE IF NOT EXISTS tblAccount (
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

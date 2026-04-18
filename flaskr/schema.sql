DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  farm_name TEXT NOT NULL,
  password TEXT NOT NULL,
  add_dtm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  mod_dtm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_dtm DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Each report stores data
CREATE TABLE report (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  producer_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  status TEXT DEFAULT 'Draft', -- FAFSA style: Draft, Submitted, Certified
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (producer_id) REFERENCES user (id)
);

-- This is where the actual "huge" data goes, row by row
CREATE TABLE report_item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id INTEGER NOT NULL,
  tract_number TEXT NOT NULL,
  field_number TEXT NOT NULL,
  crop_type TEXT NOT NULL,
  intended_use TEXT,
  acreage REAL NOT NULL,
  share_percentage REAL DEFAULT 100.0,
  FOREIGN KEY (report_id) REFERENCES report (id)
);
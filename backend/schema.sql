CREATE DATABASE IF NOT EXISTS opentools_auditable;
USE opentools_auditable;

CREATE TABLE IF NOT EXISTS Client (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255),
    dirigeant VARCHAR(255),
    adresse VARCHAR(255),
    postal_code VARCHAR(50),
    contact_mail VARCHAR(255),
    contact_phone VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    started_at DATETIME,
    finished_at DATETIME,
    client_id INT,
    user_id INT,
    title VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    started_at DATETIME,
    finished_at DATETIME,
    audit_id INT,
    title VARCHAR(255),
    used_tool VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS convention (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audit_id INT,
    signed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS list_ip (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(255) UNIQUE,
    convention_id INT,
    cidr VARCHAR(50),
    environnement VARCHAR(255),
    domaine_name VARCHAR(255),
    deepscan BOOLEAN DEFAULT FALSE,
    true_cmd_port TEXT
);

ALTER TABLE list_ip ADD COLUMN IF NOT EXISTS true_cmd_port TEXT;

CREATE TABLE IF NOT EXISTS list_port (
    id INT AUTO_INCREMENT PRIMARY KEY,
    port_number INT,
    list_ip_id INT,
    status VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    CVE VARCHAR(50),
    CVSS VARCHAR(100),
    vulnerability_name VARCHAR(255),
    criticity FLOAT,
    description TEXT,
    risk TEXT,
    EPSS FLOAT,
    EPSS_percentile FLOAT,
    CWE VARCHAR(255),
    remediation TEXT,
    source VARCHAR(255),
    external_link TEXT,
    ip_id INT,
    port_id INT,
    used_tool VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS misconfiguration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    remediation TEXT,
    used_tool VARCHAR(100),
    risk TEXT
);

CREATE TABLE IF NOT EXISTS opentools_auditable_configuration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    color1 VARCHAR(50),
    color2 VARCHAR(50),
    color3 VARCHAR(50),
    font_size VARCHAR(50),
    font_color VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS param_nmap (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aggressiveness INT DEFAULT 0,
    output_file VARCHAR(20) NULL
);

CREATE TABLE IF NOT EXISTS log_nmap (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_ip_id INT,
    log TEXT,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS param_nikto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aggressiveness INT DEFAULT 0,
    tuning_option VARCHAR(32) NULL,
    output_file VARCHAR(20) NULL
);

CREATE TABLE IF NOT EXISTS log_nikto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_ip_id INT,
    log TEXT,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS param_wpscan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aggressiveness BOOLEAN DEFAULT FALSE,
    output_file VARCHAR(20) NULL,
    enumeration_mode VARCHAR(20) DEFAULT 'vulnerable',
    enumeration_option VARCHAR(64) DEFAULT '-e vp,vt,tt,cb,dbe,u,m'
);

ALTER TABLE param_wpscan ADD COLUMN IF NOT EXISTS enumeration_mode VARCHAR(20) DEFAULT 'vulnerable';
ALTER TABLE param_wpscan ADD COLUMN IF NOT EXISTS enumeration_option VARCHAR(64) DEFAULT '-e vp,vt,tt,cb,dbe,u,m';

CREATE TABLE IF NOT EXISTS log_wpscan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_ip_id INT,
    log TEXT,
    enumeration_option VARCHAR(64),
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE log_wpscan ADD COLUMN IF NOT EXISTS enumeration_option VARCHAR(64);

CREATE TABLE IF NOT EXISTS param_nuclei (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aggressiveness INT DEFAULT 0,
    severity VARCHAR(128) DEFAULT 'info,low,medium,high,critical',
    output_file VARCHAR(20) NULL
);

CREATE TABLE IF NOT EXISTS log_nuclei (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_ip_id INT,
    log TEXT,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS log_ndv (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_ip_id INT,
    request TEXT,
    log TEXT,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS log_circl (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_ip_id INT,
    request TEXT,
    log TEXT,
    horodatage TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE log_ndv MODIFY log LONGTEXT;
ALTER TABLE log_circl MODIFY log LONGTEXT;
ALTER TABLE log_nmap MODIFY log LONGTEXT;
ALTER TABLE log_nikto MODIFY log LONGTEXT;
ALTER TABLE log_wpscan MODIFY log LONGTEXT;
ALTER TABLE log_nuclei MODIFY log LONGTEXT;

INSERT INTO param_nmap (aggressiveness, output_file)
SELECT 0, NULL WHERE NOT EXISTS (SELECT 1 FROM param_nmap);

INSERT INTO param_nikto (aggressiveness, tuning_option, output_file)
SELECT 0, NULL, NULL WHERE NOT EXISTS (SELECT 1 FROM param_nikto);

INSERT INTO param_wpscan (aggressiveness, output_file, enumeration_mode, enumeration_option)
SELECT FALSE, NULL, 'vulnerable', '-e vp,vt,tt,cb,dbe,u,m' WHERE NOT EXISTS (SELECT 1 FROM param_wpscan);

INSERT INTO param_nuclei (aggressiveness, severity, output_file)
SELECT 0, 'info,low,medium,high,critical', NULL WHERE NOT EXISTS (SELECT 1 FROM param_nuclei);

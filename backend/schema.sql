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
    deepscan BOOLEAN DEFAULT FALSE
);

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
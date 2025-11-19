CREATE TABLE users (
    traveler_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    is_local TINYINT(1) NOT NULL,
    is_pwd TINYINT(1) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    fare DECIMAL(10,2) NOT NULL,
    qr_filename VARCHAR(500) NOT NULL,
    is_paid TINYINT(1) NOT NULL DEFAULT 0
);


CREATE TABLE ticket_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    traveler_id INT NOT NULL,
    action VARCHAR(255) NOT NULL,
    timestamp DATETIME NOT NULL,
    details TEXT,
    
    CONSTRAINT fk_traveler
    FOREIGN KEY (traveler_id) REFERENCES users(traveler_id)
        ON UPDATE CASCADE 
        ON DELETE CASCADE
);
    

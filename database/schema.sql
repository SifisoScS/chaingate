-- ChainGate Crypto Compliance System Database Schema
-- For SQL Server

CREATE DATABASE chaingate;
GO

USE chaingate;
GO

-- Users Table
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) UNIQUE NOT NULL,
    email NVARCHAR(100) UNIQUE NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(20) NOT NULL CHECK (role IN ('player', 'admin')),
    kyc_status NVARCHAR(20) DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'verified', 'rejected', 'expired')),
    risk_level NVARCHAR(20) DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high')),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Wallets Table
CREATE TABLE wallets (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    address NVARCHAR(255) NOT NULL,
    balance DECIMAL(18,8) DEFAULT 0.00000000,
    currency NVARCHAR(10) DEFAULT 'BTC',
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Transactions Table
CREATE TABLE transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    type NVARCHAR(20) NOT NULL CHECK (type IN ('deposit', 'withdrawal', 'transfer')),
    amount DECIMAL(18,8) NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'completed', 'failed', 'cancelled')),
    tx_hash NVARCHAR(255),
    from_address NVARCHAR(255),
    to_address NVARCHAR(255),
    confirmations INT DEFAULT 0,
    risk_score DECIMAL(5,2) DEFAULT 0.00,
    flagged BIT DEFAULT 0,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- KYC Documents Table
CREATE TABLE kyc_documents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    document_type NVARCHAR(50) NOT NULL,
    document_number NVARCHAR(100),
    file_path NVARCHAR(500),
    status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    verified_by INT FOREIGN KEY REFERENCES users(id),
    verified_at DATETIME2,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);

-- Risk Assessments Table
CREATE TABLE risk_assessments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL FOREIGN KEY REFERENCES users(id),
    risk_score DECIMAL(5,2) NOT NULL,
    risk_factors NVARCHAR(MAX),
    assessment_date DATETIME2 DEFAULT GETDATE(),
    assessed_by INT FOREIGN KEY REFERENCES users(id)
);

-- Audit Logs Table
CREATE TABLE audit_logs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT FOREIGN KEY REFERENCES users(id),
    action NVARCHAR(100) NOT NULL,
    resource NVARCHAR(100),
    details NVARCHAR(MAX),
    ip_address NVARCHAR(45),
    user_agent NVARCHAR(500),
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Compliance Rules Table
CREATE TABLE compliance_rules (
    id INT IDENTITY(1,1) PRIMARY KEY,
    rule_name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    rule_type NVARCHAR(50) NOT NULL,
    threshold DECIMAL(18,8),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Insert Default Data
INSERT INTO users (username, email, password_hash, role, kyc_status, risk_level) VALUES 
('admin', 'admin@chaingate.com', 'pbkdf2:sha256:260000$abc123$xyz456', 'admin', 'verified', 'low'),
('alice', 'alice@demo.com', 'pbkdf2:sha256:260000$def456$uvw789', 'player', 'verified', 'low');

INSERT INTO wallets (user_id, address, balance) VALUES 
(1, 'admin_wallet_001', 0.00000000),
(2, 'bc1qalice123456789', 0.12580000);

INSERT INTO compliance_rules (rule_name, description, rule_type, threshold) VALUES 
('Daily Deposit Limit', 'Maximum daily deposit amount per user', 'deposit_limit', 1.00000000),
('Withdrawal Limit', 'Maximum single withdrawal amount', 'withdrawal_limit', 0.50000000),
('Transaction Monitoring', 'Flag transactions above threshold', 'transaction_monitoring', 0.10000000);

GO

-- Create Indexes for Performance
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_kyc_documents_user_id ON kyc_documents(user_id);

GO

PRINT 'ChainGate database schema created successfully!';
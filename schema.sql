-- chaingate-system/database/schema.sql
-- SQL Server Schema for ChainGate Crypto Compliance System

-- Enable IDENTITY_INSERT for tables with explicit ID insertion (if needed for seed data)
-- SET IDENTITY_INSERT [TableName] ON;

-- Users Table
CREATE TABLE Users (
    id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(255) NOT NULL UNIQUE,
    email NVARCHAR(255) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(50) NOT NULL CHECK (role IN ('player', 'admin')),
    kyc_status NVARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'verified', 'rejected', 'flagged')),
    risk_level NVARCHAR(50) NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high')),
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Wallets Table
CREATE TABLE Wallets (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL UNIQUE,
    btc_address NVARCHAR(255) NOT NULL UNIQUE,
    balance DECIMAL(18, 8) NOT NULL DEFAULT 0.0,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- Transactions Table
CREATE TABLE Transactions (
    id NVARCHAR(255) PRIMARY KEY, -- Using NVARCHAR for simulated transaction IDs (UUIDs or hashes)
    user_id INT NOT NULL,
    type NVARCHAR(50) NOT NULL CHECK (type IN ('deposit', 'withdrawal', 'transfer')),
    amount DECIMAL(18, 8) NOT NULL,
    currency NVARCHAR(10) NOT NULL DEFAULT 'BTC',
    status NVARCHAR(50) NOT NULL CHECK (status IN ('initiated', 'pending', 'confirmed', 'completed', 'rejected', 'flagged', 'failed', 'broadcasting')),
    from_address NVARCHAR(255),
    to_address NVARCHAR(255),
    tx_hash NVARCHAR(255), -- Simulated blockchain transaction hash
    confirmations INT DEFAULT 0,
    fee DECIMAL(18, 8) DEFAULT 0.0,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    admin_notes NVARCHAR(MAX),
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- KYCDocuments Table
CREATE TABLE KYCDocuments (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    document_type NVARCHAR(100) NOT NULL CHECK (document_type IN ('passport', 'id_card', 'utility_bill', 'other')),
    file_path NVARCHAR(MAX) NOT NULL, -- Encrypted path to stored document
    status NVARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    uploaded_at DATETIME DEFAULT GETDATE(),
    reviewed_by INT, -- Admin user ID
    reviewed_at DATETIME,
    comments NVARCHAR(MAX),
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (reviewed_by) REFERENCES Users(id)
);

-- RiskAssessments Table
CREATE TABLE RiskAssessments (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT NOT NULL,
    score INT NOT NULL CHECK (score >= 0 AND score <= 10),
    reason NVARCHAR(MAX),
    assessed_by INT, -- Admin or system user ID
    assessed_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (assessed_by) REFERENCES Users(id)
);

-- AuditLogs Table
CREATE TABLE AuditLogs (
    id INT PRIMARY KEY IDENTITY(1,1),
    user_id INT,
    action NVARCHAR(255) NOT NULL,
    details NVARCHAR(MAX),
    timestamp DATETIME DEFAULT GETDATE(),
    ip_address NVARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

-- ComplianceReports Table
CREATE TABLE ComplianceReports (
    id INT PRIMARY KEY IDENTITY(1,1),
    report_type NVARCHAR(100) NOT NULL,
    generated_by INT, -- Admin or system user ID
    generated_at DATETIME DEFAULT GETDATE(),
    start_date DATE,
    end_date DATE,
    file_path NVARCHAR(MAX) NOT NULL, -- Path to generated report file
    FOREIGN KEY (generated_by) REFERENCES Users(id)
);

-- SystemSettings Table
CREATE TABLE SystemSettings (
    id INT PRIMARY KEY IDENTITY(1,1),
    [key] NVARCHAR(255) NOT NULL UNIQUE,
    value NVARCHAR(MAX),
    description NVARCHAR(MAX),
    updated_by INT, -- Admin user ID
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (updated_by) REFERENCES Users(id)
);

-- Indexes for performance
CREATE INDEX IX_Transactions_UserId ON Transactions (user_id);
CREATE INDEX IX_Transactions_Status ON Transactions (status);
CREATE INDEX IX_KYCDocuments_UserId ON KYCDocuments (user_id);
CREATE INDEX IX_RiskAssessments_UserId ON RiskAssessments (user_id);
CREATE INDEX IX_AuditLogs_UserId ON AuditLogs (user_id);
CREATE INDEX IX_ComplianceReports_ReportType ON ComplianceReports (report_type);



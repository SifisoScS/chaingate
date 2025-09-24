from src.database import db, BaseModel
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship

class User(UserMixin, BaseModel):
    __tablename__ = 'users'
    
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'player' or 'admin'
    kyc_status = db.Column(db.String(20), default='pending')
    risk_level = db.Column(db.String(20), default='low')
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    kyc_documents = relationship("KYCDocument", back_populates="user")
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def is_kyc_verified(self):
        """Check if KYC is verified"""
        return self.kyc_status == 'verified'

class Wallet(BaseModel):
    __tablename__ = 'wallets'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Numeric(18, 8), default=0.00000000)
    currency = db.Column(db.String(10), default='BTC')
    
    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship("Transaction", back_populates="wallet")

class Transaction(BaseModel):
    __tablename__ = 'transactions'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, transfer
    amount = db.Column(db.Numeric(18, 8), nullable=False)
    status = db.Column(db.String(20), default='pending')
    tx_hash = db.Column(db.String(255))
    from_address = db.Column(db.String(255))
    to_address = db.Column(db.String(255))
    confirmations = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Numeric(5, 2), default=0.00)
    flagged = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    wallet = relationship("Wallet", back_populates="transactions")

class KYCDocument(BaseModel):
    __tablename__ = 'kyc_documents'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    document_number = db.Column(db.String(100))
    file_path = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    
    # Relationships
    user = relationship("User", back_populates="kyc_documents")

class RiskAssessment(BaseModel):
    __tablename__ = 'risk_assessments'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    risk_score = db.Column(db.Numeric(5, 2), nullable=False)
    risk_factors = db.Column(db.Text)
    assessed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100))
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))

class ComplianceRule(BaseModel):
    __tablename__ = 'compliance_rules'
    
    rule_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    rule_type = db.Column(db.String(50), nullable=False)
    threshold = db.Column(db.Numeric(18, 8))
    is_active = db.Column(db.Boolean, default=True)
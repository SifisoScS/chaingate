#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from src.models.user import db, User, Wallet, SystemSetting
from src.services.bitcoin_simulator import BitcoinSimulator

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def init_database():
    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        print("Checking for existing users...")
        existing_users = User.query.all()
        print(f"Found {len(existing_users)} existing users")

        if not existing_users:
            print("Creating demo users...")

            # Create demo player users
            demo_users = [
                {
                    'username': 'alice_johnson',
                    'email': 'alice@demo.com',
                    'password': 'demo123',
                    'kyc_status': 'verified',
                    'risk_level': 'low'
                },
                {
                    'username': 'bob_wilson',
                    'email': 'bob@demo.com',
                    'password': 'demo123',
                    'kyc_status': 'pending',
                    'risk_level': 'medium'
                },
                {
                    'username': 'charlie_brown',
                    'email': 'charlie@demo.com',
                    'password': 'demo123',
                    'kyc_status': 'flagged',
                    'risk_level': 'high'
                }
            ]

            bitcoin_simulator = BitcoinSimulator()

            for user_data in demo_users:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    role='player',
                    kyc_status=user_data['kyc_status'],
                    risk_level=user_data['risk_level']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
                print(f"Created user: {user.username}")

                # Create wallet for demo user
                btc_address = bitcoin_simulator.generate_address(user.id)
                wallet = Wallet(
                    user_id=user.id,
                    btc_address=btc_address,
                    balance=0.0
                )
                db.session.add(wallet)
                print(f"Created wallet for {user.username}: {btc_address}")

            # Create system settings
            settings = [
                {
                    'key': 'confirmation_threshold',
                    'value': '3',
                    'description': 'Number of confirmations required for deposits'
                },
                {
                    'key': 'deposit_confirmation_interval_min_seconds',
                    'value': '30',
                    'description': 'Minimum seconds between deposit confirmations'
                },
                {
                    'key': 'deposit_confirmation_interval_max_seconds',
                    'value': '120',
                    'description': 'Maximum seconds between deposit confirmations'
                },
                {
                    'key': 'withdrawal_broadcast_delay_seconds',
                    'value': '60',
                    'description': 'Delay before broadcasting withdrawal'
                },
                {
                    'key': 'transaction_failure_rate_percent',
                    'value': '5',
                    'description': 'Percentage chance of transaction failure'
                }
            ]

            for setting_data in settings:
                setting = SystemSetting(
                    key=setting_data['key'],
                    value=setting_data['value'],
                    description=setting_data['description'],
                    updated_by=None
                )
                db.session.add(setting)

            try:
                db.session.commit()
                print("Database initialized successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error initializing database: {e}")
                return False
        else:
            print("Database already has users, skipping initialization")

        # Verify the database
        users = User.query.all()
        print(f"\nDatabase verification:")
        print(f"Total users: {len(users)}")
        for user in users:
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            print(f"  {user.username} ({user.email}) - Wallet: {wallet.btc_address if wallet else 'None'} - Balance: {wallet.balance if wallet else 'N/A'}")

        return True

if __name__ == '__main__':
    if success := init_database():
        print("\nDatabase initialization completed successfully!")
    else:
        print("\nDatabase initialization failed!")
        sys.exit(1)

import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.user import Wallet, db
from src.routes.auth import auth_bp
from src.routes.player import player_bp

from src.services.notification_service import socketio, notify_transaction_update, notify_risk_alert, notify_compliance_report

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'services', 'static'))
app.config['SECRET_KEY'] = 'chaingate_secret_key_2024_demo'

# Configure CORS to allow credentials (cookies)
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(player_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and seed data
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")

        # Import models after db is created
        from src.models.user import User, SystemSetting

        if existing_users := User.query.all():
            print(f"Database already has {len(existing_users)} users, skipping initialization")

        else:
            print("Creating demo users...")

            # Create demo player users if they don't exist
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

            for user_data in demo_users:
                existing_user = User.query.filter_by(email=user_data['email']).first()
                if not existing_user:
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
                    from src.services.bitcoin_simulator import BitcoinSimulator
                    bitcoin_simulator = BitcoinSimulator()
                    btc_address = bitcoin_simulator.generate_address(user.id)
                    wallet = Wallet(
                        user_id=user.id,
                        btc_address=btc_address,
                        balance=0.0
                    )
                    db.session.add(wallet)
                    print(f"Created wallet for {user.username}: {btc_address}")

            # Create system settings if they don't exist
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
                existing_setting = SystemSetting.query.filter_by(key=setting_data['key']).first()
                if not existing_setting:
                    setting = SystemSetting(
                        key=setting_data['key'],
                        value=setting_data['value'],
                        description=setting_data['description'],
                        updated_by=None
                    )
                    db.session.add(setting)

            db.session.commit()
            print("Database initialized with demo data")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    index_path = os.path.join(static_folder_path, 'index.html')
    return (
        send_from_directory(static_folder_path, 'index.html')
        if os.path.exists(index_path)
        else ("index.html not found", 404)
    )

if __name__ == '__main__':
    socketio.init_app(app, cors_allowed_origins="*")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

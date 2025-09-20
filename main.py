import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.auth import auth_bp
from src.routes.player import player_bp
from src.routes.admin import admin_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'chaingate_secret_key_2024_demo'

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(player_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and seed data
with app.app_context():
    db.create_all()
    
    # Check if we need to seed initial data
    from src.models.user import User, SystemSetting
    
    # Create admin user if doesn't exist
    admin_user = User.query.filter_by(email='admin@chaingate.com').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@chaingate.com',
            role='admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
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
    
    # Create system settings if they don't exist
    settings = [
        {
            'key': 'confirmation_threshold',
            'value': '3',
            'description': 'Number of confirmations required for deposits'
        },
        {
            'key': 'withdrawal_approval_threshold',
            'value': '1.0',
            'description': 'BTC amount threshold for admin approval'
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
                updated_by=admin_user.id if admin_user else None
            )
            db.session.add(setting)
    
    try:
        db.session.commit()
        print("Database initialized with demo data")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing database: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


from datetime import datetime
from flask import Blueprint, Flask, request, jsonify
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from src import config
from ..database import db
from ..models.user import User, AuditLog
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            
            # Log the login
            audit_log = AuditLog(
                user_id=user.id,
                action='user_login',
                resource='/api/auth/login',
                details=f'User {user.email} logged in successfully'
            )
            db.session.add(audit_log)
            db.session.commit()
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'kyc_status': user.kyc_status,
                    'risk_level': user.risk_level
                }
            })
        else:
            return jsonify({'error': 'Invalid credentials or inactive account'}), 401
            
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Configure login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.player import player_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(player_bp, url_prefix='/api/player')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Logging middleware
    @app.before_request
    def log_request():
        if request.endpoint and 'static' not in request.endpoint:
            audit_log = AuditLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                action=f'{request.method} {request.endpoint}',
                resource=request.path,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit_log)
            db.session.commit()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Database tables created successfully!")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
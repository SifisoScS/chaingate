from flask import Blueprint, jsonify, request, session
from src.models.user import User, Wallet, db
from src.services.bitcoin_simulator import BitcoinSimulator
import uuid

auth_bp = Blueprint('auth', __name__)
bitcoin_simulator = BitcoinSimulator()

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Validate required fields
        if not data or not data.get('username') or not data.get('email') or not data.get('password'):
            return jsonify({'status': 'error', 'message': 'Username, email, and password are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'status': 'error', 'message': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'status': 'error', 'message': 'Username already taken'}), 400
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'player')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create wallet for the user
        btc_address = bitcoin_simulator.generate_address(user.id)
        wallet = Wallet(
            user_id=user.id,
            btc_address=btc_address,
            balance=0.0
        )
        db.session.add(wallet)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401
        
        if not user.is_active:
            return jsonify({'status': 'error', 'message': 'Account is suspended'}), 403
        
        # Create session
        session['user_id'] = user.id
        session['role'] = user.role
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user_id': user.id,
            'role': user.role
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    }), 200

@auth_bp.route('/auth/status', methods=['GET'])
def status():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.is_active:
            return jsonify({
                'is_authenticated': True,
                'user_id': user.id,
                'role': user.role,
                'username': user.username
            }), 200
    
    return jsonify({'is_authenticated': False}), 200


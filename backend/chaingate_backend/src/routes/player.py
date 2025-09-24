from flask import Blueprint, jsonify, request, session
from src.models.user import User, Wallet, Transaction, db
from src.services.bitcoin_simulator import BitcoinSimulator
import qrcode
import io
import base64
from datetime import datetime, timedelta

player_bp = Blueprint('player', __name__)
bitcoin_simulator = BitcoinSimulator()

def require_player_auth():
    """Decorator to require player authentication"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    
    user = User.query.get(session['user_id'])
    if not user or not user.is_active:
        return jsonify({'status': 'error', 'message': 'Account not active'}), 403
    
    return None

@player_bp.route('/player/balance', methods=['GET'])
def get_balance():
    auth_error = require_player_auth()
    if auth_error:
        return auth_error
    
    try:
        user_id = session['user_id']
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        
        if not wallet:
            return jsonify({'status': 'error', 'message': 'Wallet not found'}), 404
        
        # Mock USD conversion rate (1 BTC = $45,000)
        usd_rate = 45000
        usd_equivalent = float(wallet.balance) * usd_rate
        
        return jsonify({
            'status': 'success',
            'btc_balance': float(wallet.balance),
            'usd_equivalent': usd_equivalent,
            'wallet_address': wallet.btc_address
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@player_bp.route('/player/deposit/address', methods=['POST'])
def generate_deposit_address():
    auth_error = require_player_auth()
    if auth_error:
        return auth_error
    
    try:
        user_id = session['user_id']
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        
        if not wallet:
            return jsonify({'status': 'error', 'message': 'Wallet not found'}), 404
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(wallet.btc_address)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        qr_code_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        qr_code_url = f"data:image/png;base64,{qr_code_base64}"
        
        return jsonify({
            'status': 'success',
            'deposit_address': wallet.btc_address,
            'qr_code_url': qr_code_url
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@player_bp.route('/player/transactions', methods=['GET'])
def get_transactions():
    auth_error = require_player_auth()
    if auth_error:
        return auth_error
    
    try:
        user_id = session['user_id']
        
        # Get query parameters
        filter_type = request.args.get('filter', 'all')  # 'deposits', 'withdrawals', 'all'
        date_range = request.args.get('date_range', '30days')  # '30days', 'all'
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = Transaction.query.filter_by(user_id=user_id)
        
        if filter_type != 'all':
            if filter_type == 'deposits':
                query = query.filter_by(type='deposit')
            elif filter_type == 'withdrawals':
                query = query.filter_by(type='withdrawal')
        
        if date_range == '30days':
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            query = query.filter(Transaction.created_at >= thirty_days_ago)
        
        # Order by most recent first
        query = query.order_by(Transaction.created_at.desc())
        
        # Paginate
        total_transactions = query.count()
        transactions = query.offset((page - 1) * limit).limit(limit).all()
        
        total_pages = (total_transactions + limit - 1) // limit
        
        return jsonify({
            'status': 'success',
            'transactions': [tx.to_dict() for tx in transactions],
            'total_pages': total_pages,
            'current_page': page,
            'total_transactions': total_transactions
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@player_bp.route('/player/withdraw', methods=['POST'])
def withdraw():
    auth_error = require_player_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.json
        
        if not data or not data.get('to_address') or not data.get('amount'):
            return jsonify({'status': 'error', 'message': 'Destination address and amount are required'}), 400
        
        user_id = session['user_id']
        to_address = data['to_address']
        amount = float(data['amount'])
        
        if amount <= 0:
            return jsonify({'status': 'error', 'message': 'Amount must be positive'}), 400
        
        # Basic Bitcoin address validation (simplified)
        if not (to_address.startswith('bc1') or to_address.startswith('1') or to_address.startswith('3')):
            return jsonify({'status': 'error', 'message': 'Invalid Bitcoin address format'}), 400
        
        transaction, error = bitcoin_simulator.process_withdrawal(user_id, to_address, amount)
        
        if error:
            return jsonify({'status': 'error', 'message': error}), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Withdrawal request submitted',
            'transaction_id': transaction.id
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@player_bp.route('/player/transaction/<string:tx_id>/status', methods=['GET'])
def get_transaction_status(tx_id):
    auth_error = require_player_auth()
    if auth_error:
        return auth_error
    
    try:
        user_id = session['user_id']
        
        # Verify transaction belongs to user
        transaction = Transaction.query.filter_by(id=tx_id, user_id=user_id).first()
        if not transaction:
            return jsonify({'status': 'error', 'message': 'Transaction not found'}), 404
        
        status_info = bitcoin_simulator.get_confirmation_status(tx_id)
        if not status_info:
            return jsonify({'status': 'error', 'message': 'Transaction status not available'}), 404
        
        return jsonify({
            'status': 'success',
            **status_info
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@player_bp.route('/player/simulate_deposit', methods=['POST'])
def simulate_deposit():
    """Demo endpoint to simulate receiving a deposit"""
    auth_error = require_player_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.json
        amount = float(data.get('amount', 0.1))  # Default 0.1 BTC
        
        if amount <= 0:
            return jsonify({'status': 'error', 'message': 'Amount must be positive'}), 400
        
        user_id = session['user_id']
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        
        if not wallet:
            return jsonify({'status': 'error', 'message': 'Wallet not found'}), 404
        
        transaction = bitcoin_simulator.simulate_deposit(user_id, wallet.btc_address, amount)
        
        return jsonify({
            'status': 'success',
            'message': 'Deposit simulation started',
            'transaction_id': transaction.id
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


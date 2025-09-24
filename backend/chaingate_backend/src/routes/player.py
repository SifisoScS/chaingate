from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db
from models.user import User, Wallet, Transaction, AuditLog
from decimal import Decimal
import logging

player_bp = Blueprint('player', __name__)

@player_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Player dashboard data"""
    try:
        user = current_user
        wallet = Wallet.query.filter_by(user_id=user.id).first()
        
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404
        
        # Get recent transactions
        transactions = Transaction.query.filter_by(user_id=user.id)\
            .order_by(Transaction.created_at.desc())\
            .limit(10)\
            .all()
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'kyc_status': user.kyc_status,
                'risk_level': user.risk_level
            },
            'wallet': {
                'address': wallet.address,
                'balance': float(wallet.balance),
                'currency': wallet.currency
            },
            'recent_transactions': [
                {
                    'id': tx.id,
                    'type': tx.type,
                    'amount': float(tx.amount),
                    'status': tx.status,
                    'created_at': tx.created_at.isoformat()
                } for tx in transactions
            ]
        })
        
    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_bp.route('/balance', methods=['GET'])
@login_required
def get_balance():
    """Get player balance"""
    try:
        wallet = Wallet.query.filter_by(user_id=current_user.id).first()
        
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404
        
        # Simulate USD conversion (1 BTC = 40000 USD for demo)
        btc_balance = float(wallet.balance)
        usd_equivalent = btc_balance * 40000
        
        return jsonify({
            'btc_balance': btc_balance,
            'usd_equivalent': usd_equivalent,
            'wallet_address': wallet.address
        })
        
    except Exception as e:
        logging.error(f"Balance error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    """Get transaction history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'transactions': [
                {
                    'id': tx.id,
                    'type': tx.type,
                    'amount': float(tx.amount),
                    'status': tx.status,
                    'tx_hash': tx.tx_hash,
                    'confirmations': tx.confirmations,
                    'created_at': tx.created_at.isoformat()
                } for tx in transactions.items
            ],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        })
        
    except Exception as e:
        logging.error(f"Transactions error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_bp.route('/simulate_deposit', methods=['POST'])
@login_required
def simulate_deposit():
    """Simulate Bitcoin deposit"""
    try:
        data = request.get_json()
        amount = Decimal(str(data.get('amount', 0.1)))
        
        if amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        wallet = Wallet.query.filter_by(user_id=current_user.id).first()
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404
        
        # Create transaction
        transaction = Transaction(
            user_id=current_user.id,
            type='deposit',
            amount=amount,
            status='completed',
            to_address=wallet.address,
            tx_hash=f'sim_tx_{current_user.id}_{Transaction.query.count() + 1}'
        )
        
        # Update balance
        wallet.balance += amount
        
        db.session.add(transaction)
        db.session.commit()
        
        # Log the deposit
        audit_log = AuditLog(
            user_id=current_user.id,
            action='simulated_deposit',
            resource='/api/player/simulate_deposit',
            details=f'Simulated deposit of {amount} BTC'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Deposit simulation successful',
            'transaction_id': transaction.id,
            'new_balance': float(wallet.balance)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Deposit simulation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@player_bp.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    """Request withdrawal"""
    try:
        data = request.get_json()
        amount = Decimal(str(data.get('amount')))
        address = data.get('address')
        
        if not amount or amount <= 0:
            return jsonify({'error': 'Invalid amount'}), 400
        
        if not address:
            return jsonify({'error': 'Destination address required'}), 400
        
        wallet = Wallet.query.filter_by(user_id=current_user.id).first()
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404
        
        if wallet.balance < amount:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Create withdrawal transaction
        transaction = Transaction(
            user_id=current_user.id,
            type='withdrawal',
            amount=amount,
            status='pending',
            from_address=wallet.address,
            to_address=address,
            tx_hash=f'withdraw_tx_{current_user.id}_{Transaction.query.count() + 1}'
        )
        
        # Reserve balance (will be deducted when approved)
        wallet.balance -= amount
        
        db.session.add(transaction)
        db.session.commit()
        
        # Log the withdrawal request
        audit_log = AuditLog(
            user_id=current_user.id,
            action='withdrawal_request',
            resource='/api/player/withdraw',
            details=f'Withdrawal request of {amount} BTC to {address}'
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Withdrawal request submitted',
            'transaction_id': transaction.id,
            'new_balance': float(wallet.balance)
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Withdrawal error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
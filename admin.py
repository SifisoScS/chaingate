from flask import Blueprint, jsonify, request, session
from src.models.user import User, Transaction, Wallet, KYCDocument, RiskAssessment, db
from src.services.bitcoin_simulator import BitcoinSimulator
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)
bitcoin_simulator = BitcoinSimulator()

def require_admin_auth():
    """Decorator to require admin authentication"""
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
    
    user = User.query.get(session['user_id'])
    if not user or not user.is_active or user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    
    return None

@admin_bp.route('/admin/transactions', methods=['GET'])
def get_all_transactions():
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        # Get query parameters
        status_filter = request.args.get('status', 'all')  # 'pending', 'flagged', 'all'
        type_filter = request.args.get('type', 'all')  # 'deposit', 'withdrawal', 'all'
        user_id_filter = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        
        # Build query
        query = Transaction.query
        
        if status_filter != 'all':
            if status_filter == 'pending':
                query = query.filter(Transaction.status.in_(['pending_admin', 'pending']))
            elif status_filter == 'flagged':
                query = query.filter_by(status='flagged')
            else:
                query = query.filter_by(status=status_filter)
        
        if type_filter != 'all':
            query = query.filter_by(type=type_filter)
        
        if user_id_filter:
            query = query.filter_by(user_id=int(user_id_filter))
        
        # Order by most recent first
        query = query.order_by(Transaction.created_at.desc())
        
        # Paginate
        total_transactions = query.count()
        transactions = query.offset((page - 1) * limit).limit(limit).all()
        
        total_pages = (total_transactions + limit - 1) // limit
        
        # Enrich with user information
        enriched_transactions = []
        for tx in transactions:
            tx_dict = tx.to_dict()
            user = User.query.get(tx.user_id)
            if user:
                tx_dict['user'] = {
                    'username': user.username,
                    'email': user.email,
                    'kyc_status': user.kyc_status,
                    'risk_level': user.risk_level
                }
            enriched_transactions.append(tx_dict)
        
        return jsonify({
            'status': 'success',
            'transactions': enriched_transactions,
            'total_pages': total_pages,
            'current_page': page,
            'total_transactions': total_transactions
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/transactions/<string:tx_id>/approve', methods=['POST'])
def approve_transaction(tx_id):
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        admin_id = session['user_id']
        success, message = bitcoin_simulator.approve_withdrawal(tx_id, admin_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'transaction_id': tx_id
            }), 200
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/transactions/<string:tx_id>/reject', methods=['POST'])
def reject_transaction(tx_id):
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.json
        reason = data.get('reason', 'No reason provided')
        admin_id = session['user_id']
        
        success, message = bitcoin_simulator.reject_withdrawal(tx_id, admin_id, reason)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'transaction_id': tx_id
            }), 200
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/transactions/<string:tx_id>/flag', methods=['POST'])
def flag_transaction(tx_id):
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        data = request.json
        reason = data.get('reason', 'Suspicious activity')
        admin_id = session['user_id']
        
        success, message = bitcoin_simulator.flag_transaction(tx_id, admin_id, reason)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'transaction_id': tx_id
            }), 200
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/users', methods=['GET'])
def get_all_users():
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        # Get query parameters
        kyc_status_filter = request.args.get('kyc_status', 'all')
        risk_level_filter = request.args.get('risk_level', 'all')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        
        # Build query
        query = User.query.filter_by(role='player')  # Only show players
        
        if kyc_status_filter != 'all':
            query = query.filter_by(kyc_status=kyc_status_filter)
        
        if risk_level_filter != 'all':
            query = query.filter_by(risk_level=risk_level_filter)
        
        # Order by most recent first
        query = query.order_by(User.created_at.desc())
        
        # Paginate
        total_users = query.count()
        users = query.offset((page - 1) * limit).limit(limit).all()
        
        total_pages = (total_users + limit - 1) // limit
        
        # Enrich with wallet and transaction info
        enriched_users = []
        for user in users:
            user_dict = user.to_dict()
            
            # Add wallet info
            wallet = Wallet.query.filter_by(user_id=user.id).first()
            if wallet:
                user_dict['wallet'] = {
                    'balance': float(wallet.balance),
                    'btc_address': wallet.btc_address
                }
            
            # Add transaction summary
            total_deposits = db.session.query(db.func.sum(Transaction.amount)).filter_by(
                user_id=user.id, type='deposit', status='completed'
            ).scalar() or 0
            
            total_withdrawals = db.session.query(db.func.sum(Transaction.amount)).filter_by(
                user_id=user.id, type='withdrawal', status='completed'
            ).scalar() or 0
            
            user_dict['transaction_summary'] = {
                'total_deposits': float(total_deposits),
                'total_withdrawals': float(total_withdrawals)
            }
            
            enriched_users.append(user_dict)
        
        return jsonify({
            'status': 'success',
            'users': enriched_users,
            'total_pages': total_pages,
            'current_page': page,
            'total_users': total_users
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Get user details
        user_dict = user.to_dict()
        
        # Get wallet
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if wallet:
            user_dict['wallet'] = wallet.to_dict()
        
        # Get KYC documents
        kyc_documents = KYCDocument.query.filter_by(user_id=user_id).all()
        user_dict['kyc_documents'] = [doc.to_dict() for doc in kyc_documents]
        
        # Get risk assessments
        risk_assessments = RiskAssessment.query.filter_by(user_id=user_id).order_by(
            RiskAssessment.assessed_at.desc()
        ).all()
        user_dict['risk_assessments'] = [assessment.to_dict() for assessment in risk_assessments]
        
        # Get recent transactions
        recent_transactions = Transaction.query.filter_by(user_id=user_id).order_by(
            Transaction.created_at.desc()
        ).limit(10).all()
        user_dict['recent_transactions'] = [tx.to_dict() for tx in recent_transactions]
        
        return jsonify({
            'status': 'success',
            'user': user_dict
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/users/<int:user_id>/suspend', methods=['POST'])
def suspend_user(user_id):
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User suspended',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/users/<int:user_id>/activate', methods=['POST'])
def activate_user(user_id):
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User activated',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_bp.route('/admin/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error
    
    try:
        # Get various statistics for the admin dashboard
        total_users = User.query.filter_by(role='player').count()
        active_users = User.query.filter_by(role='player', is_active=True).count()
        
        pending_transactions = Transaction.query.filter(
            Transaction.status.in_(['pending_admin', 'pending'])
        ).count()
        
        flagged_transactions = Transaction.query.filter_by(status='flagged').count()
        
        # Today's transactions
        today = datetime.utcnow().date()
        today_transactions = Transaction.query.filter(
            db.func.date(Transaction.created_at) == today
        ).count()
        
        # KYC status breakdown
        kyc_pending = User.query.filter_by(role='player', kyc_status='pending').count()
        kyc_verified = User.query.filter_by(role='player', kyc_status='verified').count()
        kyc_flagged = User.query.filter_by(role='player', kyc_status='flagged').count()
        
        # Risk level breakdown
        risk_low = User.query.filter_by(role='player', risk_level='low').count()
        risk_medium = User.query.filter_by(role='player', risk_level='medium').count()
        risk_high = User.query.filter_by(role='player', risk_level='high').count()
        
        return jsonify({
            'status': 'success',
            'stats': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'inactive': total_users - active_users
                },
                'transactions': {
                    'pending': pending_transactions,
                    'flagged': flagged_transactions,
                    'today': today_transactions
                },
                'kyc': {
                    'pending': kyc_pending,
                    'verified': kyc_verified,
                    'flagged': kyc_flagged
                },
                'risk': {
                    'low': risk_low,
                    'medium': risk_medium,
                    'high': risk_high
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from database import db
from models.user import User, Transaction, AuditLog

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """Admin dashboard data"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Get basic statistics
        total_users = User.query.count()
        total_transactions = Transaction.query.count()
        pending_kyc = User.query.filter_by(kyc_status='pending').count()
        flagged_transactions = Transaction.query.filter_by(flagged=True).count()
        
        # Get recent activities
        recent_transactions = Transaction.query.order_by(
            Transaction.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_transactions': total_transactions,
                'pending_kyc': pending_kyc,
                'flagged_transactions': flagged_transactions
            },
            'recent_activities': [
                {
                    'id': tx.id,
                    'user_id': tx.user_id,
                    'type': tx.type,
                    'amount': float(tx.amount),
                    'status': tx.status,
                    'created_at': tx.created_at.isoformat()
                } for tx in recent_transactions
            ]
        })
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/transactions', methods=['GET'])
@login_required
def get_all_transactions():
    """Get all transactions for admin review"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        transactions = Transaction.query.order_by(
            Transaction.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'transactions': [
                {
                    'id': tx.id,
                    'user_id': tx.user_id,
                    'type': tx.type,
                    'amount': float(tx.amount),
                    'status': tx.status,
                    'risk_score': float(tx.risk_score),
                    'flagged': tx.flagged,
                    'created_at': tx.created_at.isoformat()
                } for tx in transactions.items
            ],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
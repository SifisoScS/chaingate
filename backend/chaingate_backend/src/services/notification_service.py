from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from src.models.user import db, User
import json

socketio = SocketIO()

# Store connected users
connected_users = {}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Remove user from connected users
    for user_id, sid in list(connected_users.items()):
        if sid == request.sid:
            del connected_users[user_id]
            break

@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    if user_id:
        connected_users[user_id] = request.sid
        join_room(f'user_{user_id}')
        print(f"User {user_id} joined room")
        emit('joined', {'message': 'Connected successfully'})

@socketio.on('leave')
def handle_leave(data):
    user_id = data.get('user_id')
    if user_id in connected_users:
        del connected_users[user_id]
        leave_room(f'user_{user_id}')
        print(f"User {user_id} left room")

def notify_user(user_id, event_type, data):
    """Send notification to a specific user"""
    room = f'user_{user_id}'
    emit(event_type, data, room=room, namespace='/')

def notify_all(event_type, data):
    """Send notification to all connected users"""
    emit(event_type, data, broadcast=True, namespace='/')

def notify_transaction_update(transaction_id, status, user_id=None):
    """Notify about transaction status changes"""
    notification_data = {
        'type': 'transaction_update',
        'transaction_id': transaction_id,
        'status': status,
        'timestamp': json.dumps(json.dumps({'timestamp': 'now'}))  # Simplified
    }
    if user_id:
        notify_user(user_id, 'notification', notification_data)
    else:
        notify_all('notification', notification_data)

def notify_risk_alert(user_id, risk_score, reason):
    """Notify about risk assessment changes"""
    notification_data = {
        'type': 'risk_alert',
        'risk_score': risk_score,
        'reason': reason,
        'timestamp': json.dumps({'timestamp': 'now'})
    }
    notify_user(user_id, 'notification', notification_data)

def notify_compliance_report(report_id, status):
    """Notify about compliance report generation"""
    notification_data = {
        'type': 'compliance_report',
        'report_id': report_id,
        'status': status,
        'timestamp': json.dumps({'timestamp': 'now'})
    }
    notify_all('notification', notification_data)

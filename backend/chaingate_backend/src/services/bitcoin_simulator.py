import uuid
import random
import hashlib
import time
from datetime import datetime, timedelta
import threading

class BitcoinSimulator:
    def __init__(self):
        self.confirmation_threshold = 3
        self.withdrawal_approval_threshold = 1.0  # BTC
        self.deposit_confirmation_interval_min_seconds = 30
        self.deposit_confirmation_interval_max_seconds = 120
        self.withdrawal_broadcast_delay_seconds = 60
        self.transaction_failure_rate_percent = 5
        
    def generate_address(self, user_id):
        """Generate a unique, realistic-looking Bitcoin address for a user"""
        # Create a mock bech32 address (starts with bc1)
        random_part = hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()[:32]
        return f"bc1q{random_part}"
    
    def generate_tx_hash(self):
        """Generate a mock transaction hash"""
        return hashlib.sha256(f"{uuid.uuid4()}{time.time()}".encode()).hexdigest()
    
    def generate_tx_id(self):
        """Generate a unique transaction ID"""
        return str(uuid.uuid4())
    
    def simulate_deposit(self, user_id, address, amount):
        """Simulate an incoming Bitcoin transaction"""
        from src.models.user import Transaction, db
        
        tx_id = self.generate_tx_id()
        tx_hash = self.generate_tx_hash()
        
        # Create initial transaction record
        transaction = Transaction(
            id=tx_id,
            user_id=user_id,
            type='deposit',
            amount=amount,
            currency='BTC',
            status='initiated',
            to_address=address,
            tx_hash=tx_hash,
            confirmations=0,
            fee=0.0
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Start confirmation simulation in background
        threading.Thread(
            target=self._simulate_deposit_confirmations,
            args=(tx_id,),
            daemon=True
        ).start()
        
        return transaction
    
    def _simulate_deposit_confirmations(self, tx_id):
        """Background process to simulate deposit confirmations"""
        from src.models.user import Transaction, Wallet, db
        from flask import current_app

        with current_app.app_context():
            try:
                # Initial delay before first confirmation
                time.sleep(random.randint(10, 30))

                transaction = Transaction.query.get(tx_id)
                if not transaction:
                    return

                # Check for random failure
                if random.randint(1, 100) <= self.transaction_failure_rate_percent:
                    return self._update_transaction_status(
                        transaction,
                        'failed',
                        'Network congestion - transaction failed'
                    )
                # Update to broadcasting
                transaction.status = 'broadcasting'
                db.session.commit()

                # Simulate confirmations
                for conf in range(1, self.confirmation_threshold + 1):
                    delay = random.randint(
                        self.deposit_confirmation_interval_min_seconds,
                        self.deposit_confirmation_interval_max_seconds
                    )
                    time.sleep(delay)

                    transaction = Transaction.query.get(tx_id)
                    if not transaction or transaction.status == 'failed':
                        return

                    transaction.confirmations = conf
                    if conf == 1:
                        transaction.status = 'pending'
                    elif conf >= self.confirmation_threshold:
                        transaction.status = 'completed'

                        if wallet := Wallet.query.filter_by(
                            user_id=transaction.user_id
                        ).first():
                            wallet.balance += transaction.amount

                    db.session.commit()

            except Exception as e:
                print(f"Error in deposit confirmation simulation: {e}")
    
    def process_withdrawal(self, user_id, to_address, amount):
        """Simulate an outgoing Bitcoin transaction"""
        from src.models.user import Transaction, Wallet, db
        
        # Check wallet balance
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if not wallet or wallet.balance < amount:
            return None, "Insufficient balance"
        
        tx_id = self.generate_tx_id()
        fee = amount * 0.001  # 0.1% fee
        
        # Create withdrawal transaction
        transaction = Transaction(
            id=tx_id,
            user_id=user_id,
            type='withdrawal',
            amount=amount,
            currency='BTC',
            status='requested',
            from_address=wallet.btc_address,
            to_address=to_address,
            fee=fee
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Process withdrawal immediately
        self._process_withdrawal(tx_id)
        
        return transaction, None
    
    def _process_withdrawal(self, tx_id):
        """Process withdrawal immediately"""
        threading.Thread(
            target=self._process_approved_withdrawal,
            args=(tx_id,),
            daemon=True
        ).start()
    

    
    def _process_approved_withdrawal(self, tx_id):
        """Process an approved withdrawal"""
        from src.models.user import Transaction, Wallet, db
        from flask import current_app

        with current_app.app_context():
            try:
                transaction = Transaction.query.get(tx_id)
                if not transaction:
                    return

                # Deduct from wallet balance
                wallet = Wallet.query.filter_by(user_id=transaction.user_id).first()
                if wallet and wallet.balance >= transaction.amount:
                    wallet.balance -= (transaction.amount + transaction.fee)
                    db.session.commit()
                else:
                    return self._update_transaction_status(
                        transaction,
                        'rejected',
                        'Insufficient balance at processing time'
                    )
                # Simulate broadcasting delay
                time.sleep(self.withdrawal_broadcast_delay_seconds)

                transaction.status = 'broadcasting'
                transaction.tx_hash = self.generate_tx_hash()
                db.session.commit()

                # Simulate network propagation
                time.sleep(random.randint(30, 120))

                transaction.status = 'completed'
                db.session.commit()

            except Exception as e:
                print(f"Error in withdrawal processing: {e}")

    def _update_transaction_status(self, transaction, status, notes):
        """Update transaction status and notes"""
        transaction.status = status
        db.session.commit()
        return
    
    def get_confirmation_status(self, tx_id):
        """Get current confirmation status of a transaction"""
        from src.models.user import Transaction

        if transaction := Transaction.query.get(tx_id):
            return {
                'transaction_id': transaction.id,
                'status': transaction.status,
                'confirmations': transaction.confirmations,
                'amount': float(transaction.amount),
                'type': transaction.type,
                'tx_hash': transaction.tx_hash
            }
        else:
            return None
    



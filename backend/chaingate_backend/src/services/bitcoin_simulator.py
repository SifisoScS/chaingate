import random
import time
from datetime import datetime
from database import db
from models.user import Transaction

class BitcoinSimulator:
    """Simulate Bitcoin transactions for testing"""
    
    def __init__(self):
        self.network_status = "online"
        self.confirmation_speed = 3  # minutes between confirmations
    
    def generate_address(self, user_id):
        """Generate a simulated Bitcoin address"""
        prefix = "bc1q"
        random_chars = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=31))
        return f"{prefix}{random_chars}"
    
    def simulate_transaction(self, transaction_id):
        """Simulate blockchain confirmation process"""
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return False
        
        # Simulate confirmations over time
        for i in range(1, 7):  # Up to 6 confirmations
            time.sleep(0.5)  # Simulate network delay
            transaction.confirmations = i
            if i >= 3:  # Consider confirmed after 3 confirmations
                transaction.status = 'confirmed'
            
            db.session.commit()
        
        return True
    
    def get_network_status(self):
        """Return current network status"""
        statuses = ["online", "slow", "congested"]
        weights = [0.8, 0.15, 0.05]  # 80% online, 15% slow, 5% congested
        return random.choices(statuses, weights=weights)[0]
    
    def calculate_fee(self, amount):
        """Calculate simulated transaction fee"""
        base_fee = 0.0001  # Base fee in BTC
        network_multiplier = {
            "online": 1.0,
            "slow": 1.5,
            "congested": 2.0
        }
        
        current_status = self.get_network_status()
        fee = base_fee * network_multiplier[current_status]
        return min(fee, amount * 0.01)  # Cap at 1% of amount

# Create global instance
bitcoin_simulator = BitcoinSimulator()
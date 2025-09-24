#!/usr/bin/env python3
"""
Simple runner script for ChainGate application
Run this from the chaingate_backend directory
"""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import create_app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Create database tables
        from database import db
        db.create_all()
        print("Database tables created successfully!")
        print("Starting ChainGate server...")
        print("Access the application at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
    
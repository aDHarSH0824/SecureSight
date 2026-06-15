#!/usr/bin/env python3
"""
Change Admin Password
=====================
A security script to update the password of the admin user.
"""

import sys
import os
import getpass

# Add root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.web.app import app, db, User
from dotenv import load_dotenv

def change_password():
    load_dotenv()
    
    with app.app_context():
        # Find the admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ Error: Admin user ('admin') not found in the database. Run db_setup.py first.")
            return
            
        print("🔐 SecureSight Admin Password Update")
        print("-----------------------------------")
        
        # Prompt securely for new password
        password = getpass.getpass("Enter new admin password: ")
        if not password:
            print("❌ Error: Password cannot be empty.")
            return
            
        confirm = getpass.getpass("Confirm new password: ")
        if password != confirm:
            print("❌ Error: Passwords do not match.")
            return
            
        # Update and save
        admin.set_password(password)
        db.session.commit()
        print("\n✅ Admin password updated successfully!")

if __name__ == '__main__':
    change_password()

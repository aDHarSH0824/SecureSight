#!/usr/bin/env python3
"""
Database Setup & Initialization
===============================
Initializes database tables and configures default entries.
"""

import sys
import os

# Add root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.web.app import app, db, User, CameraSetting
from dotenv import load_dotenv

def init_db():
    load_dotenv()
    
    # Ensure config and data directories exist
    os.makedirs("config", exist_ok=True)
    os.makedirs(os.path.join("data", "alerts"), exist_ok=True)
    os.makedirs(os.path.join("data", "models"), exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    with app.app_context():
        print("🔨 Initializing database...")
        db.create_all()
        
        # Check if default admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin', 
                role='admin', 
                email='admin@example.com',
                first_name='System',
                last_name='Admin',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("👤 Created default admin user (username: admin, password: admin123)")
        else:
            print("👤 Default admin user already exists")
            
        # Check if there is at least one default camera setting
        if not CameraSetting.query.first():
            default_cam = CameraSetting(
                source="0",
                detections=["motion", "object", "face"],
                object_threshold=0.5,
                motion_threshold=30
            )
            db.session.add(default_cam)
            db.session.commit()
            print("📹 Added default Camera 0 setting to database")
            
        print("✅ Database initialization complete!")

if __name__ == '__main__':
    init_db()

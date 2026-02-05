#!/usr/bin/env python3
"""
Database initialization script.

Run this script to create all database tables.

Usage:
    python scripts/init_db.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from backend.models.database import engine, Base

# Import all models to register them
from backend.models.user import User
from backend.models.chat_history import ChatSession, ChatMessage
from backend.models.profile import LearningProfile, KnowledgePointRecord


def init_database():
    """Initialize database tables"""
    settings = get_settings()
    
    print("=" * 50)
    print("AI Tutor Database Initialization")
    print("=" * 50)
    print(f"\nDatabase: {settings.mysql_database}")
    print(f"Host: {settings.mysql_host}:{settings.mysql_port}")
    print(f"User: {settings.mysql_user}")
    print()
    
    try:
        # Create all tables
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # List created tables
        print("\nTables created:")
        for table in Base.metadata.sorted_tables:
            print(f"  ✓ {table.name}")
        
        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. MySQL server is running")
        print("  2. Database exists (create it manually if needed)")
        print("  3. .env file has correct credentials")
        print("\nTo create database manually:")
        print(f"  mysql -u root -p -e 'CREATE DATABASE IF NOT EXISTS {settings.mysql_database};'")
        sys.exit(1)


if __name__ == "__main__":
    init_database()

"""
Database Initialization Script

Runs Alembic migrations to create or update the database schema.
Use this instead of creating tables directly.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.session import init_db, get_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database"""
    print("="*60)
    print("DATABASE MIGRATIONS")
    print("="*60)
    print()
    
    try:
        # Get engine to verify connection
        engine = get_engine()
        print("✅ Database connection established")
        
        # Run Alembic migrations
        print("Running Alembic migrations (upgrade head)...")
        init_db(drop_all=False)
        
        print()
        print("="*60)
        print("✅ DATABASE MIGRATIONS COMPLETE")
        print("="*60)
        print()
        print("Schema is up to date.")
        print("You can now start the application.")
        print()
        
    except Exception as e:
        print()
        print("="*60)
        print("❌ DATABASE INITIALIZATION FAILED")
        print("="*60)
        print(f"Error: {e}")
        print()
        print("Please check:")
        print("1. Database server is running")
        print("2. Database credentials in .env are correct")
        print("3. Database exists and user has permissions")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


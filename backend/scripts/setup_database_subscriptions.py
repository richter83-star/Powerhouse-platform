"""
Script to create subscription tables in the database.

This will execute the SQL from schema.sql to create the
subscriptions, invoices, and payment_methods tables.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_subscription_tables():
    """Create subscription-related tables"""
    print("Creating subscription tables...")
    print("=" * 60)
    
    engine = get_engine()
    
    # Read the subscription table SQL from schema.sql
    schema_file = Path(__file__).parent.parent / "database" / "schema.sql"
    
    if not schema_file.exists():
        print(f"ERROR: schema.sql not found at {schema_file}")
        sys.exit(1)
    
    with open(schema_file, 'r') as f:
        sql_content = f.read()
    
    # Extract subscription table creation SQL
    # Find the subscription tables section
    start_marker = "-- Subscription and Billing Tables"
    end_marker = "-- Create indexes for subscriptions"
    
    start_idx = sql_content.find(start_marker)
    end_idx = sql_content.find(end_marker)
    
    if start_idx == -1:
        print("ERROR: Could not find subscription tables section in schema.sql")
        sys.exit(1)
    
    if end_idx == -1:
        # If end marker not found, take everything after start
        subscription_sql = sql_content[start_idx:]
    else:
        subscription_sql = sql_content[start_idx:end_idx]
    
    # Also get the indexes
    indexes_start = sql_content.find("-- Create indexes for subscriptions")
    indexes_end = sql_content.find("-- Create indexes for performance")
    
    if indexes_start != -1:
        if indexes_end != -1:
            indexes_sql = sql_content[indexes_start:indexes_end]
        else:
            indexes_sql = sql_content[indexes_start:indexes_start + 2000]  # Take reasonable chunk
        subscription_sql += "\n" + indexes_sql
    
    # Split into individual statements
    statements = [s.strip() for s in subscription_sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for statement in statements:
                if statement:
                    try:
                        conn.execute(text(statement))
                        # Extract table name for logging
                        if "CREATE TABLE" in statement.upper():
                            table_name = statement.split("IF NOT EXISTS")[1].split("(")[0].strip() if "IF NOT EXISTS" in statement.upper() else statement.split("TABLE")[1].split("(")[0].strip()
                            print(f"✓ Created table: {table_name}")
                        elif "CREATE INDEX" in statement.upper():
                            index_name = statement.split("IF NOT EXISTS")[1].split("ON")[0].strip() if "IF NOT EXISTS" in statement.upper() else statement.split("INDEX")[1].split("ON")[0].strip()
                            print(f"✓ Created index: {index_name}")
                    except Exception as e:
                        # Check if it's a "already exists" error
                        error_msg = str(e).lower()
                        if "already exists" in error_msg or "duplicate" in error_msg:
                            print(f"⚠ Table/index already exists (skipping)")
                        else:
                            print(f"⚠ Warning: {e}")
            
            trans.commit()
            print("\n" + "=" * 60)
            print("✓ Database tables created successfully!")
            print("=" * 60)
            
        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    try:
        create_subscription_tables()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


"""
Simple Stripe integration test (standalone, no app dependencies).
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct import of settings (minimal dependencies)
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class TestSettings(BaseSettings):
    stripe_secret_key: Optional[str] = Field(default=None)
    stripe_webhook_secret: Optional[str] = Field(default=None)
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

test_settings = TestSettings()

print("Stripe Integration - Simple Test")
print("=" * 60)

# Test 1: Environment Variables
print("\n1. Environment Variables:")
if test_settings.stripe_secret_key:
    key_type = "LIVE" if "live" in test_settings.stripe_secret_key else "TEST"
    print(f"  ✓ STRIPE_SECRET_KEY: {key_type} mode ({test_settings.stripe_secret_key[:20]}...)")
else:
    print("  ✗ STRIPE_SECRET_KEY: Not set")

if test_settings.stripe_webhook_secret:
    print(f"  ✓ STRIPE_WEBHOOK_SECRET: Set ({test_settings.stripe_webhook_secret[:20]}...)")
else:
    print("  ✗ STRIPE_WEBHOOK_SECRET: Not set")

# Test 2: Stripe Package
print("\n2. Stripe Package:")
try:
    import stripe
    print(f"  ✓ Stripe package installed")
    
    if test_settings.stripe_secret_key:
        stripe.api_key = test_settings.stripe_secret_key
        account = stripe.Account.retrieve()
        print(f"  ✓ Stripe API connection successful")
        print(f"    Account ID: {account.id}")
except ImportError:
    print("  ✗ Stripe package not installed (pip install stripe)")
except Exception as e:
    print(f"  ⚠ Stripe API test failed: {e}")

# Test 3: Configuration Files
print("\n3. Configuration Files:")
files_to_check = [
    "api/billing_routes.py",
    "core/commercial/stripe_service.py",
    "database/schema.sql"
]

for file_path in files_to_check:
    full_path = Path(__file__).parent.parent / file_path
    if full_path.exists():
        print(f"  ✓ {file_path}")
    else:
        print(f"  ✗ {file_path} - Missing")

print("\n" + "=" * 60)
print("✓ Basic checks complete!")
print("\nFor full integration test, ensure all dependencies are installed:")
print("  pip install stripe psycopg2-binary")
print("\nThen run: python scripts/verify_stripe_setup.py")


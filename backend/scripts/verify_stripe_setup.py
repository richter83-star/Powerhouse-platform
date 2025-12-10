"""
Script to verify Stripe integration setup.

Checks:
1. Environment variables are set
2. Stripe API connection works
3. Database tables exist
4. Webhook configuration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from database.session import get_engine
from sqlalchemy import text, inspect
import stripe

print("Verifying Stripe Integration Setup...")
print("=" * 60)

# Check 1: Environment Variables
print("\n1. Checking Environment Variables...")
checks_passed = 0
total_checks = 0

total_checks += 1
if settings.stripe_secret_key:
    print("  ✓ STRIPE_SECRET_KEY is set")
    checks_passed += 1
else:
    print("  ✗ STRIPE_SECRET_KEY is NOT set")

total_checks += 1
if settings.stripe_publishable_key:
    print("  ✓ STRIPE_PUBLISHABLE_KEY is set")
    checks_passed += 1
else:
    print("  ⚠ STRIPE_PUBLISHABLE_KEY is NOT set (optional)")

total_checks += 1
if settings.stripe_webhook_secret:
    print("  ✓ STRIPE_WEBHOOK_SECRET is set")
    checks_passed += 1
else:
    print("  ✗ STRIPE_WEBHOOK_SECRET is NOT set")

# Check 2: Stripe API Connection
print("\n2. Testing Stripe API Connection...")
total_checks += 1
try:
    stripe.api_key = settings.stripe_secret_key
    # Try to list products (lightweight operation)
    stripe.Product.list(limit=1)
    print("  ✓ Stripe API connection successful")
    checks_passed += 1
except Exception as e:
    print(f"  ✗ Stripe API connection failed: {e}")

# Check 3: Database Tables
print("\n3. Checking Database Tables...")
total_checks += 1
try:
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ['subscriptions', 'invoices', 'payment_methods']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if not missing_tables:
        print("  ✓ All subscription tables exist")
        checks_passed += 1
    else:
        print(f"  ✗ Missing tables: {', '.join(missing_tables)}")
        print("     Run: python scripts/setup_database_subscriptions.py")
except Exception as e:
    print(f"  ✗ Database check failed: {e}")

# Check 4: Subscription Plans Configuration
print("\n4. Checking Subscription Plans Configuration...")
total_checks += 1
try:
    from api.billing_routes import SUBSCRIPTION_PLANS
    plans_with_price_ids = [p for p in SUBSCRIPTION_PLANS if p.get("stripe_price_id")]
    
    if len(plans_with_price_ids) >= 3:  # At least 3 paid plans should have Price IDs
        print(f"  ✓ {len(plans_with_price_ids)} plans have Stripe Price IDs configured")
        checks_passed += 1
    else:
        print(f"  ⚠ Only {len(plans_with_price_ids)} plans have Stripe Price IDs")
        print("     Run: python scripts/setup_stripe_subscriptions.py")
        print("     Then update billing_routes.py with the Price IDs")
except Exception as e:
    print(f"  ⚠ Could not check plans: {e}")

# Check 5: Webhook Endpoint
print("\n5. Webhook Configuration...")
print("  ℹ Webhook endpoint should be configured in Stripe Dashboard:")
print("     URL: https://yourdomain.com/api/billing/webhook")
print("     Secret: Should match STRIPE_WEBHOOK_SECRET")
print("     Events: customer.subscription.*, invoice.paid, invoice.payment_failed")

# Summary
print("\n" + "=" * 60)
print(f"Summary: {checks_passed}/{total_checks} checks passed")
print("=" * 60)

if checks_passed == total_checks:
    print("\n✓ All checks passed! Stripe integration is ready.")
    sys.exit(0)
else:
    print(f"\n⚠ {total_checks - checks_passed} check(s) failed. Please fix the issues above.")
    sys.exit(1)


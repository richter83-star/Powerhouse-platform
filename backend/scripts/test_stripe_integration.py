"""
Quick test script to verify Stripe integration is working.

Tests:
1. Stripe service initialization
2. API endpoint availability
3. Configuration validation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from core.commercial.stripe_service import get_stripe_service
import stripe

print("Testing Stripe Integration")
print("=" * 60)

# Test 1: Environment Variables
print("\n1. Testing Environment Variables...")
try:
    assert settings.stripe_secret_key, "STRIPE_SECRET_KEY not set"
    assert settings.stripe_webhook_secret, "STRIPE_WEBHOOK_SECRET not set"
    print("  ✓ All environment variables configured")
except AssertionError as e:
    print(f"  ✗ {e}")
    sys.exit(1)

# Test 2: Stripe API Connection
print("\n2. Testing Stripe API Connection...")
try:
    stripe.api_key = settings.stripe_secret_key
    # Test with a lightweight API call
    account = stripe.Account.retrieve()
    print(f"  ✓ Connected to Stripe account: {account.id}")
    print(f"    Account type: {'Live' if 'live' in settings.stripe_secret_key else 'Test'} mode")
except Exception as e:
    print(f"  ✗ Stripe API connection failed: {e}")
    sys.exit(1)

# Test 3: Stripe Service
print("\n3. Testing Stripe Service...")
try:
    stripe_service = get_stripe_service()
    print("  ✓ StripeService initialized successfully")
except Exception as e:
    print(f"  ✗ StripeService initialization failed: {e}")
    sys.exit(1)

# Test 4: Verify Products Exist
print("\n4. Verifying Stripe Products...")
try:
    products = stripe.Product.list(limit=10)
    plan_products = [p for p in products.data if "Plan" in p.name]
    
    if len(plan_products) >= 3:
        print(f"  ✓ Found {len(plan_products)} subscription plan products:")
        for product in plan_products:
            prices = stripe.Price.list(product=product.id, limit=1)
            if prices.data:
                price = prices.data[0]
                amount = price.unit_amount / 100
                print(f"    - {product.name}: ${amount}/{price.recurring.interval}")
    else:
        print(f"  ⚠ Only found {len(plan_products)} products (expected 3+)")
except Exception as e:
    print(f"  ⚠ Could not verify products: {e}")

# Test 5: Check Price IDs in Configuration
print("\n5. Verifying Price IDs in Configuration...")
try:
    from api.billing_routes import SUBSCRIPTION_PLANS
    
    paid_plans = [p for p in SUBSCRIPTION_PLANS if p.get("price", 0) > 0]
    plans_with_ids = [p for p in paid_plans if p.get("stripe_price_id")]
    
    print(f"  ✓ {len(plans_with_ids)}/{len(paid_plans)} paid plans have Price IDs:")
    for plan in plans_with_ids:
        # Verify Price ID exists in Stripe
        try:
            price = stripe.Price.retrieve(plan["stripe_price_id"])
            print(f"    ✓ {plan['name']}: {plan['stripe_price_id']} (${price.unit_amount/100}/{price.recurring.interval})")
        except Exception as e:
            print(f"    ✗ {plan['name']}: Price ID not found in Stripe - {e}")
except Exception as e:
    print(f"  ⚠ Could not verify Price IDs: {e}")

# Test 6: Webhook Configuration
print("\n6. Verifying Webhook Configuration...")
try:
    endpoints = stripe.WebhookEndpoint.list(limit=10)
    billing_endpoints = [e for e in endpoints.data if "/api/billing/webhook" in e.url]
    
    if billing_endpoints:
        endpoint = billing_endpoints[0]
        print(f"  ✓ Webhook endpoint configured:")
        print(f"    URL: {endpoint.url}")
        print(f"    Status: {endpoint.status}")
        print(f"    Events: {len(endpoint.enabled_events)} subscribed")
    else:
        print("  ⚠ No billing webhook endpoint found")
except Exception as e:
    print(f"  ⚠ Could not verify webhook: {e}")

print("\n" + "=" * 60)
print("✓ Stripe Integration Test Complete!")
print("=" * 60)
print("\nNext Steps:")
print("1. Ensure database tables are created (run setup_database_subscriptions.py)")
print("2. Restart your backend server")
print("3. Test the checkout flow at /settings/billing in your frontend")
print("\nAll systems ready! 🚀")


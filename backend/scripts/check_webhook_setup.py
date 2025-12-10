"""
Script to help verify and configure Stripe webhook setup.

This script checks webhook configuration and provides instructions.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
import stripe

print("Stripe Webhook Setup Check")
print("=" * 60)

# Check webhook secret
if settings.stripe_webhook_secret:
    print(f"✓ Webhook secret configured: {settings.stripe_webhook_secret[:20]}...")
else:
    print("✗ STRIPE_WEBHOOK_SECRET not configured")
    sys.exit(1)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key

print("\nChecking Stripe Webhook Endpoints...")
print("-" * 60)

try:
    # List webhook endpoints
    endpoints = stripe.WebhookEndpoint.list(limit=10)
    
    if endpoints.data:
        print(f"\nFound {len(endpoints.data)} webhook endpoint(s):\n")
        for endpoint in endpoints.data:
            print(f"  URL: {endpoint.url}")
            print(f"  Status: {endpoint.status}")
            print(f"  Events: {len(endpoint.enabled_events)} events")
            print(f"  Created: {endpoint.created}")
            
            # Check if it matches our expected endpoint
            if "/api/billing/webhook" in endpoint.url:
                print("  ✓ This endpoint matches our billing webhook!")
                
                # Check events
                required_events = [
                    "customer.subscription.created",
                    "customer.subscription.updated",
                    "customer.subscription.deleted",
                    "invoice.paid",
                    "invoice.payment_failed"
                ]
                
                enabled_event_names = [e for e in endpoint.enabled_events]
                missing_events = [e for e in required_events if e not in enabled_event_names]
                
                if not missing_events:
                    print("  ✓ All required events are subscribed!")
                else:
                    print(f"  ⚠ Missing events: {', '.join(missing_events)}")
                    print("     Add these in Stripe Dashboard → Webhooks → Your endpoint")
            else:
                print("  ⚠ This endpoint doesn't match our billing webhook")
            
            print()
    else:
        print("\n⚠ No webhook endpoints found in Stripe")
        print("\nTo create a webhook endpoint:")
        print("1. Go to https://dashboard.stripe.com/webhooks")
        print("2. Click 'Add endpoint'")
        print("3. Enter URL: https://yourdomain.com/api/billing/webhook")
        print("4. Select these events:")
        print("   - customer.subscription.created")
        print("   - customer.subscription.updated")
        print("   - customer.subscription.deleted")
        print("   - invoice.paid")
        print("   - invoice.payment_failed")
        print("5. Copy the signing secret and add to .env as STRIPE_WEBHOOK_SECRET")
    
    print("\n" + "=" * 60)
    print("Webhook Configuration Summary:")
    print("=" * 60)
    print(f"Expected URL: https://yourdomain.com/api/billing/webhook")
    print(f"Webhook Secret: {settings.stripe_webhook_secret[:20]}...")
    print("\nFor local development, use Stripe CLI:")
    print("  stripe listen --forward-to localhost:8001/api/billing/webhook")
    print("  (Use the whsec_... secret from the CLI output)")
    
except stripe.error.StripeError as e:
    print(f"\n✗ Error checking webhooks: {e}")
    sys.exit(1)


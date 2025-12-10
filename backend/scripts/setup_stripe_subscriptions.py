"""
Script to create Stripe Products and Prices for subscription plans.

This script will create the products and prices in Stripe and output
the Price IDs that need to be added to billing_routes.py
"""

import os
import sys
import stripe
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Initialize Stripe
if not settings.stripe_secret_key:
    print("ERROR: STRIPE_SECRET_KEY not found in environment variables")
    print("Please add it to your .env file")
    sys.exit(1)

stripe.api_key = settings.stripe_secret_key

# Subscription plans to create (monthly and annual)
PLANS = [
    {
        "name": "Starter Plan",
        "description": "Perfect for small teams getting started",
        "price": 29.00,  # $29.00
        "annual_price": 290.00,  # $290/year (2 months free = 10/12 pricing)
        "currency": "usd",
        "interval": "month",
        "plan_id": "starter"
    },
    {
        "name": "Professional Plan",
        "description": "For growing businesses with advanced needs",
        "price": 99.00,  # $99.00
        "annual_price": 990.00,  # $990/year (2 months free = 10/12 pricing)
        "currency": "usd",
        "interval": "month",
        "plan_id": "professional"
    },
    {
        "name": "Enterprise Plan",
        "description": "For large organizations with custom requirements",
        "price": 299.00,  # $299.00
        "annual_price": 2990.00,  # $2990/year (2 months free = 10/12 pricing)
        "currency": "usd",
        "interval": "month",
        "plan_id": "enterprise"
    }
]


def create_stripe_products():
    """Create Stripe products and prices for all plans"""
    print("Creating Stripe Products and Prices...")
    print("=" * 60)
    
    price_ids = {}
    
    for plan in PLANS:
        try:
            # Check if product already exists
            products = stripe.Product.list(limit=100)
            existing_product = None
            for product in products.data:
                if product.name == plan["name"]:
                    existing_product = product
                    print(f"✓ Found existing product: {plan['name']}")
                    break
            
            # Create product if it doesn't exist
            if not existing_product:
                product = stripe.Product.create(
                    name=plan["name"],
                    description=plan["description"]
                )
                print(f"✓ Created product: {plan['name']} (ID: {product.id})")
            else:
                product = existing_product
            
            # Check if price already exists
            prices = stripe.Price.list(product=product.id, limit=100)
            existing_price = None
            for price in prices.data:
                if (price.unit_amount == int(plan["price"] * 100) and 
                    price.currency == plan["currency"] and
                    price.recurring and
                    price.recurring.interval == plan["interval"]):
                    existing_price = price
                    print(f"✓ Found existing price: ${plan['price']}/{plan['interval']}")
                    break
            
            # Create monthly price if it doesn't exist
            if not existing_price:
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan["price"] * 100),  # Convert to cents
                    currency=plan["currency"],
                    recurring={
                        "interval": "month"
                    }
                )
                print(f"✓ Created monthly price: ${plan['price']}/month (ID: {price.id})")
            else:
                price = existing_price
            
            price_ids[f"{plan['plan_id']}_monthly"] = price.id
            
            # Create annual price
            annual_prices = stripe.Price.list(product=product.id, limit=100)
            existing_annual_price = None
            for p in annual_prices.data:
                if (p.unit_amount == int(plan.get("annual_price", plan["price"] * 10) * 100) and 
                    p.currency == plan["currency"] and
                    p.recurring and
                    p.recurring.interval == "year"):
                    existing_annual_price = p
                    print(f"✓ Found existing annual price: ${plan.get('annual_price', plan['price'] * 10)}/year")
                    break
            
            if not existing_annual_price:
                annual_price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan.get("annual_price", plan["price"] * 10) * 100),
                    currency=plan["currency"],
                    recurring={
                        "interval": "year"
                    }
                )
                print(f"✓ Created annual price: ${plan.get('annual_price', plan['price'] * 10)}/year (ID: {annual_price.id})")
                price_ids[f"{plan['plan_id']}_annual"] = annual_price.id
            else:
                price_ids[f"{plan['plan_id']}_annual"] = existing_annual_price.id
            
        except stripe.error.StripeError as e:
            print(f"✗ Error creating {plan['name']}: {e}")
            continue
    
    print("\n" + "=" * 60)
    print("STRIPE PRICE IDs - Monthly and Annual:")
    print("=" * 60)
    print()
    print("# Monthly prices (already in billing_routes.py):")
    for plan_id, price_id in price_ids.items():
        if "_monthly" in plan_id:
            base_id = plan_id.replace("_monthly", "")
            print(f'  {base_id}: {price_id}')
    print()
    print("# Annual prices (add to billing_routes.py):")
    for plan_id, price_id in price_ids.items():
        if "_annual" in plan_id:
            base_id = plan_id.replace("_annual", "")
            print(f'  {base_id}_annual: {price_id}')
    print()
    print("=" * 60)
    print("✓ Stripe setup complete!")
    print()
    print("Next steps:")
    print("1. Annual prices created - update billing_routes.py with annual_price_id fields")
    print("2. Run: python scripts/setup_database_subscriptions.py")
    
    return price_ids


if __name__ == "__main__":
    try:
        create_stripe_products()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


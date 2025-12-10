# Stripe Integration - Quick Reference

## API Endpoints

### Subscription Management
- `POST /api/billing/subscribe` - Create checkout session
- `GET /api/billing/subscription` - Get current subscription
- `POST /api/billing/subscription/cancel` - Cancel subscription
- `POST /api/billing/subscription/resume` - Resume subscription
- `GET /api/billing/plans` - List available plans
- `GET /api/billing/invoices` - Get invoice history
- `GET /api/billing/payment-methods` - Get payment methods
- `POST /api/billing/webhook` - Stripe webhook handler

## Subscription Plans

| Plan | Price | Stripe Price ID |
|------|-------|----------------|
| Free | $0 | N/A |
| Starter | $29/month | `price_1Sc6AEBkploTMGtNdKGbHHon` |
| Professional | $99/month | `price_1Sc6AFBkploTMGtNqbqd5sB8` |
| Enterprise | $299/month | `price_1Sc6AFBkploTMGtNtFX7DZju` |

## Environment Variables

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Webhook Events

The system handles these Stripe webhook events:
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

## Testing

### Test Checkout Flow
1. Navigate to `/settings/billing`
2. Click "Subscribe" on any plan
3. Complete Stripe Checkout
4. Verify subscription in database

### Test Webhook (Local)
```bash
stripe listen --forward-to localhost:8001/api/billing/webhook
stripe trigger customer.subscription.created
```

## Helper Scripts

- `scripts/setup_stripe_subscriptions.py` - Create products/prices
- `scripts/setup_database_subscriptions.py` - Create database tables
- `scripts/verify_stripe_setup.py` - Verify configuration
- `scripts/check_webhook_setup.py` - Check webhook config
- `scripts/test_stripe_integration.py` - Test integration

## Troubleshooting

### Check Configuration
```bash
python scripts/verify_stripe_setup.py
```

### Check Webhook
```bash
python scripts/check_webhook_setup.py
```

### Test Integration
```bash
python scripts/test_stripe_integration.py
```

## Database Tables

- `subscriptions` - Subscription records
- `invoices` - Invoice history
- `payment_methods` - Payment methods

## Files

- `backend/core/commercial/stripe_service.py` - Stripe service layer
- `backend/api/billing_routes.py` - API endpoints
- `backend/database/schema.sql` - Database schema
- `backend/docs/STRIPE_WEBHOOK_SETUP.md` - Webhook setup guide


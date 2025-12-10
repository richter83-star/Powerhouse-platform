# Stripe Webhook Setup Guide

This guide explains how to set up Stripe webhooks for the Powerhouse billing system.

## Overview

Stripe webhooks allow Stripe to notify your application about subscription events in real-time. This is essential for keeping subscription data synchronized between Stripe and your database.

## Webhook Endpoint

The webhook endpoint is located at:
```
POST /api/billing/webhook
```

**Important**: This endpoint is exempt from authentication middleware because it uses Stripe's signature verification instead.

## Required Environment Variables

Add these to your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...  # or sk_live_... for production
STRIPE_PUBLISHABLE_KEY=pk_test_...  # or pk_live_... for production
STRIPE_WEBHOOK_SECRET=whsec_...  # Webhook signing secret from Stripe Dashboard
```

## Stripe Price IDs Configuration

Before using subscriptions, you need to:

1. Create Products and Prices in Stripe Dashboard
2. Update `SUBSCRIPTION_PLANS` in `backend/api/billing_routes.py` with the Stripe Price IDs

For each subscription plan, create a Product and Price in Stripe:
- Go to **Products** in Stripe Dashboard
- Create a product for each plan (e.g., "Starter Plan", "Professional Plan")
- Create a recurring Price for each product (monthly or yearly)
- Copy the Price ID (starts with `price_`)
- Update the `stripe_price_id` field in `SUBSCRIPTION_PLANS` array

Example:
```python
{
    "id": "starter",
    "name": "Starter",
    "stripe_price_id": "price_1234567890abcdef",  # From Stripe Dashboard
    ...
}
```

**Note**: The "free" plan doesn't need a Stripe Price ID since it's $0.

## Setup Steps

### 1. Get Your Webhook Secret

1. Log in to the [Stripe Dashboard](https://dashboard.stripe.com)
2. Go to **Developers** → **Webhooks**
3. Click **Add endpoint**
4. Enter your webhook URL:
   - **Development**: `http://localhost:8001/api/billing/webhook` (use Stripe CLI for local testing)
   - **Production**: `https://yourdomain.com/api/billing/webhook`
5. Select the following events to subscribe to:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
6. Click **Add endpoint**
7. Copy the **Signing secret** (starts with `whsec_`) and add it to your `.env` file as `STRIPE_WEBHOOK_SECRET`

### 2. Local Development with Stripe CLI

For local development, use the Stripe CLI to forward webhooks to your local server:

1. Install the [Stripe CLI](https://stripe.com/docs/stripe-cli)
2. Login to Stripe:
   ```bash
   stripe login
   ```
3. Forward webhooks to your local server:
   ```bash
   stripe listen --forward-to localhost:8001/api/billing/webhook
   ```
4. The CLI will display a webhook signing secret. Use this as your `STRIPE_WEBHOOK_SECRET` for local development.

### 3. Test Webhook Events

You can trigger test webhook events using the Stripe CLI:

```bash
# Test subscription created
stripe trigger customer.subscription.created

# Test subscription updated
stripe trigger customer.subscription.updated

# Test invoice paid
stripe trigger invoice.paid
```

## Webhook Event Handlers

The following events are handled:

### `customer.subscription.created`
- Creates a new subscription record in the database
- Associates subscription with user and tenant
- Stores subscription metadata

### `customer.subscription.updated`
- Updates subscription status, period dates, and cancellation status
- Syncs changes from Stripe to database

### `customer.subscription.deleted`
- Marks subscription as canceled in database
- Records cancellation timestamp

### `invoice.paid`
- Creates or updates invoice record
- Links invoice to subscription
- Stores invoice PDF URL

### `invoice.payment_failed`
- Logs payment failure
- Can trigger notifications (to be implemented)

## Security

The webhook endpoint verifies the Stripe signature using `stripe.Webhook.construct_event()`. This ensures that:

1. The request actually came from Stripe
2. The payload hasn't been tampered with
3. The webhook secret matches

**Never disable signature verification in production!**

## Troubleshooting

### Webhook Not Receiving Events

1. Check that your webhook endpoint URL is correct and accessible
2. Verify `STRIPE_WEBHOOK_SECRET` is set correctly
3. Check Stripe Dashboard → Webhooks → Recent events for delivery status
4. Review application logs for webhook processing errors

### Signature Verification Failed

1. Ensure `STRIPE_WEBHOOK_SECRET` matches the signing secret from Stripe Dashboard
2. For local development, use the secret from `stripe listen` command
3. Check that the raw request body is being passed to `construct_webhook_event()` (not parsed JSON)

### Database Errors

1. Ensure subscription tables exist (run `backend/database/schema.sql`)
2. Check database connection settings
3. Verify user_id and tenant_id are present in subscription metadata

## Production Checklist

- [ ] Webhook endpoint is publicly accessible (HTTPS required)
- [ ] `STRIPE_WEBHOOK_SECRET` is set in production environment
- [ ] Webhook events are subscribed in Stripe Dashboard
- [ ] Webhook endpoint is exempt from authentication (already configured)
- [ ] Error logging is enabled for webhook processing
- [ ] Database backup strategy is in place

## Additional Resources

- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Webhook Security Best Practices](https://stripe.com/docs/webhooks/signatures)


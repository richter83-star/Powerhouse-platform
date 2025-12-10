"""
Billing API Routes for Stripe Subscription Management

Handles subscription creation, management, invoices, and webhooks.
"""

import logging
from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from database.session import get_db
from core.commercial.stripe_service import get_stripe_service
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["Billing"])

# Request/Response Models
class SubscribeRequest(BaseModel):
    plan_id: str
    interval: Optional[str] = "month"  # "month" or "year"

class ChangePlanRequest(BaseModel):
    new_plan_id: str
    interval: Optional[str] = "month"  # "month" or "year"
    proration_behavior: Optional[str] = "always_invoice"  # "always_invoice", "create_prorations", "none"

class SubscriptionResponse(BaseModel):
    id: Optional[str] = None
    plan_id: Optional[str] = None
    plan_name: Optional[str] = None
    status: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    amount: int = 0
    currency: str = "usd"

class InvoiceResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    date: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    pdf_url: Optional[str] = None

class PaymentMethodResponse(BaseModel):
    id: str
    type: str
    card: Optional[Dict[str, Any]] = None
    is_default: bool = False

class PlanResponse(BaseModel):
    id: str
    name: str
    price: int
    currency: str
    interval: str
    features: List[str]
    popular: bool = False


# Helper function to get user context
def get_user_context(request: Request) -> Tuple[str, str]:
    """Extract user_id and tenant_id from request state"""
    user_id = getattr(request.state, 'user_id', None)
    tenant_id = getattr(request.state, 'tenant_id', None)
    
    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User context not found"
        )
    
    return user_id, tenant_id


# Helper function to get user email from database
def get_user_email(db: Session, user_id: str) -> Optional[str]:
    """Get user email from database"""
    result = db.execute(
        text("SELECT email FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    row = result.fetchone()
    return row[0] if row else None


# Subscription Plans (should be moved to database or config in production)
SUBSCRIPTION_PLANS = [
    {
        "id": "free",
        "name": "Free",
        "price": 0,
        "currency": "usd",
        "interval": "month",
        "features": [
            "3 AI agents",
            "5 workflows",
            "100 API calls/hour",
            "1 GB storage",
            "Basic support"
        ],
        "stripe_price_id": None,  # Free plan doesn't need Stripe Price ID
        "trial_days": 0,
        "popular": False
    },
    {
        "id": "starter",
        "name": "Starter",
        "price": 2900,  # $29.00 in cents
        "currency": "usd",
        "interval": "month",
        "features": [
            "10 AI agents",
            "20 workflows",
            "1,000 API calls/hour",
            "10 GB storage",
            "Email support",
            "Priority processing"
        ],
        "stripe_price_id": "price_1Sc6AEBkploTMGtNdKGbHHon",  # Created via setup_stripe_subscriptions.py
        "stripe_price_id_annual": "price_1ScDBNBkploTMGtNd24Fxauh",  # Annual price
        "annual_price": 29000,  # $290.00 in cents (2 months free)
        "trial_days": 14,  # 14-day free trial
        "popular": False
    },
    {
        "id": "professional",
        "name": "Professional",
        "price": 9900,  # $99.00 in cents
        "currency": "usd",
        "interval": "month",
        "features": [
            "Unlimited agents",
            "Unlimited workflows",
            "10,000 API calls/hour",
            "100 GB storage",
            "Priority support",
            "Advanced analytics",
            "Custom integrations"
        ],
        "stripe_price_id": "price_1Sc6AFBkploTMGtNqbqd5sB8",  # Created via setup_stripe_subscriptions.py
        "stripe_price_id_annual": "price_1ScDBOBkploTMGtN0uVY7SXP",  # Annual price
        "annual_price": 99000,  # $990.00 in cents (2 months free)
        "trial_days": 14,  # 14-day free trial
        "popular": True
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "price": 29900,  # $299.00 in cents
        "currency": "usd",
        "interval": "month",
        "features": [
            "Unlimited everything",
            "Dedicated support",
            "SLA guarantee",
            "Custom deployment",
            "On-premise option",
            "Advanced security",
            "Compliance certifications"
        ],
        "stripe_price_id": "price_1Sc6AFBkploTMGtNtFX7DZju",  # Created via setup_stripe_subscriptions.py
        "stripe_price_id_annual": "price_1ScDBOBkploTMGtNNKoJxZJX",  # Annual price
        "annual_price": 299000,  # $2990.00 in cents (2 months free)
        "trial_days": 14,  # 14-day free trial
        "popular": False
    }
]


@router.post("/subscribe")
async def create_subscription(
    request: SubscribeRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout session for subscription.
    
    Returns checkout URL that frontend should redirect to.
    """
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Find plan
        plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == request.plan_id), None)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Determine which price ID to use based on interval
        interval = request.interval or "month"
        if interval == "year":
            price_id = plan.get("stripe_price_id_annual")
            if not price_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Annual pricing not available for plan {request.plan_id}"
                )
        else:
            price_id = plan.get("stripe_price_id")
            if not price_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stripe price ID not configured for plan {request.plan_id}"
                )
        
        # Get user email
        user_email = get_user_email(db, user_id)
        if not user_email:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get or create Stripe customer
        customer = stripe_service.create_or_get_customer(
            email=user_email,
            metadata={"user_id": user_id, "tenant_id": tenant_id}
        )
        
        # Build success and cancel URLs
        frontend_url = settings.frontend_url
        success_url = f"{frontend_url}/billing?success=true&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{frontend_url}/billing?canceled=true"
        
        # Create checkout session with trial period if applicable
        trial_days = plan.get("trial_days", 0)
        session = stripe_service.create_checkout_session(
            price_id=price_id,
            customer_id=customer["id"],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "plan_id": request.plan_id,
                "interval": interval
            },
            trial_period_days=trial_days if trial_days > 0 else None
        )
        
        return {
            "checkout_url": session["url"],
            "session_id": session["id"]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating subscription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/subscription")
async def get_subscription(
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Get current subscription details"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get subscription from database
        result = db.execute(
            text("""
                SELECT stripe_customer_id, stripe_subscription_id, plan_id, plan_name,
                       status, current_period_start, current_period_end,
                       cancel_at_period_end, amount, currency
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row:
            return {"subscription": None}
        
        # Get latest subscription from Stripe
        stripe_subscription = None
        if row[1]:  # stripe_subscription_id
            stripe_subscription = stripe_service.get_subscription(row[1])
        
        # Return database record, enriched with Stripe data if available
        return {
            "subscription": {
                "plan_id": row[2],
                "plan_name": row[3],
                "status": row[4],
                "current_period_start": row[5].isoformat() if row[5] else None,
                "current_period_end": row[6].isoformat() if row[6] else None,
                "cancel_at_period_end": row[7],
                "amount": int(row[8]) if row[8] else 0,
                "currency": row[9] or "usd"
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting subscription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get subscription")


@router.post("/subscription/cancel")
async def cancel_subscription(
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Cancel subscription at end of billing period"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get subscription from database
        result = db.execute(
            text("""
                SELECT stripe_subscription_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Active subscription not found")
        
        # Cancel in Stripe
        stripe_service.cancel_subscription(row[0], cancel_at_period_end=True)
        
        # Update database
        db.execute(
            text("""
                UPDATE subscriptions
                SET cancel_at_period_end = TRUE, updated_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
            """),
            {"subscription_id": row[0]}
        )
        db.commit()
        
        return {"message": "Subscription will be canceled at end of billing period"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.post("/subscription/resume")
async def resume_subscription(
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Resume a canceled subscription"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get subscription from database
        result = db.execute(
            text("""
                SELECT stripe_subscription_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                AND cancel_at_period_end = TRUE
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Canceled subscription not found")
        
        # Resume in Stripe
        stripe_service.resume_subscription(row[0])
        
        # Update database
        db.execute(
            text("""
                UPDATE subscriptions
                SET cancel_at_period_end = FALSE, updated_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
            """),
            {"subscription_id": row[0]}
        )
        db.commit()
        
        return {"message": "Subscription resumed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming subscription: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to resume subscription")


@router.post("/subscription/change-plan")
async def change_subscription_plan(
    request: ChangePlanRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Change subscription plan with proration"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get current subscription
        result = db.execute(
            text("""
                SELECT stripe_subscription_id, plan_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Active subscription not found")
        
        subscription_id = row[0]
        current_plan_id = row[1]
        
        # Find new plan
        new_plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == request.new_plan_id), None)
        if not new_plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Determine price ID based on interval
        interval = request.interval or "month"
        if interval == "year":
            new_price_id = new_plan.get("stripe_price_id_annual")
            if not new_price_id:
                raise HTTPException(status_code=400, detail="Annual pricing not available for this plan")
        else:
            new_price_id = new_plan.get("stripe_price_id")
            if not new_price_id:
                raise HTTPException(status_code=400, detail="Price ID not configured for this plan")
        
        # Change plan with proration
        updated_subscription = stripe_service.change_subscription_plan(
            subscription_id=subscription_id,
            new_price_id=new_price_id,
            proration_behavior=request.proration_behavior or "always_invoice"
        )
        
        # Update database
        db.execute(
            text("""
                UPDATE subscriptions
                SET plan_id = :plan_id,
                    stripe_price_id = :price_id,
                    amount = :amount,
                    updated_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
            """),
            {
                "subscription_id": subscription_id,
                "plan_id": request.new_plan_id,
                "price_id": new_price_id,
                "amount": updated_subscription.get("amount", 0)
            }
        )
        db.commit()
        
        return {
            "message": "Subscription plan changed successfully",
            "subscription": updated_subscription
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing subscription plan: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to change subscription plan")


@router.get("/subscription/change-plan/preview")
async def preview_plan_change(
    new_plan_id: str,
    interval: Optional[str] = "month",
    request_obj: Request = None,
    db: Session = Depends(get_db)
):
    """Preview proration for a plan change"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get current subscription
        result = db.execute(
            text("""
                SELECT stripe_subscription_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Active subscription not found")
        
        # Find new plan
        new_plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == new_plan_id), None)
        if not new_plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Determine price ID
        if interval == "year":
            new_price_id = new_plan.get("stripe_price_id_annual")
        else:
            new_price_id = new_plan.get("stripe_price_id")
        
        if not new_price_id:
            raise HTTPException(status_code=400, detail="Price ID not configured for this plan")
        
        # Calculate proration
        proration = stripe_service.calculate_proration(
            subscription_id=row[0],
            new_price_id=new_price_id
        )
        
        # Get current plan ID
        result_plan = db.execute(
            text("""
                SELECT plan_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row_plan = result_plan.fetchone()
        current_plan_id = row_plan[0] if row_plan else None
        
        return {
            "current_plan": current_plan_id,
            "new_plan": new_plan_id,
            "proration": proration
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing plan change: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to preview plan change")


@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    plans_list = []
    for plan in SUBSCRIPTION_PLANS:
        plan_data = {
            "id": plan["id"],
            "name": plan["name"],
            "price": plan["price"],
            "currency": plan["currency"],
            "interval": plan["interval"],
            "features": plan["features"],
            "trial_days": plan.get("trial_days", 0),
            "popular": plan.get("popular", False)
        }
        # Add annual pricing if available
        if plan.get("annual_price"):
            plan_data["annual_price"] = plan["annual_price"]
            # Calculate savings percentage
            monthly_yearly = plan["price"] * 12
            if monthly_yearly > 0:
                savings = ((monthly_yearly - plan["annual_price"]) / monthly_yearly) * 100
                plan_data["annual_savings_percent"] = round(savings, 0)
        plans_list.append(plan_data)
    
    return {"plans": plans_list}


@router.get("/invoices")
async def get_invoices(
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Get invoice history"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get Stripe customer ID
        result = db.execute(
            text("""
                SELECT stripe_customer_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            return {"invoices": []}
        
        # Get invoices from Stripe
        invoices = stripe_service.get_invoices(row[0], limit=20)
        
        return {"invoices": invoices}
    
    except Exception as e:
        logger.error(f"Error getting invoices: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get invoices")


@router.get("/payment-methods")
async def get_payment_methods(
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Get payment methods"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get Stripe customer ID
        result = db.execute(
            text("""
                SELECT stripe_customer_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            return {"payment_methods": []}
        
        # Get payment methods from Stripe
        payment_methods = stripe_service.get_payment_methods(row[0])
        
        return {"payment_methods": payment_methods}
    
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get payment methods")


@router.post("/payment-methods/setup-intent")
async def create_setup_intent(
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Create a SetupIntent for adding a new payment method"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get or create Stripe customer
        user_email = get_user_email(db, user_id)
        if not user_email:
            raise HTTPException(status_code=404, detail="User not found")
        
        customer = stripe_service.create_or_get_customer(
            email=user_email,
            metadata={"user_id": user_id, "tenant_id": tenant_id}
        )
        
        # Create setup intent
        setup_intent = stripe_service.create_setup_intent(
            customer_id=customer["id"],
            metadata={"user_id": user_id, "tenant_id": tenant_id}
        )
        
        return setup_intent
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating setup intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create setup intent")


class AddPaymentMethodRequest(BaseModel):
    payment_method_id: str

@router.post("/payment-methods")
async def add_payment_method(
    request: AddPaymentMethodRequest,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Attach a payment method to customer"""
    try:
        payment_method_id = request.payment_method_id
        
        if not payment_method_id:
            raise HTTPException(status_code=400, detail="payment_method_id is required")
        
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get Stripe customer ID
        user_email = get_user_email(db, user_id)
        if not user_email:
            raise HTTPException(status_code=404, detail="User not found")
        
        customer = stripe_service.create_or_get_customer(
            email=user_email,
            metadata={"user_id": user_id, "tenant_id": tenant_id}
        )
        
        # Attach payment method
        payment_method = stripe_service.attach_payment_method(
            payment_method_id=payment_method_id,
            customer_id=customer["id"]
        )
        
        return {"payment_method": payment_method, "message": "Payment method added successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding payment method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add payment method")


@router.delete("/payment-methods/{payment_method_id}")
async def delete_payment_method(
    payment_method_id: str,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Delete a payment method"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Verify payment method belongs to user's customer
        result = db.execute(
            text("""
                SELECT stripe_customer_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Verify payment method belongs to this customer
        payment_methods = stripe_service.get_payment_methods(row[0])
        if not any(pm["id"] == payment_method_id for pm in payment_methods):
            raise HTTPException(status_code=403, detail="Payment method not found or access denied")
        
        # Detach payment method
        stripe_service.detach_payment_method(payment_method_id)
        
        return {"message": "Payment method deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting payment method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete payment method")


@router.post("/payment-methods/{payment_method_id}/set-default")
async def set_default_payment_method(
    payment_method_id: str,
    request_obj: Request,
    db: Session = Depends(get_db)
):
    """Set a payment method as default"""
    try:
        user_id, tenant_id = get_user_context(request_obj)
        stripe_service = get_stripe_service()
        
        # Get Stripe customer ID
        result = db.execute(
            text("""
                SELECT stripe_customer_id
                FROM subscriptions
                WHERE tenant_id = :tenant_id AND user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"tenant_id": tenant_id, "user_id": user_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Verify payment method belongs to this customer
        payment_methods = stripe_service.get_payment_methods(row[0])
        if not any(pm["id"] == payment_method_id for pm in payment_methods):
            raise HTTPException(status_code=403, detail="Payment method not found or access denied")
        
        # Set as default
        stripe_service.set_default_payment_method(
            customer_id=row[0],
            payment_method_id=payment_method_id
        )
        
        return {"message": "Default payment method updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default payment method: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to set default payment method")


@router.post("/webhook")
async def stripe_webhook(
    request: Request
):
    """
    Handle Stripe webhook events.
    
    This endpoint should be exempt from authentication middleware.
    It verifies webhook signatures from Stripe.
    """
    try:
        stripe_service = get_stripe_service()
        
        # Get raw body and signature
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        # Verify and construct event
        event = stripe_service.construct_webhook_event(payload, sig_header)
        
        # Handle different event types
        event_type = event["type"]
        data = event["data"]["object"]
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        # Process subscription events
        if event_type == "customer.subscription.created":
            await handle_subscription_created(data, request)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(data, request)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(data, request)
        elif event_type == "invoice.paid":
            await handle_invoice_paid(data, request)
        elif event_type == "invoice.payment_failed":
            await handle_invoice_payment_failed(data, request)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"status": "success"}
    
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_subscription_created(subscription: Dict[str, Any], request: Request):
    """Handle subscription.created webhook"""
    from database.session import get_db
    from sqlalchemy.orm import Session
    
    db = next(get_db())
    try:
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")
        tenant_id = metadata.get("tenant_id")
        
        if not user_id or not tenant_id:
            logger.warning("Subscription created without user_id/tenant_id in metadata")
            return
        
        # Extract plan info
        items = subscription.get("items", {}).get("data", [])
        price = items[0].get("price", {}) if items else {}
        plan_id = metadata.get("plan_id", "unknown")
        plan_name = price.get("nickname") or price.get("id") or plan_id
        
        # Insert or update subscription
        db.execute(
            text("""
                INSERT INTO subscriptions (
                    tenant_id, user_id, stripe_customer_id, stripe_subscription_id,
                    stripe_price_id, plan_id, plan_name, status,
                    current_period_start, current_period_end,
                    cancel_at_period_end, amount, currency
                ) VALUES (
                    :tenant_id, :user_id, :customer_id, :subscription_id,
                    :price_id, :plan_id, :plan_name, :status,
                    TO_TIMESTAMP(:period_start), TO_TIMESTAMP(:period_end),
                    :cancel_at_period_end, :amount, :currency
                )
                ON CONFLICT (stripe_subscription_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    current_period_start = EXCLUDED.current_period_start,
                    current_period_end = EXCLUDED.current_period_end,
                    cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                    updated_at = NOW()
            """),
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "customer_id": subscription["customer"],
                "subscription_id": subscription["id"],
                "price_id": price.get("id") if price else None,
                "plan_id": plan_id,
                "plan_name": plan_name,
                "status": subscription["status"],
                "period_start": subscription["current_period_start"],
                "period_end": subscription["current_period_end"],
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
                "amount": price.get("unit_amount", 0) if price else 0,
                "currency": price.get("currency", "usd") if price else "usd"
            }
        )
        db.commit()
        logger.info(f"Subscription created: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription.created: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def handle_subscription_updated(subscription: Dict[str, Any], request: Request):
    """Handle subscription.updated webhook"""
    from database.session import get_db
    from sqlalchemy.orm import Session
    
    db = next(get_db())
    try:
        db.execute(
            text("""
                UPDATE subscriptions
                SET status = :status,
                    current_period_start = TO_TIMESTAMP(:period_start),
                    current_period_end = TO_TIMESTAMP(:period_end),
                    cancel_at_period_end = :cancel_at_period_end,
                    updated_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
            """),
            {
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "period_start": subscription["current_period_start"],
                "period_end": subscription["current_period_end"],
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False)
            }
        )
        db.commit()
        logger.info(f"Subscription updated: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription.updated: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def handle_subscription_deleted(subscription: Dict[str, Any], request: Request):
    """Handle subscription.deleted webhook"""
    from database.session import get_db
    from sqlalchemy.orm import Session
    
    db = next(get_db())
    try:
        db.execute(
            text("""
                UPDATE subscriptions
                SET status = 'canceled',
                    canceled_at = NOW(),
                    updated_at = NOW()
                WHERE stripe_subscription_id = :subscription_id
            """),
            {"subscription_id": subscription["id"]}
        )
        db.commit()
        logger.info(f"Subscription deleted: {subscription['id']}")
    except Exception as e:
        logger.error(f"Error handling subscription.deleted: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def handle_invoice_paid(invoice: Dict[str, Any], request: Request):
    """Handle invoice.paid webhook"""
    from database.session import get_db
    from sqlalchemy.orm import Session
    
    db = next(get_db())
    try:
        # Get subscription to find tenant_id and user_id
        result = db.execute(
            text("""
                SELECT tenant_id, user_id, id
                FROM subscriptions
                WHERE stripe_subscription_id = :subscription_id
            """),
            {"subscription_id": invoice.get("subscription")}
        )
        row = result.fetchone()
        
        if not row:
            logger.warning(f"Invoice paid for unknown subscription: {invoice.get('subscription')}")
            return
        
        # Insert or update invoice
        db.execute(
            text("""
                INSERT INTO invoices (
                    subscription_id, tenant_id, user_id, stripe_invoice_id,
                    amount, currency, status, period_start, period_end,
                    invoice_date, pdf_url
                ) VALUES (
                    :subscription_id, :tenant_id, :user_id, :invoice_id,
                    :amount, :currency, :status,
                    TO_TIMESTAMP(:period_start), TO_TIMESTAMP(:period_end),
                    TO_TIMESTAMP(:invoice_date), :pdf_url
                )
                ON CONFLICT (stripe_invoice_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = NOW()
            """),
            {
                "subscription_id": row[2],
                "tenant_id": row[0],
                "user_id": row[1],
                "invoice_id": invoice["id"],
                "amount": invoice["amount_paid"],
                "currency": invoice["currency"],
                "status": invoice["status"],
                "period_start": invoice.get("period_start"),
                "period_end": invoice.get("period_end"),
                "invoice_date": invoice["created"],
                "pdf_url": invoice.get("invoice_pdf")
            }
        )
        db.commit()
        logger.info(f"Invoice paid: {invoice['id']}")
    except Exception as e:
        logger.error(f"Error handling invoice.paid: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def handle_invoice_payment_failed(invoice: Dict[str, Any], request: Request):
    """Handle invoice.payment_failed webhook"""
    logger.warning(f"Invoice payment failed: {invoice['id']}")
    # Could send notification email here
    # Could update subscription status to past_due


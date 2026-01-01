"""
Stripe Service for Payment Processing and Subscriptions

Handles Stripe Checkout sessions, subscription management, and webhook processing.
"""

import logging
import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key
elif settings.environment == "production":
    logger.warning("Stripe secret key not configured. Stripe functionality will be disabled.")


class StripeService:
    """Service for interacting with Stripe API"""
    
    def __init__(self):
        if not settings.stripe_secret_key:
            raise ValueError("Stripe secret key must be configured")
    
    def create_checkout_session(
        self,
        price_id: str,
        customer_email: Optional[str] = None,
        customer_id: Optional[str] = None,
        success_url: str = "http://localhost:3000/billing?success=true",
        cancel_url: str = "http://localhost:3000/billing?canceled=true",
        metadata: Optional[Dict[str, str]] = None,
        trial_period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription.
        
        Args:
            price_id: Stripe Price ID for the subscription plan
            customer_email: Customer email (if creating new customer)
            customer_id: Existing Stripe customer ID
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancellation
            metadata: Additional metadata to attach to the session
        
        Returns:
            Dictionary with checkout session details including 'url'
        """
        try:
            session_params = {
                "mode": "subscription",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {}
            }
            
            if customer_id:
                session_params["customer"] = customer_id
            elif customer_email:
                session_params["customer_email"] = customer_email
            
            # Add trial period if specified
            if trial_period_days and trial_period_days > 0:
                session_params["subscription_data"] = {
                    "trial_period_days": trial_period_days
                }
            
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(f"Created Stripe checkout session: {session.id}")
            return {
                "id": session.id,
                "url": session.url,
                "customer": session.customer
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve subscription details from Stripe.
        
        Args:
            subscription_id: Stripe subscription ID
        
        Returns:
            Subscription object as dictionary or None if not found
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return self._format_subscription(subscription)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving subscription {subscription_id}: {e}")
            return None
    
    def get_customer_subscription(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the active subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
        
        Returns:
            Active subscription or None
        """
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status="active",
                limit=1
            )
            if subscriptions.data:
                return self._format_subscription(subscriptions.data[0])
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving customer subscription: {e}")
            return None
    
    def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            cancel_at_period_end: If True, cancel at end of billing period
        
        Returns:
            Updated subscription object
        """
        try:
            if cancel_at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Canceled subscription: {subscription_id}")
            return self._format_subscription(subscription)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription {subscription_id}: {e}")
            raise
    
    def resume_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume a canceled subscription.
        
        Args:
            subscription_id: Stripe subscription ID
        
        Returns:
            Updated subscription object
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"Resumed subscription: {subscription_id}")
            return self._format_subscription(subscription)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error resuming subscription {subscription_id}: {e}")
            raise
    
    def update_subscription(
        self,
        subscription_id: str,
        price_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update subscription to a different plan.
        
        Args:
            subscription_id: Stripe subscription ID
            price_id: New Stripe Price ID
        
        Returns:
            Updated subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": price_id
                }],
                proration_behavior="always_invoice"
            )
            updated = stripe.Subscription.retrieve(subscription_id)
            logger.info(f"Updated subscription {subscription_id} to price {price_id}")
            return self._format_subscription(updated)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription {subscription_id}: {e}")
            raise
    
    def change_subscription_plan(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "always_invoice"
    ) -> Dict[str, Any]:
        """
        Change subscription plan with proration options.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe Price ID
            proration_behavior: "always_invoice", "create_prorations", or "none"
        
        Returns:
            Updated subscription with proration details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            current_item_id = subscription["items"]["data"][0].id
            
            # Calculate proration
            proration_date = int(datetime.now().timestamp())
            
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": current_item_id,
                    "price": new_price_id
                }],
                proration_behavior=proration_behavior,
                proration_date=proration_date if proration_behavior != "none" else None
            )
            
            # Get upcoming invoice to show proration amount
            upcoming_invoice = None
            if proration_behavior != "none":
                try:
                    upcoming_invoice = stripe.Invoice.upcoming(
                        customer=subscription.customer,
                        subscription=subscription_id
                    )
                except:
                    pass
            
            result = self._format_subscription(updated_subscription)
            if upcoming_invoice:
                result["proration_amount"] = upcoming_invoice.amount_due - (upcoming_invoice.subscription_details.get("billing_cycle_anchor", 0) if hasattr(upcoming_invoice, 'subscription_details') else 0)
                result["next_invoice_amount"] = upcoming_invoice.amount_due
            
            logger.info(f"Changed subscription {subscription_id} to price {new_price_id} with proration: {proration_behavior}")
            return result
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error changing subscription plan: {e}")
            raise
    
    def calculate_proration(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> Dict[str, Any]:
        """
        Calculate proration amount for a plan change without applying it.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New Stripe Price ID
        
        Returns:
            Proration calculation details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Get upcoming invoice with new price
            upcoming_invoice = stripe.Invoice.upcoming(
                customer=subscription.customer,
                subscription=subscription_id,
                subscription_items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_price_id
                }]
            )
            
            # Get current subscription amount
            current_price = subscription["items"]["data"][0]["price"]
            current_amount = current_price.unit_amount if current_price else 0
            
            # Calculate proration
            proration_amount = upcoming_invoice.amount_due - current_amount
            
            return {
                "current_amount": current_amount,
                "new_amount": upcoming_invoice.amount_due,
                "proration_amount": proration_amount,
                "next_invoice_date": datetime.fromtimestamp(upcoming_invoice.period_end).isoformat() if upcoming_invoice.period_end else None
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error calculating proration: {e}")
            raise
    
    def create_or_get_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Stripe customer or retrieve existing one.
        
        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata
        
        Returns:
            Customer object as dictionary
        """
        try:
            # Check if customer exists
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                customer = customers.data[0]
                logger.info(f"Retrieved existing customer: {customer.id}")
            else:
                # Create new customer
                customer = stripe.Customer.create(
                    email=email,
                    name=name,
                    metadata=metadata or {}
                )
                logger.info(f"Created new customer: {customer.id}")
            
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating/getting customer: {e}")
            raise
    
    def get_invoices(self, customer_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
        
        Returns:
            List of invoice dictionaries
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            return [self._format_invoice(inv) for inv in invoices.data]
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving invoices: {e}")
            return []
    
    def get_payment_methods(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get payment methods for a customer.
        
        Args:
            customer_id: Stripe customer ID
        
        Returns:
            List of payment method dictionaries
        """
        try:
            # Get customer to find default payment method
            customer = stripe.Customer.retrieve(customer_id)
            default_pm_id = customer.invoice_settings.default_payment_method
            
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            
            formatted = []
            for pm in payment_methods.data:
                pm_dict = self._format_payment_method(pm)
                pm_dict["is_default"] = (pm.id == default_pm_id) if default_pm_id else False
                formatted.append(pm_dict)
            
            return formatted
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment methods: {e}")
            return []
    
    def create_setup_intent(
        self,
        customer_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a SetupIntent for collecting payment methods.
        
        Args:
            customer_id: Stripe customer ID
            metadata: Additional metadata
        
        Returns:
            SetupIntent with client_secret
        """
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=["card"],
                metadata=metadata or {}
            )
            logger.info(f"Created setup intent: {setup_intent.id}")
            return {
                "id": setup_intent.id,
                "client_secret": setup_intent.client_secret,
                "status": setup_intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating setup intent: {e}")
            raise
    
    def attach_payment_method(
        self,
        payment_method_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """
        Attach a payment method to a customer.
        
        Args:
            payment_method_id: Stripe payment method ID
            customer_id: Stripe customer ID
        
        Returns:
            Attached payment method
        """
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
            return self._format_payment_method(payment_method)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error attaching payment method: {e}")
            raise
    
    def detach_payment_method(self, payment_method_id: str) -> bool:
        """
        Detach a payment method from a customer.
        
        Args:
            payment_method_id: Stripe payment method ID
        
        Returns:
            True if successful
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            logger.info(f"Detached payment method: {payment_method_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error detaching payment method: {e}")
            raise
    
    def set_default_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Set a payment method as the default for a customer.
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
        
        Returns:
            Updated customer object
        """
        try:
            customer = stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
            logger.info(f"Set default payment method {payment_method_id} for customer {customer_id}")
            return {
                "id": customer.id,
                "default_payment_method": customer.invoice_settings.default_payment_method
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error setting default payment method: {e}")
            raise
    
    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        """
        Verify and construct webhook event from Stripe.
        
        Args:
            payload: Raw request body
            sig_header: Stripe signature header
        
        Returns:
            Event object
        """
        if not settings.stripe_webhook_secret:
            raise ValueError("Stripe webhook secret must be configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.stripe_webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise
    
    def _format_subscription(self, subscription: Any) -> Dict[str, Any]:
        """Format Stripe subscription object to internal format"""
        price = subscription["items"]["data"][0]["price"] if subscription["items"]["data"] else None
        
        return {
            "id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status,
            "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
            "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "canceled_at": datetime.fromtimestamp(subscription.canceled_at).isoformat() if subscription.canceled_at else None,
            "price_id": price.id if price else None,
            "amount": subscription["items"]["data"][0]["price"]["unit_amount"] if subscription["items"]["data"] and price else 0,
            "currency": price.currency if price else "usd",
            "plan_name": price.nickname or price.id if price else None
        }
    
    def _format_invoice(self, invoice: Any) -> Dict[str, Any]:
        """Format Stripe invoice object to internal format"""
        return {
            "id": invoice.id,
            "amount": invoice.amount_paid,
            "currency": invoice.currency,
            "status": invoice.status,
            "date": datetime.fromtimestamp(invoice.created).isoformat(),
            "period_start": datetime.fromtimestamp(invoice.period_start).isoformat() if invoice.period_start else None,
            "period_end": datetime.fromtimestamp(invoice.period_end).isoformat() if invoice.period_end else None,
            "pdf_url": invoice.invoice_pdf,
            "subscription_id": invoice.subscription
        }
    
    def _format_payment_method(self, pm: Any) -> Dict[str, Any]:
        """Format Stripe payment method object to internal format"""
        card = pm.card if hasattr(pm, "card") else None
        return {
            "id": pm.id,
            "type": pm.type,
            "card": {
                "brand": card.brand if card else None,
                "last4": card.last4 if card else None,
                "exp_month": card.exp_month if card else None,
                "exp_year": card.exp_year if card else None
            } if card else None,
            "is_default": getattr(pm, "is_default", False)
        }
    
    def create_meter(
        self,
        display_name: str,
        event_name: str,
        value_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Meter for usage tracking.
        
        Args:
            display_name: Human-readable name for the meter
            event_name: Event name to track (e.g., "api_call", "agent_execution")
            value_settings: Value settings for the meter
        
        Returns:
            Meter object as dictionary
        """
        try:
            meter = stripe.billing.Meter.create(
                display_name=display_name,
                event_name=event_name,
                value_settings=value_settings or {"event_payload_key": "quantity"}
            )
            logger.info(f"Created Stripe meter: {meter.id} for {event_name}")
            return {
                "id": meter.id,
                "display_name": meter.display_name,
                "event_name": meter.event_name,
                "status": meter.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating meter: {e}")
            raise
    
    def record_usage_event(
        self,
        meter_id: str,
        identifier: str,
        value: float,
        timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Record a usage event to a Stripe Meter.
        
        Args:
            meter_id: Stripe Meter ID
            identifier: Unique identifier (e.g., customer_id, subscription_id)
            value: Usage value to record
            timestamp: Unix timestamp (defaults to now)
        
        Returns:
            Event record
        """
        try:
            event = stripe.billing.MeterEvent.create(
                meter=meter_id,
                identifier=identifier,
                value=value,
                event_name=stripe.billing.Meter.retrieve(meter_id).event_name,
                timestamp=timestamp or int(datetime.now().timestamp())
            )
            logger.debug(f"Recorded usage event: {event.id} for meter {meter_id}")
            return {
                "id": event.id,
                "meter_id": meter_id,
                "identifier": identifier,
                "value": value
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error recording usage event: {e}")
            raise
    
    def create_usage_based_price(
        self,
        product_id: str,
        meter_id: str,
        currency: str = "usd",
        billing_scheme: str = "per_unit"
    ) -> Dict[str, Any]:
        """
        Create a usage-based price with a meter.
        
        Args:
            product_id: Stripe Product ID
            meter_id: Stripe Meter ID
            currency: Currency code
            billing_scheme: "per_unit" or "tiered"
        
        Returns:
            Price object as dictionary
        """
        try:
            price = stripe.Price.create(
                product=product_id,
                currency=currency,
                billing_scheme=billing_scheme,
                recurring={
                    "interval": "month",
                    "usage_type": "metered"
                },
                meter=meter_id
            )
            logger.info(f"Created usage-based price: {price.id}")
            return {
                "id": price.id,
                "product_id": product_id,
                "meter_id": meter_id,
                "currency": currency
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating usage-based price: {e}")
            raise
    
    def get_meter_usage_summary(
        self,
        meter_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for a meter.
        
        Args:
            meter_id: Stripe Meter ID
            start_time: Start timestamp (Unix)
            end_time: End timestamp (Unix)
        
        Returns:
            Usage summary
        """
        try:
            # Note: Stripe doesn't have a direct API for this in older versions
            # This would need to query meter events or use Stripe's reporting API
            # For now, return basic meter info
            meter = stripe.billing.Meter.retrieve(meter_id)
            return {
                "meter_id": meter.id,
                "display_name": meter.display_name,
                "event_name": meter.event_name,
                "status": meter.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting meter usage: {e}")
            raise


# Global instance
_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """Get or create Stripe service instance"""
    global _stripe_service
    if _stripe_service is None:
        if settings.stripe_secret_key:
            _stripe_service = StripeService()
        else:
            raise ValueError("Stripe secret key not configured")
    return _stripe_service


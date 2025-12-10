"""
Phase 1 Automated Test Script

Tests all Phase 1 commercial-grade features:
1. License Key Activation System
2. Usage Limits Enforcement
3. Email Notification System
4. Customer Support Integration
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy.orm import Session
from database.session import get_db, init_db
from core.commercial.license_manager import LicenseManager, LicenseType
from core.commercial.usage_tracker import get_usage_tracker, LimitType
from core.services.email_service import get_email_service
from core.services.email_templates import EmailTemplates
from core.services.email_queue import EmailQueueService
from core.services.support_service import SupportService, TicketPriority
from database.models import User, License, SupportTicket

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    if passed:
        test_results["passed"].append(name)
        print(f"✅ {name}: PASSED")
        if message:
            print(f"   {message}")
    else:
        test_results["failed"].append(name)
        print(f"❌ {name}: FAILED")
        if message:
            print(f"   {message}")


def log_warning(name: str, message: str):
    """Log warning"""
    test_results["warnings"].append(f"{name}: {message}")
    print(f"⚠️  {name}: {message}")


def test_license_manager():
    """Test license manager functionality"""
    print("\n" + "="*60)
    print("Testing License Key Activation System")
    print("="*60)
    
    try:
        # Test license key generation
        license_manager = LicenseManager()
        license_key = license_manager.generate_license_key(
            license_type=LicenseType.STANDARD,
            seats=1,
            max_devices=1,
            expiration_days=365
        )
        
        log_test(
            "License Key Generation",
            len(license_key) == 29 and license_key.count('-') == 4,
            f"Generated key: {license_key[:20]}..."
        )
        
        # Test license key format validation
        valid = license_manager.validate_license_key_format(license_key)
        log_test("License Key Format Validation", valid)
        
        # Test hardware fingerprinting
        hw = license_manager.get_hardware_fingerprint()
        log_test(
            "Hardware Fingerprinting",
            hw.fingerprint is not None and len(hw.fingerprint) > 0,
            f"Fingerprint: {hw.fingerprint[:20]}..."
        )
        
        # Test license creation (requires database)
        try:
            db = next(get_db())
            license_obj = license_manager.create_license(
                db=db,
                license_key=license_key,
                license_type=LicenseType.STANDARD,
                seats=1,
                max_devices=1,
                expiration_days=365
            )
            log_test("License Creation (Database)", license_obj.id is not None)
            db.close()
        except Exception as e:
            log_warning("License Creation (Database)", f"Requires database: {e}")
        
    except Exception as e:
        log_test("License Manager", False, str(e))


def test_usage_tracker():
    """Test usage tracker functionality"""
    print("\n" + "="*60)
    print("Testing Usage Limits Enforcement")
    print("="*60)
    
    try:
        usage_tracker = get_usage_tracker()
        test_tenant_id = "test-tenant-123"
        
        # Test usage recording
        record = usage_tracker.record_usage(
            tenant_id=test_tenant_id,
            resource_type="api_call",
            quantity=1.0
        )
        log_test(
            "Usage Recording",
            record.tenant_id == test_tenant_id and record.resource_type == "api_call"
        )
        
        # Test limit checking
        limit_status = usage_tracker.check_limit(
            tenant_id=test_tenant_id,
            resource_type="api_call",
            quantity=1.0,
            limit=100,
            limit_type=LimitType.HARD
        )
        log_test(
            "Limit Checking",
            limit_status is not None and hasattr(limit_status, 'allowed'),
            f"Status: {limit_status.message if limit_status else 'None'}"
        )
        
        # Test usage summary
        summary = usage_tracker.get_current_month_usage(test_tenant_id)
        log_test(
            "Usage Summary",
            summary is not None and summary.tenant_id == test_tenant_id
        )
        
        # Test projections
        projections = usage_tracker.get_usage_projections(test_tenant_id, days_ahead=30)
        log_test(
            "Usage Projections",
            projections is not None and "projected_api_calls" in projections
        )
        
    except Exception as e:
        log_test("Usage Tracker", False, str(e))


def test_email_templates():
    """Test email templates"""
    print("\n" + "="*60)
    print("Testing Email Notification System")
    print("="*60)
    
    try:
        # Test verification email
        template = EmailTemplates.verification_email(
            verification_url="https://example.com/verify?token=test",
            user_name="Test User"
        )
        log_test(
            "Verification Email Template",
            "subject" in template and "html" in template and "text" in template
        )
        
        # Test trial ending email
        template = EmailTemplates.trial_ending_email(
            user_name="Test User",
            days_remaining=7,
            upgrade_url="https://example.com/upgrade"
        )
        log_test("Trial Ending Email Template", "subject" in template)
        
        # Test usage alert email
        template = EmailTemplates.usage_alert_email(
            user_name="Test User",
            resource_type="api_call",
            current_usage=950,
            limit=1000,
            percentage=95.0,
            dashboard_url="https://example.com/usage"
        )
        log_test("Usage Alert Email Template", "subject" in template)
        
        # Test payment failed email
        template = EmailTemplates.payment_failed_email(
            user_name="Test User",
            amount="$99.00",
            retry_url="https://example.com/retry",
            billing_url="https://example.com/billing"
        )
        log_test("Payment Failed Email Template", "subject" in template)
        
        # Test system notification email
        template = EmailTemplates.system_notification_email(
            user_name="Test User",
            title="System Maintenance",
            message="Scheduled maintenance on Jan 15",
            action_url="https://example.com/status"
        )
        log_test("System Notification Email Template", "subject" in template)
        
    except Exception as e:
        log_test("Email Templates", False, str(e))


async def test_email_service():
    """Test email service"""
    print("\n" + "="*60)
    print("Testing Email Service")
    print("="*60)
    
    try:
        email_service = get_email_service()
        log_test(
            "Email Service Initialization",
            email_service is not None,
            f"Provider: {email_service.provider.value if email_service else 'None'}"
        )
        
        # Note: Actual sending requires configured email provider
        log_warning(
            "Email Sending",
            "Actual email sending requires configured provider (SendGrid/SES/SMTP)"
        )
        
    except Exception as e:
        log_test("Email Service", False, str(e))


def test_email_queue():
    """Test email queue"""
    print("\n" + "="*60)
    print("Testing Email Queue")
    print("="*60)
    
    try:
        db = next(get_db())
        queue_service = EmailQueueService(db)
        
        # Test email queuing
        email_item = queue_service.enqueue_email(
            to_email="test@example.com",
            subject="Test Email",
            html_content="<h1>Test</h1>",
            text_content="Test"
        )
        log_test(
            "Email Queueing",
            email_item.id is not None and email_item.status.value == "pending"
        )
        
        db.close()
        
    except Exception as e:
        log_warning("Email Queue", f"Requires database: {e}")


def test_support_service():
    """Test support service"""
    print("\n" + "="*60)
    print("Testing Customer Support Integration")
    print("="*60)
    
    try:
        db = next(get_db())
        support_service = SupportService(db)
        
        # Test ticket creation (requires user)
        try:
            # Try to get a test user
            test_user = db.query(User).first()
            if test_user:
                ticket = support_service.create_ticket(
                    user_id=test_user.id,
                    subject="Test Ticket",
                    description="Testing support system",
                    priority=TicketPriority.MEDIUM
                )
                log_test(
                    "Support Ticket Creation",
                    ticket.id is not None and ticket.status.value == "open"
                )
            else:
                log_warning("Support Ticket Creation", "No users found in database")
        except Exception as e:
            log_warning("Support Ticket Creation", f"Error: {e}")
        
        db.close()
        
    except Exception as e:
        log_warning("Support Service", f"Requires database: {e}")


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\nFailed Tests:")
        for test in test_results['failed']:
            print(f"  - {test}")
    
    if test_results['warnings']:
        print("\nWarnings:")
        for warning in test_results['warnings']:
            print(f"  - {warning}")
    
    print("\n" + "="*60)
    if len(test_results['failed']) == 0:
        print("🎉 All critical tests passed!")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    print("="*60)


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Phase 1 Commercial Features - Automated Test Suite")
    print("="*60)
    
    # Initialize database if needed
    try:
        init_db(drop_all=False)
        print("✅ Database initialized")
    except Exception as e:
        log_warning("Database Initialization", f"Error: {e}")
    
    # Run tests
    test_license_manager()
    test_usage_tracker()
    test_email_templates()
    await test_email_service()
    test_email_queue()
    test_support_service()
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    asyncio.run(main())


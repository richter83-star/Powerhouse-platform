# Phase 1 Testing Guide

This guide helps you test all Phase 1 commercial-grade features.

## Prerequisites

1. **Database Setup**: Ensure your database is running and accessible
2. **Backend Running**: Start the backend server (`2_START_BACKEND.bat` or `uvicorn api.main:app`)
3. **Frontend Running**: Start the frontend (`npm run dev` in `frontend/app`)
4. **Authentication**: Have a test user account created

## Test Checklist

### ✅ 1. License Key Activation System

#### Test License Generation (Admin/Backend)
```bash
# Test via API or Python script
POST /api/v1/license/generate
{
  "license_type": "standard",
  "seats": 1,
  "max_devices": 1,
  "expiration_days": 365
}
```

#### Test License Activation (Frontend)
1. Navigate to `/settings/license`
2. Enter a license key (format: XXXX-XXXX-XXXX-XXXX-XXXX)
3. Click "Activate License"
4. Verify:
   - License appears in "My Licenses"
   - Status shows as "ACTIVE"
   - Device count is updated

#### Test License Validation
1. Click "Validate" button with a license key
2. Verify validation message shows correct status
3. Test with expired/revoked licenses

#### Test Hardware Fingerprinting
1. Check "Device Information" section shows hardware fingerprint
2. Activate same license on different device
3. Verify device count increases
4. Test deactivation removes device

**Expected Results:**
- ✅ License keys generate correctly
- ✅ Activation binds to hardware fingerprint
- ✅ Multi-device support works
- ✅ Validation shows correct status
- ✅ Deactivation works

---

### ✅ 2. Usage Limits Enforcement

#### Test Usage Tracking
```bash
# Make API calls and verify usage is tracked
GET /api/v1/usage/current-month
```

#### Test Limit Enforcement
1. Make API calls up to your tier limit
2. Verify:
   - At 80%: Warning header appears
   - At 90%: Warning header appears
   - At 95%: Critical warning
   - At 100%: Request blocked with 429 status

#### Test Usage Dashboard
1. Navigate to `/billing/usage`
2. Verify:
   - Current month usage displays
   - Usage status cards show percentages
   - Warnings appear at thresholds
   - Projections calculate correctly
   - Trends show historical data

#### Test Usage API
```bash
# Get current usage
GET /api/v1/usage/current-month

# Get usage status
GET /api/v1/usage/status

# Get projections
GET /api/v1/usage/projections?days_ahead=30

# Get trends
GET /api/v1/usage/trends?months=6
```

**Expected Results:**
- ✅ Usage is tracked in real-time
- ✅ Limits are enforced (hard limits block)
- ✅ Soft limits show warnings
- ✅ Dashboard displays all metrics
- ✅ Projections calculate correctly

---

### ✅ 3. Email Notification System

#### Test Email Templates
```python
# Test via Python script or API
from core.services.email_templates import EmailTemplates

# Test verification email
template = EmailTemplates.verification_email(
    verification_url="https://example.com/verify?token=abc123",
    user_name="Test User"
)

# Test trial ending email
template = EmailTemplates.trial_ending_email(
    user_name="Test User",
    days_remaining=7,
    upgrade_url="https://example.com/upgrade"
)

# Test usage alert
template = EmailTemplates.usage_alert_email(
    user_name="Test User",
    resource_type="api_call",
    current_usage=950,
    limit=1000,
    percentage=95.0,
    dashboard_url="https://example.com/usage"
)
```

#### Test Email Queue
```python
# Test email queueing
from core.services.email_queue import EmailQueueService
from database.session import get_db

db = next(get_db())
queue_service = EmailQueueService(db)

# Queue an email
email_item = queue_service.enqueue_email(
    to_email="test@example.com",
    subject="Test Email",
    html_content="<h1>Test</h1>",
    text_content="Test"
)

# Process queue
await queue_service.process_queue()
```

#### Test Email Service
```python
# Test sending email
from core.services.email_service import get_email_service

email_service = get_email_service()
success = await email_service.send_email(
    to_email="test@example.com",
    subject="Test",
    html_content="<h1>Test</h1>"
)
```

**Expected Results:**
- ✅ All email templates render correctly
- ✅ Emails queue successfully
- ✅ Queue processes and sends emails
- ✅ Retry logic works on failures
- ✅ Failed emails are tracked

---

### ✅ 4. Customer Support Integration

#### Test Support Ticket Creation
1. Navigate to `/support`
2. Click "New Ticket"
3. Fill in:
   - Subject: "Test Issue"
   - Description: "Testing support system"
   - Priority: Medium
4. Click "Create Ticket"
5. Verify ticket appears in list

#### Test Support Chat Widget
1. Look for floating "Support" button (bottom-right)
2. Click to open chat widget
3. Select or create a ticket
4. Send messages
5. Verify:
   - Messages appear in chat
   - Messages are threaded correctly
   - Status updates work

#### Test Support API
```bash
# Create ticket
POST /api/v1/support/tickets
{
  "subject": "Test Ticket",
  "description": "Testing support API",
  "priority": "medium"
}

# Get tickets
GET /api/v1/support/tickets

# Get specific ticket
GET /api/v1/support/tickets/{ticket_id}

# Add message
POST /api/v1/support/tickets/{ticket_id}/messages
{
  "message": "This is a test message"
}

# Get messages
GET /api/v1/support/tickets/{ticket_id}/messages
```

#### Test Error-to-Ticket Conversion
```bash
# Create ticket from error
POST /api/v1/support/tickets/create-from-error
{
  "error_message": "Test error",
  "error_context": {
    "path": "/api/test",
    "method": "GET"
  }
}
```

**Expected Results:**
- ✅ Tickets create successfully
- ✅ Messages thread correctly
- ✅ Chat widget works
- ✅ API endpoints respond correctly
- ✅ Error-to-ticket conversion works

---

## Automated Test Script

Run the automated test script:

```bash
# Windows
python backend/scripts/test_phase1.py

# Or manually test each component
```

## Common Issues & Solutions

### Issue: License activation fails
**Solution**: Check that hardware fingerprinting is working. Verify `LICENSE_SECRET_KEY` is set in environment.

### Issue: Usage limits not enforcing
**Solution**: 
1. Verify middleware is added to `api/main.py`
2. Check tenant tier configuration
3. Verify usage tracker is recording usage

### Issue: Emails not sending
**Solution**:
1. Check email provider configuration (SendGrid/SES/SMTP)
2. Verify credentials are set in environment
3. Check email queue for failed emails

### Issue: Support tickets not creating
**Solution**:
1. Verify database tables are created (`support_tickets`, `support_messages`)
2. Check authentication is working
3. Verify API routes are registered

## Database Verification

Verify all new tables exist:

```sql
-- Check license tables
SELECT * FROM licenses LIMIT 1;
SELECT * FROM license_activations LIMIT 1;

-- Check email queue
SELECT * FROM email_queue LIMIT 1;

-- Check support tables
SELECT * FROM support_tickets LIMIT 1;
SELECT * FROM support_messages LIMIT 1;
```

## Next Steps

After Phase 1 testing is complete:
1. Document any issues found
2. Fix critical bugs
3. Proceed to Phase 2 implementation


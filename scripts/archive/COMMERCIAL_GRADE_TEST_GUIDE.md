# Commercial-Grade System - Complete Test Guide

This guide provides comprehensive testing instructions for all commercial-grade features across Phase 1, Phase 2, and Phase 3.

## Quick Start

### Automated Testing
```bash
# Run comprehensive test suite
TEST_COMMERCIAL_GRADE.bat

# Or manually
python backend/scripts/test_commercial_grade.py
```

## Complete Feature Test Matrix

### ✅ Phase 1: Critical Features

#### 1. License Key Activation System

**Backend Tests:**
```python
# Test license generation
license_manager = LicenseManager()
key = license_manager.generate_license_key(
    license_type=LicenseType.STANDARD,
    seats=1,
    expiration_days=365
)

# Test activation
license_obj, activation = license_manager.activate_license(
    db=db,
    license_key=key,
    hardware_fingerprint=hw.fingerprint
)

# Test validation
validation = license_manager.validate_license(db, key)
```

**API Tests:**
```bash
# Get hardware fingerprint
GET /api/v1/license/hardware-fingerprint

# Validate license
POST /api/v1/license/validate
{
  "license_key": "XXXX-XXXX-XXXX-XXXX-XXXX"
}

# Activate license (requires auth)
POST /api/v1/license/activate
{
  "license_key": "XXXX-XXXX-XXXX-XXXX-XXXX",
  "device_name": "My Computer"
}

# Get my licenses
GET /api/v1/license/my-licenses
```

**Frontend Tests:**
1. Navigate to `/settings/license`
2. Test license activation
3. Verify hardware fingerprint display
4. Test license validation
5. Test multi-device support

**Expected Results:**
- ✅ License keys generate in correct format
- ✅ Activation binds to hardware fingerprint
- ✅ Validation shows correct status
- ✅ Multi-device support works
- ✅ Deactivation removes device

---

#### 2. Usage Limits Enforcement

**Backend Tests:**
```python
usage_tracker = get_usage_tracker()

# Test limit checking
limit_status = usage_tracker.check_limit(
    tenant_id="test",
    resource_type="api_call",
    quantity=1.0,
    limit=100,
    limit_type=LimitType.HARD
)

# Test projections
projections = usage_tracker.get_usage_projections("test", days_ahead=30)
```

**API Tests:**
```bash
# Get current usage
GET /api/v1/usage/current-month

# Get usage status
GET /api/v1/usage/status

# Get projections
GET /api/v1/usage/projections?days_ahead=30

# Make API calls to test limit enforcement
# Should see warnings at 80%, 90%, 95%
# Should be blocked at 100%
```

**Frontend Tests:**
1. Navigate to `/billing/usage`
2. Verify usage metrics display
3. Check limit warnings appear
4. Test projections calculation
5. Verify trends display

**Expected Results:**
- ✅ Usage tracked in real-time
- ✅ Hard limits block at 100%
- ✅ Soft limits show warnings (80%, 90%, 95%)
- ✅ Dashboard displays all metrics
- ✅ Projections calculate correctly

---

#### 3. Email Notification System

**Backend Tests:**
```python
# Test all templates
templates = [
    EmailTemplates.verification_email(...),
    EmailTemplates.trial_ending_email(...),
    EmailTemplates.payment_failed_email(...),
    EmailTemplates.usage_alert_email(...),
    EmailTemplates.system_notification_email(...)
]

# Test email queue
queue_service = EmailQueueService(db)
email_item = queue_service.enqueue_email(...)
await queue_service.process_queue()
```

**Expected Results:**
- ✅ All email templates render correctly
- ✅ Emails queue successfully
- ✅ Queue processes and sends emails
- ✅ Retry logic works on failures

---

#### 4. Customer Support Integration

**API Tests:**
```bash
# Create ticket
POST /api/v1/support/tickets
{
  "subject": "Test Issue",
  "description": "Testing support",
  "priority": "medium"
}

# Get tickets
GET /api/v1/support/tickets

# Add message
POST /api/v1/support/tickets/{ticket_id}/messages
{
  "message": "This is a test message"
}
```

**Frontend Tests:**
1. Navigate to `/support`
2. Create a test ticket
3. Test chat widget (bottom-right button)
4. Send messages
5. Verify message threading

**Expected Results:**
- ✅ Tickets create successfully
- ✅ Messages thread correctly
- ✅ Chat widget works
- ✅ Error-to-ticket conversion works

---

### ✅ Phase 2: Post-Launch Features

#### 5. Onboarding Flow

**API Tests:**
```bash
# Get onboarding status
GET /api/onboarding/status

# Update step
POST /api/onboarding/step
{
  "step_id": "welcome",
  "completed": true
}

# Complete onboarding
POST /api/onboarding/complete
{
  "use_case": "sales"
}
```

**Frontend Tests:**
1. Navigate to `/onboarding`
2. Go through all steps
3. Verify progress tracking
4. Test skip functionality
5. Complete onboarding

**Expected Results:**
- ✅ Progress tracks correctly
- ✅ Steps complete in order
- ✅ Sample workflow creation works
- ✅ Skip functionality works

---

#### 6. SLA Monitoring & Reporting

**API Tests:**
```bash
# Get SLA metrics
GET /api/v1/sla/metrics

# Get uptime
GET /api/v1/sla/uptime?days=30

# Get service health
GET /api/v1/sla/health

# Check for breaches
GET /api/v1/sla/breach-check
```

**Frontend Tests:**
1. Navigate to `/admin/sla`
2. Verify uptime display
3. Check response time metrics
4. View error rate
5. Test breach alerts

**Expected Results:**
- ✅ Uptime tracked correctly
- ✅ Response times monitored
- ✅ Error rates calculated
- ✅ Breach detection works
- ✅ Dashboard displays all metrics

---

#### 7. Advanced Error Recovery

**Backend Tests:**
```python
# Test circuit breaker
circuit_breaker = get_circuit_breaker("test")
result = circuit_breaker.call(failing_function)

# Test retry handler
@retry(max_attempts=3)
def test_function():
    ...
```

**Expected Results:**
- ✅ Circuit breaker opens on failures
- ✅ Retry with exponential backoff works
- ✅ Health check includes SLA metrics

---

#### 8. Compliance & Certifications

**API Tests:**
```bash
# Record consent
POST /api/v1/compliance/consent
{
  "consent_type": "analytics",
  "version": "1.0",
  "consented": true
}

# Request data export
POST /api/v1/compliance/export/request?format=json

# Request data deletion
POST /api/v1/compliance/deletion/request?deletion_type=full
```

**Frontend Tests:**
1. Navigate to `/legal/consent`
2. Test consent toggles
3. Request data export
4. Request data deletion (with caution!)

**Expected Results:**
- ✅ Consent records correctly
- ✅ Data export works
- ✅ Data deletion with verification works

---

### ✅ Phase 3: Enhancement Features

#### 9. White-Label Options

**API Tests:**
```bash
# Get branding (any user)
GET /api/v1/whitelabel/config

# Update white-label (Enterprise only)
POST /api/v1/whitelabel/config
{
  "logo_url": "https://example.com/logo.png",
  "primary_color": "#FF0000",
  "company_name": "Custom Company"
}
```

**Expected Results:**
- ✅ Branding returns for all users
- ✅ White-label config requires Enterprise tier
- ✅ Custom branding applies correctly

---

#### 10. SSO/SAML Integration

**API Tests:**
```bash
# Configure SAML (Enterprise only)
POST /api/v1/sso/saml/configure
{
  "entity_id": "...",
  "sso_url": "...",
  "x509_cert": "..."
}

# Get SAML request
GET /api/v1/sso/saml/request

# Configure OAuth
POST /api/v1/sso/oauth/configure
{
  "provider": "google",
  "client_id": "...",
  "client_secret": "..."
}

# Get OAuth authorization URL
GET /api/v1/sso/oauth/authorize
```

**Expected Results:**
- ✅ SAML configuration works
- ✅ OAuth configuration works
- ✅ SSO requires Enterprise tier

---

#### 11. Advanced Security Features

**Backend Tests:**
```python
# Test IP whitelisting
ip_service = IPWhitelistService(db)
ip_service.add_ip("tenant_id", "192.168.1.1")
allowed = ip_service.is_ip_allowed("tenant_id", "192.168.1.1")

# Test MFA enforcement
mfa_service = MFAEnforcementService(db)
required = mfa_service.is_mfa_required("tenant_id")
```

**Expected Results:**
- ✅ IP whitelisting works
- ✅ MFA enforcement per tier works
- ✅ Security features require Enterprise tier

---

## Integration Testing

### End-to-End Scenarios

#### Scenario 1: New User Onboarding
1. User signs up
2. Goes through onboarding
3. Activates license
4. Creates first workflow
5. Checks usage dashboard
6. Receives usage alerts via email

#### Scenario 2: Enterprise Customer
1. Enterprise tenant created
2. White-label branding configured
3. SAML SSO configured
4. IP whitelist set up
5. MFA enforced
6. Custom domain configured

#### Scenario 3: Usage Limit Enforcement
1. User makes API calls
2. Usage tracked in real-time
3. Warnings at 80%, 90%, 95%
4. Hard limit blocks at 100%
5. User upgrades plan
6. Limits reset

#### Scenario 4: Support Workflow
1. User encounters error
2. Creates support ticket from error dialog
3. Support team responds
4. Issue resolved
5. Ticket closed

---

## Performance Testing

### Load Testing
```bash
# Test with high request volume
# Monitor SLA metrics during load
# Verify circuit breakers activate
# Check retry logic under load
```

### Stress Testing
```bash
# Test system under extreme load
# Verify graceful degradation
# Check error recovery
# Monitor SLA compliance
```

---

## Security Testing

### Authentication Tests
- ✅ JWT token validation
- ✅ License key validation
- ✅ SSO authentication
- ✅ MFA enforcement

### Authorization Tests
- ✅ Tenant isolation
- ✅ Feature gating by tier
- ✅ IP whitelisting
- ✅ Admin-only endpoints

### Data Protection Tests
- ✅ GDPR data export
- ✅ GDPR data deletion
- ✅ Consent management
- ✅ Privacy compliance

---

## Test Checklist

### Phase 1 Features
- [ ] License key generation
- [ ] License activation
- [ ] Hardware fingerprinting
- [ ] Usage tracking
- [ ] Limit enforcement
- [ ] Email templates
- [ ] Email queue
- [ ] Support tickets
- [ ] Support chat

### Phase 2 Features
- [ ] Onboarding progress
- [ ] Sample workflows
- [ ] SLA tracking
- [ ] Uptime monitoring
- [ ] Circuit breakers
- [ ] Retry handlers
- [ ] GDPR compliance
- [ ] Consent management

### Phase 3 Features
- [ ] White-label branding
- [ ] SAML SSO
- [ ] OAuth SSO
- [ ] IP whitelisting
- [ ] MFA enforcement

---

## Success Criteria

✅ **All Phase 1 tests pass** - Critical features working
✅ **All Phase 2 tests pass** - Post-launch features working
✅ **All Phase 3 tests pass** - Enhancement features working
✅ **No critical errors** - System stable
✅ **Performance acceptable** - Response times within SLA
✅ **Security validated** - All security features working

---

## Next Steps After Testing

1. **Fix Critical Issues**: Address any failed tests
2. **Performance Tuning**: Optimize based on test results
3. **Security Review**: Validate all security features
4. **Documentation**: Update user guides
5. **Deployment**: Deploy to production

---

## Support

If you encounter issues during testing:
1. Check logs in `backend/logs/`
2. Review error messages
3. Verify database tables exist
4. Check environment variables
5. Review API documentation at `/docs`


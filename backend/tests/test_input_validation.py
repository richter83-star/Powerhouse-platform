"""
Tests for input validation and sanitization.
"""
import pytest
from pydantic import ValidationError

from core.security.input_validation import (
    InputSanitizer,
    validate_email,
    validate_url,
    SecureString
)


@pytest.mark.unit
@pytest.mark.security
class TestInputSanitizer:
    """Test input sanitization."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = InputSanitizer.sanitize_string("test string")
        assert result == "test string"
    
    def test_sanitize_string_removes_null_bytes(self):
        """Test null byte removal."""
        result = InputSanitizer.sanitize_string("test\x00string")
        assert "\x00" not in result
    
    def test_sanitize_string_html_escape(self):
        """Test HTML escaping when not allowing HTML."""
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>", allow_html=False)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result or "script" not in result.lower()
    
    def test_sanitize_string_removes_xss_patterns(self):
        """Test XSS pattern removal."""
        xss_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>"
        ]
        
        for xss_input in xss_inputs:
            result = InputSanitizer.sanitize_string(xss_input)
            # Should not contain dangerous patterns
            assert "javascript:" not in result.lower()
            assert "<script" not in result.lower()
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        data = {
            "name": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "nested": {
                "value": "javascript:alert('xss')"
            }
        }
        
        sanitized = InputSanitizer.sanitize_dict(data)
        
        assert "<script>" not in sanitized["name"]
        assert sanitized["email"] == "test@example.com"
        assert "javascript:" not in sanitized["nested"]["value"]
    
    def test_validate_no_sql_injection(self):
        """Test SQL injection detection."""
        safe_inputs = [
            "normal string",
            "user@example.com",
            "SELECT * FROM users"  # This should be detected
        ]
        
        assert InputSanitizer.validate_no_sql_injection(safe_inputs[0]) is True
        assert InputSanitizer.validate_no_sql_injection(safe_inputs[1]) is True
        assert InputSanitizer.validate_no_sql_injection(safe_inputs[2]) is False
    
    def test_validate_no_sql_injection_patterns(self):
        """Test various SQL injection patterns."""
        sql_injection_patterns = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--"
        ]
        
        for pattern in sql_injection_patterns:
            result = InputSanitizer.validate_no_sql_injection(pattern)
            assert result is False, f"Should detect SQL injection in: {pattern}"
    
    def test_validate_no_xss(self):
        """Test XSS detection."""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src=javascript:alert('xss')>"
        ]
        
        for pattern in xss_patterns:
            result = InputSanitizer.validate_no_xss(pattern)
            assert result is False, f"Should detect XSS in: {pattern}"
    
    def test_validate_no_command_injection(self):
        """Test command injection detection."""
        command_injection_patterns = [
            "; ls -la",
            "| cat /etc/passwd",
            "& whoami",
            "`id`"
        ]
        
        for pattern in command_injection_patterns:
            result = InputSanitizer.validate_no_command_injection(pattern)
            assert result is False, f"Should detect command injection in: {pattern}"


@pytest.mark.unit
@pytest.mark.security
class TestValidationFunctions:
    """Test validation utility functions."""
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@example",
            "user space@example.com"
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False
    
    def test_validate_url_valid(self):
        """Test valid URL validation."""
        valid_urls = [
            "https://example.com",
            "http://example.com/path",
            "https://example.com:8080/path?query=value"
        ]
        
        for url in valid_urls:
            assert validate_url(url) is True
    
    def test_validate_url_invalid(self):
        """Test invalid URL validation."""
        invalid_urls = [
            "not a url",
            "ftp://example.com",  # Not in allowed schemes
            "javascript:alert('xss')",
            "example.com"  # Missing scheme
        ]
        
        for url in invalid_urls:
            assert validate_url(url) is False
    
    def test_validate_url_allowed_schemes(self):
        """Test URL validation with custom allowed schemes."""
        assert validate_url("https://example.com", ["https"]) is True
        assert validate_url("http://example.com", ["https"]) is False


@pytest.mark.unit
@pytest.mark.security
class TestSecureString:
    """Test SecureString Pydantic model."""
    
    def test_secure_string_valid(self):
        """Test SecureString with valid input."""
        secure = SecureString(value="normal string")
        assert secure.value == "normal string"
    
    def test_secure_string_sql_injection(self):
        """Test SecureString rejects SQL injection."""
        with pytest.raises(ValidationError):
            SecureString(value="'; DROP TABLE users; --")
    
    def test_secure_string_xss(self):
        """Test SecureString rejects XSS."""
        with pytest.raises(ValidationError):
            SecureString(value="<script>alert('xss')</script>")
    
    def test_secure_string_command_injection(self):
        """Test SecureString rejects command injection."""
        with pytest.raises(ValidationError):
            SecureString(value="; ls -la")
    
    def test_secure_string_sanitizes(self):
        """Test SecureString sanitizes input."""
        secure = SecureString(value="test<script>alert('xss')</script>")
        # Should sanitize and not raise error
        assert "<script>" not in secure.value.lower()


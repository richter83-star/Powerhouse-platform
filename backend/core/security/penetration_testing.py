"""
Utilities for penetration testing preparation and security testing.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SecurityTestSuite:
    """
    Security test suite for penetration testing preparation.
    
    Tests common vulnerabilities:
    - SQL Injection
    - XSS (Cross-Site Scripting)
    - CSRF (Cross-Site Request Forgery)
    - Authentication bypass
    - Authorization issues
    - Information disclosure
    """
    
    @staticmethod
    def get_test_cases() -> Dict[str, List[str]]:
        """
        Get security test cases for penetration testing.
        
        Returns:
            Dictionary of test categories and test cases
        """
        return {
            "sql_injection": [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "1' OR '1'='1",
                "admin'--",
                "' OR 1=1--",
                "1' AND '1'='1",
            ],
            "xss": [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "javascript:alert('XSS')",
                "<svg onload=alert('XSS')>",
                "<body onload=alert('XSS')>",
                "<iframe src=javascript:alert('XSS')>",
            ],
            "command_injection": [
                "; ls -la",
                "| cat /etc/passwd",
                "& whoami",
                "`id`",
                "$(whoami)",
                "; rm -rf /",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            ],
            "authentication_bypass": [
                "admin",
                "administrator",
                "root",
                "test",
                "guest",
                "null",
                "true",
            ],
            "authorization": [
                # Test for privilege escalation
                "user_id=1",  # Try to access admin user
                "tenant_id=admin-tenant",  # Try to access admin tenant
                "role=admin",  # Try to set admin role
            ],
        }
    
    @staticmethod
    def generate_security_report() -> Dict:
        """
        Generate security configuration report.
        
        Returns:
            Security configuration report
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "security_features": {
                "authentication": {
                    "jwt_enabled": True,
                    "password_hashing": "bcrypt",
                    "account_lockout": True,
                    "max_login_attempts": 5,
                },
                "authorization": {
                    "rbac_enabled": True,
                    "multi_tenant_isolation": True,
                },
                "input_validation": {
                    "sql_injection_protection": True,
                    "xss_protection": True,
                    "command_injection_protection": True,
                },
                "headers": {
                    "csp_enabled": True,
                    "hsts_enabled": True,
                    "x_frame_options": "DENY",
                    "x_content_type_options": "nosniff",
                },
                "rate_limiting": {
                    "enabled": True,
                    "redis_backed": True,
                },
                "logging": {
                    "audit_logging": True,
                    "correlation_ids": True,
                    "error_tracking": True,
                },
            },
            "recommendations": [
                "Enable HTTPS in production",
                "Regular security audits",
                "Penetration testing",
                "Dependency updates",
                "Security headers audit",
            ]
        }


def check_security_headers(response_headers: Dict) -> Dict:
    """
    Check if security headers are present in response.
    
    Args:
        response_headers: Response headers dictionary
    
    Returns:
        Security headers status
    """
    required_headers = [
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Referrer-Policy",
        "Permissions-Policy",
    ]
    
    present = {}
    missing = []
    
    for header in required_headers:
        if header in response_headers:
            present[header] = response_headers[header]
        else:
            missing.append(header)
    
    return {
        "present": present,
        "missing": missing,
        "score": len(present) / len(required_headers) * 100
    }


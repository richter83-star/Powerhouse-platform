"""
Email templates for transactional emails.
"""
from typing import Dict, Any


class EmailTemplates:
    """Email templates for various transactional emails."""
    
    @staticmethod
    def verification_email(verification_url: str, user_name: str = "User") -> Dict[str, str]:
        """
        Email verification template.
        
        Args:
            verification_url: URL to verify email
            user_name: User's name
            
        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        subject = "Verify Your Powerhouse Account"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Powerhouse Platform</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Verify Your Email Address</h2>
                <p>Hi {user_name},</p>
                <p>Thank you for signing up for Powerhouse! Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Verify Email Address</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{verification_url}</p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">This link will expire in 24 hours.</p>
                <p style="color: #666; font-size: 14px;">If you didn't create an account, you can safely ignore this email.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 Powerhouse Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Verify Your Email Address
        
        Hi {user_name},
        
        Thank you for signing up for Powerhouse! Please verify your email address by visiting:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, you can safely ignore this email.
        
        © 2025 Powerhouse Platform. All rights reserved.
        """
        
        return {
            "subject": subject,
            "html": html,
            "text": text
        }
    
    @staticmethod
    def password_reset_email(reset_url: str, user_name: str = "User") -> Dict[str, str]:
        """
        Password reset email template.
        
        Args:
            reset_url: URL to reset password
            user_name: User's name
            
        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        subject = "Reset Your Powerhouse Password"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Powerhouse Platform</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Reset Your Password</h2>
                <p>Hi {user_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Reset Password</a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                <p style="color: #666; font-size: 14px; margin-top: 30px;">This link will expire in 1 hour.</p>
                <p style="color: #d32f2f; font-size: 14px; font-weight: bold;">If you didn't request this, please ignore this email. Your password will not be changed.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 Powerhouse Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Reset Your Password
        
        Hi {user_name},
        
        We received a request to reset your password. Visit the link below to create a new password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email. Your password will not be changed.
        
        © 2025 Powerhouse Platform. All rights reserved.
        """
        
        return {
            "subject": subject,
            "html": html,
            "text": text
        }
    
    @staticmethod
    def welcome_email(user_name: str, dashboard_url: str) -> Dict[str, str]:
        """
        Welcome email template.
        
        Args:
            user_name: User's name
            dashboard_url: URL to dashboard
            
        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        subject = "Welcome to Powerhouse!"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Powerhouse</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Welcome to Powerhouse!</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Hi {user_name},</h2>
                <p>Welcome to Powerhouse! We're excited to have you on board.</p>
                <p>Powerhouse is a powerful multi-agent AI platform that helps you automate complex business workflows. Here's what you can do:</p>
                <ul style="color: #666;">
                    <li>Create and orchestrate AI agents</li>
                    <li>Build custom workflows</li>
                    <li>Integrate with your existing tools</li>
                    <li>Scale your operations with intelligent automation</li>
                </ul>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{dashboard_url}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Go to Dashboard</a>
                </div>
                <p>Need help getting started? Check out our <a href="{dashboard_url}/docs" style="color: #667eea;">documentation</a> or reach out to our support team.</p>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 Powerhouse Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Welcome to Powerhouse!
        
        Hi {user_name},
        
        Welcome to Powerhouse! We're excited to have you on board.
        
        Powerhouse is a powerful multi-agent AI platform that helps you automate complex business workflows.
        
        Get started: {dashboard_url}
        
        Need help? Check out our documentation or reach out to our support team.
        
        © 2025 Powerhouse Platform. All rights reserved.
        """
        
        return {
            "subject": subject,
            "html": html,
            "text": text
        }
    
    @staticmethod
    def subscription_confirmation_email(
        user_name: str,
        plan_name: str,
        amount: str,
        billing_url: str
    ) -> Dict[str, str]:
        """
        Subscription confirmation email template.
        
        Args:
            user_name: User's name
            plan_name: Subscription plan name
            amount: Subscription amount
            billing_url: URL to billing page
            
        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        subject = f"Subscription Confirmed - {plan_name}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Subscription Confirmed</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Subscription Confirmed</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333; margin-top: 0;">Hi {user_name},</h2>
                <p>Thank you for subscribing to <strong>{plan_name}</strong>!</p>
                <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Plan:</strong> {plan_name}</p>
                    <p style="margin: 5px 0;"><strong>Amount:</strong> {amount}</p>
                </div>
                <p>Your subscription is now active. You can manage your billing and subscription at any time:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{billing_url}" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">Manage Billing</a>
                </div>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2025 Powerhouse Platform. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"""
        Subscription Confirmed
        
        Hi {user_name},
        
        Thank you for subscribing to {plan_name}!
        
        Plan: {plan_name}
        Amount: {amount}
        
        Your subscription is now active. Manage your billing: {billing_url}
        
        © 2025 Powerhouse Platform. All rights reserved.
        """
        
        return {
            "subject": subject,
            "html": html,
            "text": text
        }


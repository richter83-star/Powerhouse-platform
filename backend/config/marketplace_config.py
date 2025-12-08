
"""
Marketplace Configuration
"""

# Platform commission percentage (15% default)
PLATFORM_COMMISSION_PERCENTAGE = 15.0

# Agent pricing based on complexity (1-10 scale)
AGENT_PRICING_TIERS = {
    1: {"min": 5.00, "max": 15.00, "name": "Basic"},
    2: {"min": 15.00, "max": 30.00, "name": "Simple"},
    3: {"min": 30.00, "max": 50.00, "name": "Moderate"},
    4: {"min": 50.00, "max": 75.00, "name": "Intermediate"},
    5: {"min": 75.00, "max": 100.00, "name": "Standard"},
    6: {"min": 100.00, "max": 150.00, "name": "Advanced"},
    7: {"min": 150.00, "max": 250.00, "name": "Professional"},
    8: {"min": 250.00, "max": 400.00, "name": "Expert"},
    9: {"min": 400.00, "max": 600.00, "name": "Premium"},
    10: {"min": 600.00, "max": 1000.00, "name": "Elite"}
}

# Complexity factors for agent pricing
COMPLEXITY_FACTORS = {
    "num_tools": 5,  # Points per tool
    "memory_enabled": 10,
    "multi_step": 15,
    "custom_logic": 20,
    "api_integrations": 10,
    "learning_capability": 25,
    "reasoning_depth": 15,
    "collaboration": 20
}

# Stripe configuration
STRIPE_CONFIG = {
    "currency": "usd",
    "payment_methods": ["card"],
    "capture_method": "automatic"
}

# Marketplace categories
CATEGORIES = {
    "agents": ["chatbot", "automation", "analytics", "research", "creative"],
    "apps": ["productivity", "analytics", "crm", "marketing", "custom"],
    "workflows": ["sales", "support", "operations", "hr", "finance"]
}


"""
Test Material Generator
Generates additional sample files and test data for the Data Manager
"""

import json
import csv
import os
from datetime import datetime, timedelta
import random

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def generate_financial_analysis():
    """Generate a financial analysis sample"""
    data = {
        "task": "Financial Performance Analysis",
        "company": "TechCorp Solutions",
        "period": "Q3 2024",
        "metrics": {
            "revenue": 2500000,
            "expenses": 1800000,
            "profit_margin": 28,
            "growth_rate": 15.5
        },
        "requirements": [
            "Identify trends and patterns",
            "Compare with previous quarters",
            "Provide strategic recommendations",
            "Forecast next quarter performance"
        ],
        "context": {
            "industry": "Software/SaaS",
            "employees": 150,
            "market": "North America"
        }
    }
    
    filename = os.path.join(SAMPLES_DIR, "financial_analysis_sample.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created: {filename}")


def generate_customer_feedback():
    """Generate customer feedback analysis sample"""
    data = {
        "task": "Customer Feedback Analysis",
        "source": "Product Reviews - Mobile App",
        "period": "Last 30 days",
        "feedback_count": 247,
        "feedback_samples": [
            {
                "id": 1,
                "rating": 5,
                "comment": "Excellent user interface, very intuitive!",
                "category": "UI/UX"
            },
            {
                "id": 2,
                "rating": 3,
                "comment": "Good features but occasional crashes",
                "category": "Stability"
            },
            {
                "id": 3,
                "rating": 4,
                "comment": "Great customer support, resolved my issue quickly",
                "category": "Support"
            }
        ],
        "analysis_goals": [
            "Identify common pain points",
            "Extract sentiment scores",
            "Categorize feedback themes",
            "Prioritize improvement areas"
        ]
    }
    
    filename = os.path.join(SAMPLES_DIR, "customer_feedback_sample.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created: {filename}")


def generate_competitive_analysis():
    """Generate competitive analysis sample"""
    data = {
        "task": "Competitive Landscape Analysis",
        "industry": "Cloud Storage",
        "competitors": [
            {
                "name": "Competitor A",
                "market_share": 35,
                "pricing_model": "Freemium",
                "key_features": ["10GB free", "File sync", "Mobile apps"],
                "strengths": ["Brand recognition", "Large user base"],
                "weaknesses": ["Limited free tier", "Slow sync"]
            },
            {
                "name": "Competitor B",
                "market_share": 25,
                "pricing_model": "Subscription",
                "key_features": ["E2E encryption", "Team collaboration"],
                "strengths": ["Security focus", "Enterprise features"],
                "weaknesses": ["Higher price", "Complex UI"]
            }
        ],
        "our_position": {
            "market_share": 15,
            "target_segment": "SMB and Enterprise"
        },
        "analysis_objectives": [
            "Identify market gaps",
            "Analyze pricing strategies",
            "Determine differentiation opportunities",
            "Create competitive positioning map"
        ]
    }
    
    filename = os.path.join(SAMPLES_DIR, "competitive_analysis_sample.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created: {filename}")


def generate_employee_batch():
    """Generate employee onboarding batch CSV"""
    filename = os.path.join(SAMPLES_DIR, "employee_onboarding_batch.csv")
    
    employees = [
        ["emp_id", "name", "department", "role", "start_date", "onboarding_tasks"],
        ["EMP001", "Alice Johnson", "Engineering", "Senior Developer", "2024-10-15", "setup_access,training,mentor_assignment"],
        ["EMP002", "Bob Smith", "Marketing", "Content Manager", "2024-10-16", "setup_access,training,team_introduction"],
        ["EMP003", "Carol White", "Sales", "Account Executive", "2024-10-18", "setup_access,crm_training,territory_assignment"],
        ["EMP004", "David Brown", "Operations", "Operations Manager", "2024-10-20", "setup_access,process_training,team_handoff"],
        ["EMP005", "Eve Davis", "Engineering", "QA Engineer", "2024-10-22", "setup_access,testing_tools,documentation"]
    ]
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(employees)
    print(f"Created: {filename}")


def generate_project_tasks():
    """Generate project tasks batch CSV"""
    filename = os.path.join(SAMPLES_DIR, "project_tasks_batch.csv")
    
    tasks = [
        ["task_id", "project", "task_name", "priority", "status", "assigned_to", "due_date"],
        ["T001", "Website Redesign", "Update homepage layout", "high", "in_progress", "Design Team", "2024-10-25"],
        ["T002", "Website Redesign", "Optimize mobile responsiveness", "high", "pending", "Frontend Team", "2024-10-30"],
        ["T003", "API v2.0", "Design new endpoints", "critical", "in_progress", "Backend Team", "2024-10-20"],
        ["T004", "API v2.0", "Write API documentation", "medium", "pending", "Tech Writers", "2024-11-05"],
        ["T005", "Customer Portal", "Implement user dashboard", "high", "in_progress", "Full Stack Team", "2024-10-28"],
        ["T006", "Customer Portal", "Add payment integration", "critical", "pending", "Backend Team", "2024-11-10"]
    ]
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(tasks)
    print(f"Created: {filename}")


def generate_research_query():
    """Generate research query sample"""
    data = {
        "task": "Market Research: AI in Healthcare",
        "research_type": "comprehensive",
        "scope": {
            "geographic": ["North America", "Europe"],
            "timeframe": "2020-2024",
            "market_segments": [
                "Diagnostic AI",
                "Treatment Planning",
                "Patient Monitoring",
                "Drug Discovery"
            ]
        },
        "research_questions": [
            "What is the current market size and projected growth?",
            "Who are the key players and their market positions?",
            "What are the regulatory challenges?",
            "What emerging technologies are being adopted?",
            "What are the investment trends?"
        ],
        "deliverables": [
            "Executive summary",
            "Detailed market analysis",
            "Competitive landscape",
            "SWOT analysis",
            "Recommendations"
        ],
        "data_sources": [
            "Industry reports",
            "Academic research",
            "Company filings",
            "News articles",
            "Expert interviews"
        ]
    }
    
    filename = os.path.join(SAMPLES_DIR, "research_query_sample.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created: {filename}")


def generate_content_strategy():
    """Generate content strategy sample"""
    data = {
        "task": "Q4 Content Strategy Planning",
        "brand": "TechStartup Inc.",
        "objectives": [
            "Increase organic traffic by 30%",
            "Generate 500 qualified leads",
            "Improve brand awareness",
            "Establish thought leadership"
        ],
        "target_audience": {
            "primary": {
                "role": "IT Decision Makers",
                "company_size": "50-500 employees",
                "industry": "Technology, Healthcare, Finance"
            },
            "secondary": {
                "role": "Technical Practitioners",
                "interests": ["DevOps", "Cloud", "Security"]
            }
        },
        "content_types": [
            "Blog posts (2-3 per week)",
            "Whitepapers (1 per month)",
            "Case studies (2 per quarter)",
            "Webinars (1 per month)",
            "Social media posts (daily)"
        ],
        "topics": [
            "AI and Machine Learning",
            "Cloud Infrastructure",
            "Cybersecurity Best Practices",
            "Digital Transformation",
            "Automation and Efficiency"
        ],
        "requirements": [
            "Create content calendar",
            "Identify keyword opportunities",
            "Define KPIs and tracking",
            "Allocate resources and budget"
        ]
    }
    
    filename = os.path.join(SAMPLES_DIR, "content_strategy_sample.json")
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Created: {filename}")


if __name__ == "__main__":
    print("Generating test materials...")
    print("-" * 50)
    
    generate_financial_analysis()
    generate_customer_feedback()
    generate_competitive_analysis()
    generate_employee_batch()
    generate_project_tasks()
    generate_research_query()
    generate_content_strategy()
    
    print("-" * 50)
    print("All test materials generated successfully!")
    print(f"Location: {SAMPLES_DIR}")

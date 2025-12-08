
"""
Learning Data Plugins

Safe, self-contained data generation plugins for agent training.
No internet connection required - all data generated internally.

Plugins:
1. CustomerSupportDataPlugin - Generate customer support scenarios
2. SalesResearchDataPlugin - Generate sales/research tasks
3. BenchmarkDatasetPlugin - Standard ML benchmarks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod
import random
import json

from utils.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# BASE PLUGIN INTERFACE
# ============================================================================

class LearningDataPlugin(ABC):
    """Base class for learning data plugins."""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return plugin name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return plugin description."""
        pass
    
    @abstractmethod
    def generate_task(self) -> Dict[str, Any]:
        """Generate a single training task."""
        pass
    
    @abstractmethod
    def generate_batch(self, size: int) -> List[Dict[str, Any]]:
        """Generate a batch of training tasks."""
        pass
    
    @abstractmethod
    def validate_result(self, task: Dict[str, Any], result: Any) -> bool:
        """Validate if agent's result is correct."""
        pass


# ============================================================================
# CUSTOMER SUPPORT DATA PLUGIN
# ============================================================================

class CustomerSupportDataPlugin(LearningDataPlugin):
    """
    Generate customer support scenarios for agent training.
    
    Scenarios include:
    - Product questions
    - Troubleshooting
    - Refund requests
    - Feature inquiries
    - Complaint handling
    """
    
    def __init__(self):
        self.products = [
            "CloudSync Pro", "DataVault Enterprise", "AgentHub Platform",
            "Analytics Suite", "Security Shield", "DevOps Toolkit"
        ]
        
        self.scenarios = {
            "product_question": [
                "How do I {action} in {product}?",
                "What are the features of {product}?",
                "Can {product} do {capability}?",
                "Is {product} compatible with {system}?"
            ],
            "troubleshooting": [
                "{product} is not {working_verb}",
                "Getting error '{error}' in {product}",
                "{product} performance is slow",
                "Cannot connect to {product}"
            ],
            "refund": [
                "I want a refund for {product}",
                "How do I cancel my {product} subscription?",
                "{product} doesn't meet my needs",
                "Billing issue with {product}"
            ],
            "feature_inquiry": [
                "Does {product} support {feature}?",
                "When will {feature} be available in {product}?",
                "How to enable {feature} in {product}?",
                "Is there a {feature} integration?"
            ]
        }
        
        self.actions = ["configure", "set up", "customize", "integrate", "deploy"]
        self.capabilities = ["automation", "reporting", "analytics", "collaboration"]
        self.systems = ["AWS", "Azure", "GCP", "Kubernetes", "Docker"]
        self.working_verbs = ["working", "loading", "starting", "syncing", "updating"]
        self.errors = ["404 Not Found", "500 Internal Error", "Connection Timeout", "Auth Failed"]
        self.features = ["SSO", "API access", "webhooks", "custom domains", "RBAC"]
    
    def get_name(self) -> str:
        return "customer_support"
    
    def get_description(self) -> str:
        return "Customer support scenario generator for agent training"
    
    def generate_task(self) -> Dict[str, Any]:
        """Generate a single customer support task."""
        scenario_type = random.choice(list(self.scenarios.keys()))
        template = random.choice(self.scenarios[scenario_type])
        
        # Fill in template
        message = template.format(
            action=random.choice(self.actions),
            product=random.choice(self.products),
            capability=random.choice(self.capabilities),
            system=random.choice(self.systems),
            working_verb=random.choice(self.working_verbs),
            error=random.choice(self.errors),
            feature=random.choice(self.features)
        )
        
        # Expected response patterns
        expected_patterns = self._get_expected_patterns(scenario_type)
        
        return {
            "id": f"cs_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}",
            "type": "customer_support",
            "scenario": scenario_type,
            "description": message,
            "customer_message": message,
            "expected_patterns": expected_patterns,
            "priority": self._get_priority(scenario_type),
            "metadata": {
                "category": scenario_type,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    def generate_batch(self, size: int) -> List[Dict[str, Any]]:
        """Generate batch of customer support tasks."""
        return [self.generate_task() for _ in range(size)]
    
    def validate_result(self, task: Dict[str, Any], result: Any) -> bool:
        """Validate agent's response to customer support task."""
        if not result or not isinstance(result, (str, dict)):
            return False
        
        result_text = str(result).lower()
        expected_patterns = task.get("expected_patterns", [])
        
        # Check if response contains expected elements
        matches = sum(1 for pattern in expected_patterns if pattern in result_text)
        
        # Need at least 50% of expected patterns
        return matches >= len(expected_patterns) * 0.5
    
    def _get_expected_patterns(self, scenario_type: str) -> List[str]:
        """Get expected patterns in response."""
        patterns = {
            "product_question": ["documentation", "guide", "help", "tutorial"],
            "troubleshooting": ["check", "verify", "restart", "update", "contact"],
            "refund": ["refund", "cancel", "billing", "policy", "process"],
            "feature_inquiry": ["available", "support", "enable", "documentation"]
        }
        return patterns.get(scenario_type, ["help", "assist"])
    
    def _get_priority(self, scenario_type: str) -> str:
        """Get task priority based on scenario."""
        high_priority = ["troubleshooting", "refund"]
        return "high" if scenario_type in high_priority else "medium"


# ============================================================================
# SALES RESEARCH DATA PLUGIN
# ============================================================================

class SalesResearchDataPlugin(LearningDataPlugin):
    """
    Generate sales and research tasks for agent training.
    
    Tasks include:
    - Market research
    - Competitor analysis
    - Lead qualification
    - Product comparisons
    - Pricing analysis
    """
    
    def __init__(self):
        self.companies = [
            "TechCorp", "DataFlow Inc", "CloudScale", "AgentAI", 
            "SystemSync", "DevForce", "SecureNet", "AnalyticsHub"
        ]
        
        self.industries = [
            "SaaS", "E-commerce", "FinTech", "HealthTech", 
            "EdTech", "Marketing", "HR Tech", "DevOps"
        ]
        
        self.research_tasks = [
            "Analyze market trends in {industry}",
            "Compare our solution with {competitor}",
            "Research {company}'s tech stack",
            "Identify potential leads in {industry}",
            "Evaluate pricing strategy for {industry}",
            "Assess {company}'s market position",
            "Research integration opportunities with {company}",
            "Analyze customer sentiment about {competitor}"
        ]
    
    def get_name(self) -> str:
        return "sales_research"
    
    def get_description(self) -> str:
        return "Sales and research task generator for agent training"
    
    def generate_task(self) -> Dict[str, Any]:
        """Generate a single sales/research task."""
        template = random.choice(self.research_tasks)
        
        task_description = template.format(
            industry=random.choice(self.industries),
            competitor=random.choice(self.companies),
            company=random.choice(self.companies)
        )
        
        return {
            "id": f"sr_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}",
            "type": "sales_research",
            "description": task_description,
            "expected_output": self._get_expected_output(task_description),
            "priority": "medium",
            "metadata": {
                "category": "research",
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    def generate_batch(self, size: int) -> List[Dict[str, Any]]:
        """Generate batch of sales/research tasks."""
        return [self.generate_task() for _ in range(size)]
    
    def validate_result(self, task: Dict[str, Any], result: Any) -> bool:
        """Validate agent's research result."""
        if not result:
            return False
        
        result_text = str(result).lower()
        expected_output = task.get("expected_output", {})
        
        # Check for key research elements
        required_elements = expected_output.get("required_elements", [])
        found_elements = sum(1 for elem in required_elements if elem in result_text)
        
        # Need at least 60% of required elements
        return found_elements >= len(required_elements) * 0.6
    
    def _get_expected_output(self, description: str) -> Dict[str, Any]:
        """Define expected output structure."""
        desc_lower = description.lower()
        
        if "analyze" in desc_lower or "research" in desc_lower:
            required = ["analysis", "data", "insights", "findings"]
        elif "compare" in desc_lower:
            required = ["comparison", "features", "pricing", "differences"]
        elif "identify" in desc_lower:
            required = ["list", "leads", "opportunities", "potential"]
        else:
            required = ["information", "details", "summary"]
        
        return {
            "required_elements": required,
            "format": "structured_report"
        }


# ============================================================================
# BENCHMARK DATASET PLUGIN
# ============================================================================

class BenchmarkDatasetPlugin(LearningDataPlugin):
    """
    Standard ML/AI benchmark tasks for agent training.
    
    Includes:
    - Classification tasks
    - Reasoning tasks
    - Logic puzzles
    - Math problems
    - Pattern recognition
    """
    
    def __init__(self):
        self.task_types = {
            "classification": self._generate_classification,
            "reasoning": self._generate_reasoning,
            "logic": self._generate_logic,
            "math": self._generate_math,
            "pattern": self._generate_pattern
        }
    
    def get_name(self) -> str:
        return "benchmark"
    
    def get_description(self) -> str:
        return "Standard benchmark dataset generator for agent training"
    
    def generate_task(self) -> Dict[str, Any]:
        """Generate a single benchmark task."""
        task_type = random.choice(list(self.task_types.keys()))
        generator = self.task_types[task_type]
        
        task_data = generator()
        task_data["id"] = f"bench_{datetime.utcnow().timestamp()}_{random.randint(1000, 9999)}"
        task_data["type"] = "benchmark"
        task_data["benchmark_type"] = task_type
        task_data["metadata"] = {
            "category": task_type,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return task_data
    
    def generate_batch(self, size: int) -> List[Dict[str, Any]]:
        """Generate batch of benchmark tasks."""
        return [self.generate_task() for _ in range(size)]
    
    def validate_result(self, task: Dict[str, Any], result: Any) -> bool:
        """Validate agent's result against expected answer."""
        expected = task.get("expected_answer")
        if expected is None:
            return False
        
        # Handle different result types
        if isinstance(result, dict):
            result = result.get("answer", result.get("result"))
        
        result_str = str(result).strip().lower()
        expected_str = str(expected).strip().lower()
        
        return result_str == expected_str
    
    def _generate_classification(self) -> Dict[str, Any]:
        """Generate classification task."""
        items = [
            ("apple", "fruit"), ("carrot", "vegetable"), ("banana", "fruit"),
            ("broccoli", "vegetable"), ("orange", "fruit"), ("potato", "vegetable")
        ]
        item, category = random.choice(items)
        
        return {
            "description": f"Classify: {item}",
            "question": f"Is {item} a fruit or vegetable?",
            "expected_answer": category,
            "priority": "low"
        }
    
    def _generate_reasoning(self) -> Dict[str, Any]:
        """Generate reasoning task."""
        scenarios = [
            {
                "question": "If all A are B, and all B are C, are all A also C?",
                "answer": "yes"
            },
            {
                "question": "If some cats are black, and some black things are soft, are all cats soft?",
                "answer": "no"
            },
            {
                "question": "If it's raining, the ground is wet. The ground is wet. Is it raining?",
                "answer": "maybe"
            }
        ]
        scenario = random.choice(scenarios)
        
        return {
            "description": "Logical reasoning task",
            "question": scenario["question"],
            "expected_answer": scenario["answer"],
            "priority": "medium"
        }
    
    def _generate_logic(self) -> Dict[str, Any]:
        """Generate logic puzzle."""
        puzzles = [
            {
                "puzzle": "You have 3 boxes: red, blue, green. Red contains 2 items, blue contains 3, green contains 1. How many total items?",
                "answer": "6"
            },
            {
                "puzzle": "If A > B and B > C, what is the relationship between A and C?",
                "answer": "a > c"
            }
        ]
        puzzle = random.choice(puzzles)
        
        return {
            "description": "Logic puzzle",
            "question": puzzle["puzzle"],
            "expected_answer": puzzle["answer"],
            "priority": "medium"
        }
    
    def _generate_math(self) -> Dict[str, Any]:
        """Generate math problem."""
        num1 = random.randint(1, 50)
        num2 = random.randint(1, 50)
        operation = random.choice(["+", "-", "*"])
        
        if operation == "+":
            answer = num1 + num2
        elif operation == "-":
            answer = num1 - num2
        else:
            answer = num1 * num2
        
        return {
            "description": "Math problem",
            "question": f"What is {num1} {operation} {num2}?",
            "expected_answer": str(answer),
            "priority": "low"
        }
    
    def _generate_pattern(self) -> Dict[str, Any]:
        """Generate pattern recognition task."""
        patterns = [
            {
                "sequence": "2, 4, 6, 8, ?",
                "answer": "10"
            },
            {
                "sequence": "1, 1, 2, 3, 5, 8, ?",
                "answer": "13"
            },
            {
                "sequence": "A, C, E, G, ?",
                "answer": "i"
            }
        ]
        pattern = random.choice(patterns)
        
        return {
            "description": "Pattern recognition",
            "question": f"Complete the sequence: {pattern['sequence']}",
            "expected_answer": pattern["answer"],
            "priority": "low"
        }


# ============================================================================
# LEARNING DATA ORCHESTRATOR
# ============================================================================

class LearningDataOrchestrator:
    """
    Orchestrates multiple learning data plugins.
    
    Manages:
    - Plugin registration
    - Task generation across plugins
    - Load balancing
    - Result validation
    """
    
    def __init__(self, plugin_service=None):
        self.plugins: Dict[str, LearningDataPlugin] = {}
        self.plugin_service = plugin_service
        self.stats = {
            "tasks_generated": 0,
            "tasks_validated": 0,
            "plugin_usage": {}
        }
        
        logger.info("LearningDataOrchestrator initialized")
    
    def register_plugin(self, plugin: LearningDataPlugin):
        """Register a learning data plugin."""
        name = plugin.get_name()
        self.plugins[name] = plugin
        self.stats["plugin_usage"][name] = 0
        logger.info(f"Registered plugin: {name} - {plugin.get_description()}")
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """List all registered plugins."""
        return [
            {
                "name": plugin.get_name(),
                "description": plugin.get_description()
            }
            for plugin in self.plugins.values()
        ]
    
    def generate_task(self, plugin_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate a single task from specified or random plugin."""
        if not self.plugins:
            raise ValueError("No plugins registered")
        
        if plugin_name:
            if plugin_name not in self.plugins:
                raise ValueError(f"Plugin not found: {plugin_name}")
            plugin = self.plugins[plugin_name]
        else:
            plugin = random.choice(list(self.plugins.values()))
        
        task = plugin.generate_task()
        self.stats["tasks_generated"] += 1
        self.stats["plugin_usage"][plugin.get_name()] += 1
        
        return task
    
    def generate_training_batch(
        self, 
        batch_size: int = 10, 
        agent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate a batch of training tasks."""
        if agent_type and agent_type in self.plugins:
            # Generate from specific plugin
            plugin = self.plugins[agent_type]
            return plugin.generate_batch(batch_size)
        else:
            # Mix of all plugins
            tasks = []
            plugins_list = list(self.plugins.values())
            
            for i in range(batch_size):
                plugin = plugins_list[i % len(plugins_list)]
                task = plugin.generate_task()
                tasks.append(task)
                self.stats["tasks_generated"] += 1
                self.stats["plugin_usage"][plugin.get_name()] += 1
            
            return tasks
    
    def validate_result(
        self, 
        task: Dict[str, Any], 
        result: Any
    ) -> Dict[str, Any]:
        """Validate agent result against task expectations."""
        task_type = task.get("type")
        
        # Find appropriate plugin
        plugin = None
        for p in self.plugins.values():
            if p.get_name() == task_type or p.get_name() in task.get("id", ""):
                plugin = p
                break
        
        if not plugin:
            return {
                "valid": False,
                "error": "No plugin found for task type"
            }
        
        is_valid = plugin.validate_result(task, result)
        self.stats["tasks_validated"] += 1
        
        return {
            "valid": is_valid,
            "task_id": task.get("id"),
            "plugin": plugin.get_name()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "total_tasks_generated": self.stats["tasks_generated"],
            "total_tasks_validated": self.stats["tasks_validated"],
            "plugin_count": len(self.plugins),
            "plugin_usage": self.stats["plugin_usage"],
            "plugins": self.list_plugins()
        }

"""
Logical Reasoner: Symbolic logic inference engine.

Performs logical reasoning using rules, facts, and constraints.
Supports forward chaining, backward chaining, and constraint satisfaction.
"""

from typing import Dict, List, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import re

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Fact:
    """Represents a logical fact."""
    predicate: str
    arguments: List[str]
    truth_value: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Rule:
    """Represents a logical rule (implication)."""
    head: Fact  # Conclusion
    body: List[Fact]  # Premises (conditions)
    name: Optional[str] = None
    priority: float = 1.0  # Rule priority/confidence


@dataclass
class Constraint:
    """Represents a logical constraint."""
    condition: Callable[[Dict[str, Any]], bool]  # Function that checks constraint
    description: str
    priority: float = 1.0


class LogicalReasoner:
    """
    Symbolic logic inference engine.
    
    Supports:
    - Forward chaining (data-driven inference)
    - Backward chaining (goal-driven inference)
    - Constraint checking
    - Rule-based reasoning
    """
    
    def __init__(self):
        """Initialize logical reasoner."""
        self.facts: Set[Fact] = set()
        self.rules: List[Rule] = []
        self.constraints: List[Constraint] = []
        self.inferred_facts: Set[Fact] = set()
        self.logger = get_logger(__name__)
    
    def add_fact(self, fact: Fact) -> None:
        """Add a fact to the knowledge base."""
        self.facts.add(fact)
    
    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the knowledge base."""
        self.rules.append(rule)
        # Sort rules by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to check."""
        self.constraints.append(constraint)
    
    def forward_chain(self, max_iterations: int = 100) -> Set[Fact]:
        """
        Perform forward chaining inference.
        
        Starts with known facts and applies rules to derive new facts.
        
        Args:
            max_iterations: Maximum inference iterations
            
        Returns:
            Set of all inferred facts
        """
        working_facts = self.facts.copy()
        new_facts = True
        iterations = 0
        
        while new_facts and iterations < max_iterations:
            new_facts = False
            iterations += 1
            
            for rule in self.rules:
                # Check if all premises are satisfied
                premises_satisfied = all(
                    self._fact_matches(working_facts, premise)
                    for premise in rule.body
                )
                
                if premises_satisfied:
                    # Check if head is already known
                    if not self._fact_matches(working_facts, rule.head):
                        working_facts.add(rule.head)
                        self.inferred_facts.add(rule.head)
                        new_facts = True
        
        self.logger.info(f"Forward chaining completed in {iterations} iterations, "
                        f"inferred {len(self.inferred_facts)} new facts")
        return self.inferred_facts
    
    def backward_chain(self, goal: Fact, max_depth: int = 10) -> Tuple[bool, List[Rule]]:
        """
        Perform backward chaining inference (goal-driven).
        
        Tries to prove a goal by finding rules that conclude it.
        
        Args:
            goal: Goal fact to prove
            max_depth: Maximum recursion depth
            
        Returns:
            (is_provable, proof_chain) tuple
        """
        if goal in self.facts:
            return True, []
        
        if max_depth <= 0:
            return False, []
        
        # Find rules that conclude the goal
        applicable_rules = [
            rule for rule in self.rules
            if self._fact_match(rule.head, goal)
        ]
        
        for rule in applicable_rules:
            # Try to prove all premises
            all_proven = True
            proof_chain = [rule]
            
            for premise in rule.body:
                if premise in self.facts:
                    continue  # Premise is already a fact
                
                # Try to prove premise
                provable, sub_proof = self.backward_chain(premise, max_depth - 1)
                if provable:
                    proof_chain.extend(sub_proof)
                else:
                    all_proven = False
                    break
            
            if all_proven:
                return True, proof_chain
        
        return False, []
    
    def check_constraints(self, context: Dict[str, Any]) -> List[Tuple[Constraint, bool]]:
        """
        Check all constraints against a context.
        
        Args:
            context: Context to check constraints against
            
        Returns:
            List of (constraint, is_satisfied) tuples
        """
        results = []
        
        for constraint in self.constraints:
            try:
                satisfied = constraint.condition(context)
                results.append((constraint, satisfied))
            except Exception as e:
                self.logger.warning(f"Constraint check failed: {e}")
                results.append((constraint, False))
        
        return results
    
    def query(self, query: Fact) -> bool:
        """
        Query if a fact is true (known or derivable).
        
        Args:
            query: Fact to query
            
        Returns:
            True if fact is known or can be proven
        """
        # Check if it's a known fact
        if query in self.facts or query in self.inferred_facts:
            return True
        
        # Try backward chaining
        provable, _ = self.backward_chain(query)
        return provable
    
    def apply_rules_to_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply rules to a context (for constraint satisfaction).
        
        Args:
            context: Context to apply rules to
            
        Returns:
            Updated context with inferred properties
        """
        updated_context = context.copy()
        changed = True
        max_iterations = 50
        iterations = 0
        
        while changed and iterations < max_iterations:
            changed = False
            iterations += 1
            
            for rule in self.rules:
                # Convert rule to context check
                premises_match = self._check_premises_in_context(rule.body, updated_context)
                
                if premises_match:
                    # Apply conclusion to context
                    if self._apply_conclusion_to_context(rule.head, updated_context):
                        changed = True
        
        return updated_context
    
    def _fact_matches(self, facts: Set[Fact], pattern: Fact) -> bool:
        """Check if any fact in set matches pattern."""
        return any(self._fact_match(fact, pattern) for fact in facts)
    
    def _fact_match(self, fact: Fact, pattern: Fact) -> bool:
        """
        Check if fact matches pattern.
        
        Supports:
        - Exact match
        - Variable matching (if pattern has variables)
        """
        if fact.predicate != pattern.predicate:
            return False
        
        if len(fact.arguments) != len(pattern.arguments):
            return False
        
        # Match arguments (supports variables in pattern starting with ?)
        for fact_arg, pattern_arg in zip(fact.arguments, pattern.arguments):
            if pattern_arg.startswith("?"):
                continue  # Variable matches anything
            if fact_arg != pattern_arg:
                return False
        
        return True
    
    def _check_premises_in_context(self, premises: List[Fact], context: Dict[str, Any]) -> bool:
        """Check if premises are satisfied in context."""
        for premise in premises:
            # Convert fact to context check
            key = f"{premise.predicate}({','.join(premise.arguments)})"
            if key not in context or context[key] != premise.truth_value:
                return False
        return True
    
    def _apply_conclusion_to_context(self, conclusion: Fact, context: Dict[str, Any]) -> bool:
        """Apply rule conclusion to context. Returns True if context changed."""
        key = f"{conclusion.predicate}({','.join(conclusion.arguments)})"
        
        if key not in context or context[key] != conclusion.truth_value:
            context[key] = conclusion.truth_value
            return True
        return False
    
    def to_prolog(self) -> str:
        """
        Export knowledge base to Prolog format.
        
        Returns:
            Prolog program as string
        """
        lines = []
        
        # Export facts
        for fact in self.facts:
            if fact.truth_value:
                args = ",".join(fact.arguments)
                lines.append(f"{fact.predicate}({args}).")
        
        # Export rules
        for rule in self.rules:
            head_args = ",".join(rule.head.arguments)
            body_conditions = [
                f"{p.predicate}({','.join(p.arguments)})"
                for p in rule.body
            ]
            body = ", ".join(body_conditions)
            lines.append(f"{rule.head.predicate}({head_args}) :- {body}.")
        
        return "\n".join(lines)


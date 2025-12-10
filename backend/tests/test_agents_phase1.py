"""
Tests for Phase 1 Agent Implementations

Tests ReAct, Chain-of-Thought, and Tree-of-Thought agents.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from llm.base import LLMResponse
from agents.react import Agent as ReActAgent
from agents.chain_of_thought import Agent as ChainOfThoughtAgent
from agents.tree_of_thought import Agent as TreeOfThoughtAgent


@pytest.mark.unit
class TestReActAgent:
    """Test ReAct agent implementation."""
    
    def test_initialization(self, mock_llm_provider, mock_tool_registry):
        """Test agent initialization and tool registry setup."""
        with patch('agents.react.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            with patch('agents.react.get_tool_registry', return_value=mock_tool_registry):
                agent = ReActAgent()
                assert agent is not None
                assert agent.llm is not None
                assert agent.tool_registry is not None
    
    def test_reasoning_loop_with_final_answer(self, mock_llm_provider, mock_tool_registry):
        """Test reasoning loop that reaches final answer."""
        # Mock LLM to return final answer
        final_answer_response = LLMResponse(
            content="Thought: I understand the problem. Final Answer: The answer is 4.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        mock_llm_provider.invoke.return_value = final_answer_response
        
        with patch('agents.react.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            with patch('agents.react.get_tool_registry', return_value=mock_tool_registry):
                agent = ReActAgent()
                context = {"task": "What is 2 + 2?"}
                result = agent.run(context)
                
                assert "4" in result or "answer" in result.lower()
                assert mock_llm_provider.invoke.called
    
    def test_reasoning_loop_with_tool_usage(self, mock_llm_provider, mock_tool_registry):
        """Test reasoning loop that uses tools."""
        # First call: wants to use tool
        tool_response = LLMResponse(
            content="Thought: I need to search for information. Action: search('test query')",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        # Second call: final answer
        final_response = LLMResponse(
            content="Thought: Based on the search results. Final Answer: The answer is X.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        mock_llm_provider.invoke.side_effect = [tool_response, final_response]
        
        # Mock tool execution
        mock_tool = Mock()
        mock_tool.execute.return_value = Mock(success=True, output="Search result: X")
        mock_tool_registry.list_tools.return_value = ["search"]
        mock_tool_registry.get_tool.return_value = mock_tool
        mock_tool_registry.list_tools.return_value = ["search"]
        
        with patch('agents.react.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            with patch('agents.react.get_tool_registry', return_value=mock_tool_registry):
                agent = ReActAgent()
                context = {"task": "Search for test information"}
                result = agent.run(context)
                
                assert result is not None
                assert mock_llm_provider.invoke.call_count >= 2
    
    def test_max_iteration_handling(self, mock_llm_provider, mock_tool_registry):
        """Test that agent stops after max iterations."""
        # Always return thought without final answer
        thought_response = LLMResponse(
            content="Thought: I'm still thinking about this problem.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        mock_llm_provider.invoke.return_value = thought_response
        
        with patch('agents.react.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            with patch('agents.react.get_tool_registry', return_value=mock_tool_registry):
                agent = ReActAgent()
                context = {"task": "Complex task", "max_iterations": 3}
                result = agent.run(context)
                
                assert result is not None
                assert mock_llm_provider.invoke.call_count <= 3
    
    def test_no_task_error(self, mock_llm_provider, mock_tool_registry):
        """Test error handling when no task is provided."""
        with patch('agents.react.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            with patch('agents.react.get_tool_registry', return_value=mock_tool_registry):
                agent = ReActAgent()
                context = {}
                result = agent.run(context)
                
                assert "error" in result.lower() or "no task" in result.lower()


@pytest.mark.unit
class TestChainOfThoughtAgent:
    """Test Chain-of-Thought agent implementation."""
    
    def test_initialization(self, mock_llm_provider):
        """Test agent initialization."""
        with patch('agents.chain_of_thought.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            agent = ChainOfThoughtAgent()
            assert agent is not None
            assert agent.llm is not None
    
    def test_step_by_step_reasoning(self, mock_llm_provider):
        """Test step-by-step reasoning generation."""
        # Mock responses for each step
        step1 = LLMResponse(
            content="Step 1: First, I need to understand the problem.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        step2 = LLMResponse(
            content="Step 2: Then, I'll break it down into components.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        final = LLMResponse(
            content="Step 3: Finally, the answer is 42.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        mock_llm_provider.invoke.side_effect = [step1, step2, final]
        
        with patch('agents.chain_of_thought.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            agent = ChainOfThoughtAgent()
            context = {"task": "Solve this step by step"}
            result = agent.run(context)
            
            assert result is not None
            assert mock_llm_provider.invoke.call_count >= 2
    
    def test_chain_completion_detection(self, mock_llm_provider):
        """Test that agent detects when reasoning chain is complete."""
        final_response = LLMResponse(
            content="Step 1: Analyze. Step 2: Compute. Step 3: Conclusion: Done.",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        mock_llm_provider.invoke.return_value = final_response
        
        with patch('agents.chain_of_thought.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            agent = ChainOfThoughtAgent()
            context = {"task": "Complete reasoning chain"}
            result = agent.run(context)
            
            assert result is not None


@pytest.mark.unit
class TestTreeOfThoughtAgent:
    """Test Tree-of-Thought agent implementation."""
    
    def test_initialization(self, mock_llm_provider):
        """Test agent initialization."""
        with patch('agents.tree_of_thought.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            agent = TreeOfThoughtAgent()
            assert agent is not None
            assert agent.llm is not None
    
    def test_tree_exploration(self, mock_llm_provider):
        """Test tree exploration and branching."""
        # Mock responses for different branches
        branch1 = LLMResponse(
            content="Branch 1: Approach A might work. Score: 0.7",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        branch2 = LLMResponse(
            content="Branch 2: Approach B is better. Score: 0.9",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            metadata={},
            timestamp=datetime.now()
        )
        mock_llm_provider.invoke.side_effect = [branch1, branch2]
        
        with patch('agents.tree_of_thought.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            agent = TreeOfThoughtAgent()
            context = {"task": "Explore different approaches"}
            result = agent.run(context)
            
            assert result is not None
            assert mock_llm_provider.invoke.called
    
    def test_path_scoring_and_selection(self, mock_llm_provider):
        """Test path scoring and best path selection."""
        # Create responses with different scores
        responses = [
            LLMResponse(
                content=f"Path {i}: Solution {i}. Score: {0.5 + i * 0.1}",
                model="test",
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                finish_reason="stop",
                metadata={},
                timestamp=datetime.now()
            )
            for i in range(3)
        ]
        mock_llm_provider.invoke.side_effect = responses
        
        with patch('agents.tree_of_thought.LLMConfig.get_llm_provider', return_value=mock_llm_provider):
            agent = TreeOfThoughtAgent()
            context = {"task": "Find best solution"}
            result = agent.run(context)
            
            assert result is not None


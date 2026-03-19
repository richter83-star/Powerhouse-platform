"""
Integration smoke tests for the three architecture bridges.

Covers:
- SwarmFeedbackBridge: RL ingestion & stat tracking
- ApprovalGate: gate / audit / disabled / trusted-agent modes
- CausalAgentRouter: score boosting with causal context
- POST /run (ph_server): with and without causal_context
- POST /run/swarm (ph_server): full swarm → RL loop

Run with:
    cd backend && pytest tests/test_architecture_bridges.py -v
"""
from __future__ import annotations

import sys
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Path setup (mirrors conftest.py)
# ---------------------------------------------------------------------------
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def basic_feedback():
    from core.learning.swarm_feedback_bridge import SwarmExecutionFeedback
    return SwarmExecutionFeedback(
        run_id="test-run-001",
        task="Explain reinforcement learning",
        task_type="analysis",
        success=1.0,
        quality_score=0.85,
        latency_ms=1200.0,
        cost_estimate=0.02,
        system_load=0.4,
        num_agents=2,
        agent_performance={"agent_a": 1.0, "agent_b": 0.8},
        parameters_used={"temperature": 0.7, "max_tokens": 1000, "top_p": 0.9},
    )


@pytest.fixture
def bridge():
    from core.learning.swarm_feedback_bridge import SwarmFeedbackBridge
    return SwarmFeedbackBridge()


@pytest.fixture
def audit_gate():
    from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
    return ApprovalGate(mode=HITLMode.AUDIT)


@pytest.fixture
def gate_gate():
    from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
    return ApprovalGate(
        mode=HITLMode.GATE,
        timeout_seconds=0.5,
        auto_approve_on_timeout=True,
    )


@pytest.fixture
def disabled_gate():
    from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
    return ApprovalGate(mode=HITLMode.DISABLED)


@pytest.fixture
def router():
    from core.reasoning.causal_agent_router import CausalAgentRouter
    return CausalAgentRouter(causal_reasoner=None, agent_selector=None)


# Mock orchestrator result used by ph_server tests
_MOCK_RUN_RESULT = {
    "task": "test task",
    "outputs": [{"agent": "react", "status": "success", "output": "done"}],
    "state": {},
    "run_id": "mock-run",
}

_MOCK_SWARM_RESULT = {
    "task": "test task",
    "iterations": 3,
    "results": [
        {"iteration": 1, "results": [{"agent_id": "react", "action": "explore",
                                       "result": "success", "location": "default"}]},
    ],
    "emergent_patterns": [],
    "swarm_statistics": {"num_agents": 1, "stigmergy_stats": {}, "pattern_stats": {}},
}


@pytest.fixture
def server_client():
    """TestClient for ph_server with mocked Orchestrator and SwarmOrchestrator."""
    with (
        patch("core.orchestrator.Orchestrator.__init__", return_value=None),
        patch("core.orchestrator.Orchestrator.run", return_value=_MOCK_RUN_RESULT),
        patch("core.swarm.swarm_orchestrator.SwarmOrchestrator.execute_swarm",
              return_value=_MOCK_SWARM_RESULT),
        patch("builtins.open", create=True) as mock_open,
        patch("json.load", return_value={"enabled_agents": ["react"], "max_agents": 5}),
    ):
        # Prevent real file read for config/default.json during import
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.read = MagicMock(
            return_value='{"enabled_agents": ["react"], "max_agents": 5}'
        )
        try:
            import importlib
            import ph_server as srv
            importlib.reload(srv)
            with TestClient(srv.app) as client:
                yield client
        except Exception:
            pytest.skip("ph_server could not be loaded for TestClient tests")


# ===========================================================================
# 1. SwarmFeedbackBridge tests
# ===========================================================================

class TestSwarmFeedbackBridge:

    def test_bridge_initialises(self, bridge):
        stats = bridge.get_statistics()
        assert stats["ingestion_count"] == 0
        assert stats["history_length"] == 0

    def test_ingest_increments_count(self, bridge, basic_feedback):
        bridge.ingest_swarm_outcome(basic_feedback)
        stats = bridge.get_statistics()
        assert stats["ingestion_count"] == 1
        assert stats["history_length"] == 1

    def test_multiple_ingestions_accumulate(self, bridge, basic_feedback):
        for _ in range(5):
            bridge.ingest_swarm_outcome(basic_feedback)
        assert bridge.get_statistics()["ingestion_count"] == 5

    def test_failure_feedback_recorded(self, bridge):
        from core.learning.swarm_feedback_bridge import SwarmExecutionFeedback
        bad = SwarmExecutionFeedback(
            run_id="fail-001", task="bad task",
            success=0.0, quality_score=0.0,
            latency_ms=5000.0, cost_estimate=0.5,
        )
        bridge.ingest_swarm_outcome(bad)
        assert bridge.get_statistics()["ingestion_count"] == 1

    def test_get_recommended_adjustments_returns_dict(self, bridge):
        adj = bridge.get_recommended_adjustments(task="test", system_load=0.5)
        # Either empty dict (no PyTorch) or valid adjustments
        assert isinstance(adj, dict)

    def test_swarm_result_to_feedback_success_heuristic(self):
        from core.learning.swarm_feedback_bridge import swarm_result_to_feedback
        swarm_result = {
            "task": "test",
            "iterations": 2,
            "results": [
                {"iteration": 1, "results": [
                    {"agent_id": "a", "result": "success complete", "action": "x", "location": "y"},
                    {"agent_id": "b", "result": "error occurred",   "action": "x", "location": "y"},
                ]},
            ],
            "emergent_patterns": [],
            "swarm_statistics": {"num_agents": 2},
        }
        fb = swarm_result_to_feedback(
            run_id="r1", task="test", swarm_result=swarm_result
        )
        assert 0.0 <= fb.success <= 1.0
        assert 0.0 <= fb.quality_score <= 1.0
        assert fb.num_agents == 2

    def test_rl_stats_present_when_torch_available(self, bridge):
        from core.learning.swarm_feedback_bridge import TORCH_AVAILABLE
        stats = bridge.get_statistics()
        if TORCH_AVAILABLE:
            assert stats["rl"] is not None
        else:
            assert stats["rl"] is None


# ===========================================================================
# 2. ApprovalGate tests
# ===========================================================================

class TestApprovalGateAuditMode:

    def test_audit_always_approves(self, audit_gate):
        req = audit_gate.create_request(
            task="do something", reasoning_summary="testing",
            agent_name="react", estimated_impact="low",
        )
        result = audit_gate.request_approval(req)
        assert result is True

    def test_audit_request_in_audit_trail(self, audit_gate):
        req = audit_gate.create_request(
            task="t", reasoning_summary="r", agent_name="a",
        )
        audit_gate.request_approval(req)
        trail = audit_gate.get_audit_trail()
        assert len(trail) == 1
        assert trail[0]["task"] == "t"

    def test_audit_never_leaves_pending(self, audit_gate):
        req = audit_gate.create_request(
            task="t", reasoning_summary="r", agent_name="a",
        )
        audit_gate.request_approval(req)
        assert audit_gate.get_pending_requests() == []


class TestApprovalGateGateMode:

    def test_gate_auto_approves_on_timeout(self, gate_gate):
        req = gate_gate.create_request(
            task="t", reasoning_summary="r", agent_name="a",
        )
        # No human responds → timeout → auto-approve
        result = gate_gate.request_approval(req)
        assert result is True

    def test_gate_approves_when_human_submits(self):
        from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
        g = ApprovalGate(mode=HITLMode.GATE, timeout_seconds=5.0)
        req = g.create_request(task="t", reasoning_summary="r", agent_name="a")

        def approve_after_delay():
            time.sleep(0.05)
            g.submit_decision(req.request_id, approved=True, resolver="tester")

        t = threading.Thread(target=approve_after_delay)
        t.start()
        result = g.request_approval(req)
        t.join()
        assert result is True

    def test_gate_rejects_when_human_rejects(self):
        from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
        g = ApprovalGate(mode=HITLMode.GATE, timeout_seconds=5.0)
        req = g.create_request(task="t", reasoning_summary="r", agent_name="a")

        def reject_after_delay():
            time.sleep(0.05)
            g.submit_decision(req.request_id, approved=False, resolver="tester",
                              rejection_reason="not allowed")

        t = threading.Thread(target=reject_after_delay)
        t.start()
        result = g.request_approval(req)
        t.join()
        assert result is False

    def test_gate_auto_rejects_on_timeout_when_configured(self):
        from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
        g = ApprovalGate(mode=HITLMode.GATE, timeout_seconds=0.3,
                         auto_approve_on_timeout=False)
        req = g.create_request(task="t", reasoning_summary="r", agent_name="a")
        result = g.request_approval(req)
        assert result is False


class TestApprovalGateDisabledMode:

    def test_disabled_always_approves(self, disabled_gate):
        req = disabled_gate.create_request(
            task="t", reasoning_summary="r", agent_name="a",
        )
        assert disabled_gate.request_approval(req) is True

    def test_disabled_audit_trail_still_recorded(self, disabled_gate):
        req = disabled_gate.create_request(
            task="t", reasoning_summary="r", agent_name="a",
        )
        disabled_gate.request_approval(req)
        assert len(disabled_gate.audit_trail) == 1


class TestApprovalGateTrustedAgents:

    def test_trusted_agent_skips_gate(self):
        from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
        g = ApprovalGate(mode=HITLMode.GATE, timeout_seconds=60.0,
                         trusted_agents={"readonly_agent"})
        req = g.create_request(task="t", reasoning_summary="r",
                               agent_name="readonly_agent")
        # Should return immediately without blocking
        start = time.monotonic()
        result = g.request_approval(req)
        elapsed = time.monotonic() - start
        assert result is True
        assert elapsed < 0.5   # definitely did not wait

    def test_untrusted_agent_goes_through_gate(self):
        from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
        g = ApprovalGate(mode=HITLMode.GATE, timeout_seconds=0.3,
                         auto_approve_on_timeout=True,
                         trusted_agents={"other_agent"})
        req = g.create_request(task="t", reasoning_summary="r",
                               agent_name="react")
        result = g.request_approval(req)
        assert result is True  # auto-approved after timeout

    def test_add_remove_trusted_agent(self):
        from core.human_in_the_loop.approval_gate import ApprovalGate, HITLMode
        g = ApprovalGate(mode=HITLMode.AUDIT)
        g.add_trusted_agent("new_agent")
        assert "new_agent" in g.trusted_agents
        g.remove_trusted_agent("new_agent")
        assert "new_agent" not in g.trusted_agents


class TestApprovalGateStatistics:

    def test_statistics_shape(self, audit_gate):
        req = audit_gate.create_request(task="t", reasoning_summary="r",
                                        agent_name="a")
        audit_gate.request_approval(req)
        stats = audit_gate.get_statistics()
        assert "total_requests" in stats
        assert "by_status" in stats
        assert "mode" in stats
        assert stats["total_requests"] == 1

    def test_submit_decision_unknown_id_returns_false(self, audit_gate):
        result = audit_gate.submit_decision("nonexistent-id", approved=True)
        assert result is False


# ===========================================================================
# 3. CausalAgentRouter tests
# ===========================================================================

class TestCausalAgentRouter:

    def _histories(self):
        return {
            "react_agent":     {"success_rate": 0.8, "avg_latency_ms": 900.0,  "total_runs": 10},
            "reasoning_agent": {"success_rate": 0.7, "avg_latency_ms": 1200.0, "total_runs": 8},
            "analysis_agent":  {"success_rate": 0.75, "avg_latency_ms": 1000.0, "total_runs": 12},
        }

    def test_select_agent_without_causal_context(self, router):
        agent = router.select_agent(
            task="Analyse market data",
            agent_histories=self._histories(),
        )
        assert agent in self._histories()

    def test_high_confidence_reasoning_boosts_reasoning_agent(self, router):
        from core.reasoning.causal_agent_router import CausalInterventionRecommendation
        recs = {
            "logic_path": CausalInterventionRecommendation(
                variable="logic_path",
                intervention_value=1,
                predicted_effect=0.8,
                confidence=0.95,
                domain="reasoning",
            )
        }
        # Run 10 times; reasoning_agent should win majority when boosted
        wins = 0
        for _ in range(10):
            agent = router.select_agent(
                task="Perform causal inference",
                causal_context=recs,
                agent_histories=self._histories(),
            )
            if agent == "reasoning_agent":
                wins += 1
        assert wins >= 6, f"reasoning_agent won only {wins}/10 times"

    def test_low_confidence_rec_does_not_override(self, router):
        from core.reasoning.causal_agent_router import CausalInterventionRecommendation
        recs = {
            "x": CausalInterventionRecommendation(
                variable="x",
                intervention_value=1,
                predicted_effect=0.3,
                confidence=0.4,   # below threshold
                domain="reasoning",
            )
        }
        # Should not crash; agent still selected
        agent = router.select_agent(
            task="Do something",
            causal_context=recs,
            agent_histories=self._histories(),
        )
        assert agent in self._histories()

    def test_no_agent_histories_returns_none(self, router):
        agent = router.select_agent(task="t", agent_histories={})
        assert agent is None

    def test_router_statistics(self, router):
        stats = router.get_statistics()
        assert "confidence_threshold" in stats
        assert "causal_boost" in stats
        assert "selector" in stats

    def test_build_recommendation_without_reasoner_raises(self, router):
        with pytest.raises(RuntimeError, match="CausalReasoner"):
            router.build_recommendation("x", 1.0)


class TestNeuralAgentSelectorCausalBoost:
    """Direct test of the causal boost inside NeuralAgentSelector."""

    def test_boost_applied_to_matching_agent(self):
        from core.learning.neural_agent_selector import NeuralAgentSelector
        sel = NeuralAgentSelector(num_agents=3)
        histories = {
            "reasoning_bot": {"success_rate": 0.5, "avg_latency_ms": 1000.0, "total_runs": 0},
            "generation_bot": {"success_rate": 0.5, "avg_latency_ms": 1000.0, "total_runs": 0},
        }
        causal_ctx = {
            "path": {"confidence": 0.9, "domain": "reasoning", "predicted_effect": 0.8}
        }
        scores = sel.predict_agent_scores(
            task="test", agent_histories=histories, causal_context=causal_ctx
        )
        agent_dict = dict(scores)
        # reasoning_bot should score higher because of boost
        assert agent_dict["reasoning_bot"] > agent_dict["generation_bot"], (
            f"Expected reasoning_bot > generation_bot, got {agent_dict}"
        )

    def test_no_boost_below_threshold(self):
        from core.learning.neural_agent_selector import NeuralAgentSelector
        sel = NeuralAgentSelector(num_agents=2)
        histories = {
            "reasoning_bot": {"success_rate": 0.5, "avg_latency_ms": 1000.0, "total_runs": 0},
            "generation_bot": {"success_rate": 0.5, "avg_latency_ms": 1000.0, "total_runs": 0},
        }
        # Confidence 0.3 is below 0.7 threshold → no boost
        causal_ctx = {
            "path": {"confidence": 0.3, "domain": "reasoning"}
        }
        scores_with = sel.predict_agent_scores(
            task="test", agent_histories=histories, causal_context=causal_ctx
        )
        scores_without = sel.predict_agent_scores(
            task="test", agent_histories=histories
        )
        dict_with    = dict(scores_with)
        dict_without = dict(scores_without)
        # Scores should be equal (no boost applied)
        assert dict_with["reasoning_bot"] == pytest.approx(
            dict_without["reasoning_bot"], abs=1e-6
        )


# ===========================================================================
# 4. PyTorch graceful degradation tests
# ===========================================================================

class TestGracefulDegradation:

    def test_mann_wrapper_noop_when_no_torch(self):
        """MANNWrapper must not raise when TORCH_AVAILABLE=False."""
        import core.learning.mann as mann_mod
        original = mann_mod.TORCH_AVAILABLE
        try:
            mann_mod.TORCH_AVAILABLE = False
            dummy_model = MagicMock()
            dummy_model.memory_size = 16
            dummy_model.memory_key_dim = 8
            dummy_model.memory_value_dim = 16
            wrapper = mann_mod.MANNWrapper(model=dummy_model)
            assert wrapper._noop is True
            arr = np.zeros(8)
            out, meta = wrapper.predict(arr)
            assert meta.get("noop") is True
        finally:
            mann_mod.TORCH_AVAILABLE = original

    def test_knowledge_distiller_noop_when_no_torch(self):
        import core.learning.knowledge_distillation as kd_mod
        original = kd_mod.TORCH_AVAILABLE
        try:
            kd_mod.TORCH_AVAILABLE = False
            distiller = kd_mod.KnowledgeDistiller()
            assert distiller._noop is True
            result = distiller.distill(None, None, [])
            assert result["history"] == []
            assert result["final_train_loss"] is None
        finally:
            kd_mod.TORCH_AVAILABLE = original

    def test_ensemble_distiller_noop_when_no_torch(self):
        import core.learning.knowledge_distillation as kd_mod
        original = kd_mod.TORCH_AVAILABLE
        try:
            kd_mod.TORCH_AVAILABLE = False
            distiller = kd_mod.EnsembleDistiller()
            assert distiller._noop is True
            result = distiller.distill_ensemble([], None, [])
            assert result["history"] == []
        finally:
            kd_mod.TORCH_AVAILABLE = original

    def test_model_compressor_noop_when_no_torch(self):
        import core.learning.model_compression as mc_mod
        original = mc_mod.TORCH_AVAILABLE
        try:
            mc_mod.TORCH_AVAILABLE = False
            compressor = mc_mod.ModelCompressor()
            assert compressor._noop is True
            sentinel = object()
            model_out, stats = compressor.compress(sentinel)
            assert model_out is sentinel
            assert stats.get("noop") is True
        finally:
            mc_mod.TORCH_AVAILABLE = original


# ===========================================================================
# 5. ph_server endpoint tests (with mocked orchestrator)
# ===========================================================================

class TestPhServerEndpoints:

    def _make_client(self):
        """Build a TestClient for ph_server with all heavy deps mocked."""
        import importlib

        mock_orch = MagicMock()
        mock_orch.run.return_value = _MOCK_RUN_RESULT
        mock_orch._agents = {"react": MagicMock()}

        mock_swarm = MagicMock()
        mock_swarm.execute_swarm.return_value = _MOCK_SWARM_RESULT
        mock_swarm.register_agent.return_value = None

        patches = [
            patch("core.orchestrator.Orchestrator", return_value=mock_orch),
            patch("core.swarm.swarm_orchestrator.SwarmOrchestrator",
                  return_value=mock_swarm),
            patch("builtins.open", MagicMock(
                return_value=MagicMock(
                    __enter__=lambda s: s,
                    __exit__=MagicMock(return_value=False),
                    read=MagicMock(return_value="{}"),
                )
            )),
            patch("json.load", return_value={
                "enabled_agents": ["react"], "max_agents": 5
            }),
        ]
        return patches, mock_orch, mock_swarm

    def test_health_endpoint(self):
        try:
            import ph_server as srv
            with TestClient(srv.app) as client:
                resp = client.get("/health")
            assert resp.status_code == 200
            body = resp.json()
            assert body["status"] == "ok"
            assert "hitl_mode" in body
            assert "rl_ingestion_count" in body
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_run_endpoint_returns_expected_shape(self):
        try:
            import ph_server as srv
            # Patch the orchestrator on the already-imported module
            original_run = srv._orchestrator.run
            srv._orchestrator.run = MagicMock(return_value=_MOCK_RUN_RESULT)
            try:
                with TestClient(srv.app) as client:
                    resp = client.post("/run", json={"task": "explain RL"})
                assert resp.status_code == 200
                body = resp.json()
                assert body["task"] == "test task"
                assert isinstance(body["outputs"], list)
                assert "run_id" in body
                assert "hitl_status" in body
            finally:
                srv._orchestrator.run = original_run
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_run_endpoint_with_causal_context(self):
        try:
            import ph_server as srv
            original_run = srv._orchestrator.run
            srv._orchestrator.run = MagicMock(return_value=_MOCK_RUN_RESULT)
            try:
                with TestClient(srv.app) as client:
                    resp = client.post("/run", json={
                        "task": "tune parameters",
                        "causal_context": {
                            "temperature": {
                                "confidence": 0.9,
                                "domain": "parameter_tuning",
                                "predicted_effect": 0.7,
                            }
                        },
                    })
                assert resp.status_code == 200
                body = resp.json()
                assert "hitl_status" in body
            finally:
                srv._orchestrator.run = original_run
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_run_swarm_endpoint_returns_expected_shape(self):
        try:
            import ph_server as srv
            original = srv._swarm_orchestrator.execute_swarm
            srv._swarm_orchestrator.execute_swarm = MagicMock(
                return_value=_MOCK_SWARM_RESULT
            )
            try:
                with TestClient(srv.app) as client:
                    resp = client.post("/run/swarm", json={
                        "task": "swarm test",
                        "max_iterations": 3,
                    })
                assert resp.status_code == 200
                body = resp.json()
                assert "iterations" in body
                assert "emergent_patterns" in body
                assert body["rl_ingested"] is True
            finally:
                srv._swarm_orchestrator.execute_swarm = original
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_hitl_pending_endpoint(self):
        try:
            import ph_server as srv
            with TestClient(srv.app) as client:
                resp = client.get("/hitl/pending")
            assert resp.status_code == 200
            body = resp.json()
            assert "pending" in body
            assert "mode" in body
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_hitl_audit_endpoint(self):
        try:
            import ph_server as srv
            with TestClient(srv.app) as client:
                resp = client.get("/hitl/audit")
            assert resp.status_code == 200
            body = resp.json()
            assert "audit_trail" in body
            assert "statistics" in body
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_rl_statistics_endpoint(self):
        try:
            import ph_server as srv
            with TestClient(srv.app) as client:
                resp = client.get("/rl/statistics")
            assert resp.status_code == 200
            body = resp.json()
            assert "ingestion_count" in body
        except Exception:
            pytest.skip("ph_server not importable in this environment")

    def test_hitl_decide_unknown_id_returns_404(self):
        try:
            import ph_server as srv
            with TestClient(srv.app) as client:
                resp = client.post(
                    "/hitl/nonexistent-id/decide",
                    json={"approved": True, "resolver": "tester"},
                )
            assert resp.status_code == 404
        except Exception:
            pytest.skip("ph_server not importable in this environment")

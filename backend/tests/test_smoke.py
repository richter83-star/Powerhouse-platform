from datetime import datetime, timedelta
import uuid

from fastapi.testclient import TestClient

from api.auth import get_current_user
from api.main import app
from api.models import User
from config.settings import settings
from database.models import AgentRun, AgentRunStatus, Project, Run, RunStatus, Tenant
from database.session import get_session


def _override_user():
    return User(
        username="smoke",
        email="smoke@example.com",
        tenant_id="smoke-tenant",
        disabled=False,
    )


def test_health_smoke():
    settings.environment = "development"
    app.dependency_overrides[get_current_user] = _override_user
    with TestClient(app) as client:
        response = client.get("/health")
    app.dependency_overrides.clear()
    assert response.status_code == 200


def test_compliance_workflow_stub(monkeypatch):
    settings.environment = "development"
    def stub_init(self, db_session=None):
        self.db = db_session
        self.agents = {}

    async def stub_start_workflow(self, *args, **kwargs):
        return "smoke-workflow-id"

    async def stub_execute_workflow(self, *args, **kwargs):
        return {"status": "completed", "results": {}}

    monkeypatch.setattr(
        "workflows.compliance.ComplianceWorkflow.__init__",
        stub_init,
    )
    monkeypatch.setattr(
        "workflows.compliance.ComplianceWorkflow.start_workflow",
        stub_start_workflow,
    )
    monkeypatch.setattr(
        "workflows.compliance.ComplianceWorkflow.execute_workflow",
        stub_execute_workflow,
    )

    app.dependency_overrides[get_current_user] = _override_user
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/workflows/compliance",
            json={"query": "CI smoke test compliance query"},
        )
    app.dependency_overrides.clear()

    assert response.status_code == 202, response.text
    payload = response.json()
    assert "workflow_id" in payload


def test_workflow_status_summary_smoke():
    settings.environment = "development"
    workflow_id = str(uuid.uuid4())
    tenant_id = _override_user().tenant_id
    project_id = str(uuid.uuid4())

    session = get_session()
    try:
        tenant = session.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            session.add(Tenant(id=tenant_id, name="Smoke Tenant"))
        session.add(Project(id=project_id, tenant_id=tenant_id, name="Smoke Project"))
        session.add(
            Run(
                id=workflow_id,
                project_id=project_id,
                tenant_id=tenant_id,
                status=RunStatus.RUNNING,
                input_data={"type": "compliance"}
            )
        )
        started_at = datetime.utcnow() - timedelta(seconds=5)
        completed_at = datetime.utcnow() - timedelta(seconds=2)
        session.add(
            AgentRun(
                id=str(uuid.uuid4()),
                run_id=workflow_id,
                tenant_id=tenant_id,
                agent_name="governor",
                agent_type="GovernorAgent",
                status=AgentRunStatus.COMPLETED,
                started_at=started_at,
                completed_at=completed_at
            )
        )
        session.add(
            AgentRun(
                id=str(uuid.uuid4()),
                run_id=workflow_id,
                tenant_id=tenant_id,
                agent_name="react",
                agent_type="Agent",
                status=AgentRunStatus.RUNNING,
                started_at=datetime.utcnow() - timedelta(seconds=1)
            )
        )
        session.commit()
    finally:
        session.close()

    app.dependency_overrides[get_current_user] = _override_user
    with TestClient(app) as client:
        response = client.get(f"/api/v1/workflows/{workflow_id}/status-summary")
    app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["workflow_id"] == workflow_id
    assert payload["status"] == "running"
    assert payload["current_step"] == "ReAct analysis"
    assert payload["progress_percentage"] >= 0
    assert 0 <= payload["progress"] <= 1
    assert len(payload["agent_statuses"]) >= 4
    assert payload["agent_statuses"][0]["agent_id"] is not None
    running_agent = next(
        (agent for agent in payload["agent_statuses"] if agent["status"] == "running"),
        None
    )
    assert running_agent is not None
    assert isinstance(running_agent["duration_seconds"], (int, float))

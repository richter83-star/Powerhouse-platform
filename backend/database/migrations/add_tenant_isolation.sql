-- ============================================================================
-- PostgreSQL Row-Level Security (RLS) Setup for Multi-Tenancy
-- ============================================================================
-- 
-- This script sets up Row-Level Security policies to enforce tenant isolation
-- at the database level. This provides defense-in-depth security.
--
-- IMPORTANT: Run this AFTER creating all tables and adding tenant_id columns.
-- ============================================================================

-- Enable RLS on all tenant-scoped tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_events ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS Policies
-- ============================================================================
-- These policies ensure users can only access data for their tenant.
-- The current_setting('app.current_tenant_id') function is set by the application
-- before executing queries.

-- Projects: Users can only see projects for their tenant
CREATE POLICY projects_tenant_isolation ON projects
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Runs: Users can only see runs for their tenant
CREATE POLICY runs_tenant_isolation ON runs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Agent Runs: Users can only see agent runs for their tenant
CREATE POLICY agent_runs_tenant_isolation ON agent_runs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Messages: Users can only see messages for their tenant
CREATE POLICY messages_tenant_isolation ON messages
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Refresh Tokens: Users can only see their own tokens for their tenant
CREATE POLICY refresh_tokens_tenant_isolation ON refresh_tokens
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Login Attempts: Users can only see login attempts for their tenant
CREATE POLICY login_attempts_tenant_isolation ON login_attempts
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- User Tenants: Users can only see their own tenant relationships
CREATE POLICY user_tenants_tenant_isolation ON user_tenants
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Model Versions: Users can only see models for their tenant (or system-wide if tenant_id is NULL)
CREATE POLICY model_versions_tenant_isolation ON model_versions
    FOR ALL
    USING (
        tenant_id IS NULL OR 
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- Learning Events: Users can only see events for their tenant (or system-wide if tenant_id is NULL)
CREATE POLICY learning_events_tenant_isolation ON learning_events
    FOR ALL
    USING (
        tenant_id IS NULL OR 
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

-- ============================================================================
-- Indexes for Performance
-- ============================================================================
-- Ensure tenant_id columns are indexed for fast filtering

CREATE INDEX IF NOT EXISTS idx_runs_tenant_id ON runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant_id ON agent_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_messages_tenant_id ON messages(tenant_id);
CREATE INDEX IF NOT EXISTS idx_model_versions_tenant_id ON model_versions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_learning_events_tenant_id ON learning_events(tenant_id);

-- ============================================================================
-- Composite Indexes for Common Query Patterns
-- ============================================================================

-- Runs: tenant_id + status (common filter)
CREATE INDEX IF NOT EXISTS idx_runs_tenant_status ON runs(tenant_id, status);

-- Runs: tenant_id + created_at (for time-based queries)
CREATE INDEX IF NOT EXISTS idx_runs_tenant_created ON runs(tenant_id, created_at DESC);

-- Agent Runs: tenant_id + agent_name (for agent-specific queries)
CREATE INDEX IF NOT EXISTS idx_agent_runs_tenant_agent ON agent_runs(tenant_id, agent_name);

-- ============================================================================
-- Notes
-- ============================================================================
-- 
-- To use RLS in application code:
-- 
-- 1. Set tenant context before queries:
--    SET LOCAL app.current_tenant_id = 'tenant-uuid';
-- 
-- 2. Or use a connection pool with tenant context:
--    connection.execute(text("SET LOCAL app.current_tenant_id = :tenant_id"), {"tenant_id": tenant_id})
-- 
-- 3. The application layer should still filter by tenant_id as a best practice,
--    but RLS provides an additional security layer.
-- 
-- ============================================================================


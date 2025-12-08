
"""
Comprehensive audit logging service with immutable event ledger.
"""
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path

class AuditEventType(Enum):
    """Types of auditable events"""
    # Authentication
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"
    AUTH_TOKEN_REVOKE = "auth.token_revoke"
    
    # Authorization
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"
    
    # Agent Operations
    AGENT_CREATE = "agent.create"
    AGENT_UPDATE = "agent.update"
    AGENT_DELETE = "agent.delete"
    AGENT_EXECUTE = "agent.execute"
    AGENT_ERROR = "agent.error"
    
    # Workflow Operations
    WORKFLOW_CREATE = "workflow.create"
    WORKFLOW_UPDATE = "workflow.update"
    WORKFLOW_DELETE = "workflow.delete"
    WORKFLOW_EXECUTE = "workflow.execute"
    WORKFLOW_COMPLETE = "workflow.complete"
    WORKFLOW_FAILED = "workflow.failed"
    
    # Configuration Changes
    CONFIG_UPDATE = "config.update"
    CONFIG_DELETE = "config.delete"
    
    # Data Operations
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    
    # System Events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    
    # Security Events
    SECURITY_BREACH_ATTEMPT = "security.breach_attempt"
    SECURITY_POLICY_CHANGE = "security.policy_change"
    
    # Compliance Events
    COMPLIANCE_CHECK = "compliance.check"
    COMPLIANCE_VIOLATION = "compliance.violation"

class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """
    Immutable audit event record.
    
    Each event includes:
    - Unique event ID
    - Timestamp
    - Event type and severity
    - Actor (user) information
    - Resource being accessed
    - Action outcome
    - Metadata
    - Cryptographic hash for integrity
    """
    event_id: str
    timestamp: str
    event_type: AuditEventType
    severity: AuditSeverity
    user_id: str
    tenant_id: str
    resource_type: str
    resource_id: str
    action: str
    outcome: str  # "success" or "failure"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        return data
    
    def compute_hash(self) -> str:
        """Compute cryptographic hash for event integrity"""
        # Create deterministic string representation
        hashable_data = (
            f"{self.event_id}|{self.timestamp}|{self.event_type.value}|"
            f"{self.user_id}|{self.tenant_id}|{self.resource_type}|"
            f"{self.resource_id}|{self.action}|{self.outcome}|{self.previous_hash}"
        )
        return hashlib.sha256(hashable_data.encode()).hexdigest()

class AuditLogger:
    """
    Immutable audit log service with blockchain-like integrity verification.
    
    Features:
    - Append-only event storage
    - Cryptographic chaining (each event links to previous)
    - Tamper detection
    - Multi-tenant isolation
    - Async write performance
    - Query capabilities
    """
    
    def __init__(self, log_dir: str = "./audit_logs"):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # In-memory cache for recent events (last event hash per tenant)
        self.last_hashes = {}  # {tenant_id: last_hash}
        
        # Event queue for async processing
        self.event_queue = asyncio.Queue()
        self._running = False
        self._processor_task = None
    
    async def start(self):
        """Start the audit log processor"""
        if not self._running:
            self._running = True
            self._processor_task = asyncio.create_task(self._process_events())
    
    async def stop(self):
        """Stop the audit log processor"""
        self._running = False
        if self._processor_task:
            await self._processor_task
    
    async def _process_events(self):
        """Background task to process audit events"""
        while self._running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._write_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing audit event: {e}")
    
    async def log(
        self,
        event_type: AuditEventType,
        user_id: str,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        outcome: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            user_id: User performing the action
            tenant_id: Tenant context
            resource_type: Type of resource (agent, workflow, config, etc.)
            resource_id: Specific resource identifier
            action: Action performed (create, read, update, delete, execute)
            outcome: "success" or "failure"
            severity: Event severity level
            ip_address: Source IP address
            user_agent: User agent string
            session_id: Session identifier
            metadata: Additional event data
            
        Returns:
            Created audit event
        """
        event_id = self._generate_event_id(tenant_id)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Get previous hash for this tenant
        previous_hash = self.last_hashes.get(tenant_id)
        
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            metadata=metadata or {},
            previous_hash=previous_hash
        )
        
        # Compute hash for this event
        event.event_hash = event.compute_hash()
        
        # Update last hash for tenant
        self.last_hashes[tenant_id] = event.event_hash
        
        # Queue event for async writing
        await self.event_queue.put(event)
        
        return event
    
    async def _write_event(self, event: AuditEvent):
        """
        Write event to append-only log file.
        
        Args:
            event: Audit event to write
        """
        # One log file per tenant per day for manageable file sizes
        date_str = event.timestamp[:10]  # YYYY-MM-DD
        log_file = self.log_dir / f"{event.tenant_id}_{date_str}.jsonl"
        
        # Append event to log file (JSONL format)
        with open(log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')
    
    def query(
        self,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Query audit logs with filtering.
        
        Args:
            tenant_id: Tenant to query
            start_date: Start of time range
            end_date: End of time range
            event_types: Filter by event types
            user_id: Filter by user
            resource_type: Filter by resource type
            severity: Filter by severity
            limit: Maximum results
            
        Returns:
            List of matching audit events
        """
        results = []
        
        # Determine which log files to scan
        log_files = self._get_log_files(tenant_id, start_date, end_date)
        
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            with open(log_file, 'r') as f:
                for line in f:
                    if len(results) >= limit:
                        break
                    
                    try:
                        event_data = json.loads(line)
                        
                        # Apply filters
                        if event_types and event_data['event_type'] not in [et.value for et in event_types]:
                            continue
                        if user_id and event_data['user_id'] != user_id:
                            continue
                        if resource_type and event_data['resource_type'] != resource_type:
                            continue
                        if severity and event_data['severity'] != severity.value:
                            continue
                        
                        # Convert back to AuditEvent
                        event_data['event_type'] = AuditEventType(event_data['event_type'])
                        event_data['severity'] = AuditSeverity(event_data['severity'])
                        event = AuditEvent(**event_data)
                        results.append(event)
                        
                    except Exception as e:
                        print(f"Error parsing audit log entry: {e}")
                        continue
        
        return results
    
    def verify_integrity(self, tenant_id: str, date: Optional[datetime] = None) -> bool:
        """
        Verify the integrity of audit log chain.
        
        Args:
            tenant_id: Tenant to verify
            date: Specific date to verify (defaults to today)
            
        Returns:
            True if chain is valid, False if tampered
        """
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{tenant_id}_{date_str}.jsonl"
        
        if not log_file.exists():
            return True  # No log file = no tampering
        
        previous_hash = None
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    event_data = json.loads(line)
                    
                    # Verify previous hash matches
                    if event_data['previous_hash'] != previous_hash:
                        return False
                    
                    # Verify event hash is correct
                    event_data['event_type'] = AuditEventType(event_data['event_type'])
                    event_data['severity'] = AuditSeverity(event_data['severity'])
                    event = AuditEvent(**event_data)
                    
                    expected_hash = event.compute_hash()
                    if event.event_hash != expected_hash:
                        return False
                    
                    previous_hash = event.event_hash
                    
                except Exception as e:
                    print(f"Error verifying audit log: {e}")
                    return False
        
        return True
    
    def _generate_event_id(self, tenant_id: str) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{tenant_id}:{timestamp}:{hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_log_files(
        self,
        tenant_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Path]:
        """Get list of log files to scan based on date range"""
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()
        
        log_files = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{tenant_id}_{date_str}.jsonl"
            log_files.append(log_file)
            current_date += timedelta(days=1)
        
        return log_files

# Global audit logger instance
audit_logger = AuditLogger()

# Helper functions for common audit events
async def log_auth_event(user_id: str, tenant_id: str, event_type: AuditEventType, outcome: str, **kwargs):
    """Log authentication event"""
    return await audit_logger.log(
        event_type=event_type,
        user_id=user_id,
        tenant_id=tenant_id,
        resource_type="auth",
        resource_id=user_id,
        action="authenticate",
        outcome=outcome,
        severity=AuditSeverity.WARNING if outcome == "failure" else AuditSeverity.INFO,
        **kwargs
    )

async def log_agent_event(user_id: str, tenant_id: str, agent_id: str, action: str, outcome: str, **kwargs):
    """Log agent operation event"""
    event_type_map = {
        "create": AuditEventType.AGENT_CREATE,
        "update": AuditEventType.AGENT_UPDATE,
        "delete": AuditEventType.AGENT_DELETE,
        "execute": AuditEventType.AGENT_EXECUTE,
    }
    
    return await audit_logger.log(
        event_type=event_type_map.get(action, AuditEventType.AGENT_EXECUTE),
        user_id=user_id,
        tenant_id=tenant_id,
        resource_type="agent",
        resource_id=agent_id,
        action=action,
        outcome=outcome,
        **kwargs
    )

async def log_data_access(user_id: str, tenant_id: str, data_id: str, action: str, outcome: str, **kwargs):
    """Log data access event"""
    event_type_map = {
        "create": AuditEventType.DATA_CREATE,
        "read": AuditEventType.DATA_READ,
        "update": AuditEventType.DATA_UPDATE,
        "delete": AuditEventType.DATA_DELETE,
        "export": AuditEventType.DATA_EXPORT,
    }
    
    return await audit_logger.log(
        event_type=event_type_map.get(action, AuditEventType.DATA_READ),
        user_id=user_id,
        tenant_id=tenant_id,
        resource_type="data",
        resource_id=data_id,
        action=action,
        outcome=outcome,
        **kwargs
    )

from datetime import timedelta

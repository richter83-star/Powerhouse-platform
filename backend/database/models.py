
"""
SQLAlchemy database models.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, JSON, Enum, Float
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class RunStatus(str, enum.Enum):
    """Status of a run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRunStatus(str, enum.Enum):
    """Status of an agent run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ModelStatus(str, enum.Enum):
    """Status of a model version."""
    TRAINING = "training"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class Tenant(Base):
    """
    Tenant model for multi-tenancy support.
    
    Each tenant represents a separate customer/organization.
    """
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name})>"


class Project(Base):
    """
    Project model.
    
    Projects group related runs together within a tenant.
    """
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    meta_data = Column("metadata", JSON, default=dict)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    runs = relationship("Run", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"


class Run(Base):
    """
    Run model.
    
    A run represents a single execution of the multi-agent system.
    """
    __tablename__ = "runs"
    
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING, nullable=False, index=True)
    config = Column(JSON, default=dict)  # Configuration used for this run
    input_data = Column(JSON)  # Input data/task
    output_data = Column(JSON)  # Final output
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("Project", back_populates="runs")
    agent_runs = relationship("AgentRun", back_populates="run", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Run(id={self.id}, status={self.status})>"


class AgentRun(Base):
    """
    Agent run model.
    
    Tracks individual agent executions within a run.
    """
    __tablename__ = "agent_runs"
    
    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False, index=True)
    agent_name = Column(String(255), nullable=False, index=True)
    agent_type = Column(String(100), nullable=False)
    status = Column(Enum(AgentRunStatus), default=AgentRunStatus.PENDING, nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_ms = Column(Float)
    
    # Relationships
    run = relationship("Run", back_populates="agent_runs")
    
    def __repr__(self):
        return f"<AgentRun(id={self.id}, agent={self.agent_name}, status={self.status})>"


class Message(Base):
    """
    Message model for agent-to-agent communication.
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False, index=True)
    sender = Column(String(255), nullable=False)
    receiver = Column(String(255), nullable=False)
    message_type = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed = Column(Integer, default=0)  # 0=pending, 1=processed
    
    # Relationships
    run = relationship("Run", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, {self.sender}->{self.receiver})>"


class ModelVersion(Base):
    """
    Model version tracking for online learning.
    
    Stores metadata and performance metrics for each model version.
    """
    __tablename__ = "model_versions"
    
    id = Column(String(36), primary_key=True)
    model_type = Column(String(100), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(Enum(ModelStatus), default=ModelStatus.TRAINING, nullable=False)
    
    # Model metadata
    parameters = Column(JSON, default=dict)
    hyperparameters = Column(JSON, default=dict)
    
    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    training_samples = Column(Integer, default=0)
    
    # Custom metrics
    metrics = Column(JSON, default=dict)
    
    # File paths
    model_file_path = Column(String(500))
    
    # Versioning
    parent_version_id = Column(String(36), ForeignKey("model_versions.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime)
    deprecated_at = Column(DateTime)
    
    # Relationships
    parent = relationship("ModelVersion", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<ModelVersion(id={self.id}, type={self.model_type}, v={self.version_number})>"


class LearningEvent(Base):
    """
    Learning event tracking for model updates.
    
    Records each learning iteration and its impact on model performance.
    """
    __tablename__ = "learning_events"
    
    id = Column(String(36), primary_key=True)
    model_version_id = Column(String(36), ForeignKey("model_versions.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # 'micro_batch', 'full_retrain', etc.
    batch_size = Column(Integer)
    samples_processed = Column(Integer)
    
    # Performance before/after
    metrics_before = Column(JSON)
    metrics_after = Column(JSON)
    improvement = Column(Float)
    
    # Timing
    duration_ms = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    model_version = relationship("ModelVersion")
    
    def __repr__(self):
        return f"<LearningEvent(id={self.id}, type={self.event_type})>"

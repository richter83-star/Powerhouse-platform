
"""
SQLAlchemy database models.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, JSON, Enum, Float, Boolean, ARRAY, Numeric
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
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
    user_tenants = relationship("UserTenant", back_populates="tenant", cascade="all, delete-orphan")
    
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
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)  # Direct tenant reference for RLS
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
    tenant = relationship("Tenant")
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
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)  # Direct tenant reference for RLS
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
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<AgentRun(id={self.id}, agent={self.agent_name}, status={self.status})>"


class Message(Base):
    """
    Message model for agent-to-agent communication.
    """
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), ForeignKey("runs.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)  # Direct tenant reference for RLS
    sender = Column(String(255), nullable=False)
    receiver = Column(String(255), nullable=False)
    message_type = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed = Column(Integer, default=0)  # 0=pending, 1=processed
    
    # Relationships
    run = relationship("Run", back_populates="messages")
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<Message(id={self.id}, {self.sender}->{self.receiver})>"


class ModelVersion(Base):
    """
    Model version tracking for online learning.
    
    Stores metadata and performance metrics for each model version.
    """
    __tablename__ = "model_versions"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)  # Nullable for system-wide models
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
    tenant = relationship("Tenant")
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
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)  # Nullable for system-wide events
    
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
    tenant = relationship("Tenant")
    model_version = relationship("ModelVersion")
    
    def __repr__(self):
        return f"<LearningEvent(id={self.id}, type={self.event_type})>"


class User(Base):
    """
    User model for authentication and authorization.
    
    Stores user credentials, profile information, and account status.
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_name = Column(String(255))
    job_title = Column(String(255))
    
    # Account status
    is_active = Column(Integer, default=1, nullable=False)  # 1=active, 0=inactive
    is_verified = Column(Integer, default=0, nullable=False)  # 1=verified, 0=unverified
    is_locked = Column(Integer, default=0, nullable=False)  # 1=locked, 0=unlocked
    locked_until = Column(DateTime, nullable=True)  # Lock expiration time
    
    # Failed login tracking
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_failed_login = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")
    user_tenants = relationship("UserTenant", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class RefreshToken(Base):
    """
    Refresh token model for JWT token management.
    
    Stores refresh tokens with expiration and revocation status.
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    
    # Token status
    is_revoked = Column(Integer, default=0, nullable=False)  # 1=revoked, 0=active
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Metadata
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"


class LoginAttempt(Base):
    """
    Login attempt tracking for security monitoring.
    
    Records all login attempts (successful and failed) for audit purposes.
    """
    __tablename__ = "login_attempts"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for failed attempts with unknown user
    email = Column(String(255), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    
    # Attempt details
    success = Column(Integer, default=0, nullable=False)  # 1=success, 0=failure
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Failure reason (if failed)
    failure_reason = Column(String(255), nullable=True)  # 'invalid_password', 'account_locked', etc.
    
    # Timestamp
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="login_attempts")
    
    def __repr__(self):
        return f"<LoginAttempt(id={self.id}, email={self.email}, success={self.success})>"


class UserTenant(Base):
    """
    User-Tenant relationship model.
    
    Links users to tenants and stores their roles within each tenant.
    """
    __tablename__ = "user_tenants"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Role storage (JSON array of role strings)
    roles = Column(JSON, default=list, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_tenants")
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<UserTenant(user_id={self.user_id}, tenant_id={self.tenant_id})>"


class EmailVerification(Base):
    """
    Email verification token model.
    
    Stores verification tokens for email confirmation.
    """
    __tablename__ = "email_verifications"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    
    # Status
    is_used = Column(Integer, default=0, nullable=False)  # 1=used, 0=unused
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<EmailVerification(id={self.id}, user_id={self.user_id}, used={self.is_used})>"


class PasswordReset(Base):
    """
    Password reset token model.
    
    Stores password reset tokens with expiration.
    """
    __tablename__ = "password_resets"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(100), unique=True, nullable=False, index=True)
    
    # Status
    is_used = Column(Integer, default=0, nullable=False)  # 1=used, 0=unused
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<PasswordReset(id={self.id}, user_id={self.user_id}, used={self.is_used})>"


class LicenseStatus(str, enum.Enum):
    """License status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    TRIAL = "trial"
    GRACE_PERIOD = "grace_period"
    INACTIVE = "inactive"


class LicenseType(str, enum.Enum):
    """License type enumeration"""
    TRIAL = "trial"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    PERPETUAL = "perpetual"


class License(Base):
    """
    License model for license key management.
    
    Stores license keys, activation status, expiration, and device binding.
    """
    __tablename__ = "licenses"
    
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)  # Nullable for system-wide licenses
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    
    # License key
    license_key = Column(String(255), unique=True, nullable=False, index=True)
    license_type = Column(Enum(LicenseType), default=LicenseType.STANDARD, nullable=False)
    
    # Status
    status = Column(Enum(LicenseStatus), default=LicenseStatus.INACTIVE, nullable=False, index=True)
    
    # Dates
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    trial_ends_at = Column(DateTime, nullable=True)  # For trial licenses
    grace_period_ends_at = Column(DateTime, nullable=True)  # Grace period after expiration
    
    # Device binding
    hardware_fingerprint = Column(String(255), nullable=True, index=True)  # Device identifier
    max_devices = Column(Integer, default=1, nullable=False)  # Multi-seat support
    device_count = Column(Integer, default=0, nullable=False)  # Current device count
    
    # License details
    seats = Column(Integer, default=1, nullable=False)  # Number of user seats
    features = Column(JSON, default=list, nullable=False)  # Enabled features
    license_metadata = Column("metadata", JSON, default=dict, nullable=False)  # Additional license metadata (renamed to avoid SQLAlchemy conflict)
    
    # Revocation
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    activations = relationship("LicenseActivation", back_populates="license", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<License(id={self.id}, key={self.license_key[:8]}..., status={self.status})>"


class LicenseActivation(Base):
    """
    License activation record.
    
    Tracks each device activation for a license (multi-seat support).
    """
    __tablename__ = "license_activations"
    
    id = Column(String(36), primary_key=True)
    license_id = Column(String(36), ForeignKey("licenses.id"), nullable=False, index=True)
    
    # Device information
    hardware_fingerprint = Column(String(255), nullable=False, index=True)
    device_name = Column(String(255), nullable=True)
    device_info = Column(JSON, default=dict, nullable=False)  # OS, CPU, etc.
    
    # Activation details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Integer, default=1, nullable=False)  # 1=active, 0=deactivated
    
    # Timestamps
    activated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deactivated_at = Column(DateTime, nullable=True)
    last_validated_at = Column(DateTime, nullable=True)  # Last license check
    
    # Relationships
    license = relationship("License", back_populates="activations")
    
    def __repr__(self):
        return f"<LicenseActivation(id={self.id}, license_id={self.license_id}, active={self.is_active})>"


class OnboardingProgress(Base):
    """
    Onboarding progress tracking model.
    
    Tracks user's progress through the onboarding flow.
    """
    __tablename__ = "onboarding_progress"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Progress tracking
    current_step = Column(String(100), nullable=False, default="welcome")
    completed_steps = Column(JSON, default=list, nullable=False)  # List of completed step IDs
    skipped = Column(Boolean, default=False, nullable=False)
    
    # User preferences
    use_case = Column(String(100), nullable=True)  # Selected use case
    preferences = Column(JSON, default=dict, nullable=False)  # Additional preferences
    
    # Sample data created
    sample_workflow_created = Column(Boolean, default=False, nullable=False)
    sample_agent_created = Column(Boolean, default=False, nullable=False)
    first_run_completed = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<OnboardingProgress(user_id={self.user_id}, step={self.current_step}, completed={self.completed_at is not None})>"


class Seller(Base):
    """
    Seller model for marketplace.
    
    Represents a user who sells items on the marketplace.
    """
    __tablename__ = "sellers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, index=True)
    stripe_account_id = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    rating = Column(Float, default=0.00, nullable=False)
    total_sales = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Float, default=0.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    listings = relationship("MarketplaceListing", back_populates="seller", cascade="all, delete-orphan")
    purchases = relationship("MarketplacePurchase", back_populates="seller", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Seller(id={self.id}, display_name={self.display_name})>"


class MarketplaceListing(Base):
    """
    Marketplace listing model.
    
    Represents an item (app, agent, workflow) for sale on the marketplace.
    """
    __tablename__ = "marketplace_listings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    complexity_score = Column(Integer, default=1, nullable=False)
    preview_images = Column(JSON, default=list, nullable=True)  # Store as JSON array
    demo_url = Column(String(500), nullable=True)
    config_data = Column(JSON, default=dict, nullable=True)
    downloads = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=0.00, nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    seller = relationship("Seller", back_populates="listings")
    purchases = relationship("MarketplacePurchase", back_populates="listing", cascade="all, delete-orphan")
    reviews = relationship("MarketplaceReview", back_populates="listing", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MarketplaceListing(id={self.id}, title={self.title}, status={self.status})>"


class MarketplacePurchase(Base):
    """
    Marketplace purchase/transaction model.
    
    Records a purchase of an item from the marketplace.
    """
    __tablename__ = "marketplace_purchases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("marketplace_listings.id"), nullable=False, index=True)
    buyer_id = Column(String(36), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    seller_amount = Column(Float, nullable=False)
    stripe_payment_id = Column(String(255), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    listing = relationship("MarketplaceListing", back_populates="purchases")
    seller = relationship("Seller", back_populates="purchases")
    reviews = relationship("MarketplaceReview", back_populates="purchase", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MarketplacePurchase(id={self.id}, listing_id={self.listing_id}, status={self.status})>"


class MarketplaceReview(Base):
    """
    Marketplace review model.
    
    Reviews and ratings for marketplace listings.
    """
    __tablename__ = "marketplace_reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("marketplace_listings.id"), nullable=False, index=True)
    purchase_id = Column(Integer, ForeignKey("marketplace_purchases.id"), nullable=False, index=True)
    buyer_id = Column(String(36), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    listing = relationship("MarketplaceListing", back_populates="reviews")
    purchase = relationship("MarketplacePurchase", back_populates="reviews")
    
    def __repr__(self):
        return f"<MarketplaceReview(id={self.id}, listing_id={self.listing_id}, rating={self.rating})>"

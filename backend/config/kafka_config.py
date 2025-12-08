
"""
Kafka configuration for the feedback pipeline.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class KafkaConfig(BaseSettings):
    """Kafka configuration settings."""
    
    # Kafka broker settings
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )
    
    # Topics
    KAFKA_OUTCOME_TOPIC: str = os.getenv(
        "KAFKA_OUTCOME_TOPIC",
        "agent-outcomes"
    )
    KAFKA_METRICS_TOPIC: str = os.getenv(
        "KAFKA_METRICS_TOPIC",
        "agent-metrics"
    )
    KAFKA_ALERTS_TOPIC: str = os.getenv(
        "KAFKA_ALERTS_TOPIC",
        "agent-alerts"
    )
    
    # Producer settings
    KAFKA_BATCH_SIZE: int = int(os.getenv("KAFKA_BATCH_SIZE", "100"))
    KAFKA_LINGER_MS: int = int(os.getenv("KAFKA_LINGER_MS", "100"))
    KAFKA_COMPRESSION: str = os.getenv("KAFKA_COMPRESSION", "gzip")
    KAFKA_MAX_RETRIES: int = int(os.getenv("KAFKA_MAX_RETRIES", "3"))
    
    # Feature flags
    ENABLE_KAFKA: bool = os.getenv("ENABLE_KAFKA", "false").lower() == "true"
    ENABLE_OUTCOME_LOGGING: bool = os.getenv("ENABLE_OUTCOME_LOGGING", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global config instance
kafka_config = KafkaConfig()

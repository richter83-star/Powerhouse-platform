
#!/usr/bin/env python3
"""
Start the Powerhouse B2B Platform with Performance Monitoring enabled.

This script starts the FastAPI server with all monitoring features enabled,
including real-time performance tracking, alerting, and reporting.
"""

import sys
import os
import uvicorn
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from api import create_app
from core.performance_monitor import init_performance_monitor
from config import get_settings
from utils.logging import setup_logging, get_logger
from database import init_db

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("Powerhouse B2B Platform - Starting with Monitoring")
    logger.info("=" * 80)
    
    # Load settings
    settings = get_settings()
    logger.info(f"Loaded settings: {settings}")
    
    # Initialize database
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)
    
    # Initialize performance monitor with custom settings
    logger.info("Initializing Performance Monitor...")
    try:
        monitor = init_performance_monitor(
            window_size_minutes=60,
            alert_thresholds={
                "success_rate_min": 0.80,
                "error_rate_max": 0.15,
                "latency_p95_max_ms": 5000,
                "cost_per_task_max": 1.0,
                "accuracy_min": 0.70,
                "memory_max_mb": 1024,
                "token_per_task_max": 5000,
            },
            enable_auto_alerts=True,
            enable_trend_analysis=True
        )
        logger.info(f"Performance Monitor initialized: {monitor}")
        
        # Sync with database to get historical metrics
        logger.info("Syncing with database for historical metrics...")
        monitor.sync_with_database(lookback_hours=24)
        
    except Exception as e:
        logger.error(f"Performance Monitor initialization failed: {e}", exc_info=True)
        sys.exit(1)
    
    # Create FastAPI app
    logger.info("Creating FastAPI application...")
    app = create_app()
    
    # Start server
    host = "0.0.0.0"
    port = 8000
    
    logger.info(f"\nStarting server at http://{host}:{port}")
    logger.info("\nAvailable endpoints:")
    logger.info("  - GET  /                           - Root endpoint")
    logger.info("  - GET  /health                     - Health check")
    logger.info("  - GET  /api/performance/health     - Performance health status")
    logger.info("  - GET  /api/performance/metrics/system - System metrics")
    logger.info("  - GET  /api/performance/metrics/agents - All agent metrics")
    logger.info("  - GET  /api/performance/alerts     - Performance alerts")
    logger.info("  - GET  /api/performance/report     - Comprehensive report")
    logger.info("  - POST /api/performance/accuracy   - Record accuracy measurement")
    logger.info("  - POST /api/performance/sync       - Sync metrics from database")
    logger.info("\nPress CTRL+C to stop the server")
    logger.info("=" * 80)
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
        monitor.stop()
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        monitor.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()

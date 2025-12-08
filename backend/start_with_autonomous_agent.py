
"""
Startup Script with Autonomous Goal-Driven Agent

Starts the application with full autonomous behavior capabilities.
Supports Windows service mode and static file serving.
"""

import os
import sys
import argparse
import json
import platform

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory
from flask_cors import CORS

from utils.logging import get_logger, setup_logging
from core.orchestrator_with_autonomous_agent import OrchestratorWithAutonomousAgent
from api.routes.autonomous_agent_routes import autonomous_agent_bp, set_agent_instance

# Setup logging
setup_logging()
logger = get_logger(__name__)


def get_config_path():
    """Get configuration path based on OS."""
    if platform.system() == 'Windows':
        # Windows: use ProgramData
        config_dir = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Powerhouse', 'config')
        config_path = os.path.join(config_dir, 'default.json')
        
        # Fallback to local config if ProgramData config doesn't exist
        if not os.path.exists(config_path):
            local_config = os.path.join(os.path.dirname(__file__), 'config', 'default.json')
            if os.path.exists(local_config):
                return local_config
        return config_path
    else:
        # Linux/Mac: use local config
        return os.path.join(os.path.dirname(__file__), 'config', 'default.json')


def get_log_path():
    """Get log path based on OS."""
    if platform.system() == 'Windows':
        # Windows: use ProgramData
        log_dir = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Powerhouse', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, 'powerhouse.log')
    else:
        # Linux/Mac: use local logs
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, 'powerhouse.log')


def create_app_with_autonomous_agent():
    """Create Flask application with autonomous agent."""
    # Check if web folder exists for serving frontend
    web_folder = os.path.join(os.path.dirname(__file__), 'web')
    has_frontend = os.path.isdir(web_folder)
    
    if has_frontend:
        app = Flask(__name__, static_folder='web', static_url_path='')
        logger.info(f"Frontend assets found at: {web_folder}")
    else:
        app = Flask(__name__)
        logger.info("No frontend assets found, API-only mode")
    
    CORS(app)
    
    # Configuration
    performance_config = {
        "alert_threshold": 0.7,
        "enable_auto_retraining": True,
        "retraining_threshold": 0.75
    }
    
    config_manager_config = {
        "enable_auto_adjustment": True,
        "adjustment_interval": 300  # 5 minutes
    }
    
    forecasting_config = {
        "auto_analysis_enabled": True,
        "analysis_interval_minutes": 60,
        "forecaster": {
            "default_method": "ensemble"
        },
        "pattern_recognizer": {
            "min_occurrences": 3,
            "time_window_hours": 168  # 1 week
        },
        "goal_setter": {
            "auto_goal_setting": True,
            "max_active_goals": 10
        }
    }
    
    executor_config = {
        "execution_interval_seconds": 60,
        "max_concurrent_goals": 3,
        "enable_learning": True
    }
    
    agent_config = {
        "autonomous_mode": True,
        "goal_sync_interval_seconds": 30,
        "analysis_interval_minutes": 60
    }
    
    # Initialize orchestrator with autonomous agent
    orchestrator = OrchestratorWithAutonomousAgent(
        performance_monitor_config=performance_config,
        config_manager_config=config_manager_config,
        forecasting_config=forecasting_config,
        executor_config=executor_config,
        agent_config=agent_config
    )
    
    # Set agent instance for API routes
    set_agent_instance(orchestrator.autonomous_agent)
    
    # Register blueprints
    app.register_blueprint(autonomous_agent_bp)
    
    # API routes
    @app.route('/health')
    def health():
        return {"status": "healthy", "autonomous_agent": "active"}, 200
    
    @app.route('/api')
    @app.route('/api/')
    def api_index():
        return {
            "service": "Powerhouse Multi-Agent Platform",
            "version": "3.0",
            "features": [
                "Autonomous Goal-Driven Behavior",
                "Predictive Forecasting",
                "Proactive Goal Setting",
                "Autonomous Execution",
                "Continuous Learning"
            ],
            "autonomous_agent": {
                "status": orchestrator.autonomous_agent.running,
                "active_goals": len(orchestrator.autonomous_agent.forecasting_engine.get_active_goals())
            }
        }, 200
    
    # Serve frontend if available
    if has_frontend:
        @app.route('/')
        def serve_index():
            index_path = os.path.join(app.static_folder, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(app.static_folder, 'index.html')
            # Fallback to API info if no frontend
            return api_index()
        
        @app.route('/<path:path>')
        def serve_static(path):
            # Try to serve the requested file
            full_path = os.path.join(app.static_folder, path)
            if os.path.exists(full_path) and os.path.isfile(full_path):
                return send_from_directory(app.static_folder, path)
            
            # For client-side routing, return index.html for non-API routes
            if not path.startswith('api/'):
                index_path = os.path.join(app.static_folder, 'index.html')
                if os.path.exists(index_path):
                    return send_from_directory(app.static_folder, 'index.html')
            
            # 404 for everything else
            return {"error": "Not found"}, 404
    else:
        # No frontend, just show API info
        @app.route('/')
        def index():
            return api_index()
    
    logger.info("Flask application with autonomous agent created")
    return app, orchestrator


def main():
    """Main entry point with CLI argument support."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Powerhouse B2B Multi-Agent Platform')
    parser.add_argument('--port', type=int, default=None,
                        help='Port to run the server on (default: from config or 5000)')
    parser.add_argument('--config', type=str, default=None,
                        help='Path to configuration file')
    parser.add_argument('--service', action='store_true',
                        help='Run as Windows service (suppresses some output)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to bind to (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = args.config or get_config_path()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from: {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
    else:
        logger.warning(f"Config file not found at {config_path}, using defaults")
    
    # Determine port
    port = args.port or config.get('server', {}).get('port') or int(os.environ.get('PORT', 5000))
    
    logger.info("=" * 80)
    logger.info("Starting Powerhouse Platform with Autonomous Goal-Driven Agent")
    logger.info(f"Platform: {platform.system()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Mode: {'Service' if args.service else 'Console'}")
    logger.info(f"Config: {config_path}")
    logger.info(f"Log: {get_log_path()}")
    logger.info("=" * 80)
    
    # Create app
    app, orchestrator = create_app_with_autonomous_agent()
    
    logger.info(f"Server starting on {args.host}:{port}")
    logger.info("Autonomous agent is ACTIVE and running")
    logger.info("=" * 80)
    
    try:
        app.run(host=args.host, port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
    finally:
        orchestrator.shutdown()
        logger.info("Shutdown complete")


if __name__ == '__main__':
    main()


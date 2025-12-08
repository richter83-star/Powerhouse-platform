"""
API routes package.
"""

# Import available route modules
try:
    from . import workflows
    HAS_WORKFLOWS = True
except ImportError:
    HAS_WORKFLOWS = False

try:
    from . import agents
    HAS_AGENTS = True
except ImportError:
    HAS_AGENTS = False

try:
    from . import auth
    HAS_AUTH = True
except ImportError:
    HAS_AUTH = False

try:
    from . import performance_routes
    HAS_PERFORMANCE = True
except ImportError:
    HAS_PERFORMANCE = False

try:
    from . import forecasting_routes
    HAS_FORECASTING = True
except ImportError:
    HAS_FORECASTING = False

try:
    from . import autonomous_agent_routes
    HAS_AUTONOMOUS = True
except ImportError:
    HAS_AUTONOMOUS = False

try:
    from . import file_management
    HAS_FILE_MANAGEMENT = True
except ImportError:
    HAS_FILE_MANAGEMENT = False

# Build __all__ dynamically based on what's available
__all__ = []
if HAS_WORKFLOWS:
    __all__.append("workflows")
if HAS_AGENTS:
    __all__.append("agents")
if HAS_AUTH:
    __all__.append("auth")
if HAS_PERFORMANCE:
    __all__.append("performance_routes")
if HAS_FORECASTING:
    __all__.append("forecasting_routes")
if HAS_AUTONOMOUS:
    __all__.append("autonomous_agent_routes")
if HAS_FILE_MANAGEMENT:
    __all__.append("file_management")


"""
Integration Ecosystem API Routes
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from ..core.integrations import (
    APICredentials,
    AuthType,
    DataFormat,
    ExportConfig,
    ImportConfig,
    PluginMetadata,
    RateLimitConfig,
    WebhookEvent,
    connector_registry,
    data_porter,
    plugin_loader,
    webhook_system,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ============================================================================
# Webhook Management
# ============================================================================

class WebhookSubscriptionCreate(BaseModel):
    url: str
    events: List[WebhookEvent]
    secret: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    max_retries: int = 3
    timeout: int = 30


class WebhookSubscriptionUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[List[WebhookEvent]] = None
    active: Optional[bool] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None


@router.post("/webhooks/subscriptions")
async def create_webhook_subscription(data: WebhookSubscriptionCreate):
    """Create a new webhook subscription"""
    subscription = webhook_system.create_subscription(
        url=data.url,
        events=data.events,
        secret=data.secret,
        headers=data.headers,
        max_retries=data.max_retries,
        timeout=data.timeout
    )
    return subscription


@router.get("/webhooks/subscriptions")
async def list_webhook_subscriptions(active_only: bool = False):
    """List all webhook subscriptions"""
    subscriptions = webhook_system.list_subscriptions(active_only=active_only)
    return {"subscriptions": subscriptions}


@router.get("/webhooks/subscriptions/{subscription_id}")
async def get_webhook_subscription(subscription_id: str):
    """Get webhook subscription by ID"""
    subscription = webhook_system.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.patch("/webhooks/subscriptions/{subscription_id}")
async def update_webhook_subscription(
    subscription_id: str,
    data: WebhookSubscriptionUpdate
):
    """Update webhook subscription"""
    update_data = data.model_dump(exclude_none=True)
    subscription = webhook_system.update_subscription(subscription_id, **update_data)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.delete("/webhooks/subscriptions/{subscription_id}")
async def delete_webhook_subscription(subscription_id: str):
    """Delete webhook subscription"""
    success = webhook_system.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"status": "deleted"}


class WebhookTrigger(BaseModel):
    event: WebhookEvent
    data: Dict


@router.post("/webhooks/trigger")
async def trigger_webhook(data: WebhookTrigger):
    """Manually trigger a webhook event"""
    deliveries = await webhook_system.trigger_event(data.event, data.data)
    return {
        "triggered": len(deliveries),
        "deliveries": deliveries
    }


@router.get("/webhooks/deliveries")
async def list_webhook_deliveries(
    subscription_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List webhook deliveries"""
    deliveries = webhook_system.list_deliveries(
        subscription_id=subscription_id,
        status=status
    )
    return {"deliveries": deliveries}


@router.get("/webhooks/deliveries/{delivery_id}")
async def get_webhook_delivery(delivery_id: str):
    """Get webhook delivery by ID"""
    delivery = webhook_system.get_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.get("/webhooks/events")
async def list_webhook_events():
    """List available webhook events"""
    return {
        "events": [event.value for event in WebhookEvent]
    }


# ============================================================================
# API Connectors
# ============================================================================

class ConnectorCreate(BaseModel):
    name: str
    base_url: str
    credentials: APICredentials
    rate_limit: Optional[RateLimitConfig] = None
    timeout: int = 30


@router.post("/connectors")
async def create_connector(data: ConnectorCreate):
    """Register a new API connector"""
    from ..core.integrations.api_connector import APIConnector
    
    # Create a generic connector
    class GenericConnector(APIConnector):
        async def test_connection(self) -> bool:
            try:
                await self.get("/")
                return True
            except:
                return False
    
    connector = GenericConnector(
        name=data.name,
        base_url=data.base_url,
        credentials=data.credentials,
        rate_limit=data.rate_limit,
        timeout=data.timeout
    )
    
    connector_registry.register(data.name, connector)
    
    return {
        "name": data.name,
        "status": "registered"
    }


@router.get("/connectors")
async def list_connectors():
    """List registered connectors"""
    return {
        "connectors": connector_registry.list()
    }


@router.get("/connectors/{name}")
async def get_connector(name: str):
    """Get connector details"""
    connector = connector_registry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    return {
        "name": connector.name,
        "base_url": connector.base_url,
        "auth_type": connector.credentials.auth_type,
        "rate_limit": connector.rate_limit
    }


@router.delete("/connectors/{name}")
async def delete_connector(name: str):
    """Unregister a connector"""
    success = connector_registry.unregister(name)
    if not success:
        raise HTTPException(status_code=404, detail="Connector not found")
    return {"status": "deleted"}


@router.post("/connectors/{name}/test")
async def test_connector(name: str):
    """Test connector connection"""
    connector = connector_registry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    success = await connector.test_connection()
    return {
        "name": name,
        "connected": success
    }


# ============================================================================
# Plugin Management
# ============================================================================

@router.get("/plugins/discover")
async def discover_plugins():
    """Discover available plugins"""
    plugins = plugin_loader.discover_plugins()
    return {
        "discovered": plugins,
        "count": len(plugins)
    }


@router.get("/plugins")
async def list_plugins(loaded_only: bool = False):
    """List plugins"""
    plugins = plugin_loader.list_plugins(loaded_only=loaded_only)
    statuses = {name: plugin_loader.get_status(name) for name in plugins}
    return {
        "plugins": plugins,
        "statuses": statuses
    }


@router.get("/plugins/{plugin_name}")
async def get_plugin_status(plugin_name: str):
    """Get plugin status"""
    status = plugin_loader.get_status(plugin_name)
    if not status:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return status


class PluginLoadRequest(BaseModel):
    config: Optional[Dict] = None


@router.post("/plugins/{plugin_name}/load")
async def load_plugin(plugin_name: str, data: PluginLoadRequest):
    """Load a plugin"""
    success = plugin_loader.load_plugin(plugin_name, data.config)
    if not success:
        status = plugin_loader.get_status(plugin_name)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load plugin: {status.error if status else 'Unknown error'}"
        )
    return {"status": "loaded"}


@router.post("/plugins/{plugin_name}/unload")
async def unload_plugin(plugin_name: str):
    """Unload a plugin"""
    success = plugin_loader.unload_plugin(plugin_name)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not loaded")
    return {"status": "unloaded"}


@router.post("/plugins/{plugin_name}/reload")
async def reload_plugin(plugin_name: str, data: PluginLoadRequest):
    """Reload a plugin"""
    success = plugin_loader.reload_plugin(plugin_name, data.config)
    if not success:
        status = plugin_loader.get_status(plugin_name)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to reload plugin: {status.error if status else 'Unknown error'}"
        )
    return {"status": "reloaded"}


class PluginExecuteRequest(BaseModel):
    args: List = []
    kwargs: Dict = {}


@router.post("/plugins/{plugin_name}/execute")
async def execute_plugin(plugin_name: str, data: PluginExecuteRequest):
    """Execute plugin logic"""
    try:
        result = plugin_loader.execute_plugin(
            plugin_name,
            *data.args,
            **data.kwargs
        )
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Data Import/Export
# ============================================================================

class DataExportRequest(BaseModel):
    data: List[Dict]
    config: ExportConfig


@router.post("/data/export")
async def export_data(request: DataExportRequest):
    """Export data to specified format"""
    output, result = await data_porter.export_data(
        request.data,
        request.config
    )
    
    # Determine content type
    content_type_map = {
        DataFormat.JSON: "application/json",
        DataFormat.CSV: "text/csv",
        DataFormat.JSONL: "application/x-ndjson"
    }
    
    content_type = content_type_map.get(request.config.format, "application/octet-stream")
    
    return Response(
        content=output,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename=export.{request.config.format.value}"
        }
    )


@router.post("/data/import")
async def import_data(
    file: UploadFile = File(...),
    format: DataFormat = DataFormat.JSON,
    validate: bool = True,
    skip_errors: bool = False
):
    """Import data from uploaded file"""
    content = await file.read()
    
    config = ImportConfig(
        format=format,
        validate=validate,
        skip_errors=skip_errors
    )
    
    records, result = await data_porter.import_data(content, config)
    
    return {
        "result": result,
        "records": records if result.successful > 0 else []
    }


@router.get("/data/import/history")
async def get_import_history():
    """Get import history"""
    return {
        "history": data_porter.get_import_history()
    }


@router.get("/data/export/history")
async def get_export_history():
    """Get export history"""
    return {
        "history": data_porter.get_export_history()
    }


# ============================================================================
# Integration Health
# ============================================================================

@router.get("/health")
async def integration_health():
    """Get integration ecosystem health status"""
    return {
        "webhooks": {
            "subscriptions": len(webhook_system.list_subscriptions(active_only=True)),
            "total_deliveries": len(webhook_system.list_deliveries())
        },
        "connectors": {
            "registered": len(connector_registry.list())
        },
        "plugins": {
            "discovered": len(plugin_loader.list_plugins()),
            "loaded": len(plugin_loader.list_plugins(loaded_only=True))
        },
        "data_operations": {
            "imports": len(data_porter.get_import_history()),
            "exports": len(data_porter.get_export_history())
        },
        "timestamp": datetime.utcnow().isoformat()
    }

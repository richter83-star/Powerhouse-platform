
"""
App Builder API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime

router = APIRouter()

class AppComponent(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    type: str  # button, input, chart, table, etc.
    properties: Dict[str, Any]
    position: Dict[str, int]  # x, y
    size: Dict[str, int]  # width, height

class AppConfig(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: str
    description: str
    components: List[AppComponent]
    layout: str  # grid, flex, custom
    theme: Optional[Dict[str, Any]] = {}
    data_sources: Optional[List[Dict[str, Any]]] = []
    workflows: Optional[List[Dict[str, Any]]] = []

class CustomApp(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    name: str
    description: str
    app_config: Dict[str, Any]
    preview_url: Optional[str]
    is_public: bool
    created_at: datetime

# Mock storage
custom_apps_db = []

@router.post("/app-builder/create")
async def create_app(config: AppConfig):
    """Create a new custom app"""
    app = {
        "id": len(custom_apps_db) + 1,
        "user_id": 1,  # Get from auth
        "name": config.name,
        "description": config.description,
        "app_config": config.model_dump(),
        "preview_url": None,
        "is_public": False,
        "created_at": datetime.now().isoformat()
    }
    
    custom_apps_db.append(app)
    
    return {
        "app": app,
        "message": "App created successfully"
    }

@router.get("/app-builder/my-apps")
async def get_my_apps():
    """Get user's custom apps"""
    user_apps = [a for a in custom_apps_db if a["user_id"] == 1]
    return {"apps": user_apps}

@router.get("/app-builder/app/{app_id}")
async def get_app(app_id: int):
    """Get app details"""
    app = next((a for a in custom_apps_db if a["id"] == app_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    return app

@router.put("/app-builder/app/{app_id}")
async def update_app(app_id: int, config: AppConfig):
    """Update custom app"""
    app = next((a for a in custom_apps_db if a["id"] == app_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    app.update({
        "name": config.name,
        "description": config.description,
        "app_config": config.model_dump()
    })
    
    return {"app": app, "message": "App updated successfully"}

@router.delete("/app-builder/app/{app_id}")
async def delete_app(app_id: int):
    """Delete custom app"""
    global custom_apps_db
    custom_apps_db = [a for a in custom_apps_db if a["id"] != app_id]
    return {"message": "App deleted successfully"}

@router.get("/app-builder/components")
async def get_available_components():
    """Get available UI components"""
    components = [
        {
            "type": "button",
            "name": "Button",
            "icon": "⬜",
            "category": "basic",
            "properties": {
                "label": "Click Me",
                "variant": "primary",
                "onClick": ""
            }
        },
        {
            "type": "input",
            "name": "Text Input",
            "icon": "📝",
            "category": "forms",
            "properties": {
                "placeholder": "Enter text",
                "type": "text",
                "required": False
            }
        },
        {
            "type": "chart",
            "name": "Chart",
            "icon": "📊",
            "category": "data",
            "properties": {
                "chartType": "bar",
                "data": [],
                "title": "Chart Title"
            }
        },
        {
            "type": "table",
            "name": "Data Table",
            "icon": "📋",
            "category": "data",
            "properties": {
                "columns": [],
                "data": [],
                "sortable": True
            }
        },
        {
            "type": "card",
            "name": "Card",
            "icon": "🎴",
            "category": "layout",
            "properties": {
                "title": "Card Title",
                "content": "",
                "variant": "default"
            }
        },
        {
            "type": "text",
            "name": "Text",
            "icon": "📄",
            "category": "basic",
            "properties": {
                "content": "Sample text",
                "size": "medium",
                "weight": "normal"
            }
        },
        {
            "type": "image",
            "name": "Image",
            "icon": "🖼️",
            "category": "media",
            "properties": {
                "src": "",
                "alt": "Image",
                "width": "100%"
            }
        },
        {
            "type": "form",
            "name": "Form",
            "icon": "📋",
            "category": "forms",
            "properties": {
                "fields": [],
                "submitLabel": "Submit"
            }
        },
        {
            "type": "agent_widget",
            "name": "AI Agent",
            "icon": "🤖",
            "category": "ai",
            "properties": {
                "agent_id": None,
                "display": "chat"
            }
        },
        {
            "type": "workflow_trigger",
            "name": "Workflow Button",
            "icon": "⚡",
            "category": "automation",
            "properties": {
                "workflow_id": None,
                "label": "Run Workflow"
            }
        }
    ]
    return {"components": components}

@router.get("/app-builder/templates")
async def get_app_templates():
    """Get pre-built app templates"""
    templates = [
        {
            "id": 1,
            "name": "Dashboard",
            "description": "Analytics dashboard with charts and metrics",
            "thumbnail": "/templates/dashboard.png",
            "components": ["chart", "card", "table"],
            "complexity": "medium"
        },
        {
            "id": 2,
            "name": "CRM",
            "description": "Customer relationship management app",
            "thumbnail": "/templates/crm.png",
            "components": ["table", "form", "card"],
            "complexity": "high"
        },
        {
            "id": 3,
            "name": "Landing Page",
            "description": "Marketing landing page",
            "thumbnail": "/templates/landing.png",
            "components": ["text", "image", "button", "form"],
            "complexity": "low"
        },
        {
            "id": 4,
            "name": "AI Chat App",
            "description": "Chat interface with AI agent",
            "thumbnail": "/templates/chat.png",
            "components": ["agent_widget", "card"],
            "complexity": "medium"
        }
    ]
    return {"templates": templates}

@router.post("/app-builder/app/{app_id}/publish")
async def publish_app(app_id: int, price: Optional[float] = None):
    """Publish app to marketplace"""
    app = next((a for a in custom_apps_db if a["id"] == app_id), None)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")
    
    app["is_public"] = True
    
    # Create marketplace listing if price provided
    if price:
        # This would create a marketplace listing
        pass
    
    return {"message": "App published successfully", "app": app}

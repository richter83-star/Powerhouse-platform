"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { LayoutDashboard, Save, Eye, Upload, Plus, Trash2, Settings2 } from "lucide-react";
import { toast } from "sonner";

interface Component {
  id: string;
  type: string;
  properties: any;
  position: { x: number; y: number };
  size: { width: number; height: number };
}

export default function AppBuilderPage() {
  const [appName, setAppName] = useState("");
  const [appDescription, setAppDescription] = useState("");
  const [components, setComponents] = useState<Component[]>([]);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const componentTypes = [
    { type: "button", name: "Button", icon: "⬜" },
    { type: "input", name: "Text Input", icon: "📝" },
    { type: "chart", name: "Chart", icon: "📊" },
    { type: "table", name: "Table", icon: "📋" },
    { type: "card", name: "Card", icon: "🎴" },
    { type: "text", name: "Text", icon: "📄" },
    { type: "agent_widget", name: "AI Agent", icon: "🤖" },
  ];

  const addComponent = (type: string) => {
    const newComponent: Component = {
      id: `${type}-${Date.now()}`,
      type,
      properties: {},
      position: { x: 50, y: 50 },
      size: { width: 200, height: 100 }
    };
    setComponents([...components, newComponent]);
    toast.success(`${type} added to canvas`);
  };

  const removeComponent = (id: string) => {
    setComponents(components.filter(c => c.id !== id));
    toast.success("Component removed");
  };

  const handleSave = async () => {
    if (!appName) {
      toast.error("Please enter an app name");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/app-builder/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: appName,
          description: appDescription,
          components: components.map(c => ({
            id: c.id,
            type: c.type,
            properties: c.properties,
            position: c.position,
            size: c.size
          })),
          layout: "grid",
          theme: {},
          data_sources: [],
          workflows: []
        })
      });

      if (response.ok) {
        toast.success("App saved successfully!");
      } else {
        toast.error("Failed to save app");
      }
    } catch (error) {
      console.error("Failed to save app:", error);
      toast.error("Failed to save app");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-slate-950 p-4">
        <div className="flex items-center justify-between max-w-[1800px] mx-auto">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              App Builder
            </h1>
            <p className="text-sm text-muted-foreground">Drag and drop visual app builder</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Eye className="h-4 w-4 mr-2" />
              Preview
            </Button>
            <Button onClick={handleSave} disabled={saving || !appName} size="sm">
              <Save className="h-4 w-4 mr-2" />
              {saving ? "Saving..." : "Save App"}
            </Button>
            <Button className="bg-gradient-to-r from-blue-600 to-purple-600" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Publish
            </Button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Components */}
        <div className="w-64 border-r bg-slate-50 p-4 overflow-y-auto">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="app-name">App Name</Label>
              <Input
                id="app-name"
                placeholder="My App"
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="app-desc">Description</Label>
              <Textarea
                id="app-desc"
                placeholder="Describe your app..."
                value={appDescription}
                onChange={(e) => setAppDescription(e.target.value)}
                rows={2}
              />
            </div>

            <div className="pt-4 border-t">
              <h3 className="font-semibold mb-3">Components</h3>
              <div className="space-y-2">
                {componentTypes.map((comp) => (
                  <Button
                    key={comp.type}
                    variant="outline"
                    className="w-full justify-start"
                    size="sm"
                    onClick={() => addComponent(comp.type)}
                  >
                    <span className="mr-2">{comp.icon}</span>
                    {comp.name}
                    <Plus className="h-3 w-3 ml-auto" />
                  </Button>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t">
              <h3 className="font-semibold mb-3">Templates</h3>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start" size="sm">
                  📊 Dashboard
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  📋 CRM
                </Button>
                <Button variant="outline" className="w-full justify-start" size="sm">
                  🤖 AI Chat
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Canvas */}
        <div className="flex-1 bg-white p-8 overflow-auto">
          <div className="min-h-full border-2 border-dashed border-gray-300 rounded-lg p-8">
            {components.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center">
                <LayoutDashboard className="h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 mb-2">Start Building Your App</h3>
                <p className="text-gray-500">
                  Drag components from the left panel or click to add them to your canvas
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {components.map((component) => (
                  <Card
                    key={component.id}
                    className={`cursor-pointer transition-all ${
                      selectedComponent === component.id ? "ring-2 ring-blue-500" : ""
                    }`}
                    onClick={() => setSelectedComponent(component.id)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <Badge variant="secondary">{component.type}</Badge>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeComponent(component.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        {component.type.replace(/_/g, " ")} component
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar - Properties */}
        <div className="w-64 border-l bg-slate-50 p-4 overflow-y-auto">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Settings2 className="h-4 w-4" />
            Properties
          </h3>
          
          {selectedComponent ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Component ID</Label>
                <Input value={selectedComponent} disabled />
              </div>
              
              <div className="space-y-2">
                <Label>Width</Label>
                <Input type="number" placeholder="200" />
              </div>
              
              <div className="space-y-2">
                <Label>Height</Label>
                <Input type="number" placeholder="100" />
              </div>
              
              <div className="space-y-2">
                <Label>Style</Label>
                <Button variant="outline" size="sm" className="w-full">
                  Edit Styles
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-8">
              Select a component to edit its properties
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

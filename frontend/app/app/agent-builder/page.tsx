"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Bot, Sparkles, TrendingUp, DollarSign, Save, Upload, Code, Brain, Zap } from "lucide-react";
import { toast } from "sonner";

interface AgentConfig {
  name: string;
  description: string;
  agent_type: string;
  capabilities: string[];
  tools: string[];
  memory_enabled: boolean;
  multi_step: boolean;
  custom_logic: string;
  api_integrations: string[];
  learning_capability: boolean;
  reasoning_depth: number;
  collaboration: boolean;
}

interface PricingInfo {
  complexity_score: number;
  tier_name: string;
  suggested_price: number;
  min_price: number;
  max_price: number;
}

const AGENT_TYPES = [
  { value: "chatbot", label: "Chatbot", icon: "💬" },
  { value: "automation", label: "Automation", icon: "⚙️" },
  { value: "analytics", label: "Analytics", icon: "📊" },
  { value: "research", label: "Research", icon: "🔍" },
  { value: "creative", label: "Creative", icon: "🎨" },
];

const AVAILABLE_TOOLS = [
  "web_search", "data_analysis", "file_processing", "api_calls", 
  "email", "calendar", "database", "image_generation", "code_execution"
];

const AVAILABLE_INTEGRATIONS = [
  "openai", "anthropic", "google", "salesforce", "slack", "stripe"
];

export default function AgentBuilderPage() {
  const [config, setConfig] = useState<AgentConfig>({
    name: "",
    description: "",
    agent_type: "chatbot",
    capabilities: [],
    tools: [],
    memory_enabled: false,
    multi_step: false,
    custom_logic: "",
    api_integrations: [],
    learning_capability: false,
    reasoning_depth: 1,
    collaboration: false,
  });

  const [pricing, setPricing] = useState<PricingInfo | null>(null);
  const [calculating, setCalculating] = useState(false);
  const [saving, setSaving] = useState(false);

  // Calculate pricing whenever config changes
  useEffect(() => {
    const debounce = setTimeout(() => {
      if (config.name && config.agent_type) {
        calculatePricing();
      }
    }, 500);

    return () => clearTimeout(debounce);
  }, [config]);

  const calculatePricing = async () => {
    setCalculating(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/agent-builder/calculate-pricing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        const data = await response.json();
        setPricing(data.pricing);
      }
    } catch (error) {
      console.error("Failed to calculate pricing:", error);
    } finally {
      setCalculating(false);
    }
  };

  const handleSaveAgent = async () => {
    if (!config.name || !config.description) {
      toast.error("Please provide agent name and description");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch("http://localhost:8000/api/v1/agent-builder/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        const data = await response.json();
        toast.success("Agent created successfully!");
        // Reset form or navigate to agent list
      } else {
        toast.error("Failed to create agent");
      }
    } catch (error) {
      console.error("Failed to save agent:", error);
      toast.error("Failed to create agent");
    } finally {
      setSaving(false);
    }
  };

  const toggleTool = (tool: string) => {
    setConfig(prev => ({
      ...prev,
      tools: prev.tools.includes(tool)
        ? prev.tools.filter(t => t !== tool)
        : [...prev.tools, tool]
    }));
  };

  const toggleIntegration = (integration: string) => {
    setConfig(prev => ({
      ...prev,
      api_integrations: prev.api_integrations.includes(integration)
        ? prev.api_integrations.filter(i => i !== integration)
        : [...prev.api_integrations, integration]
    }));
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Agent Builder
          </h1>
          <p className="text-muted-foreground">
            Create custom AI agents with intelligent pricing based on complexity
          </p>
        </div>
        <Button
          onClick={handleSaveAgent}
          disabled={saving || !config.name}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
        >
          <Save className="h-4 w-4 mr-2" />
          {saving ? "Saving..." : "Save Agent"}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5" />
                Basic Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Agent Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Customer Support Assistant"
                  value={config.name}
                  onChange={(e) => setConfig({ ...config, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what your agent does..."
                  value={config.description}
                  onChange={(e) => setConfig({ ...config, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="agent_type">Agent Type</Label>
                <Select value={config.agent_type} onValueChange={(value) => setConfig({ ...config, agent_type: value })}>
                  <SelectTrigger id="agent_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AGENT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.icon} {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Tools & Capabilities */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Tools & Capabilities
              </CardTitle>
              <CardDescription>
                Select the tools your agent can use (affects pricing)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {AVAILABLE_TOOLS.map((tool) => (
                  <Button
                    key={tool}
                    variant={config.tools.includes(tool) ? "default" : "outline"}
                    size="sm"
                    onClick={() => toggleTool(tool)}
                    className="justify-start"
                  >
                    {config.tools.includes(tool) && "✓ "}
                    {tool.replace(/_/g, " ")}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Advanced Features */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Advanced Features
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Memory Enabled</Label>
                  <p className="text-sm text-muted-foreground">Agent remembers conversation history</p>
                </div>
                <Switch
                  checked={config.memory_enabled}
                  onCheckedChange={(checked) => setConfig({ ...config, memory_enabled: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Multi-Step Reasoning</Label>
                  <p className="text-sm text-muted-foreground">Agent can break down complex tasks</p>
                </div>
                <Switch
                  checked={config.multi_step}
                  onCheckedChange={(checked) => setConfig({ ...config, multi_step: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Learning Capability</Label>
                  <p className="text-sm text-muted-foreground">Agent improves from feedback</p>
                </div>
                <Switch
                  checked={config.learning_capability}
                  onCheckedChange={(checked) => setConfig({ ...config, learning_capability: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Collaboration</Label>
                  <p className="text-sm text-muted-foreground">Can work with other agents</p>
                </div>
                <Switch
                  checked={config.collaboration}
                  onCheckedChange={(checked) => setConfig({ ...config, collaboration: checked })}
                />
              </div>

              <div className="space-y-2">
                <Label>Reasoning Depth: {config.reasoning_depth}</Label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={config.reasoning_depth}
                  onChange={(e) => setConfig({ ...config, reasoning_depth: parseInt(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Basic</span>
                  <span>Deep</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Integrations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                API Integrations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {AVAILABLE_INTEGRATIONS.map((integration) => (
                  <Button
                    key={integration}
                    variant={config.api_integrations.includes(integration) ? "default" : "outline"}
                    size="sm"
                    onClick={() => toggleIntegration(integration)}
                    className="justify-start"
                  >
                    {config.api_integrations.includes(integration) && "✓ "}
                    {integration}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pricing Panel */}
        <div className="space-y-6">
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                Pricing Calculator
              </CardTitle>
              <CardDescription>
                Based on agent complexity
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {calculating ? (
                <div className="flex justify-center items-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                </div>
              ) : pricing ? (
                <>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Complexity Score</span>
                      <Badge variant="secondary" className="text-lg">
                        {pricing.complexity_score}/10
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Tier</span>
                      <Badge className="bg-gradient-to-r from-purple-600 to-pink-600">
                        {pricing.tier_name}
                      </Badge>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="text-center space-y-2">
                        <p className="text-sm text-muted-foreground">Suggested Price</p>
                        <p className="text-4xl font-bold text-purple-600">
                          ${pricing.suggested_price.toFixed(2)}
                        </p>
                      </div>
                    </div>

                    <div className="pt-4 border-t text-sm space-y-2">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Min Price</span>
                        <span>${pricing.min_price.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Max Price</span>
                        <span>${pricing.max_price.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-purple-50 rounded-lg space-y-2">
                    <p className="text-sm font-medium text-purple-900">Platform Fee</p>
                    <p className="text-xs text-purple-700">
                      15% commission on sales
                    </p>
                    <p className="text-sm text-purple-900">
                      You earn: ${(pricing.suggested_price * 0.85).toFixed(2)}
                    </p>
                  </div>
                </>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <p>Configure your agent to see pricing</p>
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                disabled={!pricing}
              >
                <Upload className="h-4 w-4 mr-2" />
                Publish to Marketplace
              </Button>
            </CardFooter>
          </Card>

          {/* Complexity Breakdown */}
          {pricing && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Complexity Factors</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tools</span>
                  <span>{config.tools.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Memory</span>
                  <span>{config.memory_enabled ? "✓" : "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Multi-Step</span>
                  <span>{config.multi_step ? "✓" : "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Integrations</span>
                  <span>{config.api_integrations.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Learning</span>
                  <span>{config.learning_capability ? "✓" : "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Reasoning Depth</span>
                  <span>{config.reasoning_depth}/5</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Collaboration</span>
                  <span>{config.collaboration ? "✓" : "—"}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

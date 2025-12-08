
"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  Webhook, 
  Plug, 
  Package, 
  Database,
  Plus,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Download,
  Upload,
  Play,
  Settings
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';

// Types
interface WebhookSubscription {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  created_at: string;
}

interface WebhookDelivery {
  id: string;
  subscription_id: string;
  status: string;
  attempts: number;
  last_attempt?: string;
  response_code?: number;
}

interface Connector {
  name: string;
  base_url: string;
  auth_type: string;
  connected?: boolean;
}

interface Plugin {
  name: string;
  version: string;
  loaded: boolean;
  enabled: boolean;
  error?: string;
}

interface IntegrationHealth {
  webhooks: { subscriptions: number; total_deliveries: number };
  connectors: { registered: number };
  plugins: { discovered: number; loaded: number };
  data_operations: { imports: number; exports: number };
}

export default function IntegrationsPage() {
  const [health, setHealth] = useState<IntegrationHealth | null>(null);
  const [activeTab, setActiveTab] = useState('webhooks');

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/integrations/health');
      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      }
    } catch (error) {
      console.error('Failed to fetch integration health:', error);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Integration Ecosystem</h1>
          <p className="text-muted-foreground mt-2">
            Manage webhooks, API connectors, plugins, and data operations
          </p>
        </div>
        <Button onClick={fetchHealth} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Health Overview */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Webhooks</CardTitle>
              <Webhook className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{health.webhooks.subscriptions}</div>
              <p className="text-xs text-muted-foreground">
                {health.webhooks.total_deliveries} deliveries
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Connectors</CardTitle>
              <Plug className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{health.connectors.registered}</div>
              <p className="text-xs text-muted-foreground">
                registered connectors
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Plugins</CardTitle>
              <Package className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{health.plugins.loaded}</div>
              <p className="text-xs text-muted-foreground">
                of {health.plugins.discovered} discovered
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Data Operations</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {health.data_operations.imports + health.data_operations.exports}
              </div>
              <p className="text-xs text-muted-foreground">
                {health.data_operations.imports} imports, {health.data_operations.exports} exports
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="webhooks">
            <Webhook className="w-4 h-4 mr-2" />
            Webhooks
          </TabsTrigger>
          <TabsTrigger value="connectors">
            <Plug className="w-4 h-4 mr-2" />
            Connectors
          </TabsTrigger>
          <TabsTrigger value="plugins">
            <Package className="w-4 h-4 mr-2" />
            Plugins
          </TabsTrigger>
          <TabsTrigger value="data">
            <Database className="w-4 h-4 mr-2" />
            Data Porter
          </TabsTrigger>
        </TabsList>

        <TabsContent value="webhooks">
          <WebhooksPanel />
        </TabsContent>

        <TabsContent value="connectors">
          <ConnectorsPanel />
        </TabsContent>

        <TabsContent value="plugins">
          <PluginsPanel />
        </TabsContent>

        <TabsContent value="data">
          <DataPorterPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Webhooks Panel
function WebhooksPanel() {
  const [subscriptions, setSubscriptions] = useState<WebhookSubscription[]>([]);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  useEffect(() => {
    fetchSubscriptions();
    fetchDeliveries();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      const response = await fetch('http://localhost:8000/integrations/webhooks/subscriptions');
      if (response.ok) {
        const data = await response.json();
        setSubscriptions(data.subscriptions || []);
      }
    } catch (error) {
      console.error('Failed to fetch subscriptions:', error);
    }
  };

  const fetchDeliveries = async () => {
    try {
      const response = await fetch('http://localhost:8000/integrations/webhooks/deliveries');
      if (response.ok) {
        const data = await response.json();
        setDeliveries(data.deliveries || []);
      }
    } catch (error) {
      console.error('Failed to fetch deliveries:', error);
    }
  };

  const deleteSubscription = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/integrations/webhooks/subscriptions/${id}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        toast.success('Subscription deleted successfully');
        fetchSubscriptions();
      } else {
        toast.error('Failed to delete subscription');
      }
    } catch (error) {
      toast.error('Failed to delete subscription');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'retrying':
        return <RefreshCw className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Webhook Subscriptions</CardTitle>
              <CardDescription>Manage webhook subscriptions for event-driven integrations</CardDescription>
            </div>
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Subscription
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Webhook Subscription</DialogTitle>
                  <DialogDescription>
                    Configure a new webhook subscription to receive events
                  </DialogDescription>
                </DialogHeader>
                <CreateWebhookForm
                  onSuccess={() => {
                    setShowCreateDialog(false);
                    fetchSubscriptions();
                  }}
                />
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {subscriptions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No webhook subscriptions configured
              </div>
            ) : (
              subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <code className="text-sm font-mono">{sub.url}</code>
                      <Badge variant={sub.active ? 'default' : 'secondary'}>
                        {sub.active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2 mt-2">
                      {sub.events.map((event) => (
                        <Badge key={event} variant="outline" className="text-xs">
                          {event}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Created: {new Date(sub.created_at).toLocaleString()}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteSubscription(sub.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Deliveries</CardTitle>
          <CardDescription>Track webhook delivery status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {deliveries.slice(0, 10).map((delivery) => (
              <div
                key={delivery.id}
                className="flex items-center justify-between p-3 border rounded"
              >
                <div className="flex items-center space-x-3">
                  {getStatusIcon(delivery.status)}
                  <div>
                    <p className="text-sm font-medium">
                      Delivery {delivery.id.slice(0, 8)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {delivery.attempts} attempt(s)
                      {delivery.response_code && ` • HTTP ${delivery.response_code}`}
                    </p>
                  </div>
                </div>
                <Badge variant={
                  delivery.status === 'delivered' ? 'default' :
                  delivery.status === 'failed' ? 'destructive' :
                  'secondary'
                }>
                  {delivery.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CreateWebhookForm({ onSuccess }: { onSuccess: () => void }) {
  const [url, setUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [availableEvents, setAvailableEvents] = useState<string[]>([]);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:8000/integrations/webhooks/events');
      if (response.ok) {
        const data = await response.json();
        setAvailableEvents(data.events || []);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/integrations/webhooks/subscriptions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, events: selectedEvents }),
      });
      
      if (response.ok) {
        toast.success('Webhook subscription created successfully');
        onSuccess();
      } else {
        toast.error('Failed to create subscription');
      }
    } catch (error) {
      toast.error('Failed to create subscription');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label>Webhook URL</Label>
        <Input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/webhook"
          required
        />
      </div>
      <div>
        <Label>Events</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {availableEvents.map((event) => (
            <label key={event} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedEvents.includes(event)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedEvents([...selectedEvents, event]);
                  } else {
                    setSelectedEvents(selectedEvents.filter((e) => e !== event));
                  }
                }}
              />
              <span className="text-sm">{event}</span>
            </label>
          ))}
        </div>
      </div>
      <Button type="submit" className="w-full">
        Create Subscription
      </Button>
    </form>
  );
}

// Connectors Panel
function ConnectorsPanel() {
  const [connectors, setConnectors] = useState<Connector[]>([]);

  useEffect(() => {
    fetchConnectors();
  }, []);

  const fetchConnectors = async () => {
    try {
      const response = await fetch('http://localhost:8000/integrations/connectors');
      if (response.ok) {
        const data = await response.json();
        setConnectors(data.connectors?.map((name: string) => ({ name, base_url: '', auth_type: 'api_key' })) || []);
      }
    } catch (error) {
      console.error('Failed to fetch connectors:', error);
    }
  };

  const testConnector = async (name: string) => {
    try {
      const response = await fetch(`http://localhost:8000/integrations/connectors/${name}/test`, {
        method: 'POST',
      });
      if (response.ok) {
        const data = await response.json();
        toast.success(data.connected ? 'Connection successful' : 'Connection failed');
        fetchConnectors();
      }
    } catch (error) {
      toast.error('Failed to test connector');
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>API Connectors</CardTitle>
            <CardDescription>Manage third-party API integrations</CardDescription>
          </div>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Add Connector
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {connectors.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No connectors configured
            </div>
          ) : (
            connectors.map((connector) => (
              <div
                key={connector.name}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <Plug className="w-8 h-8 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{connector.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {connector.auth_type}
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => testConnector(connector.name)}
                >
                  Test Connection
                </Button>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Plugins Panel
function PluginsPanel() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const response = await fetch('http://localhost:8000/integrations/plugins');
      if (response.ok) {
        const data = await response.json();
        const pluginsData = data.plugins || [];
        const statuses = data.statuses || {};
        
        const pluginsWithStatus = pluginsData.map((name: string) => ({
          name,
          version: statuses[name]?.version || '1.0.0',
          loaded: statuses[name]?.loaded || false,
          enabled: statuses[name]?.enabled || false,
          error: statuses[name]?.error,
        }));
        
        setPlugins(pluginsWithStatus);
      }
    } catch (error) {
      console.error('Failed to fetch plugins:', error);
    }
  };

  const loadPlugin = async (name: string) => {
    try {
      const response = await fetch(`http://localhost:8000/integrations/plugins/${name}/load`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: {} }),
      });
      
      if (response.ok) {
        toast.success('Plugin loaded successfully');
        fetchPlugins();
      } else {
        toast.error('Failed to load plugin');
      }
    } catch (error) {
      toast.error('Failed to load plugin');
    }
  };

  const unloadPlugin = async (name: string) => {
    try {
      const response = await fetch(`http://localhost:8000/integrations/plugins/${name}/unload`, {
        method: 'POST',
      });
      
      if (response.ok) {
        toast.success('Plugin unloaded successfully');
        fetchPlugins();
      } else {
        toast.error('Failed to unload plugin');
      }
    } catch (error) {
      toast.error('Failed to unload plugin');
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Plugin System</CardTitle>
            <CardDescription>Manage dynamic plugins and extensions</CardDescription>
          </div>
          <Button onClick={fetchPlugins}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Discover Plugins
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {plugins.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No plugins discovered
            </div>
          ) : (
            plugins.map((plugin) => (
              <div
                key={plugin.name}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <Package className="w-8 h-8 text-muted-foreground" />
                  <div>
                    <div className="flex items-center space-x-2">
                      <p className="font-medium">{plugin.name}</p>
                      <Badge variant="outline">{plugin.version}</Badge>
                      {plugin.loaded && (
                        <Badge variant="default">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Loaded
                        </Badge>
                      )}
                    </div>
                    {plugin.error && (
                      <p className="text-sm text-red-500 mt-1">{plugin.error}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {plugin.loaded ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => unloadPlugin(plugin.name)}
                    >
                      Unload
                    </Button>
                  ) : (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => loadPlugin(plugin.name)}
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Load
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Data Porter Panel
function DataPorterPanel() {
  const [importHistory, setImportHistory] = useState<any[]>([]);
  const [exportHistory, setExportHistory] = useState<any[]>([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const [importRes, exportRes] = await Promise.all([
        fetch('http://localhost:8000/integrations/data/import/history'),
        fetch('http://localhost:8000/integrations/data/export/history'),
      ]);
      
      if (importRes.ok && exportRes.ok) {
        const importData = await importRes.json();
        const exportData = await exportRes.json();
        setImportHistory(importData.history || []);
        setExportHistory(exportData.history || []);
      }
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  const handleImport = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', 'json');

    try {
      const response = await fetch('http://localhost:8000/integrations/data/import', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`Imported ${data.result.successful} records successfully`);
        fetchHistory();
      } else {
        toast.error('Failed to import data');
      }
    } catch (error) {
      toast.error('Failed to import data');
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Import Data</CardTitle>
            <CardDescription>Upload and import data from files</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="border-2 border-dashed rounded-lg p-8 text-center">
                <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-sm text-muted-foreground mb-4">
                  Drag and drop or click to upload
                </p>
                <Input
                  type="file"
                  accept=".json,.csv,.jsonl"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleImport(file);
                  }}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Supported formats: JSON, CSV, JSONL
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Export Data</CardTitle>
            <CardDescription>Export data in various formats</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label>Export Format</Label>
                <Select defaultValue="json">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="json">JSON</SelectItem>
                    <SelectItem value="csv">CSV</SelectItem>
                    <SelectItem value="jsonl">JSONL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button className="w-full">
                <Download className="w-4 h-4 mr-2" />
                Export Data
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Operation History</CardTitle>
          <CardDescription>Track import and export operations</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="imports">
            <TabsList>
              <TabsTrigger value="imports">Imports ({importHistory.length})</TabsTrigger>
              <TabsTrigger value="exports">Exports ({exportHistory.length})</TabsTrigger>
            </TabsList>
            <TabsContent value="imports" className="space-y-2">
              {importHistory.slice(0, 5).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <p className="text-sm font-medium">
                      {item.successful} of {item.total_records} records
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {item.failed} failed • {item.duration_seconds.toFixed(2)}s
                    </p>
                  </div>
                  {item.successful === item.total_records ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-yellow-500" />
                  )}
                </div>
              ))}
            </TabsContent>
            <TabsContent value="exports" className="space-y-2">
              {exportHistory.slice(0, 5).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 border rounded">
                  <div>
                    <p className="text-sm font-medium">
                      {item.total_records} records • {(item.file_size_bytes / 1024).toFixed(1)} KB
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {item.format} • {item.duration_seconds.toFixed(2)}s
                    </p>
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

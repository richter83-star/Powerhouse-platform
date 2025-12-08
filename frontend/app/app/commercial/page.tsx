
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Building2, DollarSign, TrendingUp, Users, Package, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

interface Tenant {
  tenant_id: string;
  name: string;
  tier: string;
  created_at: string;
  is_active: boolean;
  limits: {
    max_agents: number;
    max_workflows: number;
    max_api_calls_per_hour: number;
    storage_limit_gb: number;
  };
  features: string[];
}

interface UsageSummary {
  tenant_id: string;
  start_date: string;
  end_date: string;
  api_calls: number;
  agent_executions: number;
  workflow_runs: number;
  storage_gb: number;
  compute_hours: number;
  total_cost: number;
  breakdown: Record<string, number>;
}

interface BillEstimate {
  tenant_id: string;
  current_month_cost: number;
  projected_month_cost: number;
  days_elapsed: number;
  breakdown: Record<string, number>;
}

export default function CommercialPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [selectedTenant, setSelectedTenant] = useState<string>("");
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [billEstimate, setBillEstimate] = useState<BillEstimate | null>(null);
  const [usageTrends, setUsageTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // New tenant form
  const [newTenant, setNewTenant] = useState({
    tenant_id: "",
    name: "",
    tier: "free"
  });

  useEffect(() => {
    fetchTenants();
  }, []);

  useEffect(() => {
    if (selectedTenant) {
      fetchUsageData(selectedTenant);
      fetchBillEstimate(selectedTenant);
      fetchUsageTrends(selectedTenant);
    }
  }, [selectedTenant]);

  const fetchTenants = async () => {
    try {
      const response = await fetch("/api/commercial/tenants");
      if (!response.ok) throw new Error("Failed to fetch tenants");
      const data = await response.json();
      setTenants(data);
      if (data.length > 0 && !selectedTenant) {
        setSelectedTenant(data[0].tenant_id);
      }
    } catch (error) {
      toast.error("Failed to load tenants");
    }
  };

  const fetchUsageData = async (tenantId: string) => {
    try {
      const response = await fetch(`/api/commercial/usage/${tenantId}/current-month`);
      if (!response.ok) throw new Error("Failed to fetch usage");
      const data = await response.json();
      setUsage(data);
    } catch (error) {
      toast.error("Failed to load usage data");
    }
  };

  const fetchBillEstimate = async (tenantId: string) => {
    try {
      const response = await fetch(`/api/commercial/billing/${tenantId}/estimate`);
      if (!response.ok) throw new Error("Failed to fetch bill estimate");
      const data = await response.json();
      setBillEstimate(data);
    } catch (error) {
      toast.error("Failed to load bill estimate");
    }
  };

  const fetchUsageTrends = async (tenantId: string) => {
    try {
      const response = await fetch(`/api/commercial/usage/${tenantId}/trends?months=6`);
      if (!response.ok) throw new Error("Failed to fetch trends");
      const data = await response.json();
      setUsageTrends(data);
    } catch (error) {
      toast.error("Failed to load usage trends");
    }
  };

  const createTenant = async () => {
    if (!newTenant.tenant_id || !newTenant.name) {
      toast.error("Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/commercial/tenants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTenant)
      });

      if (!response.ok) throw new Error("Failed to create tenant");
      
      toast.success("Tenant created successfully");
      setNewTenant({ tenant_id: "", name: "", tier: "free" });
      fetchTenants();
    } catch (error) {
      toast.error("Failed to create tenant");
    } finally {
      setLoading(false);
    }
  };

  const updateTenantTier = async (tenantId: string, newTier: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/commercial/tenants/${tenantId}/tier`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_tier: newTier })
      });

      if (!response.ok) throw new Error("Failed to update tier");
      
      toast.success("Tenant tier updated successfully");
      fetchTenants();
    } catch (error) {
      toast.error("Failed to update tier");
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier: string) => {
    const colors = {
      free: "default",
      starter: "secondary",
      professional: "blue",
      enterprise: "purple"
    };
    return colors[tier as keyof typeof colors] || "default";
  };

  const currentTenant = tenants.find(t => t.tenant_id === selectedTenant);

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Commercial Management</h1>
          <p className="text-muted-foreground">
            Multi-tenancy, billing, and usage tracking
          </p>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tenants">Tenants</TabsTrigger>
          <TabsTrigger value="usage">Usage & Billing</TabsTrigger>
          <TabsTrigger value="create">Create Tenant</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Overview Stats */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Tenants</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{tenants.length}</div>
                <p className="text-xs text-muted-foreground">
                  {tenants.filter(t => t.is_active).length} active
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${billEstimate?.projected_month_cost.toFixed(2) || "0.00"}
                </div>
                <p className="text-xs text-muted-foreground">
                  ${billEstimate?.current_month_cost.toFixed(2) || "0.00"} this month
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">API Calls</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {usage?.api_calls.toLocaleString() || 0}
                </div>
                <p className="text-xs text-muted-foreground">This month</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Agent Executions</CardTitle>
                <Package className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {usage?.agent_executions || 0}
                </div>
                <p className="text-xs text-muted-foreground">This month</p>
              </CardContent>
            </Card>
          </div>

          {/* Current Tenant Details */}
          {currentTenant && (
            <Card>
              <CardHeader>
                <CardTitle>Current Tenant: {currentTenant.name}</CardTitle>
                <CardDescription>Tenant ID: {currentTenant.tenant_id}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Subscription Tier</span>
                  <Badge variant={getTierColor(currentTenant.tier) as any}>
                    {currentTenant.tier.toUpperCase()}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Max Agents</p>
                    <p className="text-lg font-semibold">
                      {currentTenant.limits.max_agents === -1 ? "∞" : currentTenant.limits.max_agents}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Max Workflows</p>
                    <p className="text-lg font-semibold">
                      {currentTenant.limits.max_workflows === -1 ? "∞" : currentTenant.limits.max_workflows}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">API Calls/Hour</p>
                    <p className="text-lg font-semibold">
                      {currentTenant.limits.max_api_calls_per_hour === -1 ? "∞" : currentTenant.limits.max_api_calls_per_hour}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Storage Limit</p>
                    <p className="text-lg font-semibold">
                      {currentTenant.limits.storage_limit_gb === -1 ? "∞" : `${currentTenant.limits.storage_limit_gb} GB`}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">Features</p>
                  <div className="flex flex-wrap gap-2">
                    {currentTenant.features.map((feature) => (
                      <Badge key={feature} variant="outline">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Usage Trends Chart */}
          {usageTrends.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Usage Trends (Last 6 Months)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={usageTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="api_calls" stroke="#8884d8" name="API Calls" />
                    <Line type="monotone" dataKey="agent_executions" stroke="#82ca9d" name="Agent Executions" />
                    <Line type="monotone" dataKey="workflow_runs" stroke="#ffc658" name="Workflow Runs" />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="tenants" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Tenants</CardTitle>
              <CardDescription>Manage tenant accounts and subscriptions</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tenant ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Tier</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tenants.map((tenant) => (
                    <TableRow key={tenant.tenant_id}>
                      <TableCell className="font-mono text-sm">{tenant.tenant_id}</TableCell>
                      <TableCell>{tenant.name}</TableCell>
                      <TableCell>
                        <Badge variant={getTierColor(tenant.tier) as any}>
                          {tenant.tier.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <Badge variant={tenant.is_active ? "default" : "secondary"}>
                          {tenant.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedTenant(tenant.tenant_id)}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <div className="flex items-center gap-4 mb-4">
            <Label>Select Tenant</Label>
            <Select value={selectedTenant} onValueChange={setSelectedTenant}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="Select tenant" />
              </SelectTrigger>
              <SelectContent>
                {tenants.map((tenant) => (
                  <SelectItem key={tenant.tenant_id} value={tenant.tenant_id}>
                    {tenant.name} ({tenant.tenant_id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {usage && (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader>
                    <CardTitle>Current Month Usage</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">API Calls</span>
                      <span className="font-semibold">{usage.api_calls.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Agent Executions</span>
                      <span className="font-semibold">{usage.agent_executions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Workflow Runs</span>
                      <span className="font-semibold">{usage.workflow_runs}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Storage</span>
                      <span className="font-semibold">{usage.storage_gb.toFixed(2)} GB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Compute Hours</span>
                      <span className="font-semibold">{usage.compute_hours.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Cost Breakdown</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {Object.entries(usage.breakdown).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm capitalize">{key.replace(/_/g, " ")}</span>
                        <span className="font-semibold">${(value as number).toFixed(4)}</span>
                      </div>
                    ))}
                    <div className="flex justify-between pt-2 border-t">
                      <span className="font-semibold">Total</span>
                      <span className="font-bold">${usage.total_cost.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>

                {billEstimate && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Bill Estimate</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Current Month</span>
                        <span className="font-semibold">${billEstimate.current_month_cost.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Projected Month</span>
                        <span className="font-semibold">${billEstimate.projected_month_cost.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Days Elapsed</span>
                        <span className="font-semibold">{billEstimate.days_elapsed}</span>
                      </div>
                      <div className="flex items-start gap-2 mt-4 p-2 bg-amber-50 dark:bg-amber-900/20 rounded">
                        <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400 mt-0.5" />
                        <p className="text-xs text-amber-600 dark:text-amber-400">
                          Projection based on current daily usage rate
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              {Object.entries(usage.breakdown).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Cost Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart
                        data={Object.entries(usage.breakdown).map(([key, value]) => ({
                          name: key.replace(/_/g, " "),
                          cost: value
                        }))}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip formatter={(value) => `$${(value as number).toFixed(4)}`} />
                        <Bar dataKey="cost" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        <TabsContent value="create" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Create New Tenant</CardTitle>
              <CardDescription>Add a new tenant to the platform</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="tenant_id">Tenant ID</Label>
                <Input
                  id="tenant_id"
                  placeholder="e.g., acme-corp"
                  value={newTenant.tenant_id}
                  onChange={(e) => setNewTenant({ ...newTenant, tenant_id: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="name">Tenant Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Acme Corporation"
                  value={newTenant.name}
                  onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tier">Subscription Tier</Label>
                <Select
                  value={newTenant.tier}
                  onValueChange={(value) => setNewTenant({ ...newTenant, tier: value })}
                >
                  <SelectTrigger id="tier">
                    <SelectValue placeholder="Select tier" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="free">Free</SelectItem>
                    <SelectItem value="starter">Starter</SelectItem>
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="enterprise">Enterprise</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button onClick={createTenant} disabled={loading} className="w-full">
                {loading ? "Creating..." : "Create Tenant"}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Subscription Tiers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  {
                    name: "Free",
                    price: "$0",
                    features: ["3 agents", "5 workflows", "100 API calls/hour", "1 GB storage"]
                  },
                  {
                    name: "Starter",
                    price: "$49",
                    features: ["10 agents", "20 workflows", "1,000 API calls/hour", "10 GB storage"]
                  },
                  {
                    name: "Professional",
                    price: "$199",
                    features: ["50 agents", "100 workflows", "10,000 API calls/hour", "100 GB storage"]
                  },
                  {
                    name: "Enterprise",
                    price: "Custom",
                    features: ["Unlimited agents", "Unlimited workflows", "Unlimited API calls", "Unlimited storage"]
                  }
                ].map((tier) => (
                  <Card key={tier.name}>
                    <CardHeader>
                      <CardTitle className="text-lg">{tier.name}</CardTitle>
                      <CardDescription className="text-2xl font-bold">{tier.price}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-sm">
                        {tier.features.map((feature, i) => (
                          <li key={i} className="flex items-center">
                            <span className="mr-2">✓</span>
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

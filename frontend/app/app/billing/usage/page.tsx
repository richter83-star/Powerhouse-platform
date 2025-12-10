'use client';

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  Download,
  BarChart3,
  Zap,
  Database,
  Workflow,
  Server
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/toast-provider';
import { useSession } from 'next-auth/react';

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

interface UsageStatus {
  resource_type: string;
  current: number;
  limit: number;
  percentage: number;
  allowed: boolean;
  message: string;
  limit_type: string;
}

interface UsageProjection {
  projected_api_calls: number;
  projected_agent_executions: number;
  projected_workflow_runs: number;
  projected_storage_gb: number;
  projected_cost: number;
  current_daily_average: {
    api_calls: number;
    agent_executions: number;
    workflow_runs: number;
    cost: number;
  };
}

export default function UsagePage() {
  const { data: session } = useSession();
  const { success, error: showError } = useToast();
  const [currentUsage, setCurrentUsage] = useState<UsageSummary | null>(null);
  const [usageStatus, setUsageStatus] = useState<UsageStatus[]>([]);
  const [projections, setProjections] = useState<UsageProjection | null>(null);
  const [trends, setTrends] = useState<UsageSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'month' | 'trends'>('month');

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  useEffect(() => {
    loadUsageData();
  }, [selectedPeriod]);

  const loadUsageData = async () => {
    try {
      setIsLoading(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load current month usage
      const currentResponse = await fetch(`${apiUrl}/api/v1/usage/current-month`, { headers });
      if (currentResponse.ok) {
        const data = await currentResponse.json();
        setCurrentUsage(data);
      }

      // Load usage status
      const statusResponse = await fetch(`${apiUrl}/api/v1/usage/status`, { headers });
      if (statusResponse.ok) {
        const data = await statusResponse.json();
        setUsageStatus(data);
      }

      // Load projections
      const projectionsResponse = await fetch(`${apiUrl}/api/v1/usage/projections?days_ahead=30`, { headers });
      if (projectionsResponse.ok) {
        const data = await projectionsResponse.json();
        setProjections(data);
      }

      // Load trends if selected
      if (selectedPeriod === 'trends') {
        const trendsResponse = await fetch(`${apiUrl}/api/v1/usage/trends?months=6`, { headers });
        if (trendsResponse.ok) {
          const data = await trendsResponse.json();
          setTrends(data);
        }
      }
    } catch (err) {
      console.error('Failed to load usage data:', err);
      showError('Load Error', 'Failed to load usage data');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (percentage: number, allowed: boolean) => {
    if (!allowed) return 'destructive';
    if (percentage >= 95) return 'destructive';
    if (percentage >= 90) return 'default';
    if (percentage >= 80) return 'secondary';
    return 'default';
  };

  const getStatusIcon = (percentage: number, allowed: boolean) => {
    if (!allowed || percentage >= 95) return AlertTriangle;
    if (percentage >= 90) return AlertTriangle;
    if (percentage >= 80) return Clock;
    return CheckCircle;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8" />
            Usage & Limits
          </h1>
          <p className="text-muted-foreground mt-2">
            Monitor your resource usage and subscription limits
          </p>
        </div>
        <Button variant="outline" onClick={loadUsageData} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Usage Status Cards */}
      {usageStatus.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {usageStatus.map((status) => {
            const StatusIcon = getStatusIcon(status.percentage, status.allowed);
            const statusColor = getStatusColor(status.percentage, status.allowed);
            
            return (
              <Card key={status.resource_type} className={status.percentage >= 90 ? 'border-orange-500' : ''}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium capitalize">
                      {status.resource_type.replace('_', ' ')}
                    </CardTitle>
                    <StatusIcon className={`h-4 w-4 ${
                      status.percentage >= 90 ? 'text-orange-500' : 
                      status.percentage >= 80 ? 'text-yellow-500' : 
                      'text-green-500'
                    }`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Usage</span>
                      <span className="font-medium">
                        {formatNumber(status.current)} / {status.limit === Infinity ? '∞' : formatNumber(status.limit)}
                      </span>
                    </div>
                    <Progress 
                      value={Math.min(status.percentage, 100)} 
                      className="h-2"
                    />
                    <p className="text-xs text-muted-foreground">
                      {status.percentage.toFixed(1)}% used
                    </p>
                    {status.percentage >= 80 && (
                      <Badge variant={statusColor} className="text-xs">
                        {status.message}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Warnings */}
      {usageStatus.some(s => s.percentage >= 90 || !s.allowed) && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Usage Limits Approaching</AlertTitle>
          <AlertDescription>
            {usageStatus
              .filter(s => s.percentage >= 90 || !s.allowed)
              .map(s => `${s.resource_type}: ${s.message}`)
              .join(', ')}
            . Consider upgrading your plan to avoid service interruption.
          </AlertDescription>
        </Alert>
      )}

      <Tabs value={selectedPeriod} onValueChange={(v) => setSelectedPeriod(v as 'month' | 'trends')}>
        <TabsList>
          <TabsTrigger value="month">Current Month</TabsTrigger>
          <TabsTrigger value="trends">Trends (6 Months)</TabsTrigger>
          <TabsTrigger value="projections">Projections</TabsTrigger>
        </TabsList>

        <TabsContent value="month" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading usage data...</p>
            </div>
          ) : currentUsage ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Zap className="h-4 w-4" />
                    API Calls
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{formatNumber(currentUsage.api_calls)}</div>
                  <p className="text-sm text-muted-foreground mt-1">This month</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Workflow className="h-4 w-4" />
                    Agent Executions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{formatNumber(currentUsage.agent_executions)}</div>
                  <p className="text-sm text-muted-foreground mt-1">This month</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    Workflow Runs
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{formatNumber(currentUsage.workflow_runs)}</div>
                  <p className="text-sm text-muted-foreground mt-1">This month</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Database className="h-4 w-4" />
                    Storage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{currentUsage.storage_gb.toFixed(2)} GB</div>
                  <p className="text-sm text-muted-foreground mt-1">Current usage</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Compute Hours
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{currentUsage.compute_hours.toFixed(2)}</div>
                  <p className="text-sm text-muted-foreground mt-1">This month</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Total Cost
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{formatCurrency(currentUsage.total_cost)}</div>
                  <p className="text-sm text-muted-foreground mt-1">This month</p>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Alert>
              <AlertTitle>No Usage Data</AlertTitle>
              <AlertDescription>
                Usage data will appear here once you start using Powerhouse.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading trends...</p>
            </div>
          ) : trends.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Usage Trends (6 Months)</CardTitle>
                <CardDescription>
                  Historical usage data to identify patterns
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {trends.map((trend, idx) => (
                    <div key={idx} className="border-b pb-4 last:border-0">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">
                          {new Date(trend.start_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {formatCurrency(trend.total_cost)}
                        </span>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">API Calls: </span>
                          <span className="font-medium">{formatNumber(trend.api_calls)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Agents: </span>
                          <span className="font-medium">{formatNumber(trend.agent_executions)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Workflows: </span>
                          <span className="font-medium">{formatNumber(trend.workflow_runs)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Storage: </span>
                          <span className="font-medium">{trend.storage_gb.toFixed(2)} GB</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Alert>
              <AlertTitle>No Trend Data</AlertTitle>
              <AlertDescription>
                Trend data will appear after you have usage history.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        <TabsContent value="projections" className="space-y-4">
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading projections...</p>
            </div>
          ) : projections ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    30-Day Projections
                  </CardTitle>
                  <CardDescription>
                    Based on current usage patterns
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">API Calls</span>
                      <span className="font-medium">{formatNumber(projections.projected_api_calls)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Daily avg: {formatNumber(projections.current_daily_average.api_calls)}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Agent Executions</span>
                      <span className="font-medium">{formatNumber(projections.projected_agent_executions)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Daily avg: {formatNumber(projections.current_daily_average.agent_executions)}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Workflow Runs</span>
                      <span className="font-medium">{formatNumber(projections.projected_workflow_runs)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Daily avg: {formatNumber(projections.current_daily_average.workflow_runs)}
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Storage</span>
                      <span className="font-medium">{projections.projected_storage_gb.toFixed(2)} GB</span>
                    </div>
                  </div>
                  <div className="pt-4 border-t">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Projected Cost</span>
                      <span className="text-2xl font-bold">{formatCurrency(projections.projected_cost)}</span>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Daily avg: {formatCurrency(projections.current_daily_average.cost)}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Daily Averages</CardTitle>
                  <CardDescription>
                    Current daily usage rates
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">API Calls/day</span>
                    <span className="font-medium">{formatNumber(projections.current_daily_average.api_calls)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Agent Executions/day</span>
                    <span className="font-medium">{formatNumber(projections.current_daily_average.agent_executions)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Workflow Runs/day</span>
                    <span className="font-medium">{formatNumber(projections.current_daily_average.workflow_runs)}</span>
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t">
                    <span className="text-sm font-medium">Cost/day</span>
                    <span className="font-bold">{formatCurrency(projections.current_daily_average.cost)}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Alert>
              <AlertTitle>No Projection Data</AlertTitle>
              <AlertDescription>
                Projections will be available after sufficient usage history.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}


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
  Server,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/toast-provider';
import { useSession } from 'next-auth/react';

interface SLAMetrics {
  period_start: string;
  period_end: string;
  uptime_percentage: number;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_response_time_ms: number;
  p95_response_time_ms: number;
  p99_response_time_ms: number;
  error_rate: number;
  sla_target: number;
  sla_status: string;
}

interface ServiceHealth {
  overall_health: string;
  is_up: boolean;
  healthy_services: number;
  total_services: number;
  health_percentage: number;
  last_check: string;
  downtime_periods: number;
}

export default function SLAPage() {
  const { data: session } = useSession();
  const { success, error: showError } = useToast();
  const [metrics, setMetrics] = useState<SLAMetrics | null>(null);
  const [health, setHealth] = useState<ServiceHealth | null>(null);
  const [uptime, setUptime] = useState<number | null>(null);
  const [responseTimes, setResponseTimes] = useState<any>(null);
  const [errorRate, setErrorRate] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [breachCheck, setBreachCheck] = useState<any>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  useEffect(() => {
    loadSLAData();
    const interval = setInterval(loadSLAData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const loadSLAData = async () => {
    try {
      setIsLoading(true);
      const token = session?.accessToken || localStorage.getItem('token') || '';
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Load all SLA data in parallel
      const [metricsRes, healthRes, uptimeRes, responseRes, errorRes, breachRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/sla/metrics`, { headers }),
        fetch(`${apiUrl}/api/v1/sla/health`, { headers }),
        fetch(`${apiUrl}/api/v1/sla/uptime?days=30`, { headers }),
        fetch(`${apiUrl}/api/v1/sla/response-times`, { headers }),
        fetch(`${apiUrl}/api/v1/sla/error-rate?days=30`, { headers }),
        fetch(`${apiUrl}/api/v1/sla/breach-check`, { headers })
      ]);

      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setMetrics(data);
      }

      if (healthRes.ok) {
        const data = await healthRes.json();
        setHealth(data);
      }

      if (uptimeRes.ok) {
        const data = await uptimeRes.json();
        setUptime(data.uptime_percentage);
      }

      if (responseRes.ok) {
        const data = await responseRes.json();
        setResponseTimes(data);
      }

      if (errorRes.ok) {
        const data = await errorRes.json();
        setErrorRate(data.error_rate_percentage);
      }

      if (breachRes.ok) {
        const data = await breachRes.json();
        setBreachCheck(data);
      }
    } catch (err) {
      console.error('Failed to load SLA data:', err);
      showError('Load Error', 'Failed to load SLA metrics');
    } finally {
      setIsLoading(false);
    }
  };

  const getSLAStatusBadge = (status: string, uptime: number, target: number) => {
    if (status === 'compliant') {
      return <Badge variant="default" className="flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Compliant</Badge>;
    } else if (status === 'at_risk') {
      return <Badge variant="secondary" className="flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> At Risk</Badge>;
    } else {
      return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Breached</Badge>;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-7xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Activity className="h-8 w-8" />
            SLA Monitoring & Reporting
          </h1>
          <p className="text-muted-foreground mt-2">
            Monitor service level agreements, uptime, and performance metrics
          </p>
        </div>
        <Button variant="outline" onClick={loadSLAData} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* SLA Breach Alert */}
      {breachCheck?.breached && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>SLA Breach Detected</AlertTitle>
          <AlertDescription>
            {breachCheck.message}
          </AlertDescription>
        </Alert>
      )}

      {/* Key Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Server className="h-4 w-4" />
                Uptime
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.uptime_percentage.toFixed(3)}%</div>
              <div className="flex items-center gap-2 mt-2">
                <p className="text-sm text-muted-foreground">Target: {metrics.sla_target}%</p>
                {getSLAStatusBadge(metrics.sla_status, metrics.uptime_percentage, metrics.sla_target)}
              </div>
              <Progress 
                value={metrics.uptime_percentage} 
                className="h-2 mt-2"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Avg Response Time
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.average_response_time_ms.toFixed(0)}ms</div>
              <p className="text-sm text-muted-foreground mt-2">
                P95: {metrics.p95_response_time_ms.toFixed(0)}ms
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Error Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{metrics.error_rate.toFixed(2)}%</div>
              <p className="text-sm text-muted-foreground mt-2">
                {formatNumber(metrics.failed_requests)} failed requests
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Total Requests
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{formatNumber(metrics.total_requests)}</div>
              <p className="text-sm text-muted-foreground mt-2">
                {formatNumber(metrics.successful_requests)} successful
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Service Health */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle>Service Health</CardTitle>
            <CardDescription>
              Overall system health and service status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Overall Status</p>
                <Badge variant={health.is_up ? "default" : "destructive"} className="mt-1">
                  {health.overall_health.toUpperCase()}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Healthy Services</p>
                <p className="text-2xl font-bold mt-1">
                  {health.healthy_services} / {health.total_services}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Health Percentage</p>
                <p className="text-2xl font-bold mt-1">{health.health_percentage.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Downtime Periods</p>
                <p className="text-2xl font-bold mt-1">{health.downtime_periods}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detailed Metrics */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="response-times">Response Times</TabsTrigger>
          <TabsTrigger value="errors">Error Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {metrics && (
            <Card>
              <CardHeader>
                <CardTitle>SLA Compliance Report</CardTitle>
                <CardDescription>
                  Period: {new Date(metrics.period_start).toLocaleDateString()} - {new Date(metrics.period_end).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Uptime</p>
                    <p className="text-2xl font-bold">{metrics.uptime_percentage.toFixed(3)}%</p>
                    <p className="text-xs text-muted-foreground">Target: {metrics.sla_target}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">SLA Status</p>
                    <div className="mt-1">
                      {getSLAStatusBadge(metrics.sla_status, metrics.uptime_percentage, metrics.sla_target)}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Requests</p>
                    <p className="text-2xl font-bold">{formatNumber(metrics.total_requests)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Success Rate</p>
                    <p className="text-2xl font-bold">
                      {((metrics.successful_requests / metrics.total_requests) * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="response-times" className="space-y-4">
          {responseTimes && (
            <Card>
              <CardHeader>
                <CardTitle>Response Time Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Average</p>
                    <p className="text-xl font-bold">{responseTimes.avg.toFixed(0)}ms</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">P95</p>
                    <p className="text-xl font-bold">{responseTimes.p95.toFixed(0)}ms</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">P99</p>
                    <p className="text-xl font-bold">{responseTimes.p99.toFixed(0)}ms</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Min</p>
                    <p className="text-xl font-bold">{responseTimes.min.toFixed(0)}ms</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Max</p>
                    <p className="text-xl font-bold">{responseTimes.max.toFixed(0)}ms</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          {metrics && (
            <Card>
              <CardHeader>
                <CardTitle>Error Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Error Rate</span>
                      <span className="text-sm font-bold">{metrics.error_rate.toFixed(2)}%</span>
                    </div>
                    <Progress value={metrics.error_rate} className="h-2" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Failed Requests</p>
                      <p className="text-2xl font-bold">{formatNumber(metrics.failed_requests)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Successful Requests</p>
                      <p className="text-2xl font-bold">{formatNumber(metrics.successful_requests)}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}


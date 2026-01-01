'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  Database,
  Cpu,
  Wifi
} from 'lucide-react';

interface PerformanceAlert {
  alert_id: string;
  level: 'info' | 'warning' | 'critical';
  metric_type: string;
  message: string;
  agent_name?: string | null;
  timestamp: string;
  recommendation?: string | null;
}

interface SystemMetrics {
  total_tasks: number;
  success_rate: number;
  error_rate: number;
  avg_latency_ms: number;
  total_cost: number;
  total_api_calls: number;
  total_tokens: number;
}

export function RealtimeMonitor() {
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [health, setHealth] = useState<{ status?: string; health_score?: number } | null>(null);
  const [agentCount, setAgentCount] = useState<number | null>(null);

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const results = await Promise.allSettled([
          fetch('/api/agents'),
          fetch(`${apiUrl}/api/performance/metrics/system?time_window_minutes=60`),
          fetch(`${apiUrl}/api/performance/health`),
          fetch(`${apiUrl}/api/performance/report?include_agents=false&time_window_minutes=60`)
        ]);

        const agentsRes = results[0].status === 'fulfilled' ? results[0].value : null;
        const metricsRes = results[1].status === 'fulfilled' ? results[1].value : null;
        const healthRes = results[2].status === 'fulfilled' ? results[2].value : null;
        const reportRes = results[3].status === 'fulfilled' ? results[3].value : null;

        if (agentsRes?.ok) {
          const data = await agentsRes.json();
          setAgentCount(data?.total_count || data?.agents?.length || 0);
        }

        if (metricsRes?.ok) {
          const data = await metricsRes.json();
          setSystemMetrics(data?.metrics || null);
        }

        if (healthRes?.ok) {
          const data = await healthRes.json();
          setHealth(data);
        }

        if (reportRes?.ok) {
          const data = await reportRes.json();
          const report = data?.report || {};
          const recentAlerts = report?.recent_alerts || [];
          setAlerts(Array.isArray(recentAlerts) ? recentAlerts : []);
          const recs = report?.recommendations || [];
          setRecommendations(Array.isArray(recs) ? recs : []);
        }
      } catch (error) {
        console.error('Failed to fetch telemetry:', error);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 15000);
    return () => clearInterval(interval);
  }, []);

  const formatLatency = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}s`;
    }
    return `${Math.round(value)}ms`;
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    return `${(value * 100).toFixed(1)}%`;
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'info':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'critical':
      case 'warning':
        return <AlertCircle className="w-4 h-4" />;
      case 'info':
        return <Activity className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const throughputPerHour = systemMetrics?.total_tasks ?? 0;
  const healthLabel = health?.status ? health.status : 'unknown';

  return (
    <div className="space-y-6">
      {/* Telemetry Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Zap className="w-6 h-6 text-blue-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{throughputPerHour}</p>
                <p className="text-xs text-slate-600">tasks/hr</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-6 h-6 text-green-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{formatLatency(systemMetrics?.avg_latency_ms ?? null)}</p>
                <p className="text-xs text-slate-600">avg latency</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Wifi className="w-6 h-6 text-purple-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{agentCount ?? '--'}</p>
                <p className="text-xs text-slate-600">agents online</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Database className="w-6 h-6 text-orange-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{alerts.length}</p>
                <p className="text-xs text-slate-600">active alerts</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{healthLabel}</p>
                <p className="text-xs text-slate-600">system health</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  Performance Alerts
                </CardTitle>
                <CardDescription>Recent alerting signals from performance monitoring</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-medium text-green-600">Live</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px] pr-4">
              <div className="space-y-3">
                {alerts.length === 0 ? (
                  <div className="text-sm text-slate-600">No alerts reported in the last hour.</div>
                ) : (
                  alerts.map((alert) => (
                    <div
                      key={alert.alert_id}
                      className="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-slate-100 rounded-lg">
                          {getLevelIcon(alert.level)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-sm font-medium text-slate-900">{alert.message}</p>
                            <Badge className={getLevelColor(alert.level)}>
                              {alert.level}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(alert.timestamp).toLocaleTimeString()}
                            </span>
                            <Badge variant="outline" className="text-xs">
                              {alert.metric_type}
                            </Badge>
                          </div>
                          {alert.recommendation && (
                            <p className="text-xs text-slate-500 mt-2">{alert.recommendation}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-purple-600" />
                  Recommended Actions
                </CardTitle>
                <CardDescription>Optimization guidance from system analysis</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-medium text-green-600">Live</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px] pr-4">
              <div className="space-y-2">
                {recommendations.length === 0 ? (
                  <div className="text-sm text-slate-600">No recommendations available.</div>
                ) : (
                  recommendations.map((rec, index) => (
                    <div
                      key={index}
                      className="p-3 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors"
                    >
                      <p className="text-sm text-slate-700">{rec}</p>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* System Metrics Snapshot */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-orange-600" />
            System Metrics Snapshot
          </CardTitle>
          <CardDescription>Aggregated performance indicators from the last hour</CardDescription>
        </CardHeader>
        <CardContent>
          {systemMetrics ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-slate-500">Success Rate</p>
                <p className="text-lg font-bold text-slate-900">{formatPercent(systemMetrics.success_rate)}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-slate-500">Error Rate</p>
                <p className="text-lg font-bold text-slate-900">{formatPercent(systemMetrics.error_rate)}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-slate-500">Total API Calls</p>
                <p className="text-lg font-bold text-slate-900">{systemMetrics.total_api_calls.toLocaleString()}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-slate-500">Tokens Used</p>
                <p className="text-lg font-bold text-slate-900">{systemMetrics.total_tokens.toLocaleString()}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-slate-500">Total Cost</p>
                <p className="text-lg font-bold text-slate-900">${(systemMetrics.total_cost || 0).toFixed(4)}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-slate-500">Health Score</p>
                <p className="text-lg font-bold text-slate-900">{health?.health_score ?? '--'}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-600">No system metrics available yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

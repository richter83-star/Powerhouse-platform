
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Network,
  AlertCircle,
  CheckCircle2,
  Clock,
  Database
} from 'lucide-react';

interface SystemMetric {
  label: string;
  value: string;
  note?: string;
}

interface HealthItem {
  label: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  detail: string;
}

interface TelemetrySummary {
  counters: number;
  gauges: number;
  histograms: number;
  checkpoints: number;
  openCircuits: number;
  totalCircuits: number;
}

export function SystemOverview() {
  const [agentCount, setAgentCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [healthItems, setHealthItems] = useState<HealthItem[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetrySummary | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);

  useEffect(() => {
    fetchOverview();
  }, []);

  const fetchOverview = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      const results = await Promise.allSettled([
        fetch('/api/agents'),
        fetch(`${apiUrl}/api/performance/metrics/system?time_window_minutes=60`),
        fetch(`${apiUrl}/api/performance/health`),
        fetch(`${apiUrl}/api/performance/report?include_agents=false&time_window_minutes=60`),
        fetch(`${apiUrl}/api/observability/health`)
      ]);

      const agentsRes = results[0].status === 'fulfilled' ? results[0].value : null;
      const metricsRes = results[1].status === 'fulfilled' ? results[1].value : null;
      const healthRes = results[2].status === 'fulfilled' ? results[2].value : null;
      const reportRes = results[3].status === 'fulfilled' ? results[3].value : null;
      const observabilityRes = results[4].status === 'fulfilled' ? results[4].value : null;

      let performanceMetrics: any = null;
      let performanceHealth: any = null;
      let reportData: any = null;
      let observabilityHealth: any = null;

      let currentAgentCount = agentCount;
      if (agentsRes?.ok) {
        const data = await agentsRes.json();
        const count = data?.total_count || data?.agents?.length || 0;
        currentAgentCount = count;
        setAgentCount(count);
      }

      if (metricsRes?.ok) {
        const data = await metricsRes.json();
        performanceMetrics = data?.metrics || null;
      }

      if (healthRes?.ok) {
        performanceHealth = await healthRes.json();
      }

      if (reportRes?.ok) {
        reportData = await reportRes.json();
      }

      if (observabilityRes?.ok) {
        observabilityHealth = await observabilityRes.json();
      }

      const formatNumber = (value: number | null | undefined) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
          return '--';
        }
        return value.toLocaleString();
      };

      const formatPercent = (value: number | null | undefined) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
          return '--';
        }
        return `${(value * 100).toFixed(1)}%`;
      };

      const formatLatency = (value: number | null | undefined) => {
        if (value === null || value === undefined || Number.isNaN(value)) {
          return '--';
        }
        if (value >= 1000) {
          return `${(value / 1000).toFixed(2)}s`;
        }
        return `${Math.round(value)}ms`;
      };

      const accuracyValue = performanceMetrics?.avg_accuracy && performanceMetrics.avg_accuracy > 0
        ? performanceMetrics.avg_accuracy
        : performanceMetrics?.avg_quality_score || null;

      const nextMetrics: SystemMetric[] = [
        {
          label: 'Active Agents',
          value: currentAgentCount === null ? '--' : currentAgentCount.toString(),
          note: 'Registered agents'
        },
        {
          label: 'Tasks Processed',
          value: formatNumber(performanceMetrics?.total_tasks),
          note: 'Last 60 min'
        },
        {
          label: 'Success Rate',
          value: formatPercent(performanceMetrics?.success_rate),
          note: 'Last 60 min'
        },
        {
          label: 'Avg Latency',
          value: formatLatency(performanceMetrics?.avg_latency_ms),
          note: 'Last 60 min'
        },
        {
          label: 'Error Rate',
          value: formatPercent(performanceMetrics?.error_rate),
          note: 'Last 60 min'
        },
        {
          label: 'Accuracy',
          value: formatPercent(accuracyValue),
          note: 'Reported accuracy'
        }
      ];

      setMetrics(nextMetrics);

      const nextHealthItems: HealthItem[] = [];
      if (performanceHealth?.status) {
        nextHealthItems.push({
          label: 'Performance Monitor',
          status: performanceHealth.status,
          detail: `Health score ${performanceHealth.health_score ?? '--'}`
        });
      }
      if (observabilityHealth?.status) {
        nextHealthItems.push({
          label: 'Observability',
          status: observabilityHealth.status,
          detail: `${observabilityHealth.circuit_breakers?.open ?? 0} open circuit(s)`
        });
        nextHealthItems.push({
          label: 'Checkpoints',
          status: (observabilityHealth.circuit_breakers?.open ?? 0) > 0 ? 'degraded' : 'healthy',
          detail: `${observabilityHealth.checkpoints?.total ?? 0} stored`
        });
      }
      if (nextHealthItems.length === 0) {
        nextHealthItems.push({
          label: 'System Health',
          status: 'unknown',
          detail: 'No health data reported'
        });
      }
      setHealthItems(nextHealthItems);

      if (observabilityHealth) {
        setTelemetry({
          counters: observabilityHealth.metrics?.counters ?? 0,
          gauges: observabilityHealth.metrics?.gauges ?? 0,
          histograms: observabilityHealth.metrics?.histograms ?? 0,
          checkpoints: observabilityHealth.checkpoints?.total ?? 0,
          openCircuits: observabilityHealth.circuit_breakers?.open ?? 0,
          totalCircuits: observabilityHealth.circuit_breakers?.total ?? 0
        });
      }

      const reportRecommendations = reportData?.report?.recommendations || reportData?.recommendations || [];
      if (Array.isArray(reportRecommendations)) {
        setRecommendations(reportRecommendations);
      }
    } catch (error) {
      console.error('Failed to fetch system overview:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'degraded': return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy': return 'text-red-600 bg-red-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'degraded': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'unhealthy': return <AlertCircle className="w-5 h-5 text-red-600" />;
      default: return <Clock className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {metrics.length === 0 ? (
          <Card className="col-span-full bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6 text-center text-slate-600">
              {loading ? 'Loading metrics...' : 'No system metrics available yet'}
            </CardContent>
          </Card>
        ) : (
          metrics.map((metric, index) => (
            <Card key={index} className="bg-white/80 backdrop-blur-sm border-slate-200 hover:shadow-lg transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <p className="text-sm font-medium text-slate-600">{metric.label}</p>
                </div>
                <p className="text-3xl font-bold text-slate-900">{metric.value}</p>
                {metric.note && (
                  <p className="text-xs text-slate-500 mt-2">
                    {metric.note}
                  </p>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* System Health Status */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5 text-blue-600" />
            System Health & Component Status
          </CardTitle>
          <CardDescription>
            Real-time monitoring of all platform components and services
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {healthItems.map((item) => (
              <div key={item.label} className="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-slate-900">
                    {item.label}
                  </h4>
                  {getStatusIcon(item.status)}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Status</span>
                    <Badge className={getStatusColor(item.status)}>
                      {item.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Details</span>
                    <span className="font-semibold text-slate-900">{item.detail}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Telemetry Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-purple-600" />
              Observability Telemetry
            </CardTitle>
            <CardDescription>Live counters and health metadata from observability</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {telemetry ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-500">Counters</p>
                  <p className="text-lg font-bold text-slate-900">{telemetry.counters}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Gauges</p>
                  <p className="text-lg font-bold text-slate-900">{telemetry.gauges}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Histograms</p>
                  <p className="text-lg font-bold text-slate-900">{telemetry.histograms}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Checkpoints</p>
                  <p className="text-lg font-bold text-slate-900">{telemetry.checkpoints}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Open Circuits</p>
                  <p className="text-lg font-bold text-slate-900">{telemetry.openCircuits}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Total Circuits</p>
                  <p className="text-lg font-bold text-slate-900">{telemetry.totalCircuits}</p>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-600">
                Observability metrics are not available yet.
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="w-5 h-5 text-green-600" />
              System Recommendations
            </CardTitle>
            <CardDescription>Actionable guidance from performance monitoring</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recommendations.length > 0 ? (
              <ul className="space-y-3 text-sm text-slate-700">
                {recommendations.map((rec, index) => (
                  <li key={index} className="p-3 border border-slate-200 rounded-lg">
                    {rec}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-600">
                No recommendations reported yet.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}


'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  Brain,
  Cpu,
  Database,
  Network,
  TrendingUp,
  Zap,
  AlertCircle,
  CheckCircle2,
  Clock,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  Info
} from 'lucide-react';

interface SystemMetric {
  label: string;
  value: string;
  change: number;
  trend: 'up' | 'down';
  status: 'success' | 'warning' | 'error' | 'neutral';
  isReal: boolean;
}

export function SystemOverview() {
  const [agentCount, setAgentCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<SystemMetric[]>([
    { label: 'Active Agents', value: '0', change: 8.3, trend: 'up', status: 'success', isReal: true },
    { label: 'Tasks Completed', value: '2,847', change: 12.5, trend: 'up', status: 'success', isReal: false },
    { label: 'Avg Response Time', value: '0.82s', change: -15.2, trend: 'down', status: 'success', isReal: false },
    { label: 'Success Rate', value: '98.4%', change: 2.1, trend: 'up', status: 'success', isReal: false },
    { label: 'Model Accuracy', value: '94.7%', change: 3.2, trend: 'up', status: 'success', isReal: false },
    { label: 'System Load', value: '42%', change: -5.1, trend: 'down', status: 'success', isReal: false }
  ]);

  useEffect(() => {
    fetchAgentCount();
  }, []);

  const fetchAgentCount = async () => {
    try {
      const response = await fetch('/api/agents');
      if (response.ok) {
        const data = await response.json();
        const count = data?.total_count || data?.agents?.length || 0;
        setAgentCount(count);
        
        // Update the Active Agents metric with real data
        setMetrics(prev => prev.map(m => 
          m.label === 'Active Agents' 
            ? { ...m, value: count.toString() }
            : m
        ));
      }
    } catch (error) {
      console.error('Failed to fetch agent count:', error);
    } finally {
      setLoading(false);
    }
  };

  const [systemHealth, setSystemHealth] = useState({
    orchestrator: { status: 'operational', uptime: '99.98%', latency: '23ms' },
    performance_monitor: { status: 'operational', uptime: '99.95%', latency: '12ms' },
    learning_system: { status: 'operational', uptime: '99.92%', latency: '45ms' },
    plugin_system: { status: 'operational', uptime: '99.99%', latency: '8ms' },
    cicd_pipeline: { status: 'operational', uptime: '99.87%', latency: '156ms' },
    database: { status: 'operational', uptime: '99.99%', latency: '5ms' }
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'text-green-600 bg-green-100';
      case 'degraded': return 'text-yellow-600 bg-yellow-100';
      case 'down': return 'text-red-600 bg-red-100';
      default: return 'text-slate-600 bg-slate-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'degraded': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'down': return <AlertCircle className="w-5 h-5 text-red-600" />;
      default: return <Clock className="w-5 h-5 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Data Source Note */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-slate-900">
                <span className="inline-flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                  <strong>Real-time Data</strong>
                </span>
                {' '}shows live system metrics | {' '}
                <span className="inline-flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-amber-500 rounded-full"></span>
                  <strong>Simulated Data</strong>
                </span>
                {' '}represents demo values for visualization purposes
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index} className={`backdrop-blur-sm border-slate-200 hover:shadow-lg transition-all duration-300 ${
            metric.isReal ? 'bg-green-50/80 border-green-300' : 'bg-amber-50/80 border-amber-300'
          }`}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-600">{metric.label}</p>
                  <div className={`w-2 h-2 rounded-full ${metric.isReal ? 'bg-green-500' : 'bg-amber-500'}`} title={metric.isReal ? 'Real-time data' : 'Simulated data'}></div>
                </div>
                <div className={`flex items-center gap-1 text-xs font-semibold ${
                  metric.trend === 'up' 
                    ? metric.status === 'success' ? 'text-green-600' : 'text-red-600'
                    : metric.status === 'success' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {metric.trend === 'up' ? (
                    <ArrowUpRight className="w-3 h-3" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3" />
                  )}
                  {Math.abs(metric.change)}%
                </div>
              </div>
              <p className="text-3xl font-bold text-slate-900">{metric.value}</p>
              <p className="text-xs text-slate-500 mt-2">
                {metric.isReal ? 'Live data' : 'Demo value'}
              </p>
            </CardContent>
          </Card>
        ))}
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
            {Object.entries(systemHealth).map(([component, data]) => (
              <div key={component} className="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-semibold text-slate-900 capitalize">
                    {component.replace(/_/g, ' ')}
                  </h4>
                  {getStatusIcon(data.status)}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Status</span>
                    <Badge className={getStatusColor(data.status)}>
                      {data.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Uptime</span>
                    <span className="font-semibold text-slate-900">{data.uptime}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Latency</span>
                    <span className="font-semibold text-slate-900">{data.latency}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Resource Utilization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-purple-600" />
              Computational Resources
            </CardTitle>
            <CardDescription>Current system resource allocation and usage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">CPU Usage</span>
                <span className="text-sm font-bold text-slate-900">42.3%</span>
              </div>
              <Progress value={42.3} className="h-3" />
              <p className="text-xs text-slate-500 mt-1">8 cores / 16 threads active</p>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Memory Usage</span>
                <span className="text-sm font-bold text-slate-900">67.8%</span>
              </div>
              <Progress value={67.8} className="h-3" />
              <p className="text-xs text-slate-500 mt-1">21.7 GB / 32 GB allocated</p>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">GPU Utilization</span>
                <span className="text-sm font-bold text-slate-900">89.2%</span>
              </div>
              <Progress value={89.2} className="h-3" />
              <p className="text-xs text-slate-500 mt-1">NVIDIA A100 - Model inference active</p>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Network I/O</span>
                <span className="text-sm font-bold text-slate-900">34.5%</span>
              </div>
              <Progress value={34.5} className="h-3" />
              <p className="text-xs text-slate-500 mt-1">↑ 45 Mbps / ↓ 128 Mbps</p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-green-600" />
              Active Goals & Objectives
            </CardTitle>
            <CardDescription>Autonomous goal-driven behavior tracking</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { goal: 'Optimize Model Accuracy', progress: 78, status: 'in-progress', priority: 'high' },
              { goal: 'Reduce Response Latency', progress: 92, status: 'in-progress', priority: 'high' },
              { goal: 'Expand Training Dataset', progress: 45, status: 'in-progress', priority: 'medium' },
              { goal: 'Plugin Integration Tests', progress: 100, status: 'completed', priority: 'low' }
            ].map((goal, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-900">{goal.goal}</span>
                    <Badge variant={goal.priority === 'high' ? 'destructive' : goal.priority === 'medium' ? 'default' : 'secondary'}>
                      {goal.priority}
                    </Badge>
                  </div>
                  <span className="text-sm font-bold text-slate-900">{goal.progress}%</span>
                </div>
                <Progress value={goal.progress} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

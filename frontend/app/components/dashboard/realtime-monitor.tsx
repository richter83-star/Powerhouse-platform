
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
  Network,
  Cpu,
  HardDrive,
  Wifi
} from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  agent: string;
  message: string;
}

interface SystemEvent {
  id: string;
  time: string;
  type: 'task' | 'agent' | 'system' | 'learning';
  description: string;
  status: 'completed' | 'in-progress' | 'failed';
}

export function RealtimeMonitor() {
  const [logs, setLogs] = useState<LogEntry[]>([
    { id: '1', timestamp: '14:32:45', level: 'success', agent: 'ReAct-001', message: 'Task #2847 completed successfully with 96.2% confidence' },
    { id: '2', timestamp: '14:32:43', level: 'info', agent: 'Evaluator-001', message: 'Validation check passed for workflow #892' },
    { id: '3', timestamp: '14:32:41', level: 'info', agent: 'Memory-001', message: 'Stored 127 new data points in episodic memory' },
    { id: '4', timestamp: '14:32:38', level: 'warning', agent: 'Governor-001', message: 'Resource threshold reached: 85% CPU utilization' },
    { id: '5', timestamp: '14:32:35', level: 'success', agent: 'Debate-001', message: 'Consensus reached after 3 deliberation rounds' },
    { id: '6', timestamp: '14:32:32', level: 'info', agent: 'Planning-001', message: 'Generated execution plan with 12 sequential steps' },
    { id: '7', timestamp: '14:32:29', level: 'success', agent: 'ReAct-001', message: 'Task #2846 completed successfully with 94.8% confidence' },
    { id: '8', timestamp: '14:32:25', level: 'info', agent: 'Learning System', message: 'Autonomous retraining triggered: performance drop detected' }
  ]);

  const [events, setEvents] = useState<SystemEvent[]>([
    { id: '1', time: '2 sec ago', type: 'task', description: 'Data Analysis #2847 Completed', status: 'completed' },
    { id: '2', time: '5 sec ago', type: 'agent', description: 'Agent ReAct-002 Started Processing', status: 'in-progress' },
    { id: '3', time: '12 sec ago', type: 'learning', description: 'Model Accuracy Check: 95.7%', status: 'completed' },
    { id: '4', time: '23 sec ago', type: 'system', description: 'Plugin System Health Check', status: 'completed' },
    { id: '5', time: '45 sec ago', type: 'task', description: 'Risk Assessment #891 Completed', status: 'completed' },
    { id: '6', time: '1 min ago', type: 'agent', description: 'Agent Memory-001 Cache Refresh', status: 'completed' }
  ]);

  const [networkMetrics, setNetworkMetrics] = useState({
    requestsPerSecond: 234,
    avgResponseTime: 82,
    activeConnections: 1247,
    dataTransfer: '45.2 MB/s',
    uptime: '99.98%'
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Add new log entry
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date().toLocaleTimeString(),
        level: ['info', 'success', 'warning'][Math.floor(Math.random() * 3)] as any,
        agent: ['ReAct-001', 'Evaluator-001', 'Governor-001', 'Memory-001'][Math.floor(Math.random() * 4)],
        message: 'Real-time system activity detected'
      };
      setLogs((prev) => [newLog, ...prev].slice(0, 50));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success': return 'bg-green-100 text-green-700 border-green-200';
      case 'info': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'warning': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'error': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'success': return <CheckCircle2 className="w-4 h-4" />;
      case 'info': return <Activity className="w-4 h-4" />;
      case 'warning': return <AlertCircle className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getEventTypeIcon = (type: string) => {
    switch (type) {
      case 'task': return <CheckCircle2 className="w-4 h-4 text-blue-600" />;
      case 'agent': return <Cpu className="w-4 h-4 text-purple-600" />;
      case 'system': return <Network className="w-4 h-4 text-green-600" />;
      case 'learning': return <Zap className="w-4 h-4 text-orange-600" />;
      default: return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Simulated Data Notice */}
      <Card className="bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
            <p className="text-sm font-medium text-slate-900">
              <strong>Demo Mode:</strong> This real-time monitor displays simulated data for demonstration purposes. Live metrics will be available in production deployment.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Network Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Zap className="w-6 h-6 text-blue-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{networkMetrics.requestsPerSecond}</p>
                <p className="text-xs text-slate-600">req/sec</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-6 h-6 text-green-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{networkMetrics.avgResponseTime}ms</p>
                <p className="text-xs text-slate-600">avg response</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Wifi className="w-6 h-6 text-purple-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{networkMetrics.activeConnections}</p>
                <p className="text-xs text-slate-600">connections</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <Database className="w-6 h-6 text-orange-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{networkMetrics.dataTransfer}</p>
                <p className="text-xs text-slate-600">throughput</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-2">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
              <div>
                <p className="text-2xl font-bold text-slate-900">{networkMetrics.uptime}</p>
                <p className="text-xs text-slate-600">uptime</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Real-time Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  System Event Stream
                </CardTitle>
                <CardDescription>Real-time event feed from all components</CardDescription>
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
                {events.map((event) => (
                  <div 
                    key={event.id} 
                    className="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-slate-100 rounded-lg">
                        {getEventTypeIcon(event.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-sm font-medium text-slate-900">{event.description}</p>
                          <Badge className={
                            event.status === 'completed' ? 'bg-green-100 text-green-700 border-0' :
                            event.status === 'in-progress' ? 'bg-blue-100 text-blue-700 border-0' :
                            'bg-red-100 text-red-700 border-0'
                          }>
                            {event.status}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {event.time}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {event.type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
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
                  Agent Activity Logs
                </CardTitle>
                <CardDescription>Detailed logging from all agent instances</CardDescription>
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
                {logs.map((log) => (
                  <div 
                    key={log.id} 
                    className="p-3 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-start gap-2 mb-2">
                      <Badge className={getLevelColor(log.level)}>
                        <span className="flex items-center gap-1">
                          {getLevelIcon(log.level)}
                          {log.level}
                        </span>
                      </Badge>
                      <span className="text-xs text-slate-500 font-mono">{log.timestamp}</span>
                      <Badge variant="outline" className="text-xs">
                        {log.agent}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-700">{log.message}</p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* System Resource Monitor */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-orange-600" />
            Live Resource Utilization
          </CardTitle>
          <CardDescription>Real-time system resource monitoring and allocation</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900 rounded-lg p-6 font-mono text-sm">
            <div className="space-y-3">
              <div className="flex items-center justify-between text-green-400">
                <span>$ system-monitor --realtime</span>
                <span className="animate-pulse">▊</span>
              </div>
              <div className="text-slate-300 space-y-1">
                <p>[14:32:48] CPU: ████████████████████░░░░░░ 78.2% (8/16 cores active)</p>
                <p>[14:32:48] MEM: ████████████████████████░░ 89.1% (28.5GB / 32GB)</p>
                <p>[14:32:48] GPU: ████████████████████████░░ 92.4% (NVIDIA A100)</p>
                <p>[14:32:48] NET: ████████░░░░░░░░░░░░░░░░░░ 34.5% (↑45Mbps ↓128Mbps)</p>
                <p>[14:32:48] DSK: ████░░░░░░░░░░░░░░░░░░░░░░ 15.7% (1.2TB / 8TB)</p>
              </div>
              <div className="text-blue-400 pt-2">
                <p>[INFO] 12 agents active • 234 req/sec • 82ms avg latency</p>
                <p>[INFO] Learning system: Model v2.47.3 • Accuracy 95.7%</p>
                <p>[INFO] Next auto-retrain: 4h 12m</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

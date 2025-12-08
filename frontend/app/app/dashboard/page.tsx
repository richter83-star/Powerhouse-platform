
'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { SystemOverview } from '@/components/dashboard/system-overview';
import { PerformanceMetrics } from '@/components/dashboard/performance-metrics';
import { AgentOrchestration } from '@/components/dashboard/agent-orchestration';
import { LearningAnalytics } from '@/components/dashboard/learning-analytics';
import { RealtimeMonitor } from '@/components/dashboard/realtime-monitor';
import { InteractiveCommandCenter } from '@/components/interactive-command-center';
import { 
  Activity,
  Brain,
  Cpu,
  TrendingUp,
  Zap,
  Terminal,
  Sparkles
} from 'lucide-react';

export default function DashboardPage() {
  const { data: session, status } = useSession() || {};
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('command');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Allow demo mode without authentication
    setLoading(false);
  }, [status, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-300 font-medium">Loading Enterprise Dashboard...</p>
        </div>
      </div>
    );
  }

  const displayName = session?.user?.name || 'Demo User';

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 animate-gradient-xy" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className={`mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30 backdrop-blur-xl">
                  <Sparkles className="w-3 h-3 mr-1" />
                  19 AI Agents Active
                </Badge>
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                Enterprise Command Center
              </h1>
              <p className="text-slate-300 text-lg">
                Welcome back, <span className="font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">{displayName}</span> • Real-time Multi-Agent Platform Monitoring
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-4 py-2 bg-green-500/20 backdrop-blur-xl border border-green-500/30 rounded-xl">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-green-300">System Online</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className={`space-y-6 transition-all duration-700 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <TabsList className="bg-white/5 backdrop-blur-xl border border-white/10 p-1" role="tablist">
            <TabsTrigger 
              value="command" 
              className="gap-2 data-[state=active]:bg-white/10 data-[state=active]:text-white text-slate-400" 
              data-interactive="true" 
              aria-label="Command Center Tab"
              onClick={() => setActiveTab('command')}
            >
              <Terminal className="w-4 h-4" />
              Command Center
            </TabsTrigger>
            <TabsTrigger 
              value="overview" 
              className="gap-2 data-[state=active]:bg-white/10 data-[state=active]:text-white text-slate-400" 
              data-interactive="true" 
              aria-label="System Overview Tab"
              onClick={() => setActiveTab('overview')}
            >
              <Activity className="w-4 h-4" />
              System Overview
            </TabsTrigger>
            <TabsTrigger 
              value="performance" 
              className="gap-2 data-[state=active]:bg-white/10 data-[state=active]:text-white text-slate-400" 
              data-interactive="true" 
              aria-label="Performance Tab"
              onClick={() => setActiveTab('performance')}
            >
              <TrendingUp className="w-4 h-4" />
              Performance
            </TabsTrigger>
            <TabsTrigger 
              value="agents" 
              className="gap-2 data-[state=active]:bg-white/10 data-[state=active]:text-white text-slate-400" 
              data-interactive="true" 
              aria-label="Agent Orchestration Tab"
              onClick={() => setActiveTab('agents')}
            >
              <Cpu className="w-4 h-4" />
              Agent Orchestration
            </TabsTrigger>
            <TabsTrigger 
              value="learning" 
              className="gap-2 data-[state=active]:bg-white/10 data-[state=active]:text-white text-slate-400" 
              data-interactive="true" 
              aria-label="Learning Analytics Tab"
              onClick={() => setActiveTab('learning')}
            >
              <Brain className="w-4 h-4" />
              Learning Analytics
            </TabsTrigger>
            <TabsTrigger 
              value="realtime" 
              className="gap-2 data-[state=active]:bg-white/10 data-[state=active]:text-white text-slate-400" 
              data-interactive="true" 
              aria-label="Real-time Monitor Tab"
              onClick={() => setActiveTab('realtime')}
            >
              <Zap className="w-4 h-4" />
              Real-time Monitor
            </TabsTrigger>
          </TabsList>

          <TabsContent value="command" className="space-y-6">
            <InteractiveCommandCenter />
          </TabsContent>

          <TabsContent value="overview" className="space-y-6">
            <SystemOverview />
          </TabsContent>

          <TabsContent value="performance" className="space-y-6">
            <PerformanceMetrics />
          </TabsContent>

          <TabsContent value="agents" className="space-y-6">
            <AgentOrchestration />
          </TabsContent>

          <TabsContent value="learning" className="space-y-6">
            <LearningAnalytics />
          </TabsContent>

          <TabsContent value="realtime" className="space-y-6">
            <RealtimeMonitor />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

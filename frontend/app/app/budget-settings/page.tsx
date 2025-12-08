
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  DollarSign, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  Save,
  RefreshCw,
  Info,
  Shield
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, Legend } from 'recharts';

interface BudgetLimits {
  daily_max_dollars: number;
  auto_loop_max_iterations: number;
  auto_loop_max_concurrent: number;
  auto_loop_iteration_cost: number;
  max_llm_calls_per_hour: number;
  max_llm_calls_per_day: number;
  warning_threshold_percent: number;
}

interface UsageStats {
  date: string;
  total_spent: number;
  llm_calls: number;
  auto_loop_iterations: number;
  agent_costs: Record<string, number>;
}

interface BudgetStatus {
  budget_remaining: number;
  usage_percent: number;
  iterations_remaining: number;
  warning: boolean;
  allowed: boolean;
}

interface Dashboard {
  limits: BudgetLimits;
  usage: UsageStats;
  status: BudgetStatus;
  emergency_stop_enabled: boolean;
}

export default function BudgetSettingsPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [limits, setLimits] = useState<BudgetLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
      const response = await fetch(`${apiUrl}/api/v1/budget/dashboard`);
      const data = await response.json();
      
      if (data.success) {
        setDashboard(data.dashboard);
        setLimits(data.dashboard.limits);
      }
    } catch (error) {
      console.error('Error fetching budget dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveLimits = async () => {
    if (!limits) return;
    
    setSaving(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    
    try {
      const response = await fetch(`${apiUrl}/api/v1/budget/limits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(limits)
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSaveMessage('✅ Budget limits saved successfully!');
        fetchDashboard();
      } else {
        setSaveMessage('❌ Failed to save budget limits');
      }
    } catch (error) {
      console.error('Error saving limits:', error);
      setSaveMessage('❌ Error saving budget limits');
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(null), 3000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading budget settings...</p>
        </div>
      </div>
    );
  }

  if (!dashboard || !limits) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <Card className="bg-red-500/10 border-red-500/30">
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-red-300">Failed to load budget settings</p>
            <Button onClick={fetchDashboard} className="mt-4">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const usagePercent = dashboard.status.usage_percent;
  const getStatusColor = () => {
    if (usagePercent < 50) return 'text-green-400';
    if (usagePercent < 75) return 'text-yellow-400';
    if (usagePercent < 90) return 'text-orange-400';
    return 'text-red-400';
  };

  const getStatusBadge = () => {
    if (usagePercent < 50) return <Badge className="bg-green-500/20 text-green-300 border-green-500/30">Healthy</Badge>;
    if (usagePercent < 75) return <Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30">Monitor</Badge>;
    if (usagePercent < 90) return <Badge className="bg-orange-500/20 text-orange-300 border-orange-500/30">Warning</Badge>;
    return <Badge className="bg-red-500/20 text-red-300 border-red-500/30">Critical</Badge>;
  };

  // Prepare chart data
  const pieData = Object.entries(dashboard.usage.agent_costs).map(([name, cost]) => ({
    name,
    value: cost
  }));

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'];

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 animate-gradient-xy" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className={`mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl">
                <DollarSign className="w-7 h-7 text-white" />
              </div>
              <div>
                {getStatusBadge()}
                <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-emerald-400 to-teal-400 bg-clip-text text-transparent mt-2">
                  Budget & Rate Limits
                </h1>
                <p className="text-slate-300 mt-1">
                  Control spending and prevent runaway costs from autonomous agents
                </p>
              </div>
            </div>
            <Button
              onClick={fetchDashboard}
              variant="outline"
              className="bg-white/5 backdrop-blur-xl border-white/10 hover:bg-white/10"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Warning Alert */}
        {dashboard.status.warning && (
          <Alert className="mb-8 bg-orange-500/10 border-orange-500/30">
            <AlertTriangle className="h-4 w-4 text-orange-400" />
            <AlertDescription className="text-orange-200">
              You are approaching your daily budget limit ({usagePercent.toFixed(1)}% used). 
              Auto loop agents may be stopped automatically.
            </AlertDescription>
          </Alert>
        )}

        {/* Critical Alert */}
        {!dashboard.status.allowed && (
          <Alert className="mb-8 bg-red-500/10 border-red-500/30">
            <Shield className="h-4 w-4 text-red-400" />
            <AlertDescription className="text-red-200">
              ⛔ Daily budget limit reached! Auto loop agents have been stopped. 
              Budget will reset at midnight.
            </AlertDescription>
          </Alert>
        )}

        {/* Save Success Message */}
        {saveMessage && (
          <Alert className={`mb-8 ${saveMessage.includes('✅') ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
            <Info className="h-4 w-4" />
            <AlertDescription>{saveMessage}</AlertDescription>
          </Alert>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Daily Budget</p>
                  <p className="text-3xl font-bold text-white">${limits.daily_max_dollars}</p>
                </div>
                <DollarSign className="w-8 h-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Spent Today</p>
                  <p className={`text-3xl font-bold ${getStatusColor()}`}>
                    ${dashboard.usage.total_spent.toFixed(2)}
                  </p>
                </div>
                <TrendingUp className={`w-8 h-8 ${getStatusColor()}`} />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Remaining</p>
                  <p className="text-3xl font-bold text-blue-400">
                    ${dashboard.status.budget_remaining.toFixed(2)}
                  </p>
                </div>
                <Activity className="w-8 h-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Usage</p>
                  <p className={`text-3xl font-bold ${getStatusColor()}`}>
                    {usagePercent.toFixed(1)}%
                  </p>
                </div>
                {dashboard.status.allowed ? (
                  <CheckCircle className="w-8 h-8 text-green-400" />
                ) : (
                  <AlertTriangle className="w-8 h-8 text-red-400" />
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Budget Settings */}
        <Card className="mb-8 bg-white/5 backdrop-blur-xl border-white/10">
          <CardHeader>
            <CardTitle className="text-2xl bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
              Daily Budget Controls
            </CardTitle>
            <CardDescription className="text-slate-300">
              Set maximum spending limits to prevent unexpected costs
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Daily Maximum Spending */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <Label className="text-lg font-semibold text-white">
                  Daily Maximum Spending
                </Label>
                <span className="text-2xl font-bold text-green-400">
                  ${limits.daily_max_dollars}
                </span>
              </div>
              <Slider
                value={[limits.daily_max_dollars]}
                onValueChange={(value) => setLimits({ ...limits, daily_max_dollars: value[0] })}
                min={10}
                max={1000}
                step={10}
                className="mb-2"
              />
              <div className="flex justify-between text-xs text-slate-400">
                <span>$10</span>
                <span>$500</span>
                <span>$1000</span>
              </div>
            </div>

            {/* Warning Threshold */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <Label className="text-lg font-semibold text-white">
                  Warning Threshold
                </Label>
                <span className="text-2xl font-bold text-orange-400">
                  {limits.warning_threshold_percent}%
                </span>
              </div>
              <Slider
                value={[limits.warning_threshold_percent]}
                onValueChange={(value) => setLimits({ ...limits, warning_threshold_percent: value[0] })}
                min={50}
                max={95}
                step={5}
                className="mb-2"
              />
              <p className="text-xs text-slate-400 mt-2">
                You'll receive warnings when spending reaches this percentage of your daily budget
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Auto Loop Limits */}
        <Card className="mb-8 bg-white/5 backdrop-blur-xl border-white/10">
          <CardHeader>
            <CardTitle className="text-2xl bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Auto Loop Agent Limits
            </CardTitle>
            <CardDescription className="text-slate-300">
              Control autonomous agents to prevent runaway costs
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Max Iterations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label className="text-sm font-semibold text-white mb-2 block">
                  Maximum Iterations Per Day
                </Label>
                <Input
                  type="number"
                  value={limits.auto_loop_max_iterations}
                  onChange={(e) => setLimits({ ...limits, auto_loop_max_iterations: parseInt(e.target.value) || 0 })}
                  className="bg-white/5 border-white/10 text-white"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Current: {dashboard.usage.auto_loop_iterations} / {limits.auto_loop_max_iterations} used
                </p>
              </div>

              <div>
                <Label className="text-sm font-semibold text-white mb-2 block">
                  Maximum Concurrent Agents
                </Label>
                <Input
                  type="number"
                  value={limits.auto_loop_max_concurrent}
                  onChange={(e) => setLimits({ ...limits, auto_loop_max_concurrent: parseInt(e.target.value) || 0 })}
                  className="bg-white/5 border-white/10 text-white"
                />
                <p className="text-xs text-slate-400 mt-1">
                  How many auto loop agents can run simultaneously
                </p>
              </div>

              <div>
                <Label className="text-sm font-semibold text-white mb-2 block">
                  Cost Per Iteration
                </Label>
                <Input
                  type="number"
                  step="0.01"
                  value={limits.auto_loop_iteration_cost}
                  onChange={(e) => setLimits({ ...limits, auto_loop_iteration_cost: parseFloat(e.target.value) || 0 })}
                  className="bg-white/5 border-white/10 text-white"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Estimated cost per auto loop iteration (USD)
                </p>
              </div>

              <div>
                <Label className="text-sm font-semibold text-white mb-2 block">
                  Iterations Remaining
                </Label>
                <div className="text-3xl font-bold text-purple-400">
                  {dashboard.status.iterations_remaining}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Resets at midnight
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* LLM Rate Limits */}
        <Card className="mb-8 bg-white/5 backdrop-blur-xl border-white/10">
          <CardHeader>
            <CardTitle className="text-2xl bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              LLM API Rate Limits
            </CardTitle>
            <CardDescription className="text-slate-300">
              Limit LLM API calls to manage costs and prevent rate limit errors
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label className="text-sm font-semibold text-white mb-2 block">
                  Max Calls Per Hour
                </Label>
                <Input
                  type="number"
                  value={limits.max_llm_calls_per_hour}
                  onChange={(e) => setLimits({ ...limits, max_llm_calls_per_hour: parseInt(e.target.value) || 0 })}
                  className="bg-white/5 border-white/10 text-white"
                />
              </div>

              <div>
                <Label className="text-sm font-semibold text-white mb-2 block">
                  Max Calls Per Day
                </Label>
                <Input
                  type="number"
                  value={limits.max_llm_calls_per_day}
                  onChange={(e) => setLimits({ ...limits, max_llm_calls_per_day: parseInt(e.target.value) || 0 })}
                  className="bg-white/5 border-white/10 text-white"
                />
              </div>
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="text-sm text-blue-200">
                💡 <strong>Tip:</strong> Today you've made {dashboard.usage.llm_calls} LLM API calls.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Cost Tracking Dashboard */}
        {pieData.length > 0 && (
          <Card className="mb-8 bg-white/5 backdrop-blur-xl border-white/10">
            <CardHeader>
              <CardTitle className="text-2xl bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent">
                Cost Breakdown by Agent
              </CardTitle>
              <CardDescription className="text-slate-300">
                Track which agents are consuming the most budget
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: $${value.toFixed(2)}`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `$${value.toFixed(2)}`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Save Button */}
        <div className="flex justify-center">
          <Button
            onClick={saveLimits}
            disabled={saving}
            size="lg"
            className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-8 py-6 text-lg font-semibold"
          >
            {saving ? (
              <>
                <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-5 h-5 mr-2" />
                Save Budget Limits
              </>
            )}
          </Button>
        </div>

        {/* Info Card */}
        <Card className="mt-8 bg-blue-500/10 border-blue-500/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-200 mb-2">Important Information</h4>
                <ul className="text-sm text-blue-100 space-y-1 list-disc list-inside">
                  <li>Budget limits reset daily at midnight (local time)</li>
                  <li>Auto loop agents will stop automatically when limits are reached</li>
                  <li>Manual tasks can still be run with warnings when budget is exceeded</li>
                  <li>Cost estimates may vary based on actual usage patterns</li>
                  <li>Changes take effect immediately after saving</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}


'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Upload,
  Play,
  Pause,
  Settings,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
  Brain,
  GitBranch,
  Zap,
  Eye,
  Download,
  RefreshCw,
  Users,
  TrendingUp,
  Activity
} from 'lucide-react';

interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  progress: number;
  currentTask: string;
  color: string;
}

interface WorkflowStep {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'active' | 'completed';
  icon: any;
}

export function InteractiveCommandCenter() {
  const [demoMode, setDemoMode] = useState(true);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [agents, setAgents] = useState<AgentStatus[]>([
    { id: '1', name: 'Data Analyzer', status: 'idle', progress: 0, currentTask: 'Waiting for input', color: 'bg-blue-500' },
    { id: '2', name: 'Pattern Detector', status: 'idle', progress: 0, currentTask: 'Waiting for input', color: 'bg-purple-500' },
    { id: '3', name: 'Risk Evaluator', status: 'idle', progress: 0, currentTask: 'Waiting for input', color: 'bg-amber-500' },
    { id: '4', name: 'Report Generator', status: 'idle', progress: 0, currentTask: 'Waiting for input', color: 'bg-green-500' },
  ]);

  const workflowSteps: WorkflowStep[] = [
    { id: 1, title: 'Upload Data', description: 'Upload your file or connect your data source', status: 'pending', icon: Upload },
    { id: 2, title: 'Configure Analysis', description: 'Select analysis type and parameters', status: 'pending', icon: Settings },
    { id: 3, title: 'Agent Processing', description: 'AI agents analyze your data', status: 'pending', icon: Brain },
    { id: 4, title: 'Review Results', description: 'Examine insights and download reports', status: 'pending', icon: CheckCircle2 },
  ];

  const [steps, setSteps] = useState(workflowSteps);

  // Simulate agent work in demo mode
  useEffect(() => {
    if (!demoMode || !isProcessing) return;

    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => {
        if (agent.status === 'working') {
          const newProgress = Math.min(agent.progress + Math.random() * 15, 100);
          const tasks = [
            'Analyzing data patterns...',
            'Extracting key insights...',
            'Running validation checks...',
            'Generating recommendations...',
            'Finalizing analysis...'
          ];
          
          if (newProgress >= 100) {
            return { ...agent, progress: 100, status: 'completed', currentTask: 'Analysis complete' };
          }
          
          return {
            ...agent,
            progress: newProgress,
            currentTask: tasks[Math.floor(Math.random() * tasks.length)]
          };
        }
        return agent;
      }));
    }, 800);

    return () => clearInterval(interval);
  }, [demoMode, isProcessing]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setCurrentStep(1);
      updateStepStatus(0, 'completed');
      updateStepStatus(1, 'active');
    }
  };

  const updateStepStatus = (stepIndex: number, status: 'pending' | 'active' | 'completed') => {
    setSteps(prev => prev.map((step, idx) => 
      idx === stepIndex ? { ...step, status } : step
    ));
  };

  const startProcessing = () => {
    setIsProcessing(true);
    setCurrentStep(2);
    updateStepStatus(1, 'completed');
    updateStepStatus(2, 'active');

    // Activate agents one by one
    const agentActivationDelay = [0, 1000, 2000, 3000];
    agents.forEach((agent, index) => {
      setTimeout(() => {
        setAgents(prev => prev.map(a => 
          a.id === agent.id ? { ...a, status: 'working', progress: 0 } : a
        ));
      }, agentActivationDelay[index]);
    });

    // Complete workflow after all agents finish
    setTimeout(() => {
      setCurrentStep(3);
      updateStepStatus(2, 'completed');
      updateStepStatus(3, 'active');
      setIsProcessing(false);
    }, 12000);
  };

  const resetWorkflow = () => {
    setUploadedFile(null);
    setIsProcessing(false);
    setCurrentStep(0);
    setSteps(workflowSteps);
    setAgents(prev => prev.map(a => ({ 
      ...a, 
      status: 'idle', 
      progress: 0, 
      currentTask: 'Waiting for input' 
    })));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'working':
        return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Demo Mode Toggle */}
      <Card className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${demoMode ? 'bg-blue-500' : 'bg-gray-500'} transition-colors`}>
                <Eye className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">
                  {demoMode ? 'Demo Mode Active' : 'Real Data Mode'}
                </h3>
                <p className="text-sm text-slate-600">
                  {demoMode 
                    ? 'Simulated data and agent behavior for demonstration' 
                    : 'Live data processing with real API connections'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-slate-700">Demo</label>
              <Switch
                checked={!demoMode}
                onCheckedChange={(checked) => setDemoMode(!checked)}
                className="data-[state=checked]:bg-green-500"
              />
              <label className="text-sm font-medium text-slate-700">Real</label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-blue-600" />
            Workflow Progress
          </CardTitle>
          <CardDescription>Follow these steps to process your data</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.id}
                  className={`relative p-4 rounded-lg border-2 transition-all ${
                    step.status === 'completed'
                      ? 'border-green-500 bg-green-50'
                      : step.status === 'active'
                      ? 'border-blue-500 bg-blue-50 shadow-lg'
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div
                      className={`p-2 rounded-lg ${
                        step.status === 'completed'
                          ? 'bg-green-500'
                          : step.status === 'active'
                          ? 'bg-blue-500'
                          : 'bg-gray-300'
                      }`}
                    >
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="text-sm font-semibold text-slate-700">Step {step.id}</div>
                  </div>
                  <h4 className="font-semibold mb-1">{step.title}</h4>
                  <p className="text-xs text-slate-600">{step.description}</p>
                  {step.status === 'completed' && (
                    <CheckCircle2 className="absolute top-2 right-2 w-5 h-5 text-green-500" />
                  )}
                  {step.status === 'active' && (
                    <div className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Upload & Configuration */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-600" />
              Data Upload & Configuration
            </CardTitle>
            <CardDescription>Upload your files or configure data sources</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* File Upload Area */}
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                uploadedFile
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 bg-gray-50 hover:border-blue-500 hover:bg-blue-50'
              }`}
            >
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileUpload}
                accept=".csv,.xlsx,.json,.txt"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                {uploadedFile ? (
                  <div className="space-y-3">
                    <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto" />
                    <div>
                      <p className="font-semibold text-green-700">File Uploaded Successfully!</p>
                      <p className="text-sm text-slate-600 mt-1">{uploadedFile.name}</p>
                      <p className="text-xs text-slate-500">
                        {(uploadedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                    <div>
                      <p className="font-semibold text-slate-700">Click to upload or drag and drop</p>
                      <p className="text-sm text-slate-500 mt-1">
                        CSV, Excel, JSON, or TXT files
                      </p>
                      <p className="text-xs text-slate-400 mt-1">Max file size: 50MB</p>
                    </div>
                  </div>
                )}
              </label>
            </div>

            {/* Configuration Options */}
            {uploadedFile && (
              <div className="space-y-3 p-4 bg-slate-50 rounded-lg border">
                <h4 className="font-semibold text-sm">Analysis Configuration</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span>Perform deep analysis</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span>Generate visualizations</span>
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span>Export detailed report</span>
                  </label>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={startProcessing}
                disabled={!uploadedFile || isProcessing}
                className="flex-1"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Analysis
                  </>
                )}
              </Button>
              <Button
                onClick={resetWorkflow}
                variant="outline"
                size="lg"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>

            {/* Instructions */}
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-sm text-blue-900 mb-2">📋 Quick Start Guide</h4>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Upload your data file using the upload area above</li>
                <li>Configure analysis options (optional)</li>
                <li>Click "Start Analysis" to process your data</li>
                <li>Watch the agents work in real-time</li>
                <li>Download your results when complete</li>
              </ol>
            </div>
          </CardContent>
        </Card>

        {/* Agent Visualization */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              AI Agents in Action
            </CardTitle>
            <CardDescription>Real-time visualization of agent activity</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`p-4 rounded-lg border-2 transition-all ${
                  agent.status === 'working'
                    ? 'border-blue-500 bg-blue-50 shadow-md'
                    : agent.status === 'completed'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full ${agent.color} flex items-center justify-center`}>
                      <Brain className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h4 className="font-semibold">{agent.name}</h4>
                      <p className="text-xs text-slate-600">{agent.currentTask}</p>
                    </div>
                  </div>
                  {getStatusIcon(agent.status)}
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600">Progress</span>
                    <span className="font-semibold">{Math.round(agent.progress)}%</span>
                  </div>
                  <Progress value={agent.progress} className="h-2" />
                </div>
                {agent.status === 'working' && (
                  <div className="flex items-center gap-1 mt-2">
                    <Zap className="w-3 h-3 text-yellow-500 animate-pulse" />
                    <span className="text-xs text-slate-600">Processing...</span>
                  </div>
                )}
              </div>
            ))}

            {/* Agent Network Visualization */}
            <div className="p-4 bg-slate-50 rounded-lg border">
              <h4 className="font-semibold text-sm mb-3">Agent Communication Network</h4>
              <div className="relative h-32 flex items-center justify-center">
                <svg className="w-full h-full">
                  {/* Connection lines */}
                  <line x1="20%" y1="50%" x2="40%" y2="30%" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="40%" y1="30%" x2="60%" y2="30%" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="60%" y1="30%" x2="80%" y2="50%" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="20%" y1="50%" x2="40%" y2="70%" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="40%" y1="70%" x2="60%" y2="70%" stroke="#cbd5e1" strokeWidth="2" />
                  <line x1="60%" y1="70%" x2="80%" y2="50%" stroke="#cbd5e1" strokeWidth="2" />
                  
                  {/* Agent nodes */}
                  {agents.map((agent, index) => {
                    const positions = [
                      { x: '20%', y: '50%' },
                      { x: '40%', y: '30%' },
                      { x: '60%', y: '70%' },
                      { x: '80%', y: '50%' },
                    ];
                    const pos = positions[index];
                    const isActive = agent.status === 'working';
                    
                    return (
                      <g key={agent.id}>
                        {isActive && (
                          <circle
                            cx={pos.x}
                            cy={pos.y}
                            r="12"
                            fill={agent.color.replace('bg-', '#')}
                            opacity="0.3"
                            className="animate-ping"
                          />
                        )}
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r="8"
                          fill={isActive ? '#3b82f6' : '#94a3b8'}
                          className="transition-all"
                        />
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results Section */}
      {currentStep >= 3 && (
        <Card className="border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              Analysis Complete
            </CardTitle>
            <CardDescription>Your results are ready for review</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Insights Generated</p>
                    <p className="text-2xl font-bold">47</p>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Confidence Score</p>
                    <p className="text-2xl font-bold">94%</p>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <CheckCircle2 className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Processing Time</p>
                    <p className="text-2xl font-bold">12s</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button className="flex-1" size="lg">
                <Download className="w-4 h-4 mr-2" />
                Download Full Report
              </Button>
              <Button variant="outline" size="lg">
                <Eye className="w-4 h-4 mr-2" />
                View Details
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

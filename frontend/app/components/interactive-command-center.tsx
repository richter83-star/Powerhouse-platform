'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Upload,
  Play,
  Settings,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
  Brain,
  GitBranch,
  Eye,
  Download,
  RefreshCw,
  Users,
  Activity
} from 'lucide-react';

interface WorkflowAgentStatus {
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  step?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  error?: { message?: string };
}

interface WorkflowStatusSummary {
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_step: string;
  agent_statuses: WorkflowAgentStatus[];
  risk_score?: number | null;
  risk_level?: string | null;
  error?: { message?: string };
}

interface WorkflowResults {
  workflow_id: string;
  status: string;
  analysis?: {
    summary?: string;
    obligations?: string[];
    gaps?: string[];
    evaluation_score?: number;
    perspectives?: Array<{ perspective?: string; analysis?: string }>;
  };
  risk_assessment?: {
    risk_level?: string;
    risk_score?: number;
    findings?: string[];
    recommendations?: string[];
    affected_regulations?: string[];
  };
  compliance_report?: string;
}

export function InteractiveCommandCenter() {
  const [query, setQuery] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatusSummary | null>(null);
  const [workflowResults, setWorkflowResults] = useState<WorkflowResults | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  const [showDetails, setShowDetails] = useState(false);
  const detailsRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!workflowId) {
      return;
    }

    let isActive = true;
    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/workflows/status?workflowId=${workflowId}`);
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.error || 'Failed to load workflow status');
        }
        if (!isActive) {
          return;
        }
        setWorkflowStatus(data);
        setIsProcessing(data.status === 'running' || data.status === 'pending');

        if (data.status === 'completed') {
          const resultsRes = await fetch(`/api/workflows/results?workflowId=${workflowId}`);
          const resultsData = await resultsRes.json();
          if (resultsRes.ok) {
            setWorkflowResults(resultsData);
          }
        }
        if (data.status === 'failed') {
          setError(data?.error?.message || 'Workflow failed');
        }
      } catch (err: any) {
        if (isActive) {
          setError(err?.message || 'Failed to fetch workflow status');
        }
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 4000);
    return () => {
      isActive = false;
      clearInterval(interval);
    };
  }, [workflowId]);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const startProcessing = async () => {
    setError('');
    setWorkflowResults(null);
    setWorkflowStatus(null);

    if (!query.trim() || query.trim().length < 10) {
      setError('Enter a compliance query (min 10 characters) before starting.');
      return;
    }

    try {
      setIsProcessing(true);
      const formData = new FormData();
      formData.append('query', query);
      if (uploadedFile) {
        formData.append('file', uploadedFile);
      }
      formData.append('parameters', JSON.stringify({}));

      const response = await fetch('/api/workflows/compliance', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error || 'Failed to start workflow');
      }

      const nextWorkflowId = data?.workflowId || data?.workflow_id;
      if (!nextWorkflowId) {
        throw new Error('Workflow ID missing from response');
      }
      setWorkflowId(nextWorkflowId);
    } catch (err: any) {
      setError(err?.message || 'Failed to start workflow');
      setIsProcessing(false);
    }
  };

  const resetWorkflow = () => {
    setUploadedFile(null);
    setQuery('');
    setWorkflowId(null);
    setWorkflowStatus(null);
    setWorkflowResults(null);
    setIsProcessing(false);
    setError('');
    setShowDetails(false);
  };

  const handleDownloadReport = () => {
    if (!workflowResults) {
      return;
    }
    const blob = new Blob([JSON.stringify(workflowResults, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `powerhouse-report-${workflowResults.workflow_id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleViewDetails = () => {
    setShowDetails(true);
    setTimeout(() => {
      detailsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
  };

  const steps = workflowStatus?.agent_statuses?.length
    ? workflowStatus.agent_statuses.map((agent, index) => ({
        id: index + 1,
        title: agent.step || agent.agent_name,
        description:
          agent.status === 'running'
            ? 'In progress'
            : agent.status === 'completed'
              ? 'Completed'
              : agent.status === 'failed'
                ? 'Failed'
                : 'Pending',
        status: agent.status === 'running' ? 'active' : agent.status === 'completed' ? 'completed' : 'pending'
      }))
    : [];

  const formatPercent = (value?: number | null) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Real Data Indicator */}
      <Card className="border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-gray-700">
                <Eye className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Compliance Workflow</h3>
                <p className="text-sm text-slate-600">Live execution using real workflow APIs</p>
              </div>
            </div>
            <Badge variant="secondary" className="bg-green-100 text-green-700 border-green-200">
              Connected
            </Badge>
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
          <CardDescription>Track compliance workflow execution</CardDescription>
        </CardHeader>
        <CardContent>
          {workflowStatus ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>Current Step: {workflowStatus.current_step}</span>
                  <span>{(workflowStatus.progress_percentage ?? 0).toFixed(0)}%</span>
                </div>
                <Progress value={workflowStatus.progress_percentage ?? 0} className="h-2" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {steps.map((step) => (
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
                        <Activity className="w-5 h-5 text-white" />
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
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-600">
              Start a workflow to see live progress updates.
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Upload & Configuration */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-600" />
              Compliance Query
            </CardTitle>
            <CardDescription>Submit a compliance question and optional document</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Compliance Query</label>
              <Textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Describe the compliance question to analyze..."
                rows={5}
              />
              <p className="text-xs text-slate-500">Minimum 10 characters.</p>
            </div>

            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                uploadedFile
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-300 bg-gray-50 hover:border-blue-500 hover:bg-blue-50'
              }`}
            >
              <Input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileUpload}
                accept=".pdf,.doc,.docx,.txt"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                {uploadedFile ? (
                  <div className="space-y-3">
                    <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto" />
                    <div>
                      <p className="font-semibold text-green-700">File Uploaded Successfully</p>
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
                        PDF, DOC, DOCX, or TXT files
                      </p>
                      <p className="text-xs text-slate-400 mt-1">Max file size: 10MB</p>
                    </div>
                  </div>
                )}
              </label>
            </div>

            {error && (
              <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
                <AlertCircle className="w-4 h-4 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                onClick={startProcessing}
                disabled={!query.trim() || isProcessing}
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

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-sm text-blue-900 mb-2">Quick Start Guide</h4>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Provide a compliance query for analysis</li>
                <li>Upload optional policy documents</li>
                <li>Click "Start Analysis" to run the workflow</li>
                <li>Monitor agent progress in real time</li>
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
            <CardDescription>Status from the active workflow</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {workflowStatus?.agent_statuses?.length ? (
              workflowStatus.agent_statuses.map((agent) => (
                <div
                  key={agent.agent_name}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    agent.status === 'running'
                      ? 'border-blue-500 bg-blue-50 shadow-md'
                      : agent.status === 'completed'
                        ? 'border-green-500 bg-green-50'
                        : agent.status === 'failed'
                          ? 'border-red-500 bg-red-50'
                          : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
                        <Brain className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h4 className="font-semibold capitalize">{agent.agent_name}</h4>
                        <p className="text-xs text-slate-600">{agent.step || 'Workflow step'}</p>
                      </div>
                    </div>
                    <Badge className={agent.status === 'running' ? 'bg-blue-100 text-blue-700 border-0' : agent.status === 'completed' ? 'bg-green-100 text-green-700 border-0' : agent.status === 'failed' ? 'bg-red-100 text-red-700 border-0' : 'bg-slate-100 text-slate-700 border-0'}>
                      {agent.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-600 space-y-1">
                    <div>Started: {agent.started_at ? new Date(agent.started_at).toLocaleTimeString() : '--'}</div>
                    <div>Completed: {agent.completed_at ? new Date(agent.completed_at).toLocaleTimeString() : '--'}</div>
                    {agent.error?.message && (
                      <div className="text-red-600">Error: {agent.error.message}</div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-sm text-slate-600">
                No active workflow agents yet. Start a workflow to view agent status.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Results Section */}
      {workflowResults && (
        <Card className="border-2 border-green-200 bg-gradient-to-r from-green-50 to-emerald-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              Analysis Complete
            </CardTitle>
            <CardDescription>Your compliance results are ready for review</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-blue-100 rounded-lg">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Risk Score</p>
                    <p className="text-2xl font-bold">
                      {formatPercent(workflowResults.risk_assessment?.risk_score ?? workflowStatus?.risk_score ?? null)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-purple-100 rounded-lg">
                    <Settings className="w-6 h-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Risk Level</p>
                    <p className="text-2xl font-bold">
                      {workflowResults.risk_assessment?.risk_level || workflowStatus?.risk_level || '--'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-green-100 rounded-lg">
                    <CheckCircle2 className="w-6 h-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-600">Evaluation Score</p>
                    <p className="text-2xl font-bold">
                      {formatPercent(workflowResults.analysis?.evaluation_score ?? null)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button className="flex-1" size="lg" onClick={handleDownloadReport}>
                <Download className="w-4 h-4 mr-2" />
                Download Full Report
              </Button>
              <Button variant="outline" size="lg" onClick={handleViewDetails}>
                <Eye className="w-4 h-4 mr-2" />
                View Details
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {showDetails && workflowResults && (
        <Card ref={detailsRef} className="border-2 border-slate-200">
          <CardHeader>
            <CardTitle>Analysis Details</CardTitle>
            <CardDescription>Summary of compliance findings and recommendations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-700">
            <p>{workflowResults.analysis?.summary || 'No summary available.'}</p>
            {workflowResults.risk_assessment?.findings?.length ? (
              <div>
                <p className="font-semibold mb-1">Findings</p>
                <ul className="list-disc list-inside space-y-1">
                  {workflowResults.risk_assessment.findings.map((finding, idx) => (
                    <li key={idx}>{finding}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {workflowResults.risk_assessment?.recommendations?.length ? (
              <div>
                <p className="font-semibold mb-1">Recommendations</p>
                <ul className="list-disc list-inside space-y-1">
                  {workflowResults.risk_assessment.recommendations.map((rec, idx) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  );
}


'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ComplianceResult } from '@/lib/types';
import { 
  FileText, 
  AlertTriangle, 
  CheckCircle,
  Download,
  ArrowLeft,
  Shield
} from 'lucide-react';
import Link from 'next/link';

export default function ResultsPage() {
  const { data: session, status } = useSession() || {};
  const router = useRouter();
  const params = useParams();
  const workflowId = params?.id as string;

  const [results, setResults] = useState<ComplianceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  useEffect(() => {
    if (status === 'authenticated' && workflowId) {
      fetchResults();
    }
  }, [status, workflowId]);

  const fetchResults = async () => {
    try {
      const response = await fetch(`/api/workflows/results?workflowId=${workflowId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch results');
      }

      const data = await response.json();
      setResults(data);
      setError('');
    } catch (err: any) {
      console.error('Results fetch error:', err);
      setError(err?.message || 'Failed to fetch results');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!results) return;
    
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `compliance-results-${workflowId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return null;
  }

  const riskColors = {
    low: 'bg-green-100 text-green-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800',
  };

  const riskIcons = {
    low: <CheckCircle className="w-5 h-5 text-green-600" />,
    medium: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
    high: <AlertTriangle className="w-5 h-5 text-orange-600" />,
    critical: <AlertTriangle className="w-5 h-5 text-red-600" />,
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Compliance Report
                </h1>
                <p className="text-gray-600">
                  Workflow ID: <span className="font-mono text-sm">{workflowId}</span>
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
              <Link href="/dashboard">
                <Button variant="ghost">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-8 bg-red-50 border-red-200">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-800">Error</h4>
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {results && (
          <>
            {/* Risk Summary */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Risk Assessment
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Overall Risk Level</p>
                    <div className="flex items-center gap-2">
                      {riskIcons?.[results?.overallRisk || 'low']}
                      <Badge className={riskColors?.[results?.overallRisk || 'low']}>
                        {results?.overallRisk?.toUpperCase() || 'LOW'}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Risk Score</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {results?.riskScore || 0}/100
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Analysis Date</p>
                    <p className="text-sm font-medium text-gray-900">
                      {results?.timestamp ? new Date(results.timestamp).toLocaleString() : 'N/A'}
                    </p>
                  </div>
                </div>
                
                {results?.summary && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-2">Executive Summary</h4>
                    <p className="text-sm text-gray-700">{results.summary}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Agent Analyses */}
            {results?.agentAnalyses && results.agentAnalyses.length > 0 && (
              <div className="mb-8 space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Agent Analyses</h2>
                {results.agentAnalyses.map((analysis, index) => (
                  <Card key={analysis?.agentId || index}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-purple-600 text-sm font-bold">
                            {analysis?.agentName?.charAt(0) || 'A'}
                          </span>
                        </div>
                        {analysis?.agentName || 'Unknown Agent'}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {analysis?.analysis && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Analysis</h4>
                          <p className="text-sm text-gray-700">{analysis.analysis}</p>
                        </div>
                      )}
                      
                      {analysis?.findings && analysis.findings.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Key Findings</h4>
                          <ul className="space-y-2">
                            {analysis.findings.map((finding, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm">
                                <span className="text-blue-600 mt-1">•</span>
                                <span className="text-gray-700">{finding}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {analysis?.recommendations && analysis.recommendations.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Recommendations</h4>
                          <ul className="space-y-2">
                            {analysis.recommendations.map((rec, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm">
                                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-700">{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Overall Recommendations */}
            {results?.recommendations && results.recommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Overall Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {results.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-white text-xs font-bold">{idx + 1}</span>
                        </div>
                        <p className="text-sm text-gray-700">{rec}</p>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}

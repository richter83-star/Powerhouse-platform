
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

  const riskLevel = results?.risk_assessment?.risk_level || 'low';
  const riskScoreRaw = results?.risk_assessment?.risk_score ?? 0;
  const riskScorePercent = Math.round(riskScoreRaw * 100);

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
                      {riskIcons?.[riskLevel as keyof typeof riskIcons]}
                      <Badge className={riskColors?.[riskLevel as keyof typeof riskColors]}>
                        {riskLevel.toUpperCase()}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Risk Score</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {riskScorePercent}/100
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">Analysis Date</p>
                    <p className="text-sm font-medium text-gray-900">
                      {results?.completed_at
                        ? new Date(results.completed_at).toLocaleString()
                        : results?.created_at
                          ? new Date(results.created_at).toLocaleString()
                          : 'N/A'}
                    </p>
                  </div>
                </div>
                
                {results?.analysis?.summary && (
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-2">Executive Summary</h4>
                    <p className="text-sm text-gray-700">{results.analysis.summary}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Findings and Recommendations */}
            {(results?.risk_assessment?.findings?.length || results?.risk_assessment?.recommendations?.length) && (
              <Card className="mb-8">
                <CardHeader>
                  <CardTitle>Findings & Recommendations</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {results?.risk_assessment?.findings && results.risk_assessment.findings.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Findings</h4>
                      <ul className="space-y-2">
                        {results.risk_assessment.findings.map((finding, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm">
                            <span className="text-blue-600 mt-1">•</span>
                            <span className="text-gray-700">{finding}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {results?.risk_assessment?.recommendations && results.risk_assessment.recommendations.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Recommendations</h4>
                      <ul className="space-y-2">
                        {results.risk_assessment.recommendations.map((rec, idx) => (
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
            )}

            {(results?.analysis?.obligations?.length || results?.analysis?.gaps?.length) && (
              <Card className="mb-8">
                <CardHeader>
                  <CardTitle>Obligations & Gaps</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {results?.analysis?.obligations && results.analysis.obligations.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Obligations</h4>
                      <ul className="space-y-2">
                        {results.analysis.obligations.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm">
                            <span className="text-blue-600 mt-1">•</span>
                            <span className="text-gray-700">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {results?.analysis?.gaps && results.analysis.gaps.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Gaps</h4>
                      <ul className="space-y-2">
                        {results.analysis.gaps.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm">
                            <span className="text-blue-600 mt-1">•</span>
                            <span className="text-gray-700">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {results?.compliance_report && (
              <Card>
                <CardHeader>
                  <CardTitle>Compliance Report</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="whitespace-pre-wrap text-sm text-gray-700">
                    {results.compliance_report}
                  </pre>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}

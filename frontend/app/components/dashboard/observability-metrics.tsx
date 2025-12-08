
"use client"

import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Activity,
  Database,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
  Zap,
  Shield,
  Archive
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface MetricsData {
  counters: Record<string, number>
  gauges: Record<string, number>
  histograms: Record<string, {
    count: number
    sum: number
    avg: number
    min: number
    max: number
  }>
}

interface CircuitBreakerState {
  name: string
  state: 'closed' | 'open' | 'half_open'
  failure_count: number
  success_count: number
  last_failure_time: number | null
  config: {
    failure_threshold: number
    success_threshold: number
    timeout: number
  }
}

interface CheckpointMetadata {
  checkpoint_id: string
  timestamp: string
  agent_id: string
  workflow_id: string
  size_bytes: number
  compressed: boolean
}

interface HealthStatus {
  status: string
  timestamp: string
  circuit_breakers: {
    total: number
    open: number
    degraded: boolean
  }
  checkpoints: {
    total: number
  }
  metrics: {
    counters: number
    gauges: number
    histograms: number
  }
}

export function ObservabilityMetrics() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [circuitBreakers, setCircuitBreakers] = useState<Record<string, CircuitBreakerState>>({})
  const [checkpoints, setCheckpoints] = useState<CheckpointMetadata[]>([])
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchObservabilityData = async () => {
    try {
      const [metricsRes, circuitBreakersRes, checkpointsRes, healthRes] = await Promise.all([
        fetch('http://localhost:8000/api/observability/metrics'),
        fetch('http://localhost:8000/api/observability/circuit-breakers'),
        fetch('http://localhost:8000/api/observability/checkpoints'),
        fetch('http://localhost:8000/api/observability/health')
      ])

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json()
        setMetrics(metricsData)
      }

      if (circuitBreakersRes.ok) {
        const cbData = await circuitBreakersRes.json()
        setCircuitBreakers(cbData)
      }

      if (checkpointsRes.ok) {
        const checkpointsData = await checkpointsRes.json()
        setCheckpoints(checkpointsData.checkpoints || [])
      }

      if (healthRes.ok) {
        const healthData = await healthRes.json()
        setHealth(healthData)
      }

      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching observability data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchObservabilityData()
    const interval = setInterval(fetchObservabilityData, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const getCircuitBreakerBadge = (state: string) => {
    switch (state) {
      case 'closed':
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />CLOSED</Badge>
      case 'open':
        return <Badge variant="destructive"><AlertCircle className="w-3 h-3 mr-1" />OPEN</Badge>
      case 'half_open':
        return <Badge variant="secondary"><Activity className="w-3 h-3 mr-1" />HALF-OPEN</Badge>
      default:
        return <Badge variant="outline">{state}</Badge>
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString()
    } catch {
      return timestamp
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">System Observability</h2>
          <p className="text-muted-foreground">
            Real-time monitoring, telemetry, and resilience metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </span>
          <Button onClick={fetchObservabilityData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Health Status */}
      {health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              System Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex flex-col items-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">
                  {health.status === 'healthy' ? (
                    <CheckCircle className="w-10 h-10 text-green-500" />
                  ) : (
                    <AlertCircle className="w-10 h-10 text-yellow-500" />
                  )}
                </div>
                <div className="text-sm text-muted-foreground mt-2">Status</div>
                <div className="text-lg font-semibold capitalize">{health.status}</div>
              </div>

              <div className="flex flex-col items-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">{health.circuit_breakers.total}</div>
                <div className="text-sm text-muted-foreground mt-2">Circuit Breakers</div>
                <div className="text-sm">
                  {health.circuit_breakers.open > 0 ? (
                    <span className="text-red-500">{health.circuit_breakers.open} open</span>
                  ) : (
                    <span className="text-green-500">All healthy</span>
                  )}
                </div>
              </div>

              <div className="flex flex-col items-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">{health.checkpoints.total}</div>
                <div className="text-sm text-muted-foreground mt-2">Checkpoints</div>
                <Archive className="w-5 h-5 text-muted-foreground mt-1" />
              </div>

              <div className="flex flex-col items-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">
                  {health.metrics.counters + health.metrics.gauges + health.metrics.histograms}
                </div>
                <div className="text-sm text-muted-foreground mt-2">Total Metrics</div>
                <TrendingUp className="w-5 h-5 text-muted-foreground mt-1" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Counters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Counters
            </CardTitle>
            <CardDescription>Cumulative event counts</CardDescription>
          </CardHeader>
          <CardContent>
            {metrics && Object.keys(metrics.counters).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(metrics.counters).slice(0, 8).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center">
                    <span className="text-sm font-medium truncate flex-1">{key}</span>
                    <Badge variant="secondary">{value}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No counter metrics available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Gauges */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Gauges
            </CardTitle>
            <CardDescription>Current values and states</CardDescription>
          </CardHeader>
          <CardContent>
            {metrics && Object.keys(metrics.gauges).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(metrics.gauges).slice(0, 8).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center">
                    <span className="text-sm font-medium truncate flex-1">{key}</span>
                    <Badge variant="outline">{value.toFixed(2)}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No gauge metrics available</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Histograms */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Histograms
            </CardTitle>
            <CardDescription>Distribution statistics</CardDescription>
          </CardHeader>
          <CardContent>
            {metrics && Object.keys(metrics.histograms).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(metrics.histograms).slice(0, 4).map(([key, value]) => (
                  <div key={key} className="space-y-2">
                    <div className="text-sm font-medium truncate">{key}</div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <div className="text-muted-foreground">Avg</div>
                        <div className="font-semibold">{value.avg.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Min</div>
                        <div className="font-semibold">{value.min.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Max</div>
                        <div className="font-semibold">{value.max.toFixed(2)}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <TrendingDown className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No histogram metrics available</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Circuit Breakers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Circuit Breakers
          </CardTitle>
          <CardDescription>
            Failure protection and automatic recovery
          </CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(circuitBreakers).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(circuitBreakers).map(([name, breaker]) => (
                <div key={name} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="font-semibold">{breaker.name}</div>
                    {getCircuitBreakerBadge(breaker.state)}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Failures</div>
                      <div className="font-semibold">
                        {breaker.failure_count} / {breaker.config.failure_threshold}
                      </div>
                      <Progress
                        value={(breaker.failure_count / breaker.config.failure_threshold) * 100}
                        className="h-2 mt-1"
                      />
                    </div>
                    
                    <div>
                      <div className="text-muted-foreground">Successes</div>
                      <div className="font-semibold">
                        {breaker.success_count} / {breaker.config.success_threshold}
                      </div>
                      <Progress
                        value={(breaker.success_count / breaker.config.success_threshold) * 100}
                        className="h-2 mt-1"
                      />
                    </div>
                  </div>
                  
                  {breaker.last_failure_time && (
                    <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Last failure: {new Date(breaker.last_failure_time * 1000).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Shield className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No circuit breakers active</p>
              <p className="text-sm mt-1">Circuit breakers will appear as they are created</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Checkpoints */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            State Checkpoints
          </CardTitle>
          <CardDescription>
            Persistent state snapshots for recovery
          </CardDescription>
        </CardHeader>
        <CardContent>
          {checkpoints.length > 0 ? (
            <div className="space-y-3">
              {checkpoints.slice(0, 10).map((checkpoint) => (
                <div
                  key={checkpoint.checkpoint_id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1">
                    <div className="font-medium text-sm mb-1">
                      {checkpoint.agent_id} / {checkpoint.workflow_id}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-2">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(checkpoint.timestamp)}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-sm font-semibold">{formatBytes(checkpoint.size_bytes)}</div>
                      {checkpoint.compressed && (
                        <Badge variant="outline" className="text-xs">Compressed</Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Archive className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No checkpoints available</p>
              <p className="text-sm mt-1">Checkpoints will be created automatically during workflow execution</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

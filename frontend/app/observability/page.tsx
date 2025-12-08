
import { Metadata } from 'next'
import { ObservabilityMetrics } from '@/components/dashboard/observability-metrics'

export const metadata: Metadata = {
  title: 'System Observability | Powerhouse B2B Platform',
  description: 'Real-time system metrics, telemetry, and resilience monitoring',
}

export default function ObservabilityPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <ObservabilityMetrics />
    </div>
  )
}

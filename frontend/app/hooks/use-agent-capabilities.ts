'use client';

import { useQuery } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface AgentCapability {
  name: string;
  capabilities: string[];
  description?: string;
}

export interface AgentCapabilitiesResponse {
  agents: AgentCapability[];
  total: number;
}

async function fetchCapabilities(): Promise<AgentCapabilitiesResponse> {
  const res = await fetch(`${API_BASE}/agents/capabilities`);
  if (!res.ok) throw new Error(`Failed to fetch agent capabilities: ${res.status}`);
  return res.json();
}

export function useAgentCapabilities() {
  return useQuery<AgentCapabilitiesResponse, Error>({
    queryKey: ['agent-capabilities'],
    queryFn: fetchCapabilities,
    staleTime: 60_000,
    retry: 2,
  });
}

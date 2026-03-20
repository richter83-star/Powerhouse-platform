export const USE_CASES = [
  {
    id: 'compliance',
    name: 'Compliance & Legal',
    description: 'Regulatory compliance, legal research, document analysis',
  },
  {
    id: 'sales',
    name: 'Sales & Marketing',
    description: 'Lead generation, customer research, market analysis',
  },
  {
    id: 'operations',
    name: 'Operations',
    description: 'Process automation, workflow optimization, task management',
  },
  {
    id: 'research',
    name: 'Research & Analysis',
    description: 'Data analysis, market research, competitive intelligence',
  },
  {
    id: 'support',
    name: 'Customer Support',
    description: 'Ticket management, knowledge base, customer service',
  },
  {
    id: 'other',
    name: 'Other',
    description: 'Custom use case or exploring the platform',
  },
];

export type UseCase = (typeof USE_CASES)[number];

export function getUseCase(id: string): UseCase | undefined {
  return USE_CASES.find((uc) => uc.id === id);
}

export function getDefaultUseCase(): UseCase {
  return USE_CASES[USE_CASES.length - 1]; // 'other'
}

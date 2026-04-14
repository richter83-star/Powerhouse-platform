
'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import {
  LayoutDashboard,
  Brain,
  GitBranch,
  Network,
  Activity,
  Sparkles,
  Database,
  Plug,
  Package,
  ShoppingBag,
  CreditCard,
  Settings,
  Headphones,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

type SystemStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  statusKey?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Platform',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'AI Agents', href: '/agents', icon: Brain, statusKey: 'agents' },
    ],
  },
  {
    title: 'Deploy',
    items: [
      { label: 'CI/CD Pipeline', href: '/cicd', icon: GitBranch },
      { label: 'Architecture', href: '/architecture', icon: Network },
    ],
  },
  {
    title: 'Monitor',
    items: [
      { label: 'Observability', href: '/observability', icon: Activity, statusKey: 'observability' },
      { label: 'AI Quality', href: '/ai-quality', icon: Sparkles },
      { label: 'Data Manager', href: '/data-manager', icon: Database },
    ],
  },
  {
    title: 'Ecosystem',
    items: [
      { label: 'Integrations', href: '/integrations', icon: Plug },
      { label: 'Plugins', href: '/plugins', icon: Package },
      { label: 'Marketplace', href: '/marketplace', icon: ShoppingBag },
    ],
  },
  {
    title: 'Account',
    items: [
      { label: 'Billing', href: '/billing', icon: CreditCard },
      { label: 'Settings', href: '/settings', icon: Settings },
      { label: 'Support', href: '/support', icon: Headphones },
    ],
  },
];

const STATUS_DOT: Record<SystemStatus, string> = {
  healthy: 'bg-green-400',
  degraded: 'bg-yellow-400',
  unhealthy: 'bg-red-400',
  unknown: 'bg-slate-600',
};

function MiniDot({ status }: { status: SystemStatus }) {
  return (
    <span
      className={`inline-block w-1.5 h-1.5 rounded-full flex-shrink-0 ${STATUS_DOT[status]}`}
    />
  );
}

export function Sidebar() {
  const { status } = useSession() || {};
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState<Record<string, SystemStatus>>({
    agents: 'unknown',
    observability: 'unknown',
  });

  const fetchStatus = useCallback(async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const [agentsRes, obsRes] = await Promise.allSettled([
      fetch('/api/agents'),
      fetch(`${apiUrl}/api/observability/health`),
    ]);

    const next: Record<string, SystemStatus> = { agents: 'unknown', observability: 'unknown' };

    if (agentsRes.status === 'fulfilled' && agentsRes.value.ok) {
      const data = await agentsRes.value.json();
      const count = data?.total_count ?? data?.agents?.length ?? 0;
      next.agents = count > 0 ? 'healthy' : 'unknown';
    }

    if (obsRes.status === 'fulfilled' && obsRes.value.ok) {
      const data = await obsRes.value.json();
      const openCircuits = data?.circuit_breakers?.open ?? 0;
      next.observability = openCircuits > 0 ? 'degraded' : 'healthy';
    }

    setSystemStatus(next);
  }, []);

  useEffect(() => {
    if (status !== 'authenticated') return;
    fetchStatus();
    const t = setInterval(fetchStatus, 30_000);
    return () => clearInterval(t);
  }, [status, fetchStatus]);

  if (status !== 'authenticated') return null;

  return (
    <aside
      className={`
        hidden md:flex flex-col flex-shrink-0 sticky top-16 h-[calc(100vh-4rem)]
        bg-slate-950/80 backdrop-blur-xl border-r border-white/8
        transition-all duration-300 overflow-hidden
        ${collapsed ? 'w-14' : 'w-56'}
      `}
    >
      {/* Toggle button */}
      <div className="flex justify-end px-2 pt-3 pb-1">
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-all duration-200"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 pb-4 space-y-1">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-2">
            {/* Section title — hidden when collapsed */}
            {!collapsed && (
              <p className="px-2 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-slate-600 select-none">
                {section.title}
              </p>
            )}
            {collapsed && <div className="my-2 mx-2 h-px bg-white/8" />}

            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive =
                pathname === item.href || pathname.startsWith(item.href + '/');
              const itemStatus = item.statusKey ? systemStatus[item.statusKey] : undefined;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? item.label : undefined}
                  className={`
                    flex items-center gap-2.5 px-2 py-2 rounded-lg text-sm transition-all duration-200 group relative
                    ${
                      isActive
                        ? 'bg-white/10 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-white/8'
                    }
                  `}
                >
                  <Icon
                    className={`w-4 h-4 flex-shrink-0 transition-colors ${
                      isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'
                    }`}
                  />
                  {!collapsed && (
                    <>
                      <span className="flex-1 truncate text-xs font-medium">{item.label}</span>
                      {itemStatus && <MiniDot status={itemStatus} />}
                    </>
                  )}
                  {/* Collapsed: status dot overlaid on icon */}
                  {collapsed && itemStatus && itemStatus !== 'unknown' && (
                    <span
                      className={`absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full ${STATUS_DOT[itemStatus]}`}
                    />
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>
    </aside>
  );
}

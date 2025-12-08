
'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  Network, 
  Shield, 
  Zap, 
  Users, 
  ArrowRight,
  Headphones,
  TrendingUp,
  Search,
  Sparkles,
  MessageSquare,
  Target,
  BarChart,
  Brain,
  FileText,
  Lightbulb,
  BarChart3,
  Settings,
  Plug,
  CheckCircle,
  Database
} from 'lucide-react';
import { useUseCase } from '@/contexts/use-case-context';

const iconMap: Record<string, any> = {
  Shield,
  Zap,
  Users,
  Network,
  Headphones,
  TrendingUp,
  Search,
  Sparkles,
  MessageSquare,
  Target,
  BarChart,
  Brain,
  FileText,
  Lightbulb,
  BarChart3,
  Settings,
  Plug,
  CheckCircle,
  Database
};

export function DynamicHome() {
  const { currentUseCase } = useUseCase();

  const getIcon = (iconName: string, className?: string) => {
    const IconComponent = iconMap[iconName];
    return IconComponent ? <IconComponent className={className} /> : null;
  };

  const getColorClasses = (color: string) => {
    const colorMap: Record<string, { bg: string; text: string; gradient: string; hover: string }> = {
      blue: { 
        bg: 'bg-blue-100', 
        text: 'text-blue-600', 
        gradient: 'from-blue-600 to-purple-600',
        hover: 'hover:from-blue-700 hover:to-purple-700'
      },
      green: { 
        bg: 'bg-green-100', 
        text: 'text-green-600', 
        gradient: 'from-green-600 to-teal-600',
        hover: 'hover:from-green-700 hover:to-teal-700'
      },
      purple: { 
        bg: 'bg-purple-100', 
        text: 'text-purple-600', 
        gradient: 'from-purple-600 to-pink-600',
        hover: 'hover:from-purple-700 hover:to-pink-700'
      },
      indigo: { 
        bg: 'bg-indigo-100', 
        text: 'text-indigo-600', 
        gradient: 'from-indigo-600 to-cyan-600',
        hover: 'hover:from-indigo-700 hover:to-cyan-700'
      },
      slate: { 
        bg: 'bg-slate-100', 
        text: 'text-slate-600', 
        gradient: 'from-slate-600 to-zinc-600',
        hover: 'hover:from-slate-700 hover:to-zinc-700'
      },
      orange: { 
        bg: 'bg-orange-100', 
        text: 'text-orange-600', 
        gradient: 'from-orange-600 to-red-600',
        hover: 'hover:from-orange-700 hover:to-red-700'
      },
      yellow: { 
        bg: 'bg-yellow-100', 
        text: 'text-yellow-600', 
        gradient: 'from-yellow-600 to-orange-600',
        hover: 'hover:from-yellow-700 hover:to-orange-700'
      },
      red: { 
        bg: 'bg-red-100', 
        text: 'text-red-600', 
        gradient: 'from-red-600 to-pink-600',
        hover: 'hover:from-red-700 hover:to-pink-700'
      },
      teal: { 
        bg: 'bg-teal-100', 
        text: 'text-teal-600', 
        gradient: 'from-teal-600 to-blue-600',
        hover: 'hover:from-teal-700 hover:to-blue-700'
      },
    };
    return colorMap[color] || colorMap.blue;
  };

  const primaryColors = getColorClasses(currentUseCase.primaryColor);
  const secondaryColors = getColorClasses(currentUseCase.secondaryColor);

  // Calculate total agent count
  const totalAgents = currentUseCase.agentGroups.reduce((sum, group) => sum + group.agents.length, 0);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className={`relative bg-gradient-to-br from-${currentUseCase.primaryColor}-50 via-white to-${currentUseCase.secondaryColor}-50 py-20`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className={`inline-flex items-center gap-2 ${primaryColors.bg} ${primaryColors.text} px-4 py-2 rounded-full text-sm font-medium mb-6`}>
              {getIcon(currentUseCase.icon, "w-4 h-4")}
              {currentUseCase.tagline}
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              {currentUseCase.heroTitle}
              <span className={primaryColors.text}> {currentUseCase.heroSubtitle}</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              {currentUseCase.description}
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/signup">
                <Button size="lg" className="gap-2">
                  Get Started
                  <ArrowRight className="w-5 h-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Powerful Features for {currentUseCase.name}
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Built for teams that need reliable, intelligent automation.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {currentUseCase.features.map((feature, index) => {
              const featureColors = index === 0 ? primaryColors : index === 1 ? secondaryColors : getColorClasses('green');
              return (
                <Card key={index} className="p-8 hover:shadow-xl transition-shadow">
                  <div className={`${featureColors.bg} w-14 h-14 rounded-lg flex items-center justify-center mb-6`}>
                    {getIcon(feature.icon, `w-7 h-7 ${featureColors.text}`)}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Agents Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              {totalAgents} Specialized AI Agents
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              A comprehensive multi-agent ecosystem designed for {currentUseCase.name.toLowerCase()}, 
              intelligent reasoning, and autonomous decision-making.
            </p>
          </div>

          {/* Agent Groups */}
          {currentUseCase.agentGroups.map((group, groupIndex) => {
            const groupColors = getColorClasses(group.color);
            return (
              <div key={groupIndex} className={groupIndex < currentUseCase.agentGroups.length - 1 ? "mb-12" : ""}>
                <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                  {getIcon(group.icon, `w-6 h-6 ${groupColors.text}`)}
                  {group.title}
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {group.agents.map((agent, agentIndex) => (
                    <Card key={agentIndex} className="p-6 bg-white hover:shadow-lg transition-shadow">
                      <div className="flex items-center gap-3 mb-3">
                        <div className={`w-10 h-10 ${groupColors.bg} rounded-full flex items-center justify-center flex-shrink-0`}>
                          {getIcon(group.icon, `w-5 h-5 ${groupColors.text}`)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 truncate">{agent.name}</h4>
                          {agent.type && (
                            <p className={`text-xs ${groupColors.text} truncate`}>{agent.type}</p>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{agent.description}</p>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}

          {/* View All Agents CTA */}
          <div className="mt-12 text-center">
            <Link href="/agents">
              <Button size="lg" variant="outline" className="gap-2">
                View All Agent Details
                <ArrowRight className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className={`py-20 bg-gradient-to-r ${primaryColors.gradient} text-white`}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to {currentUseCase.ctaText}?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join enterprise teams using Powerhouse to automate {currentUseCase.name.toLowerCase()}.
          </p>
          <Link href="/signup">
            <Button size="lg" variant="secondary" className="gap-2">
              Start Free Trial
              <ArrowRight className="w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}

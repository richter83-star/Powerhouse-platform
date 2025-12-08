
'use client';

import Link from 'next/link';
import { useSession, signOut } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { UseCaseSelector } from '@/components/use-case-selector';
import { useUseCase } from '@/contexts/use-case-context';
import { 
  Network, 
  LayoutDashboard, 
  Users, 
  LogOut,
  Menu,
  X,
  Package,
  GitBranch,
  Settings,
  ChevronDown,
  Database,
  FileText,
  Activity,
  Plug,
  Sparkles,
  Building2
} from 'lucide-react';
import { useState } from 'react';

export function Navbar() {
  const { data: session, status } = useSession() || {};
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { currentUseCase } = useUseCase();

  const isLoggedIn = status === 'authenticated';
  
  // Only show technical/system links for generic use case
  const showSystemLinks = currentUseCase.id === 'generic';

  return (
    <nav className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-xl border-b border-white/10 shadow-lg">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center gap-4">
            <Link href={isLoggedIn ? '/dashboard' : '/'} className="flex items-center gap-2 group">
              <div className="p-1.5 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg group-hover:scale-110 transition-transform duration-300">
                <Network className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Powerhouse
                </span>
                <p className="text-[10px] text-slate-400 -mt-1">{currentUseCase.tagline}</p>
              </div>
            </Link>
            
            {/* Use Case Selector */}
            <div className="hidden lg:block border-l border-white/10 pl-4">
              <UseCaseSelector />
            </div>
          </div>

          {/* Desktop Navigation */}
          {isLoggedIn && (
            <div className="hidden md:flex items-center gap-1">
              <Link 
                href="/dashboard" 
                className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-300"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              
              <Link 
                href="/agents" 
                className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-300"
              >
                <Users className="w-4 h-4" />
                Agents
              </Link>

              {/* Marketplace Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-300">
                    <Package className="w-4 h-4" />
                    Marketplace
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48 bg-slate-900 border-white/10 backdrop-blur-xl">
                  <DropdownMenuItem asChild>
                    <Link href="/marketplace" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                      <Package className="w-4 h-4" />
                      Browse Marketplace
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/agent-builder" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                      <Users className="w-4 h-4" />
                      Agent Builder
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/app-builder" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                      <LayoutDashboard className="w-4 h-4" />
                      App Builder
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem asChild>
                    <Link href="/my-sales" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                      <Database className="w-4 h-4" />
                      My Sales
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/budget-settings" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                      <Settings className="w-4 h-4" />
                      Budget Settings
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Only show System menu for generic use case */}
              {showSystemLinks && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-300">
                      <Settings className="w-4 h-4" />
                      System
                      <ChevronDown className="w-3 h-3" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-48 bg-slate-900 border-white/10 backdrop-blur-xl">
                    <DropdownMenuItem asChild>
                      <Link href="/architecture" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Network className="w-4 h-4" />
                        Architecture
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/plugins" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Package className="w-4 h-4" />
                        Plugins
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/cicd" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <GitBranch className="w-4 h-4" />
                        CI/CD Pipeline
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/observability" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Activity className="w-4 h-4" />
                        Observability
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/integrations" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Plug className="w-4 h-4" />
                        Integrations
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/ai-quality" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Sparkles className="w-4 h-4" />
                        AI Quality
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuItem asChild>
                      <Link href="/commercial" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Building2 className="w-4 h-4" />
                        Commercial
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator className="bg-white/10" />
                    <DropdownMenuItem asChild>
                      <Link href="/data-manager" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Database className="w-4 h-4" />
                        Data Manager
                      </Link>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          )}

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isLoggedIn ? (
              <div className="flex items-center gap-3">
                <Link 
                  href="/settings"
                  className="flex items-center gap-2 px-3 py-2 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg transition-all duration-300"
                >
                  <Settings className="w-4 h-4" />
                </Link>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button className="flex items-center gap-2 px-3 py-2 hover:bg-white/10 rounded-lg transition-all duration-300">
                      <div className="text-right">
                        <p className="text-sm font-medium text-white">
                          {session?.user?.name}
                        </p>
                        <p className="text-xs text-slate-400">Administrator</p>
                      </div>
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48 bg-slate-900 border-white/10 backdrop-blur-xl">
                    <DropdownMenuItem asChild>
                      <Link href="/settings" className="flex items-center gap-2 w-full cursor-pointer text-slate-300 hover:text-white hover:bg-white/10">
                        <Settings className="w-4 h-4" />
                        Settings
                      </Link>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator className="bg-white/10" />
                    <DropdownMenuItem 
                      onClick={() => signOut({ callbackUrl: '/' })}
                      className="flex items-center gap-2 cursor-pointer text-red-400 hover:text-red-300 hover:bg-red-500/10"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-white/10">
                    Login
                  </Button>
                </Link>
                <Link href="/signup">
                  <Button size="sm" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-slate-300 hover:text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-white/10 bg-slate-900/50 backdrop-blur-xl">
            {isLoggedIn && (
              <div className="flex flex-col gap-2 mb-4">
                <Link 
                  href="/dashboard" 
                  className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Link>
                <Link 
                  href="/agents" 
                  className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Users className="w-4 h-4" />
                  Agents
                </Link>
                
                {showSystemLinks && (
                  <>
                    <div className="px-3 py-2 text-xs font-semibold text-slate-400 uppercase mt-2">System</div>
                    <Link 
                      href="/architecture" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Network className="w-4 h-4" />
                      Architecture
                    </Link>
                    <Link 
                      href="/plugins" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Package className="w-4 h-4" />
                      Plugins
                    </Link>
                    <Link 
                      href="/cicd" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <GitBranch className="w-4 h-4" />
                      CI/CD
                    </Link>
                    <Link 
                      href="/observability" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Activity className="w-4 h-4" />
                      Observability
                    </Link>
                    <Link 
                      href="/integrations" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Plug className="w-4 h-4" />
                      Integrations
                    </Link>
                    <Link 
                      href="/ai-quality" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Sparkles className="w-4 h-4" />
                      AI Quality
                    </Link>
                    <Link 
                      href="/commercial" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Building2 className="w-4 h-4" />
                      Commercial
                    </Link>
                    <Link 
                      href="/data-manager" 
                      className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Database className="w-4 h-4" />
                      Data Manager
                    </Link>
                  </>
                )}
              </div>
            )}
            <div className="flex flex-col gap-2">
              {isLoggedIn ? (
                <>
                  <div className="text-sm mb-2 px-3">
                    <p className="font-medium text-white">{session?.user?.name}</p>
                    <p className="text-xs text-slate-400">Administrator</p>
                  </div>
                  <Link 
                    href="/settings" 
                    className="flex items-center gap-2 text-slate-300 hover:text-white py-2 px-3 hover:bg-white/10 rounded-lg transition-all duration-300"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </Link>
                  <Button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      signOut({ callbackUrl: '/' });
                    }}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2 w-full border-white/10 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="ghost" size="sm" className="w-full text-slate-300 hover:text-white hover:bg-white/10">
                      Login
                    </Button>
                  </Link>
                  <Link href="/signup" onClick={() => setMobileMenuOpen(false)}>
                    <Button size="sm" className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                      Get Started
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

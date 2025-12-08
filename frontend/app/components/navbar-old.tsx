
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
import { 
  Network, 
  LayoutDashboard, 
  FileSearch, 
  Users, 
  LogOut,
  Menu,
  X,
  Package,
  GitBranch,
  Settings,
  ChevronDown,
  Database
} from 'lucide-react';
import { useState } from 'react';

export function Navbar() {
  const { data: session, status } = useSession() || {};
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isLoggedIn = status === 'authenticated';

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center gap-4">
            <Link href={isLoggedIn ? '/dashboard' : '/'} className="flex items-center gap-2">
              <div className="p-1.5 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg">
                <Network className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
                  Powerhouse
                </span>
                <p className="text-[10px] text-slate-500 -mt-1">AI Platform</p>
              </div>
            </Link>
            
            {/* Use Case Selector */}
            <div className="hidden lg:block border-l border-gray-300 pl-4">
              <UseCaseSelector />
            </div>
          </div>

          {/* Desktop Navigation */}
          {isLoggedIn && (
            <div className="hidden md:flex items-center gap-1">
              <Link 
                href="/dashboard" 
                className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              
              {/* System Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                    <Settings className="w-4 h-4" />
                    System
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-48">
                  <DropdownMenuItem asChild>
                    <Link href="/architecture" className="flex items-center gap-2 w-full cursor-pointer">
                      <Network className="w-4 h-4" />
                      Architecture
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/plugins" className="flex items-center gap-2 w-full cursor-pointer">
                      <Package className="w-4 h-4" />
                      Plugins
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/cicd" className="flex items-center gap-2 w-full cursor-pointer">
                      <GitBranch className="w-4 h-4" />
                      CI/CD Pipeline
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Link 
                href="/data-manager" 
                className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <Database className="w-4 h-4" />
                Data Manager
              </Link>
              <Link 
                href="/agents" 
                className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <Users className="w-4 h-4" />
                Agents
              </Link>
            </div>
          )}

          {/* Auth Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isLoggedIn ? (
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {session?.user?.name}
                  </p>
                  <p className="text-xs text-gray-500">Administrator</p>
                </div>
                <Button
                  onClick={() => signOut({ callbackUrl: '/' })}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Login
                  </Button>
                </Link>
                <Link href="/signup">
                  <Button size="sm">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
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
          <div className="md:hidden py-4 border-t border-gray-200">
            {isLoggedIn && (
              <div className="flex flex-col gap-2 mb-4">
                <Link 
                  href="/dashboard" 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600 py-2 px-3 hover:bg-blue-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  Dashboard
                </Link>
                <Link 
                  href="/architecture" 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600 py-2 px-3 hover:bg-blue-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Network className="w-4 h-4" />
                  Architecture
                </Link>
                <Link 
                  href="/plugins" 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600 py-2 px-3 hover:bg-blue-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Package className="w-4 h-4" />
                  Plugins
                </Link>
                <Link 
                  href="/cicd" 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600 py-2 px-3 hover:bg-blue-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <GitBranch className="w-4 h-4" />
                  CI/CD
                </Link>
                <Link 
                  href="/data-manager" 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600 py-2 px-3 hover:bg-blue-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Database className="w-4 h-4" />
                  Data Manager
                </Link>
                <Link 
                  href="/agents" 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600 py-2 px-3 hover:bg-blue-50 rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  <Users className="w-4 h-4" />
                  Agents
                </Link>
              </div>
            )}
            <div className="flex flex-col gap-2">
              {isLoggedIn ? (
                <>
                  <div className="text-sm text-gray-600 mb-2 px-3">
                    <p className="font-medium text-gray-900">{session?.user?.name}</p>
                    <p className="text-xs">Administrator</p>
                  </div>
                  <Button
                    onClick={() => signOut({ callbackUrl: '/' })}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2 w-full"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="ghost" size="sm" className="w-full">
                      Login
                    </Button>
                  </Link>
                  <Link href="/signup" onClick={() => setMobileMenuOpen(false)}>
                    <Button size="sm" className="w-full">
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

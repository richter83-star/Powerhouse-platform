
import Link from 'next/link';
import { Network } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Network className="w-8 h-8 text-blue-500" />
              <span className="text-xl font-bold text-white">Powerhouse</span>
            </div>
            <p className="text-sm text-gray-400">
              Enterprise-grade B2B multi-agent platform for intelligent automation and decision-making.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Platform</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/dashboard" className="hover:text-blue-400 transition-colors">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link href="/architecture" className="hover:text-blue-400 transition-colors">
                  Architecture
                </Link>
              </li>
              <li>
                <Link href="/agents" className="hover:text-blue-400 transition-colors">
                  Agent Management
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-white font-semibold mb-4">Company</h3>
            <p className="text-sm text-gray-400">
              © 2025 Powerhouse Platform. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}

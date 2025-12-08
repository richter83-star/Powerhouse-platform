
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/components/auth-provider';
import { UseCaseProvider } from '@/contexts/use-case-context';
import { PreferencesProvider } from '@/contexts/preferences-context';
import { ToastProvider } from '@/components/toast-provider';
import { ErrorBoundary } from '@/components/error-boundary';
import { AccessibilityWidget } from '@/components/accessibility-widget';
import { Navbar } from '@/components/navbar';
import { Footer } from '@/components/footer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Powerhouse B2B Platform',
  description: 'Enterprise-grade multi-agent platform for any business challenge',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ErrorBoundary>
          <AuthProvider>
            <PreferencesProvider>
              <ToastProvider>
                <UseCaseProvider>
                  <div className="min-h-screen flex flex-col">
                    <a href="#main-content" className="skip-to-content">
                      Skip to main content
                    </a>
                    <Navbar />
                    <main id="main-content" className="flex-1">
                      {children}
                    </main>
                    <Footer />
                    <AccessibilityWidget />
                  </div>
                </UseCaseProvider>
              </ToastProvider>
            </PreferencesProvider>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}

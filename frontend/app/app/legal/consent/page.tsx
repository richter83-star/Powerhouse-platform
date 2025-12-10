'use client';

import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  CheckCircle, 
  XCircle, 
  Download,
  Trash2,
  AlertTriangle,
  FileText,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { useToast } from '@/components/toast-provider';
import { useSession } from 'next-auth/react';

interface Consent {
  id: string;
  consent_type: string;
  version: string;
  consented: boolean;
  created_at: string;
  revoked_at: string | null;
}

interface ExportRequest {
  id: string;
  status: string;
  format: string;
  requested_at: string;
  completed_at: string | null;
  expires_at: string | null;
  file_path: string | null;
}

export default function ConsentPage() {
  const { data: session } = useSession();
  const { success, error: showError } = useToast();
  const [consents, setConsents] = useState<Consent[]>([]);
  const [exportRequests, setExportRequests] = useState<ExportRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [privacyVersion] = useState('1.0'); // Current privacy policy version

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  useEffect(() => {
    loadConsents();
    loadExportRequests();
  }, []);

  const loadConsents = async () => {
    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/compliance/consent`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConsents(data);
      }
    } catch (err) {
      console.error('Failed to load consents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadExportRequests = async () => {
    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      // This would need an endpoint to list export requests
      // For now, we'll just track locally
    } catch (err) {
      console.error('Failed to load export requests:', err);
    }
  };

  const handleConsentChange = async (consentType: string, consented: boolean) => {
    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      
      if (consented) {
        const response = await fetch(`${apiUrl}/api/v1/compliance/consent`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            consent_type: consentType,
            version: privacyVersion,
            consented: true
          })
        });

        if (response.ok) {
          success('Consent Updated', `You have ${consented ? 'granted' : 'revoked'} ${consentType} consent`);
          await loadConsents();
        }
      } else {
        const response = await fetch(`${apiUrl}/api/v1/compliance/consent/revoke/${consentType}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          success('Consent Revoked', `You have revoked ${consentType} consent`);
          await loadConsents();
        }
      }
    } catch (err: any) {
      showError('Update Failed', err.message || 'Failed to update consent');
    }
  };

  const handleRequestExport = async () => {
    try {
      setIsExporting(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/compliance/export/request?format=json`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        success('Export Requested', 'Your data export has been requested. You will be notified when it is ready.');
        await loadExportRequests();
      } else {
        const errorData = await response.json();
        showError('Export Failed', errorData.detail || 'Failed to request data export');
      }
    } catch (err: any) {
      showError('Export Error', err.message || 'Failed to request data export');
    } finally {
      setIsExporting(false);
    }
  };

  const handleRequestDeletion = async () => {
    try {
      setIsDeleting(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/compliance/deletion/request?deletion_type=full`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        success('Deletion Requested', 'Your data deletion request has been submitted. You will receive a verification email.');
        setDeleteDialogOpen(false);
      } else {
        const errorData = await response.json();
        showError('Deletion Failed', errorData.detail || 'Failed to request data deletion');
      }
    } catch (err: any) {
      showError('Deletion Error', err.message || 'Failed to request data deletion');
    } finally {
      setIsDeleting(false);
    }
  };

  const getConsentStatus = (consentType: string) => {
    const consent = consents.find(c => c.consent_type === consentType && !c.revoked_at);
    return consent?.consented ?? false;
  };

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Shield className="h-8 w-8" />
          Privacy & Consent Management
        </h1>
        <p className="text-muted-foreground mt-2">
          Manage your privacy preferences and data rights (GDPR compliant)
        </p>
      </div>

      {/* Consent Management */}
      <Card>
        <CardHeader>
          <CardTitle>Consent Preferences</CardTitle>
          <CardDescription>
            Control how your data is used. You can change these preferences at any time.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex-1">
              <Label htmlFor="necessary" className="text-base font-medium">
                Necessary Cookies
              </Label>
              <p className="text-sm text-muted-foreground mt-1">
                Required for the platform to function. Cannot be disabled.
              </p>
            </div>
            <Switch id="necessary" checked={true} disabled />
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex-1">
              <Label htmlFor="analytics" className="text-base font-medium">
                Analytics
              </Label>
              <p className="text-sm text-muted-foreground mt-1">
                Help us improve by sharing usage analytics (anonymized).
              </p>
            </div>
            <Switch
              id="analytics"
              checked={getConsentStatus('analytics')}
              onCheckedChange={(checked) => handleConsentChange('analytics', checked)}
            />
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex-1">
              <Label htmlFor="marketing" className="text-base font-medium">
                Marketing
              </Label>
              <p className="text-sm text-muted-foreground mt-1">
                Receive product updates and marketing communications.
              </p>
            </div>
            <Switch
              id="marketing"
              checked={getConsentStatus('marketing')}
              onCheckedChange={(checked) => handleConsentChange('marketing', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Data Export */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Data Export (Right to Data Portability)
          </CardTitle>
          <CardDescription>
            Request a copy of all your personal data in a machine-readable format.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert className="mb-4">
            <FileText className="h-4 w-4" />
            <AlertTitle>About Data Export</AlertTitle>
            <AlertDescription>
              You can request a complete export of all your personal data. The export will be available for 30 days.
            </AlertDescription>
          </Alert>
          <Button onClick={handleRequestExport} disabled={isExporting}>
            {isExporting ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Requesting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Request Data Export
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Data Deletion */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5" />
            Data Deletion (Right to be Forgotten)
          </CardTitle>
          <CardDescription>
            Request permanent deletion of all your personal data.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Warning: Permanent Deletion</AlertTitle>
            <AlertDescription>
              This action cannot be undone. All your data, including workflows, agents, and account information, will be permanently deleted.
            </AlertDescription>
          </Alert>
          
          <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive">
                <Trash2 className="h-4 w-4 mr-2" />
                Request Data Deletion
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirm Data Deletion</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete all your data? This action is permanent and cannot be undone.
                  You will receive a verification email to confirm this request.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleRequestDeletion} disabled={isDeleting}>
                  {isDeleting ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Confirm Deletion'
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Privacy Policy */}
      <Card>
        <CardHeader>
          <CardTitle>Privacy Policy</CardTitle>
          <CardDescription>
            Current version: {privacyVersion}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            By using Powerhouse, you agree to our Privacy Policy and Terms of Service.
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              View Privacy Policy
            </Button>
            <Button variant="outline" size="sm">
              View Terms of Service
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


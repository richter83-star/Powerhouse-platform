'use client';

import React, { useState, useEffect } from 'react';
import { 
  Key, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  RefreshCw,
  Download,
  Trash2,
  Plus,
  Shield,
  Monitor,
  Calendar
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useToast } from '@/components/toast-provider';
import { useSession } from 'next-auth/react';

interface LicenseInfo {
  license_key: string;
  type: string;
  status: string;
  seats: number;
  max_devices: number;
  device_count: number;
  features: string[];
  issued_at: string | null;
  activated_at: string | null;
  expires_at: string | null;
  trial_ends_at: string | null;
  validation: {
    valid: boolean;
    message: string;
    days_remaining: number | null;
    grace_period_days: number | null;
  };
  activations: Array<{
    device_name: string | null;
    activated_at: string;
    last_validated_at: string | null;
  }>;
}

export default function LicensePage() {
  const { data: session } = useSession();
  const { success, error: showError } = useToast();
  const [licenseKey, setLicenseKey] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [isActivating, setIsActivating] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [myLicenses, setMyLicenses] = useState<LicenseInfo[]>([]);
  const [selectedLicense, setSelectedLicense] = useState<LicenseInfo | null>(null);
  const [hardwareFingerprint, setHardwareFingerprint] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

  useEffect(() => {
    loadMyLicenses();
    loadHardwareFingerprint();
  }, []);

  const loadHardwareFingerprint = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/v1/license/hardware-fingerprint`);
      if (response.ok) {
        const data = await response.json();
        setHardwareFingerprint(data.fingerprint);
      }
    } catch (err) {
      console.error('Failed to load hardware fingerprint:', err);
    }
  };

  const loadMyLicenses = async () => {
    try {
      setIsLoading(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/license/my-licenses`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMyLicenses(data);
        if (data.length > 0 && !selectedLicense) {
          loadLicenseInfo(data[0].license_key);
        }
      }
    } catch (err) {
      console.error('Failed to load licenses:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadLicenseInfo = async (key: string) => {
    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/license/info/${key}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedLicense(data);
      }
    } catch (err) {
      console.error('Failed to load license info:', err);
    }
  };

  const handleActivate = async () => {
    if (!licenseKey.trim()) {
      showError('License key required', 'Please enter a license key');
      return;
    }

    try {
      setIsActivating(true);
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/license/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          license_key: licenseKey.trim(),
          device_name: deviceName.trim() || undefined
        })
      });

      const data = await response.json();

      if (response.ok) {
        success('License Activated', 'Your license has been activated successfully');
        setLicenseKey('');
        setDeviceName('');
        await loadMyLicenses();
        if (data.license?.key) {
          await loadLicenseInfo(data.license.key);
        }
      } else {
        showError('Activation Failed', data.detail || 'Failed to activate license');
      }
    } catch (err: any) {
      showError('Activation Error', err.message || 'Failed to activate license');
    } finally {
      setIsActivating(false);
    }
  };

  const handleValidate = async () => {
    if (!licenseKey.trim()) {
      showError('License key required', 'Please enter a license key');
      return;
    }

    try {
      setIsValidating(true);
      const response = await fetch(`${apiUrl}/api/v1/license/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          license_key: licenseKey.trim()
        })
      });

      const data = await response.json();

      if (data.valid) {
        success('License Valid', data.message);
      } else {
        showError('License Invalid', data.message);
      }
    } catch (err: any) {
      showError('Validation Error', err.message || 'Failed to validate license');
    } finally {
      setIsValidating(false);
    }
  };

  const handleDeactivate = async (key: string) => {
    if (!confirm('Are you sure you want to deactivate this license on this device?')) {
      return;
    }

    try {
      const token = (session as any)?.accessToken || localStorage.getItem('token');
      const response = await fetch(`${apiUrl}/api/v1/license/deactivate?license_key=${encodeURIComponent(key)}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        success('Device Deactivated', 'License has been deactivated on this device');
        await loadMyLicenses();
      } else {
        const data = await response.json();
        showError('Deactivation Failed', data.detail || 'Failed to deactivate device');
      }
    } catch (err: any) {
      showError('Deactivation Error', err.message || 'Failed to deactivate device');
    }
  };

  const getStatusBadge = (status: string, valid: boolean) => {
    const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline", icon: any }> = {
      active: { variant: "default", icon: CheckCircle },
      trial: { variant: "secondary", icon: Clock },
      grace_period: { variant: "outline", icon: AlertTriangle },
      expired: { variant: "destructive", icon: XCircle },
      revoked: { variant: "destructive", icon: XCircle },
      inactive: { variant: "outline", icon: Clock }
    };

    const config = variants[status.toLowerCase()] || variants.inactive;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6 max-w-6xl">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Key className="h-8 w-8" />
          License Management
        </h1>
        <p className="text-muted-foreground mt-2">
          Activate and manage your Powerhouse licenses
        </p>
      </div>

      {/* Activate License Card */}
      <Card>
        <CardHeader>
          <CardTitle>Activate License</CardTitle>
          <CardDescription>
            Enter your license key to activate Powerhouse on this device
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="license-key">License Key</Label>
            <Input
              id="license-key"
              placeholder="XXXX-XXXX-XXXX-XXXX-XXXX"
              value={licenseKey}
              onChange={(e) => setLicenseKey(e.target.value.toUpperCase())}
              className="font-mono"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="device-name">Device Name (Optional)</Label>
            <Input
              id="device-name"
              placeholder="My Computer"
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button 
              onClick={handleActivate} 
              disabled={isActivating || !licenseKey.trim()}
              className="flex-1"
            >
              {isActivating ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Activating...
                </>
              ) : (
                <>
                  <Key className="h-4 w-4 mr-2" />
                  Activate License
                </>
              )}
            </Button>
            <Button 
              variant="outline" 
              onClick={handleValidate} 
              disabled={isValidating || !licenseKey.trim()}
            >
              {isValidating ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  <Shield className="h-4 w-4 mr-2" />
                  Validate
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* My Licenses */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>My Licenses</CardTitle>
              <CardDescription>
                Licenses associated with your account
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadMyLicenses}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground mt-2">Loading licenses...</p>
            </div>
          ) : myLicenses.length === 0 ? (
            <Alert>
              <AlertTitle>No Licenses</AlertTitle>
              <AlertDescription>
                You don't have any licenses yet. Activate a license key above to get started.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-4">
              {myLicenses.map((license) => (
                <Card 
                  key={license.license_key} 
                  className={`cursor-pointer transition-colors ${
                    selectedLicense?.license_key === license.license_key 
                      ? 'border-primary' 
                      : ''
                  }`}
                  onClick={() => loadLicenseInfo(license.license_key)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <code className="text-sm font-mono bg-muted px-2 py-1 rounded">
                            {license.license_key}
                          </code>
                          {getStatusBadge(license.status, license.validation?.valid ?? false)}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Monitor className="h-4 w-4" />
                            {license.device_count} / {license.max_devices} devices
                          </span>
                          <span className="flex items-center gap-1">
                            <Shield className="h-4 w-4" />
                            {license.seats} seats
                          </span>
                          {license.validation?.days_remaining !== null && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              {license.validation?.days_remaining} days remaining
                            </span>
                          )}
                        </div>
                        {license.validation?.message && (
                          <p className="text-sm text-muted-foreground">{license.validation?.message}</p>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeactivate(license.license_key);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* License Details */}
      {selectedLicense && (
        <Card>
          <CardHeader>
            <CardTitle>License Details</CardTitle>
            <CardDescription>
              Detailed information about the selected license
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">License Key</Label>
                <code className="block mt-1 text-sm font-mono bg-muted px-2 py-1 rounded">
                  {selectedLicense.license_key}
                </code>
              </div>
              <div>
                <Label className="text-muted-foreground">Type</Label>
                <p className="mt-1 capitalize">{selectedLicense.type}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Status</Label>
                <div className="mt-1">
                  {getStatusBadge(selectedLicense.status, selectedLicense.validation.valid)}
                </div>
              </div>
              <div>
                <Label className="text-muted-foreground">Seats</Label>
                <p className="mt-1">{selectedLicense.seats}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Devices</Label>
                <p className="mt-1">{selectedLicense.device_count} / {selectedLicense.max_devices}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Issued</Label>
                <p className="mt-1">{formatDate(selectedLicense.issued_at)}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Activated</Label>
                <p className="mt-1">{formatDate(selectedLicense.activated_at)}</p>
              </div>
              {selectedLicense.expires_at && (
                <div>
                  <Label className="text-muted-foreground">Expires</Label>
                  <p className="mt-1">{formatDate(selectedLicense.expires_at)}</p>
                </div>
              )}
              {selectedLicense.trial_ends_at && (
                <div>
                  <Label className="text-muted-foreground">Trial Ends</Label>
                  <p className="mt-1">{formatDate(selectedLicense.trial_ends_at)}</p>
                </div>
              )}
            </div>

            {selectedLicense.features.length > 0 && (
              <div>
                <Label className="text-muted-foreground">Features</Label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedLicense.features.map((feature, idx) => (
                    <Badge key={idx} variant="secondary">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {selectedLicense.activations.length > 0 && (
              <div>
                <Label className="text-muted-foreground">Active Devices</Label>
                <div className="mt-2 space-y-2">
                  {selectedLicense.activations.map((activation, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-muted rounded">
                      <div>
                        <p className="font-medium">
                          {activation.device_name || 'Unnamed Device'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Activated: {formatDate(activation.activated_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedLicense.validation && (
              <Alert variant={selectedLicense.validation.valid ? "default" : "destructive"}>
                <AlertTitle>Validation Status</AlertTitle>
                <AlertDescription>
                  {selectedLicense.validation.message}
                  {selectedLicense.validation.days_remaining !== null && (
                    <span className="block mt-1">
                      {selectedLicense.validation.days_remaining} days remaining
                    </span>
                  )}
                  {selectedLicense.validation.grace_period_days !== null && (
                    <span className="block mt-1">
                      Grace period: {selectedLicense.validation.grace_period_days} days remaining
                    </span>
                  )}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Hardware Fingerprint Info */}
      {hardwareFingerprint && (
        <Card>
          <CardHeader>
            <CardTitle>Device Information</CardTitle>
            <CardDescription>
              Hardware fingerprint for this device
            </CardDescription>
          </CardHeader>
          <CardContent>
            <code className="text-xs font-mono bg-muted px-2 py-1 rounded block break-all">
              {hardwareFingerprint}
            </code>
            <p className="text-sm text-muted-foreground mt-2">
              This fingerprint is used to bind your license to this device.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}


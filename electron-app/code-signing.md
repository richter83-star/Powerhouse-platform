# Code Signing Configuration

## Overview

Code signing is essential for commercial software distribution. It:
- Removes Windows security warnings
- Builds user trust
- Prevents "Unknown Publisher" warnings
- Required for Windows SmartScreen approval

## Setup Instructions

### Option 1: Using a Code Signing Certificate (Recommended)

1. **Obtain a Code Signing Certificate**
   - Purchase from a trusted Certificate Authority (CA):
     - DigiCert (~$400-600/year)
     - Sectigo (~$200-400/year)
     - GlobalSign (~$300-500/year)
   - Or use extended validation (EV) certificate for immediate trust

2. **Export Certificate**
   - Export your certificate as a `.pfx` file
   - Set a password for the certificate

3. **Configure electron-builder**

   Edit `electron-app/package.json` and add to the `build.win` section:

   ```json
   "win": {
     "target": ["nsis"],
     "certificateFile": "path/to/certificate.pfx",
     "certificatePassword": "your-certificate-password",
     "signingHashAlgorithms": ["sha256"],
     "sign": "path/to/signtool.exe"
   }
   ```

   **OR** use environment variables (more secure):

   ```json
   "win": {
     "target": ["nsis"],
     "certificateFile": "${env.CERTIFICATE_FILE}",
     "certificatePassword": "${env.CERTIFICATE_PASSWORD}"
   }
   ```

4. **Set Environment Variables** (if using env vars)

   ```batch
   set CERTIFICATE_FILE=C:\path\to\certificate.pfx
   set CERTIFICATE_PASSWORD=your-password
   ```

### Option 2: Self-Signed Certificate (Development Only)

**WARNING**: Self-signed certificates will still show warnings. Only use for testing.

1. **Create Self-Signed Certificate**

   ```batch
   makecert -r -pe -n "CN=Powerhouse AI" -ss My -len 2048 -sv Powerhouse.pvk Powerhouse.cer
   pvk2pfx -pvk Powerhouse.pvk -spc Powerhouse.cer -pfx Powerhouse.pfx -po password
   ```

2. **Configure as above**

### Option 3: Sign After Build (Manual)

If you prefer to sign manually after building:

1. Build the installer normally
2. Use `signtool.exe` (from Windows SDK):

   ```batch
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "dist\Powerhouse Setup 1.0.0.exe"
   ```

## Verification

After signing, verify the signature:

```batch
signtool verify /pa "dist\Powerhouse Setup 1.0.0.exe"
```

Or check file properties in Windows Explorer - you should see a "Digital Signatures" tab.

## Troubleshooting

### "SignTool Error: The specified timestamp server either could not be reached"

- Try a different timestamp server:
  - `http://timestamp.digicert.com`
  - `http://timestamp.verisign.com/scripts/timstamp.dll`
  - `http://timestamp.comodoca.com`

### "Certificate file not found"

- Use absolute paths
- Check file permissions
- Ensure `.pfx` file is accessible

### "Invalid certificate password"

- Verify password is correct
- Check for special characters that need escaping
- Try using environment variable instead

## Best Practices

1. **Keep Certificate Secure**
   - Never commit certificate files to version control
   - Use environment variables for passwords
   - Store certificates in secure location

2. **Timestamp All Signatures**
   - Ensures signature remains valid after certificate expires
   - Use reliable timestamp servers

3. **Test Signing**
   - Test on clean Windows machine
   - Verify no warnings appear
   - Check Windows SmartScreen behavior

4. **Renewal**
   - Set reminders before certificate expiration
   - Update signing configuration with new certificate
   - Re-sign all distributed installers if needed

## Cost Considerations

- **Standard Code Signing**: $200-600/year
- **EV Code Signing**: $400-800/year (immediate SmartScreen trust)
- **Self-Signed**: Free (but shows warnings)

For commercial distribution, a standard code signing certificate is highly recommended.


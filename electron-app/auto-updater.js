/**
 * Powerhouse Auto-Updater
 * Handles automatic updates and version checking
 */

const { app, dialog, shell } = require('electron');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const UPDATE_CHECK_URL = 'https://powerhouse.ai/api/updates/check';
const CURRENT_VERSION = app.getVersion();
const UPDATE_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours

let updateCheckInterval = null;

/**
 * Check for updates
 */
async function checkForUpdates(showNoUpdateDialog = false) {
  try {
    console.log('[Updater] Checking for updates...');
    
    const updateInfo = await fetchUpdateInfo();
    
    if (!updateInfo) {
      if (showNoUpdateDialog) {
        dialog.showMessageBox({
          type: 'info',
          title: 'No Updates Available',
          message: `You are running the latest version of Powerhouse (${CURRENT_VERSION}).`,
          buttons: ['OK']
        });
      }
      return false;
    }
    
    if (isNewerVersion(updateInfo.version, CURRENT_VERSION)) {
      return await promptUpdate(updateInfo);
    } else {
      if (showNoUpdateDialog) {
        dialog.showMessageBox({
          type: 'info',
          title: 'No Updates Available',
          message: `You are running the latest version of Powerhouse (${CURRENT_VERSION}).`,
          buttons: ['OK']
        });
      }
      return false;
    }
  } catch (error) {
    console.error('[Updater] Error checking for updates:', error);
    if (showNoUpdateDialog) {
      dialog.showErrorBox(
        'Update Check Failed',
        `Failed to check for updates: ${error.message}`
      );
    }
    return false;
  }
}

/**
 * Fetch update information from server
 */
function fetchUpdateInfo() {
  return new Promise((resolve, reject) => {
    const url = new URL(UPDATE_CHECK_URL);
    url.searchParams.append('version', CURRENT_VERSION);
    url.searchParams.append('platform', process.platform);
    url.searchParams.append('arch', process.arch);
    
    https.get(url.toString(), (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          if (res.statusCode === 200) {
            const updateInfo = JSON.parse(data);
            resolve(updateInfo);
          } else if (res.statusCode === 204) {
            // No updates available
            resolve(null);
          } else {
            reject(new Error(`Server returned status ${res.statusCode}`));
          }
        } catch (error) {
          reject(error);
        }
      });
    }).on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * Compare version strings
 */
function isNewerVersion(newVersion, currentVersion) {
  const newParts = newVersion.split('.').map(Number);
  const currentParts = currentVersion.split('.').map(Number);
  
  for (let i = 0; i < Math.max(newParts.length, currentParts.length); i++) {
    const newPart = newParts[i] || 0;
    const currentPart = currentParts[i] || 0;
    
    if (newPart > currentPart) return true;
    if (newPart < currentPart) return false;
  }
  
  return false;
}

/**
 * Prompt user to update
 */
async function promptUpdate(updateInfo) {
  const response = await dialog.showMessageBox({
    type: 'info',
    title: 'Update Available',
    message: `A new version of Powerhouse is available!`,
    detail: `Version ${updateInfo.version} is now available. You are currently running ${CURRENT_VERSION}.\n\n${updateInfo.releaseNotes || ''}\n\nWould you like to download and install it now?`,
    buttons: ['Download Update', 'Remind Me Later', 'Skip This Version'],
    defaultId: 0,
    cancelId: 1
  });
  
  if (response.response === 0) {
    // Download update
    return await downloadUpdate(updateInfo);
  } else if (response.response === 2) {
    // Skip this version
    saveSkippedVersion(updateInfo.version);
    return false;
  }
  
  return false;
}

/**
 * Download and install update
 */
async function downloadUpdate(updateInfo) {
  const downloadPath = path.join(app.getPath('temp'), `Powerhouse-Setup-${updateInfo.version}.exe`);
  
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(downloadPath);
    
    https.get(updateInfo.downloadUrl, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Download failed with status ${response.statusCode}`));
        return;
      }
      
      const totalSize = parseInt(response.headers['content-length'], 10);
      let downloadedSize = 0;
      
      response.pipe(file);
      
      response.on('data', (chunk) => {
        downloadedSize += chunk.length;
        const progress = (downloadedSize / totalSize) * 100;
        // Could emit progress event here for UI updates
      });
      
      file.on('finish', () => {
        file.close();
        
        // Show dialog to run installer
        dialog.showMessageBox({
          type: 'info',
          title: 'Download Complete',
          message: 'Update downloaded successfully.',
          detail: 'The installer will now launch. Please follow the installation wizard.',
          buttons: ['OK']
        }).then(() => {
          // Launch installer
          spawn(downloadPath, [], {
            detached: true,
            stdio: 'ignore'
          }).unref();
          
          // Quit app to allow update
          app.quit();
          resolve(true);
        });
      });
      
      file.on('error', (error) => {
        fs.unlink(downloadPath, () => {});
        reject(error);
      });
    }).on('error', (error) => {
      fs.unlink(downloadPath, () => {});
      reject(error);
    });
  });
}

/**
 * Save skipped version to prevent re-prompting
 */
function saveSkippedVersion(version) {
  const skippedPath = path.join(app.getPath('userData'), 'skipped-versions.json');
  let skipped = [];
  
  try {
    if (fs.existsSync(skippedPath)) {
      skipped = JSON.parse(fs.readFileSync(skippedPath, 'utf8'));
    }
  } catch (error) {
    console.error('[Updater] Error reading skipped versions:', error);
  }
  
  if (!skipped.includes(version)) {
    skipped.push(version);
    fs.writeFileSync(skippedPath, JSON.stringify(skipped, null, 2));
  }
}

/**
 * Check if version was skipped
 */
function isVersionSkipped(version) {
  const skippedPath = path.join(app.getPath('userData'), 'skipped-versions.json');
  
  try {
    if (fs.existsSync(skippedPath)) {
      const skipped = JSON.parse(fs.readFileSync(skippedPath, 'utf8'));
      return skipped.includes(version);
    }
  } catch (error) {
    console.error('[Updater] Error reading skipped versions:', error);
  }
  
  return false;
}

/**
 * Start automatic update checking
 */
function startAutoUpdateCheck() {
  // Check immediately on startup (after a delay)
  setTimeout(() => {
    checkForUpdates(false);
  }, 30000); // 30 seconds after startup
  
  // Then check periodically
  updateCheckInterval = setInterval(() => {
    checkForUpdates(false);
  }, UPDATE_INTERVAL);
}

/**
 * Stop automatic update checking
 */
function stopAutoUpdateCheck() {
  if (updateCheckInterval) {
    clearInterval(updateCheckInterval);
    updateCheckInterval = null;
  }
}

module.exports = {
  checkForUpdates,
  startAutoUpdateCheck,
  stopAutoUpdateCheck,
  isVersionSkipped
};


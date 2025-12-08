const { app, BrowserWindow, Tray, Menu } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');

let mainWindow = null;
let tray = null;
let backendProcess = null;
let frontendProcess = null;
let isQuitting = false;

const FRONTEND_PORT = 3000;
const BACKEND_PORT = 8001;
const APP_NAME = 'Powerhouse';

// Get paths
const isPackaged = app.isPackaged;
const appPath = isPackaged ? path.dirname(app.getPath('exe')) : path.join(__dirname, '..');

function log(message) {
  console.log(`[Powerhouse] ${message}`);
}

function checkService(port, serviceName) {
  return new Promise((resolve) => {
    const options = {
      hostname: 'localhost',
      port: port,
      path: '/',
      method: 'GET',
      timeout: 1000
    };

    const req = http.request(options, (res) => {
      log(`${serviceName} is running on port ${port}`);
      resolve(true);
    });

    req.on('error', () => {
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function waitForService(port, serviceName, maxAttempts = 30) {
  log(`Waiting for ${serviceName} to start...`);
  
  for (let i = 0; i < maxAttempts; i++) {
    const isRunning = await checkService(port, serviceName);
    if (isRunning) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  return false;
}

function startDatabase() {
  return new Promise((resolve) => {
    log('Starting database...');
    
    const dockerCompose = spawn('docker-compose', ['up', '-d'], {
      cwd: appPath,
      shell: true
    });

    dockerCompose.on('close', (code) => {
      if (code === 0) {
        log('Database started successfully');
        setTimeout(() => resolve(true), 5000);
      } else {
        log(`Database failed to start (code ${code})`);
        resolve(false);
      }
    });
  });
}

function startBackend() {
  return new Promise((resolve) => {
    log('Starting backend...');
    
    const backendPath = path.join(appPath, 'backend');
    const venvPython = path.join(backendPath, 'venv', 'Scripts', 'python.exe');
    
    backendProcess = spawn(venvPython, ['app.py'], {
      cwd: backendPath,
      shell: true,
      stdio: 'inherit'
    });

    backendProcess.on('error', (err) => {
      log(`Backend error: ${err.message}`);
      resolve(false);
    });

    setTimeout(async () => {
      const isReady = await waitForService(BACKEND_PORT, 'Backend', 15);
      resolve(isReady);
    }, 3000);
  });
}

function startFrontend() {
  return new Promise((resolve) => {
    log('Starting frontend...');
    
    const frontendPath = path.join(appPath, 'frontend', 'app');
    
    frontendProcess = spawn('npm', ['run', 'dev'], {
      cwd: frontendPath,
      shell: true,
      stdio: 'inherit'
    });

    frontendProcess.on('error', (err) => {
      log(`Frontend error: ${err.message}`);
      resolve(false);
    });

    setTimeout(async () => {
      const isReady = await waitForService(FRONTEND_PORT, 'Frontend', 30);
      resolve(isReady);
    }, 5000);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: APP_NAME,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    },
    show: false
  });

  mainWindow.loadURL('data:text/html,<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;background:linear-gradient(135deg,#667eea,#764ba2);color:white;font-family:sans-serif;"><div style="text-align:center;"><h1>🏢 Powerhouse</h1><p>Starting services...</p></div></body></html>');

  mainWindow.show();

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      return false;
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Powerhouse',
      click: () => {
        if (mainWindow) mainWindow.show();
      }
    },
    {
      label: 'Hide Powerhouse',
      click: () => {
        if (mainWindow) mainWindow.hide();
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  if (tray) {
    tray.setContextMenu(contextMenu);
  }
}

async function startServices() {
  try {
    const dbStarted = await startDatabase();
    if (!dbStarted) return false;

    const backendStarted = await startBackend();
    if (!backendStarted) return false;

    const frontendStarted = await startFrontend();
    if (!frontendStarted) return false;

    log('All services started successfully!');
    return true;
  } catch (error) {
    log(`Error starting services: ${error.message}`);
    return false;
  }
}

function stopServices() {
  log('Stopping services...');

  if (frontendProcess) {
    try {
      process.kill(frontendProcess.pid);
    } catch (err) {}
  }

  if (backendProcess) {
    try {
      process.kill(backendProcess.pid);
    } catch (err) {}
  }

  spawn('docker-compose', ['down'], {
    cwd: appPath,
    shell: true
  });
}

app.whenReady().then(async () => {
  createWindow();
  createTray();

  const started = await startServices();

  if (started) {
    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`);
  } else {
    mainWindow.loadURL('data:text/html,<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;background:#ff4444;color:white;font-family:sans-serif;"><div style="text-align:center;"><h1>⚠️ Failed to Start</h1><p>Could not start Powerhouse services.</p></div></body></html>');
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    isQuitting = true;
    app.quit();
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  stopServices();
});

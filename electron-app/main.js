const { app, BrowserWindow, Tray, Menu, dialog } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

// Commercial-grade modules
const systemCheck = require('./system-check');
const updater = require('./auto-updater');

let mainWindow = null;
let tray = null;
let backendProcess = null;
let frontendProcess = null;
let dbProcess = null;
let isQuitting = false;

const FRONTEND_PORT = 3000;
const BACKEND_PORT = 8001;
const DB_PORT = 5434;
const APP_NAME = 'Powerhouse';

// Get the correct shell for Windows
function getShell() {
  if (process.platform === 'win32') {
    return process.env.COMSPEC || 'C:\\Windows\\System32\\cmd.exe';
  }
  return '/bin/sh';
}

// Get paths
const isPackaged = app.isPackaged;
const appPath = isPackaged 
  ? path.dirname(app.getPath('exe')) 
  : path.join(__dirname, '..');
const resourcesPath = isPackaged 
  ? path.join(path.dirname(app.getPath('exe')), 'resources')
  : path.join(__dirname, '..');

// Runtime paths
const backendPath = path.join(resourcesPath, 'backend');
const frontendPath = path.join(resourcesPath, 'frontend', 'app');
const dbPath = path.join(resourcesPath, 'postgres');
const dataPath = path.join(app.getPath('userData'), 'data');

// Ensure data directory exists
if (!fs.existsSync(dataPath)) {
  fs.mkdirSync(dataPath, { recursive: true });
}

function log(message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [Powerhouse] ${message}`);
  
  // Also log to file in production
  if (isPackaged) {
    const logPath = path.join(dataPath, 'powerhouse.log');
    fs.appendFileSync(logPath, `[${timestamp}] ${message}\n`);
  }
}

function checkService(port, serviceName) {
  return new Promise((resolve) => {
    // For database port, just check if it's listening (Postgres doesn't have HTTP /health)
    if (port === DB_PORT) {
      const net = require('net');
      const socket = new net.Socket();
      socket.setTimeout(1000);
      socket.on('connect', () => {
        socket.destroy();
        log(`${serviceName} is running on port ${port}`);
        resolve(true);
      });
      socket.on('timeout', () => {
        socket.destroy();
        resolve(false);
      });
      socket.on('error', () => {
        resolve(false);
      });
      socket.connect(port, 'localhost');
      return;
    }
    
    // For HTTP services: backend has /health, frontend just needs to respond on /
    const path = port === BACKEND_PORT ? '/health' : '/';
    const options = {
      hostname: 'localhost',
      port: port,
      path: path,
      method: 'GET',
      timeout: 2000
    };

    const req = http.request(options, (res) => {
      log(`${serviceName} is running on port ${port} (status: ${res.statusCode})`);
      resolve(true);
    });

    req.on('error', (err) => {
      log(`${serviceName} check failed: ${err.message}`);
      resolve(false);
    });

    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });

    req.end();
  });
}

async function waitForService(port, serviceName, maxAttempts = 60) {
  log(`Waiting for ${serviceName} to start on port ${port}...`);
  
  for (let i = 0; i < maxAttempts; i++) {
    const isRunning = await checkService(port, serviceName);
    if (isRunning) {
      log(`${serviceName} is ready!`);
      return true;
    }
    if (i % 10 === 0 && i > 0) {
      log(`${serviceName} still not ready after ${i} seconds...`);
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  log(`${serviceName} failed to start after ${maxAttempts} seconds`);
  return false;
}

function startDatabase() {
  return new Promise(async (resolve) => {
    log('Checking if database is already running...');
    
    // First check if database is already running
    const isRunning = await checkService(DB_PORT, 'Database');
    if (isRunning) {
      log('Database is already running, skipping startup');
      resolve(true);
      return;
    }
    
    log('Database not running, starting...');
    
    // Try Docker first (if available)
    exec('docker --version', (error) => {
      if (!error) {
        log('Using Docker for database...');
        // Try to start from project root (where docker-compose.yml is)
        const projectRoot = path.join(resourcesPath, '..', '..');
        const dockerComposeFile = path.join(projectRoot, 'docker-compose.yml');
        
        if (!fs.existsSync(dockerComposeFile)) {
          log('docker-compose.yml not found, trying portable PostgreSQL...');
          startPortableDatabase().then(resolve);
          return;
        }
        
        const dockerCompose = spawn('docker-compose', ['up', '-d', 'postgres', 'redis'], {
          cwd: projectRoot,
          shell: getShell(),
          stdio: 'pipe'
        });

        dockerCompose.on('error', (err) => {
          log(`Docker error: ${err.message}`);
          log('Trying portable PostgreSQL...');
          startPortableDatabase().then(resolve);
        });

        dockerCompose.on('close', (code) => {
          if (code === 0) {
            log('Database started successfully via Docker');
            setTimeout(async () => {
              const ready = await waitForService(DB_PORT, 'Database', 30);
              resolve(ready);
            }, 5000);
          } else {
            log(`Docker database failed (code ${code}), trying portable PostgreSQL...`);
            startPortableDatabase().then(resolve);
          }
        });

        dockerCompose.stderr.on('data', (data) => {
          log(`Docker: ${data.toString()}`);
        });
      } else {
        log('Docker not available, trying portable PostgreSQL...');
        startPortableDatabase().then(resolve);
      }
    });
  });
}

function startPortableDatabase() {
  return new Promise((resolve) => {
    const pgDataDir = path.join(dataPath, 'postgres_data');
    const pgBinPath = path.join(dbPath, 'bin');
    const pgInitdb = path.join(pgBinPath, 'initdb.exe');
    const pgServer = path.join(pgBinPath, 'pg_ctl.exe');

    // Check if PostgreSQL binaries exist
    if (!fs.existsSync(pgInitdb) || !fs.existsSync(pgServer)) {
      log('Portable PostgreSQL binaries not found. Docker is required to run Powerhouse.');
      log(`Expected location: ${pgBinPath}`);
      resolve(false);
      return;
    }

    // Check if PostgreSQL is already initialized
    if (!fs.existsSync(pgDataDir)) {
      log('Initializing PostgreSQL database...');
      const initProcess = spawn(pgInitdb, ['-D', pgDataDir, '-U', 'postgres', '--locale=C', '--encoding=UTF8'], {
        cwd: dbPath,
        shell: false,
        stdio: 'pipe'
      });

      initProcess.on('error', (err) => {
        log(`PostgreSQL initialization error: ${err.message}`);
        if (err.code === 'ENOENT') {
          log('PostgreSQL binaries not found. Docker is required.');
        }
        resolve(false);
      });

      initProcess.on('close', (code) => {
        if (code === 0) {
          log('PostgreSQL initialized successfully');
          startPgServer(pgServer, pgDataDir).then(resolve);
        } else {
          log(`PostgreSQL initialization failed (code ${code})`);
          resolve(false);
        }
      });
    } else {
      log('PostgreSQL data directory exists, starting server...');
      startPgServer(pgServer, pgDataDir).then(resolve);
    }
  });
}

function startPgServer(pgServer, dataDir) {
  return new Promise((resolve) => {
    const serverProcess = spawn(pgServer, [
      'start', '-D', dataDir, '-l', path.join(dataPath, 'postgres.log'),
      '-o', `-p ${DB_PORT} -h localhost`
    ], {
      cwd: dbPath,
      shell: false,
      stdio: 'pipe'
    });

    dbProcess = serverProcess;

    serverProcess.on('error', (err) => {
      log(`PostgreSQL server error: ${err.message}`);
      if (err.code === 'ENOENT') {
        log('PostgreSQL binaries not found. Docker is required.');
      }
      resolve(false);
    });

    serverProcess.on('close', (code) => {
      log(`PostgreSQL server process exited with code ${code}`);
    });

    setTimeout(async () => {
      const isReady = await waitForService(DB_PORT, 'Database', 30);
      resolve(isReady);
    }, 3000);
  });
}

function startBackend() {
  return new Promise(async (resolve) => {
    log('Checking if backend is already running...');
    
    // First check if backend is already running
    const isRunning = await checkService(BACKEND_PORT, 'Backend');
    if (isRunning) {
      log('Backend is already running, skipping startup');
      resolve(true);
      return;
    }
    
    log('Backend not running, starting...');
    
    // Try bundled Python first, then system Python
    const pythonExe = path.join(backendPath, 'python', 'python.exe');
    const systemPython = 'python';
    const pythonPath = fs.existsSync(pythonExe) ? pythonExe : systemPython;
    
    const backendScript = path.join(backendPath, 'powerhouse_backend.exe');
    const backendPy = path.join(backendPath, 'api', 'main.py');
    
    let backendCmd, backendArgs;
    
    if (fs.existsSync(backendScript)) {
      // Use PyInstaller executable
      backendCmd = backendScript;
      backendArgs = [];
    } else {
      // Use Python script
      backendCmd = pythonPath;
      backendArgs = ['-m', 'uvicorn', 'api.main:app', '--host', '0.0.0.0', '--port', '8001'];
    }
    
    log(`Starting backend with: ${backendCmd}`);
    
    // Use shell for Python commands, false for direct executables
    const useShell = !fs.existsSync(backendCmd) || backendCmd === 'python';
    backendProcess = spawn(backendCmd, backendArgs, {
      cwd: backendPath,
      shell: useShell ? getShell() : false,
      stdio: 'pipe',
      env: {
        ...process.env,
        PYTHONPATH: backendPath,
        DATABASE_URL: `postgresql://postgres:postgres@localhost:${DB_PORT}/powerhouse`
      }
    });

    backendProcess.stdout.on('data', (data) => {
      log(`Backend: ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      log(`Backend Error: ${data.toString().trim()}`);
    });

    backendProcess.on('error', (err) => {
      log(`Backend error: ${err.message}`);
      resolve(false);
    });

    backendProcess.on('close', (code) => {
      log(`Backend process exited with code ${code}`);
    });

    setTimeout(async () => {
      const isReady = await waitForService(BACKEND_PORT, 'Backend', 30);
      resolve(isReady);
    }, 5000);
  });
}

function startFrontend() {
  return new Promise(async (resolve) => {
    log('Checking if frontend is already running...');
    
    // First check if frontend is already running
    const isRunning = await checkService(FRONTEND_PORT, 'Frontend');
    if (isRunning) {
      log('Frontend is already running, skipping startup');
      resolve(true);
      return;
    }
    
    log('Frontend not running, starting...');
    
    // Try bundled Node.js first, then system Node
    const nodeExe = path.join(frontendPath, '..', 'node', 'node.exe');
    const systemNode = 'node';
    const nodePath = fs.existsSync(nodeExe) ? nodeExe : systemNode;
    
    const npmCmd = path.join(frontendPath, '..', 'node', 'npm.cmd');
    const systemNpm = 'npm';
    const npmPath = fs.existsSync(npmCmd) ? npmCmd : systemNpm;
    
    // Check if Next.js is already built
    const nextBuild = path.join(frontendPath, '.next');
    const isBuilt = fs.existsSync(nextBuild);
    
    if (isBuilt) {
      // Use production build
      log('Using production build of Next.js');
      frontendProcess = spawn(nodePath, [
        path.join(frontendPath, 'node_modules', '.bin', 'next'),
        'start'
      ], {
        cwd: frontendPath,
        shell: fs.existsSync(nodePath) ? false : getShell(),
        stdio: 'pipe',
        env: {
          ...process.env,
          PORT: FRONTEND_PORT,
          NODE_ENV: 'production',
          NEXT_PUBLIC_API_URL: `http://localhost:${BACKEND_PORT}`
        }
      });
    } else {
      // Use development mode
      log('Using development mode (building Next.js...)');
      frontendProcess = spawn(nodePath, [
        path.join(frontendPath, 'node_modules', '.bin', 'next'),
        'dev',
        '-p', FRONTEND_PORT.toString()
      ], {
        cwd: frontendPath,
        shell: fs.existsSync(nodePath) ? false : getShell(),
        stdio: 'pipe',
        env: {
          ...process.env,
          PORT: FRONTEND_PORT,
          NEXT_PUBLIC_API_URL: `http://localhost:${BACKEND_PORT}`
        }
      });
    }

    frontendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) log(`Frontend: ${output}`);
    });

    frontendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      if (output && !output.includes('webpack')) {
        log(`Frontend Error: ${output}`);
      }
    });

    frontendProcess.on('error', (err) => {
      log(`Frontend error: ${err.message}`);
      resolve(false);
    });

    frontendProcess.on('close', (code) => {
      log(`Frontend process exited with code ${code}`);
    });

    setTimeout(async () => {
      const isReady = await waitForService(FRONTEND_PORT, 'Frontend', 60);
      resolve(isReady);
    }, 10000);
  });
}

function createWindow() {
  try {
    const iconPath = path.join(resourcesPath, 'icon.ico');
    const hasIcon = fs.existsSync(iconPath);

    mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      title: APP_NAME,
      icon: hasIcon ? iconPath : undefined,
      fullscreen: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      },
      show: false,
      backgroundColor: '#1a1a1a'
    });

  const loadingHTML = `
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {
          margin: 0;
          padding: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .container {
          text-align: center;
        }
        h1 {
          font-size: 3em;
          margin: 0 0 20px 0;
          font-weight: 300;
        }
        p {
          font-size: 1.2em;
          margin: 10px 0;
        }
        .spinner {
          border: 4px solid rgba(255, 255, 255, 0.3);
          border-top: 4px solid white;
          border-radius: 50%;
          width: 40px;
          height: 40px;
          animation: spin 1s linear infinite;
          margin: 20px auto;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🏢 Powerhouse</h1>
        <div class="spinner"></div>
        <p>Starting services...</p>
        <p style="font-size: 0.9em; opacity: 0.8;">This may take a minute</p>
      </div>
    </body>
    </html>
  `;

  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(loadingHTML)}`);
  mainWindow.show();
  mainWindow.setFullScreen(true);

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      if (tray) {
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: APP_NAME,
          message: 'Powerhouse is still running',
          detail: 'The application has been minimized to the system tray. Right-click the tray icon to quit.',
          buttons: ['OK']
        });
      }
      return false;
    }
  });

    mainWindow.on('closed', () => {
      mainWindow = null;
    });
  } catch (error) {
    log(`Error creating window: ${error.message}`);
    log(error.stack);
    throw error;
  }
}

function createTray() {
  try {
    // Try multiple icon paths
    const iconPaths = [
      path.join(resourcesPath, 'icon.ico'),
      path.join(resourcesPath, 'build', 'icon.ico'),
      path.join(appPath, 'icon.ico'),
      path.join(__dirname, 'icon.ico'),
      path.join(__dirname, 'build', 'icon.ico')
    ];
    
    let iconPath = null;
    for (const testPath of iconPaths) {
      if (fs.existsSync(testPath)) {
        iconPath = testPath;
        break;
      }
    }
    
    // If no icon found, try to use window icon or create a fallback
    if (!iconPath) {
      // Try to get icon from build directory
      const buildIconPath = path.join(resourcesPath, 'build', 'icon.ico');
      if (fs.existsSync(buildIconPath)) {
        iconPath = buildIconPath;
      } else {
        // Create a simple native image as fallback or skip tray
        const { nativeImage } = require('electron');
        try {
          // Create a minimal 16x16 icon as fallback
          const fallbackIcon = nativeImage.createEmpty();
          tray = new Tray(fallbackIcon);
          log('Created tray with fallback icon (empty image)');
        } catch (fallbackError) {
          log(`Could not create tray: no icon found and fallback failed: ${fallbackError.message}`);
          return; // Skip tray creation if we can't create any icon
        }
      }
    }
    
    if (!tray && iconPath) {
      // Validate the icon file before using it
      try {
        const stats = fs.statSync(iconPath);
        if (stats.isFile() && stats.size > 0) {
          tray = new Tray(iconPath);
          log(`Tray created with icon: ${iconPath}`);
        } else {
          throw new Error('Icon file is empty or invalid');
        }
      } catch (iconError) {
        log(`Icon file validation failed: ${iconError.message}`);
        // Try fallback
        const { nativeImage } = require('electron');
        const fallbackIcon = nativeImage.createEmpty();
        tray = new Tray(fallbackIcon);
        log('Created tray with fallback icon due to validation error');
      }
    }
    
    if (!tray) {
      log('Skipping tray creation - no valid icon found');
      return;
    }
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Powerhouse',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
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
      label: 'Open in Browser',
      click: () => {
        const { shell } = require('electron');
        shell.openExternal(`http://localhost:${FRONTEND_PORT}`);
      }
    },
    { type: 'separator' },
    {
      label: 'Quit Powerhouse',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);
  
  tray.setToolTip(APP_NAME);
  tray.setContextMenu(contextMenu);
  
    tray.on('click', () => {
      if (mainWindow) {
        mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
      }
    });
  } catch (error) {
    log(`Error creating tray: ${error.message}`);
    log(error.stack);
    // Don't throw - tray is optional
  }
}

async function startServices() {
  try {
    log('=== Starting Powerhouse Services ===');
    
    const dbStarted = await startDatabase();
    if (!dbStarted) {
      log('Failed to start database');
      return false;
    }

    const backendStarted = await startBackend();
    if (!backendStarted) {
      log('Failed to start backend');
      return false;
    }

    const frontendStarted = await startFrontend();
    if (!frontendStarted) {
      log('Failed to start frontend');
      return false;
    }

    log('=== All services started successfully! ===');
    return true;
  } catch (error) {
    log(`Error starting services: ${error.message}`);
    log(error.stack);
    return false;
  }
}

function stopServices() {
  log('Stopping services...');

  if (frontendProcess) {
    try {
      if (process.platform === 'win32') {
        exec(`taskkill /PID ${frontendProcess.pid} /T /F`, () => {});
      } else {
        process.kill(frontendProcess.pid, 'SIGTERM');
      }
      log('Frontend stopped');
    } catch (err) {
      log(`Error stopping frontend: ${err.message}`);
    }
  }

  if (backendProcess) {
    try {
      if (process.platform === 'win32') {
        exec(`taskkill /PID ${backendProcess.pid} /T /F`, () => {});
      } else {
        process.kill(backendProcess.pid, 'SIGTERM');
      }
      log('Backend stopped');
    } catch (err) {
      log(`Error stopping backend: ${err.message}`);
    }
  }

  if (dbProcess) {
    try {
      if (process.platform === 'win32') {
        exec(`taskkill /PID ${dbProcess.pid} /T /F`, () => {});
      } else {
        process.kill(dbProcess.pid, 'SIGTERM');
      }
      log('Database stopped');
    } catch (err) {
      log(`Error stopping database: ${err.message}`);
    }
  }

  // Try to stop Docker containers
  spawn('docker-compose', ['down'], {
    cwd: resourcesPath,
    shell: getShell(),
    stdio: 'ignore'
  });
}

app.whenReady().then(async () => {
  try {
    log('=== Powerhouse Desktop App Starting ===');
    log(`App Path: ${appPath}`);
    log(`Resources Path: ${resourcesPath}`);
    log(`Data Path: ${dataPath}`);
    
    // System requirements check
    log('Checking system requirements...');
    const systemRequirements = await systemCheck.checkSystemRequirements();
    
    if (!systemRequirements.passed) {
      const errorMsg = systemRequirements.errors.join('\n\n');
      dialog.showErrorBox(
        'System Requirements Not Met',
        `Powerhouse cannot start because your system does not meet the minimum requirements:\n\n${errorMsg}\n\nPlease resolve these issues and try again.`
      );
      app.quit();
      return;
    }
    
    // Log system info
    const systemInfo = systemCheck.getSystemInfo();
    log(`System Info: ${JSON.stringify(systemInfo, null, 2)}`);
    
    // Create window and tray first (so dialog can attach to window if needed)
    createWindow();
    createTray();
    
    // Show warnings if any (after window is created)
    if (systemRequirements.warnings.length > 0) {
      const warningMsg = systemRequirements.warnings.join('\n\n');
      try {
        const result = await dialog.showMessageBox(mainWindow, {
          type: 'warning',
          title: 'System Warnings',
          message: 'Your system has some warnings:',
          detail: warningMsg + '\n\nPowerhouse will attempt to start, but you may experience issues.',
          buttons: ['Continue', 'Quit'],
          defaultId: 0
        });
        if (result.response === 1) {
          app.quit();
          return;
        }
      } catch (err) {
        log(`Error showing warning dialog: ${err.message}`);
        // Continue anyway
      }
    }
    
    // Start auto-updater
    updater.startAutoUpdateCheck();

    const started = await startServices();

    if (started) {
    log(`Loading frontend at http://localhost:${FRONTEND_PORT}`);
    // Wait a moment for frontend to fully initialize
    await new Promise(resolve => setTimeout(resolve, 2000));
    // Try to load frontend, with fallback
    mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`).catch((err) => {
      log(`Failed to load frontend: ${err.message}`);
      log(`Trying again in 3 seconds...`);
      setTimeout(() => {
        mainWindow.loadURL(`http://localhost:${FRONTEND_PORT}`).catch((err2) => {
          log(`Second attempt failed: ${err2.message}`);
          // Show error page
          const errorHTML = `
            <!DOCTYPE html>
            <html>
            <head>
              <style>
                body {
                  margin: 0;
                  padding: 40px;
                  display: flex;
                  justify-content: center;
                  align-items: center;
                  min-height: 100vh;
                  background: #ff8800;
                  color: white;
                  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                .container {
                  text-align: center;
                  max-width: 600px;
                }
                h1 { font-size: 2.5em; margin: 0 0 20px 0; }
                p { font-size: 1.1em; line-height: 1.6; }
                a { color: white; text-decoration: underline; }
              </style>
            </head>
            <body>
              <div class="container">
                <h1>⚠️ Frontend Not Ready</h1>
                <p>Services are running but frontend is not responding.</p>
                <p>Try opening in browser: <a href="http://localhost:${FRONTEND_PORT}">http://localhost:${FRONTEND_PORT}</a></p>
                <p>Or check the log file: ${dataPath}\\powerhouse.log</p>
              </div>
            </body>
            </html>
          `;
          mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHTML)}`);
        });
      }, 3000);
    });
  } else {
    const errorHTML = `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #ff4444;
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          }
          .container {
            text-align: center;
            max-width: 600px;
          }
          h1 { font-size: 2.5em; margin: 0 0 20px 0; }
          p { font-size: 1.1em; line-height: 1.6; }
          .log {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: left;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>⚠️ Failed to Start</h1>
          <p>Could not start Powerhouse services.</p>
          <p>Please check the log file for details:</p>
          <p style="font-family: monospace; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 4px;">${dataPath}\\powerhouse.log</p>
          <p>You can also try running the services manually using the batch files.</p>
        </div>
      </body>
      </html>
    `;
    mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHTML)}`);
    }
  } catch (error) {
    log(`Fatal error during startup: ${error.message}`);
    log(error.stack);
    
    // Try to show error dialog if window exists
    if (mainWindow) {
      const errorHTML = `
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {
              margin: 0;
              padding: 40px;
              display: flex;
              justify-content: center;
              align-items: center;
              min-height: 100vh;
              background: #ff4444;
              color: white;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .container {
              text-align: center;
              max-width: 600px;
            }
            h1 { font-size: 2.5em; margin: 0 0 20px 0; }
            p { font-size: 1.1em; line-height: 1.6; }
            .error {
              background: rgba(0,0,0,0.3);
              padding: 20px;
              border-radius: 8px;
              margin-top: 20px;
              text-align: left;
              font-family: monospace;
              font-size: 0.9em;
              word-break: break-all;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>⚠️ Startup Error</h1>
            <p>Powerhouse encountered a fatal error during startup.</p>
            <div class="error">${error.message}</div>
            <p style="margin-top: 20px;">Check the log file: ${dataPath}\\powerhouse.log</p>
          </div>
        </body>
        </html>
      `;
      mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHTML)}`);
    } else {
      // Window doesn't exist, show error dialog
      dialog.showErrorBox(
        'Powerhouse Startup Error',
        `Powerhouse encountered a fatal error:\n\n${error.message}\n\nCheck the log file: ${dataPath}\\powerhouse.log`
      );
      app.quit();
    }
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Don't quit on Windows, just hide to tray
    if (mainWindow) mainWindow.hide();
  }
});

app.on('before-quit', () => {
  isQuitting = true;
  updater.stopAutoUpdateCheck();
  stopServices();
});

app.on('will-quit', () => {
  stopServices();
});

/**
 * Powerhouse System Requirements Checker
 * Validates system meets minimum requirements before installation/launch
 */

const os = require('os');
const { exec } = require('child_process');
const http = require('http');
const { promisify } = require('util');

const execAsync = promisify(exec);

const MIN_RAM_GB = 4;
const MIN_DISK_SPACE_GB = 2;
const REQUIRED_PORTS = [3000, 8001, 5434];

/**
 * System requirements
 */
const REQUIREMENTS = {
  os: {
    windows: {
      minVersion: '10.0.0',
      name: 'Windows 10 or later'
    }
  },
  ram: {
    minGB: MIN_RAM_GB,
    recommendedGB: 8
  },
  disk: {
    minGB: MIN_DISK_SPACE_GB,
    recommendedGB: 5
  },
  ports: REQUIRED_PORTS,
  optional: {
    docker: {
      name: 'Docker Desktop',
      description: 'Required for database (or portable PostgreSQL will be used)'
    }
  }
};

/**
 * Check all system requirements
 */
async function checkSystemRequirements() {
  const results = {
    passed: true,
    errors: [],
    warnings: [],
    info: []
  };
  
  // Check OS
  const osCheck = checkOS();
  if (!osCheck.passed) {
    results.passed = false;
    results.errors.push(osCheck.error);
  } else {
    results.info.push(osCheck.info);
  }
  
  // Check RAM
  const ramCheck = await checkRAM();
  if (!ramCheck.passed) {
    results.passed = false;
    results.errors.push(ramCheck.error);
  } else if (ramCheck.warning) {
    results.warnings.push(ramCheck.warning);
  } else {
    results.info.push(ramCheck.info);
  }
  
  // Check disk space
  const diskCheck = await checkDiskSpace();
  if (!diskCheck.passed) {
    results.passed = false;
    results.errors.push(diskCheck.error);
  } else if (diskCheck.warning) {
    results.warnings.push(diskCheck.warning);
  } else {
    results.info.push(diskCheck.info);
  }
  
  // Check ports
  const portsCheck = await checkPorts();
  if (!portsCheck.passed) {
    results.warnings.push(...portsCheck.warnings);
  }
  if (portsCheck.info && portsCheck.info.length > 0) {
    results.info.push(...portsCheck.info);
  }
  if (portsCheck.passed && (!portsCheck.info || portsCheck.info.length === 0)) {
    results.info.push('All required ports are available');
  }
  
  // Check optional requirements
  const dockerCheck = await checkDocker();
  if (!dockerCheck.available) {
    results.warnings.push(dockerCheck.warning);
  } else {
    results.info.push('Docker Desktop is available');
  }
  
  return results;
}

/**
 * Check operating system
 */
function checkOS() {
  const platform = os.platform();
  const release = os.release();
  
  if (platform !== 'win32') {
    return {
      passed: false,
      error: `Unsupported operating system: ${platform}. Powerhouse requires Windows 10 or later.`
    };
  }
  
  // Parse Windows version
  const versionParts = release.split('.');
  const majorVersion = parseInt(versionParts[0], 10);
  
  if (majorVersion < 10) {
    return {
      passed: false,
      error: `Unsupported Windows version: ${release}. Powerhouse requires Windows 10 or later.`
    };
  }
  
  return {
    passed: true,
    info: `Operating system: Windows ${release} ✓`
  };
}

/**
 * Check available RAM
 */
async function checkRAM() {
  const totalMemoryGB = os.totalmem() / (1024 * 1024 * 1024);
  const freeMemoryGB = os.freemem() / (1024 * 1024 * 1024);
  
  if (totalMemoryGB < REQUIREMENTS.ram.minGB) {
    return {
      passed: false,
      error: `Insufficient RAM: ${totalMemoryGB.toFixed(1)} GB available. Minimum required: ${REQUIREMENTS.ram.minGB} GB.`
    };
  }
  
  if (totalMemoryGB < REQUIREMENTS.ram.recommendedGB) {
    return {
      passed: true,
      warning: `Low RAM: ${totalMemoryGB.toFixed(1)} GB available. Recommended: ${REQUIREMENTS.ram.recommendedGB} GB or more for optimal performance.`,
      info: `RAM: ${totalMemoryGB.toFixed(1)} GB total, ${freeMemoryGB.toFixed(1)} GB free`
    };
  }
  
  return {
    passed: true,
    info: `RAM: ${totalMemoryGB.toFixed(1)} GB total, ${freeMemoryGB.toFixed(1)} GB free ✓`
  };
}

/**
 * Check available disk space
 */
async function checkDiskSpace() {
  try {
    const { stdout } = await execAsync('wmic logicaldisk get size,freespace,caption');
    const lines = stdout.split('\n').filter(line => line.trim());
    
    // Find C: drive
    const cDriveLine = lines.find(line => line.includes('C:'));
    if (cDriveLine) {
      const parts = cDriveLine.trim().split(/\s+/);
      const freeSpaceBytes = parseInt(parts[parts.length - 2], 10);
      const freeSpaceGB = freeSpaceBytes / (1024 * 1024 * 1024);
      
      if (freeSpaceGB < REQUIREMENTS.disk.minGB) {
        return {
          passed: false,
          error: `Insufficient disk space: ${freeSpaceGB.toFixed(1)} GB available. Minimum required: ${REQUIREMENTS.disk.minGB} GB.`
        };
      }
      
      if (freeSpaceGB < REQUIREMENTS.disk.recommendedGB) {
        return {
          passed: true,
          warning: `Low disk space: ${freeSpaceGB.toFixed(1)} GB available. Recommended: ${REQUIREMENTS.disk.recommendedGB} GB or more.`,
          info: `Disk space: ${freeSpaceGB.toFixed(1)} GB free on C: drive`
        };
      }
      
      return {
        passed: true,
        info: `Disk space: ${freeSpaceGB.toFixed(1)} GB free on C: drive ✓`
      };
    }
  } catch (error) {
    // If we can't check, assume it's OK but warn
    return {
      passed: true,
      warning: 'Could not verify disk space. Please ensure at least 2 GB is available.'
    };
  }
  
  return {
    passed: true,
    info: 'Disk space: Available (could not determine exact amount)'
  };
}

/**
 * Check if required ports are available OR if services are already running
 */
async function checkPorts() {
  const warnings = [];
  const info = [];
  
  for (const port of REQUIREMENTS.ports) {
    // First check if port is free (for new installs)
    const isAvailable = await checkPort(port);
    
    if (!isAvailable) {
      // Port is in use - check if it's actually a Powerhouse service responding
      const isServiceRunning = await checkServiceRunning(port);
      if (isServiceRunning) {
        // Great! Service is already running
        const serviceName = port === 3000 ? 'Frontend' : port === 8001 ? 'Backend' : 'Database';
        info.push(`${serviceName} is already running on port ${port} ✓`);
      } else {
        // Port is in use by something else - that's a problem
        warnings.push(`Port ${port} is in use by another application. Powerhouse may not start correctly.`);
      }
    } else {
      info.push(`Port ${port} is available`);
    }
  }
  
  return {
    passed: warnings.length === 0,
    warnings,
    info
  };
}

/**
 * Check if a service is actually running and responding on a port
 */
function checkServiceRunning(port) {
  return new Promise((resolve) => {
    if (port === 5434) {
      // Database - check TCP connection
      const net = require('net');
      const socket = new net.Socket();
      socket.setTimeout(1000);
      socket.on('connect', () => {
        socket.destroy();
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
    
    // HTTP services - check if they respond
    const path = port === 8001 ? '/health' : '/';
    const options = {
      hostname: 'localhost',
      port: port,
      path: path,
      method: 'GET',
      timeout: 2000
    };

    const req = http.request(options, (res) => {
      resolve(res.statusCode >= 200 && res.statusCode < 500);
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

/**
 * Check if a specific port is available
 */
function checkPort(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const server = net.createServer();
    
    server.listen(port, () => {
      server.once('close', () => {
        resolve(true);
      });
      server.close();
    });
    
    server.on('error', () => {
      resolve(false);
    });
  });
}

/**
 * Check if Docker is available
 */
async function checkDocker() {
  try {
    await execAsync('docker --version');
    return {
      available: true
    };
  } catch (error) {
    return {
      available: false,
      warning: 'Docker Desktop is not installed or not running. Powerhouse will use portable PostgreSQL instead.'
    };
  }
}

/**
 * Get system information summary
 */
function getSystemInfo() {
  return {
    platform: os.platform(),
    arch: os.arch(),
    release: os.release(),
    totalMemory: `${(os.totalmem() / (1024 * 1024 * 1024)).toFixed(1)} GB`,
    freeMemory: `${(os.freemem() / (1024 * 1024 * 1024)).toFixed(1)} GB`,
    cpus: os.cpus().length,
    hostname: os.hostname(),
    homeDir: os.homedir(),
    tempDir: os.tmpdir()
  };
}

module.exports = {
  checkSystemRequirements,
  getSystemInfo,
  REQUIREMENTS
};


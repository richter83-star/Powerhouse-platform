/* eslint-disable no-console */
const { app, BrowserWindow, shell, ipcMain, dialog, Menu } = require("electron");
const path = require("path");
const fs = require("fs");
const os = require("os");
const http = require("http");
const { spawn } = require("child_process");

const PRODUCT_NAME = "Powerhouse Enterprise";
const APP_ID = "powerhouse-enterprise-desktop";

// Locked to avoid collisions with common dev ports
const NEXT_HOST = "127.0.0.1";
const NEXT_PORT = 3210;
const NEXT_URL = `http://${NEXT_HOST}:${NEXT_PORT}`;

let mainWindow = null;
let nextProc = null;

function nowIso() {
  return new Date().toISOString();
}

function ensureDir(p) {
  try {
    fs.mkdirSync(p, { recursive: true });
  } catch (_) {}
}

function getUserDataDir() {
  // Electron userData is stable even if app path changes
  return app.getPath("userData");
}

function getConfigPaths() {
  const userData = getUserDataDir();
  const configDir = path.join(userData, "config");
  const envPath = path.join(configDir, "app.env");
  const logDir = path.join(userData, "logs");
  const logPath = path.join(logDir, "app.log");
  return { userData, configDir, envPath, logDir, logPath };
}

function createLogger() {
  const { logDir, logPath } = getConfigPaths();
  ensureDir(logDir);

  return {
    log: (msg) => {
      const line = `[${nowIso()}] ${msg}\n`;
      try {
        fs.appendFileSync(logPath, line, "utf8");
      } catch (_) {}
      console.log(line.trimEnd());
    },
    path: () => logPath,
  };
}

const logger = createLogger();

function parseEnvFile(envPath) {
  if (!fs.existsSync(envPath)) return {};
  const raw = fs.readFileSync(envPath, "utf8");
  const out = {};
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx === -1) continue;
    const k = trimmed.slice(0, idx).trim();
    let v = trimmed.slice(idx + 1).trim();
    // Strip surrounding quotes
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    out[k] = v;
  }
  return out;
}

function writeDefaultEnv(envPath) {
  const template = [
    "# Powerhouse Enterprise Desktop config",
    "# Fill this in to use real data:",
    "# DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require",
    "",
    "# Optional:",
    "# NEXT_PUBLIC_APP_ENV=prod",
    "",
  ].join(os.EOL);

  ensureDir(path.dirname(envPath));
  if (!fs.existsSync(envPath)) fs.writeFileSync(envPath, template, "utf8");
}

function sanitizeBundledEnvFiles(nextAppDir) {
  // This is the key: bundled .env inside runtime can force demo/placeholder behavior.
  // We nuke it so ONLY user config (app.env) controls runtime.
  const candidates = [
    ".env",
    ".env.local",
    ".env.production",
    ".env.production.local",
    ".env.development",
    ".env.development.local",
  ];

  for (const file of candidates) {
    const p = path.join(nextAppDir, file);
    try {
      if (fs.existsSync(p)) {
        fs.unlinkSync(p);
        logger.log(`Removed bundled env file: ${p}`);
      }
    } catch (e) {
      logger.log(`WARN: Could not remove ${p}: ${String(e && e.message ? e.message : e)}`);
    }
  }

  // Also remove any ".env.*" variants conservatively
  try {
    const items = fs.readdirSync(nextAppDir);
    for (const name of items) {
      if (name.startsWith(".env.") && name.length > 5) {
        const p = path.join(nextAppDir, name);
        try {
          fs.unlinkSync(p);
          logger.log(`Removed bundled env file: ${p}`);
        } catch (e) {
          logger.log(`WARN: Could not remove ${p}: ${String(e && e.message ? e.message : e)}`);
        }
      }
    }
  } catch (_) {}
}

function getRuntimePaths() {
  const resourcesPath = process.resourcesPath;
  const runtimeRoot = path.join(resourcesPath, "runtime");

  const nodeExe = path.join(runtimeRoot, "node", "node.exe");
  const nextAppDir = path.join(runtimeRoot, "next", "app");
  const serverJs = path.join(nextAppDir, "server.js");

  return { resourcesPath, runtimeRoot, nodeExe, nextAppDir, serverJs };
}

function waitForHttp(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    const start = Date.now();

    const tick = () => {
      const req = http.get(url, (res) => {
        res.resume();
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) return resolve(true);
        return retry();
      });
      req.on("error", retry);
      req.setTimeout(2000, () => {
        req.destroy(new Error("timeout"));
      });

      function retry() {
        if (Date.now() - start > timeoutMs) return reject(new Error(`Timeout waiting for ${url}`));
        setTimeout(tick, 250);
      }
    };

    tick();
  });
}

function createMainWindow(startUrl) {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    show: true,
    webPreferences: {
      // If you have a preload, wire it here; leaving off keeps this safer by default.
      // preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.on("closed", () => (mainWindow = null));
  mainWindow.loadURL(startUrl);
}

function buildMenu() {
  const { envPath } = getConfigPaths();
  const template = [
    {
      label: PRODUCT_NAME,
      submenu: [
        {
          label: "Open Config File",
          click: async () => {
            try {
              writeDefaultEnv(envPath);
              await shell.openPath(envPath);
              logger.log(`Open config requested: ${envPath}`);
            } catch (e) {
              dialog.showErrorBox(PRODUCT_NAME, `Could not open config file:\n${String(e)}`);
            }
          },
        },
        {
          label: "Open Logs",
          click: async () => {
            try {
              await shell.openPath(logger.path());
            } catch (e) {
              dialog.showErrorBox(PRODUCT_NAME, `Could not open log file:\n${String(e)}`);
            }
          },
        },
        { type: "separator" },
        { role: "quit" },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

async function startNextServer() {
  const { envPath } = getConfigPaths();
  writeDefaultEnv(envPath);

  const envFromFile = parseEnvFile(envPath);
  const { nodeExe, nextAppDir, serverJs, resourcesPath } = getRuntimePaths();

  logger.log(`=== ${PRODUCT_NAME} starting ===`);
  logger.log(`userData: ${getUserDataDir()}`);
  logger.log(`envPath: ${envPath}`);
  logger.log(`resourcesPath: ${resourcesPath}`);
  logger.log(`nodeExe: ${nodeExe}`);
  logger.log(`nextAppDir: ${nextAppDir}`);
  logger.log(`serverJs: ${serverJs}`);
  logger.log(`url: ${NEXT_URL}`);

  if (!fs.existsSync(nodeExe)) {
    throw new Error(`Missing node.exe: ${nodeExe}`);
  }
  if (!fs.existsSync(serverJs)) {
    throw new Error(`Missing Next server.js: ${serverJs}`);
  }

  // Kill any bundled env shipped with runtime (prevents “demo mode” getting stuck)
  sanitizeBundledEnvFiles(nextAppDir);

  const hasDb = Boolean(envFromFile.DATABASE_URL && String(envFromFile.DATABASE_URL).trim().length > 0);

  // Force a single deterministic rule:
  // - If DATABASE_URL is missing -> demo mode ON (but no tacky UI toggle needed)
  // - If DATABASE_URL exists -> demo mode OFF
  const mergedEnv = {
    ...process.env,
    ...envFromFile,
    NODE_ENV: "production",
    HOSTNAME: NEXT_HOST,
    PORT: String(NEXT_PORT),
    PH_DEMO_MODE: hasDb ? "0" : "1",
    // If any code uses dotenv/config implicitly, these reduce surprises (harmless otherwise)
    DOTENV_CONFIG_PATH: "NUL",
    DOTENV_CONFIG_OVERRIDE: "1",
  };

  logger.log(`dbConfigured=${hasDb ? "true" : "false"} PH_DEMO_MODE=${mergedEnv.PH_DEMO_MODE}`);

  // Ensure Next runs with a real filesystem cwd (not inside asar)
  nextProc = spawn(nodeExe, [serverJs], {
    cwd: nextAppDir,
    env: mergedEnv,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  nextProc.stdout.on("data", (d) => logger.log(`[next stdout] ${String(d).trimEnd()}`));
  nextProc.stderr.on("data", (d) => logger.log(`[next stderr] ${String(d).trimEnd()}`));
  nextProc.on("exit", (code, signal) => {
    logger.log(`Next server exited. code=${code} signal=${signal}`);
    nextProc = null;
  });

  await waitForHttp(NEXT_URL, 60000);
}

function loadConfigUi() {
  // Use packaged config.html if present; otherwise fall back to a simple inline page.
  // This keeps “Open config file” + “Relaunch” paths available even when Next fails.
  const configHtmlPath = path.join(process.resourcesPath, "app.asar", "electron", "config.html");

  if (fs.existsSync(configHtmlPath)) {
    logger.log(`Loading config UI: ${configHtmlPath}`);
    createMainWindow(`file://${configHtmlPath}`);
    return;
  }

  const { envPath } = getConfigPaths();
  const html = `
  <html>
    <body style="font-family: sans-serif; padding: 24px;">
      <h2>${PRODUCT_NAME} Config</h2>
      <p>Config file:</p>
      <pre>${envPath}</pre>
      <button onclick="require('electron').shell.openPath('${envPath.replace(/\\/g, "\\\\")}')">Open config</button>
      <button onclick="location.reload()">Relaunch</button>
      <p style="margin-top: 16px; color: #666;">If the app shows demo data, set DATABASE_URL and relaunch.</p>
    </body>
  </html>`;
  const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(html)}`;
  createMainWindow(dataUrl);
}

async function boot() {
  buildMenu();

  try {
    await startNextServer();
    createMainWindow(NEXT_URL);
  } catch (e) {
    logger.log(`BOOT ERROR: ${String(e && e.message ? e.message : e)}`);
    loadConfigUi();
  }
}

app.setName(PRODUCT_NAME);

app.on("ready", boot);

app.on("window-all-closed", () => {
  // Windows behavior: quit when all windows closed.
  app.quit();
});

app.on("before-quit", () => {
  try {
    if (nextProc) nextProc.kill();
  } catch (_) {}
});

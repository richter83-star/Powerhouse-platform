import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Paths
const desktopRoot = path.resolve(__dirname, "..");            // frontend/desktop
const nextAppRoot = path.resolve(desktopRoot, "..", "app");   // frontend/app

const standaloneSrc = path.join(nextAppRoot, ".next", "standalone");
const staticSrc = path.join(nextAppRoot, ".next", "static");
const publicSrc = path.join(nextAppRoot, "public");

const nextDestRoot = path.join(desktopRoot, ".next");
const standaloneDest = path.join(nextDestRoot, "standalone");
const staticDest = path.join(nextDestRoot, "static");

// In some builds, standalone output nests the app under "app/"
const standaloneAppDest = path.join(standaloneDest, "app");
const standaloneAppStaticDest = path.join(standaloneAppDest, ".next", "static");
const standaloneAppPublicDest = path.join(standaloneAppDest, "public");

// Also provide public at desktop root for any code that expects it there
const publicDest = path.join(desktopRoot, "public");

function log(msg) {
  console.log(`[prep-runtime] ${msg}`);
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function removeRecursive(target) {
  if (!fs.existsSync(target)) return;
  const stat = fs.statSync(target);
  if (stat.isDirectory()) {
    for (const entry of fs.readdirSync(target)) {
      removeRecursive(path.join(target, entry));
    }
    fs.rmdirSync(target);
  } else {
    fs.unlinkSync(target);
  }
}

function copyFile(src, dest) {
  ensureDir(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

function copyRecursive(src, dest) {
  if (!fs.existsSync(src)) throw new Error(`Source does not exist: ${src}`);
  const stat = fs.statSync(src);

  if (stat.isDirectory()) {
    ensureDir(dest);
    for (const entry of fs.readdirSync(src)) {
      copyRecursive(path.join(src, entry), path.join(dest, entry));
    }
  } else {
    copyFile(src, dest);
  }
}

function pathExists(p) {
  try {
    return fs.existsSync(p);
  } catch {
    return false;
  }
}

function requireExists(p, hint) {
  if (!pathExists(p)) {
    throw new Error(`${hint}\nMissing path: ${p}`);
  }
}

function main() {
  log(`desktopRoot: ${desktopRoot}`);
  log(`nextAppRoot: ${nextAppRoot}`);

  // 1) Validate Next standalone output exists
  requireExists(
    standaloneSrc,
    `Next standalone output not found.\nMake sure next.config has output: "standalone" and you ran the Next build.`
  );

  // server.js can be either standalone/server.js or standalone/app/server.js
  const serverA = path.join(standaloneSrc, "server.js");
  const serverB = path.join(standaloneSrc, "app", "server.js");
  if (!pathExists(serverA) && !pathExists(serverB)) {
    throw new Error(
      `Next standalone folder exists, but server.js not found.\nLooked for:\n- ${serverA}\n- ${serverB}`
    );
  }
  log(`Found standalone server at: ${pathExists(serverA) ? serverA : serverB}`);

  // 2) Clean desktop runtime payload
  log(`Cleaning desktop runtime payload: ${nextDestRoot}`);
  removeRecursive(nextDestRoot);
  removeRecursive(publicDest);

  // 3) Copy standalone bundle as-is (preserves nested /app layout if present)
  log(`Copying standalone:\n  ${standaloneSrc}\n→ ${standaloneDest}`);
  copyRecursive(standaloneSrc, standaloneDest);

  // 4) Copy static assets
  if (pathExists(staticSrc)) {
    log(`Copying static:\n  ${staticSrc}\n→ ${staticDest}`);
    copyRecursive(staticSrc, staticDest);

    // Also copy into standalone/app/.next/static if standalone has "app/" folder
    if (pathExists(standaloneAppDest)) {
      log(`Copying static into standalone app:\n  ${staticSrc}\n→ ${standaloneAppStaticDest}`);
      copyRecursive(staticSrc, standaloneAppStaticDest);
    } else {
      log(`No standalone/app folder detected; skipping standalone app static copy.`);
    }
  } else {
    log(`No .next/static found at ${staticSrc} (skipping).`);
  }

  // 5) Copy public assets
  if (pathExists(publicSrc)) {
    log(`Copying public:\n  ${publicSrc}\n→ ${publicDest}`);
    copyRecursive(publicSrc, publicDest);

    if (pathExists(standaloneAppDest)) {
      log(`Copying public into standalone app:\n  ${publicSrc}\n→ ${standaloneAppPublicDest}`);
      copyRecursive(publicSrc, standaloneAppPublicDest);
    }
  } else {
    log(`No public folder found at ${publicSrc} (skipping).`);
  }

  log("prep-runtime complete ✅");
}

try {
  main();
} catch (err) {
  console.error("[prep-runtime] ERROR:", err?.stack || err?.message || err);
  process.exit(1);
}

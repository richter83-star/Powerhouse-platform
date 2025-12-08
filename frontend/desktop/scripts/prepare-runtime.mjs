import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// scripts/ -> desktop/
const desktopDir = path.resolve(__dirname, "..");
const nextAppDir = path.resolve(desktopDir, "..", "app");

const runtimeRoot = path.join(desktopDir, "runtime");
const nodeDir = path.join(runtimeRoot, "node");
const nextBundleRoot = path.join(runtimeRoot, "next");

function rm(p) {
  fs.rmSync(p, { recursive: true, force: true });
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function copyFile(src, dst) {
  ensureDir(path.dirname(dst));
  fs.copyFileSync(src, dst);
}

function copyDir(src, dst) {
  ensureDir(dst);
  fs.cpSync(src, dst, { recursive: true, force: true });
}

function exists(p) {
  try { return fs.existsSync(p); } catch { return false; }
}

function findServerJs(root) {
  const candidates = [
    path.join(root, "server.js"),
    path.join(root, "app", "server.js"),
    path.join(root, ".next", "standalone", "server.js"),
    path.join(root, ".next", "standalone", "app", "server.js")
  ];
  for (const p of candidates) if (exists(p)) return p;

  const stack = [root];
  let steps = 0;
  while (stack.length && steps++ < 5000) {
    const dir = stack.pop();
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); }
    catch { continue; }

    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isFile() && e.name.toLowerCase() === "server.js") return full;
      if (e.isDirectory()) stack.push(full);
    }
  }
  return null;
}

function main() {
  console.log("== prepare-runtime ==");
  console.log("desktopDir:", desktopDir);
  console.log("nextAppDir:", nextAppDir);

  // Must have Next build outputs
  const standaloneSrc = path.join(nextAppDir, ".next", "standalone");
  const staticSrc = path.join(nextAppDir, ".next", "static");
  const publicSrc = path.join(nextAppDir, "public");

  if (!exists(standaloneSrc)) {
    throw new Error(`Missing ${standaloneSrc}. Run Next build first: (cd ../app) npm run build`);
  }
  if (!exists(staticSrc)) {
    throw new Error(`Missing ${staticSrc}. Run Next build first: (cd ../app) npm run build`);
  }

  // Clean + recreate runtime
  rm(runtimeRoot);
  ensureDir(nodeDir);
  ensureDir(nextBundleRoot);

  // Bundle node.exe (the node running this script)
  const nodeExeSrc = process.execPath;
  const nodeExeDst = path.join(nodeDir, "node.exe");
  copyFile(nodeExeSrc, nodeExeDst);
  console.log("Bundled node.exe:", nodeExeDst);

  // Copy standalone tree to runtime/next
  // NOTE: Next standalone output often contains a top-level folder matching project dir name (e.g. "app/")
  copyDir(standaloneSrc, nextBundleRoot);
  console.log("Copied standalone ->", nextBundleRoot);

  // Find server.js inside runtime/next
  const serverJs = findServerJs(nextBundleRoot);
  if (!serverJs) {
    throw new Error(`server.js not found under ${nextBundleRoot} after copy.`);
  }

  // Project root = folder containing server.js
  const projectRoot = path.dirname(serverJs);
  console.log("Detected server.js:", serverJs);
  console.log("Project root:", projectRoot);

  // Copy .next/static into <projectRoot>/.next/static
  const dstStatic = path.join(projectRoot, ".next", "static");
  copyDir(staticSrc, dstStatic);
  console.log("Copied static ->", dstStatic);

  // Copy public/ into <projectRoot>/public (if present)
  if (exists(publicSrc)) {
    const dstPublic = path.join(projectRoot, "public");
    copyDir(publicSrc, dstPublic);
    console.log("Copied public ->", dstPublic);
  } else {
    console.log("No public/ folder found; skipping.");
  }

  // Build info
  const info = [
    `builtAt=${new Date().toISOString()}`,
    `nodeExeSrc=${nodeExeSrc}`,
    `serverJs=${serverJs}`,
    `projectRoot=${projectRoot}`
  ].join("\n");
  fs.writeFileSync(path.join(runtimeRoot, "BUILD_INFO.txt"), info, "utf8");

  console.log("prepare-runtime complete.");
}

main();

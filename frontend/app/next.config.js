const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: process.env.NEXT_DIST_DIR || ".next",

  // Standalone is the most compatible for Electron packaging.
  output: process.env.NEXT_OUTPUT_MODE || "standalone",

  experimental: {
    // Keep tracing rooted at repo/frontend level
    outputFileTracingRoot: path.join(__dirname, "../"),
  },

  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },

  images: { unoptimized: true },
};

module.exports = nextConfig;

const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: process.env.NEXT_DIST_DIR || ".next",

  // Standalone is the most compatible for Electron packaging.
  // Disable standalone mode in Docker (use default mode instead)
  output: process.env.NEXT_OUTPUT_MODE || (process.env.DOCKER_BUILD ? undefined : "standalone"),

  experimental: {
    // Keep tracing rooted at repo/frontend level
    outputFileTracingRoot: path.join(__dirname, "../"),
  },

  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: false },

  images: { unoptimized: true },
};

module.exports = nextConfig;

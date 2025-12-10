const fs = require('fs');
const path = require('path');

// Create a 256x256 ICO file
// ICO format: Header + Directory Entry + Bitmap Data

// ICO File Header (6 bytes)
const icoHeader = Buffer.from([
  0x00, 0x00,  // Reserved (must be 0)
  0x01, 0x00,  // Type (1 = ICO)
  0x01, 0x00   // Number of images
]);

// Directory Entry (16 bytes) - 256x256, 32-bit RGBA
const directoryEntry = Buffer.from([
  0x00,        // Width (0 = 256)
  0x00,        // Height (0 = 256)
  0x00,        // Color palette (0 = no palette)
  0x00,        // Reserved
  0x01, 0x00,  // Color planes
  0x20, 0x00,  // Bits per pixel (32 = RGBA)
  0x00, 0x00, 0x00, 0x00,  // Image size (will calculate)
  0x16, 0x00, 0x00, 0x00   // Offset to image data (22 bytes = header + directory)
]);

// Bitmap Info Header (40 bytes) - BITMAPINFOHEADER
const bitmapInfoHeader = Buffer.from([
  0x28, 0x00, 0x00, 0x00,  // Header size (40 bytes)
  0x00, 0x01, 0x00, 0x00,  // Width (256)
  0x00, 0x01, 0x00, 0x00,  // Height (512 = 256*2 for top-down + bottom-up)
  0x01, 0x00,              // Color planes
  0x20, 0x00,              // Bits per pixel (32)
  0x00, 0x00, 0x00, 0x00,  // Compression (0 = none)
  0x00, 0x00, 0x00, 0x00,  // Image size (can be 0 for uncompressed)
  0x00, 0x00, 0x00, 0x00,  // X pixels per meter
  0x00, 0x00, 0x00, 0x00,  // Y pixels per meter
  0x00, 0x00, 0x00, 0x00,  // Colors used
  0x00, 0x00, 0x00, 0x00   // Important colors
]);

// Bitmap Data: 256x256 pixels, 32-bit RGBA = 262,144 bytes
// Create a simple gradient pattern (blue to purple)
const bitmapData = Buffer.alloc(262144);
for (let y = 0; y < 256; y++) {
  for (let x = 0; x < 256; x++) {
    const offset = (y * 256 + x) * 4;
    // RGBA format (little-endian: BGRA in memory)
    const r = Math.floor((x / 256) * 255);      // Red gradient
    const g = Math.floor((y / 256) * 255);      // Green gradient
    const b = 200;                              // Blue constant
    const a = 255;                              // Alpha (opaque)
    
    bitmapData[offset] = b;     // Blue
    bitmapData[offset + 1] = g;  // Green
    bitmapData[offset + 2] = r;  // Red
    bitmapData[offset + 3] = a;  // Alpha
  }
}

// Calculate image size
const imageSize = bitmapInfoHeader.length + bitmapData.length;
directoryEntry.writeUInt32LE(imageSize, 8);

// Combine all parts
const fullIco = Buffer.concat([
  icoHeader,
  directoryEntry,
  bitmapInfoHeader,
  bitmapData
]);

const iconPath = path.join(__dirname, 'build', 'icon.ico');

// Ensure build directory exists
const buildDir = path.dirname(iconPath);
if (!fs.existsSync(buildDir)) {
  fs.mkdirSync(buildDir, { recursive: true });
}

// Write icon file
fs.writeFileSync(iconPath, fullIco);

console.log(`✅ Created 256x256 icon at: ${iconPath}`);
console.log(`   Size: ${fullIco.length} bytes`);
console.log(`   Format: 256x256, 32-bit RGBA`);

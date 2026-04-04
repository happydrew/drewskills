#!/usr/bin/env node

/**
 * Image conversion script using sharp
 * Usage: node convert.js <input> <output> [options]
 *    or: node convert.js --input-env=IMG_IN --output-env=IMG_OUT [options]
 */

const fs = require('fs');
const path = require('path');
const { loadModule } = require('./module-resolver');

let sharp;
try {
  sharp = loadModule('sharp');
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}

// Parse command line arguments
const options = {};
let inputPath;
let outputPath;

process.argv.slice(2).forEach(arg => {
  if (!arg.startsWith('--') && !inputPath) {
    inputPath = arg;
  } else if (!arg.startsWith('--') && !outputPath) {
    outputPath = arg;
  } else if (arg.startsWith('--input-env=')) {
    inputPath = process.env[arg.split('=')[1]];
  } else if (arg.startsWith('--output-env=')) {
    outputPath = process.env[arg.split('=')[1]];
  } else if (arg.startsWith('--quality=')) {
    options.quality = parseInt(arg.split('=')[1], 10);
  } else if (arg.startsWith('--width=')) {
    options.width = parseInt(arg.split('=')[1], 10);
  } else if (arg.startsWith('--height=')) {
    options.height = parseInt(arg.split('=')[1], 10);
  }
});

if (!inputPath || !outputPath) {
  console.error('Usage: node convert.js <input> <output> [--quality=85] [--width=<px>] [--height=<px>]');
  console.error('   or: node convert.js --input-env=IMG_IN --output-env=IMG_OUT [--quality=85] [--width=<px>] [--height=<px>]');
  process.exit(1);
}

// Check if input file exists
if (!fs.existsSync(inputPath)) {
  console.error(`Error: Input file not found: ${inputPath}`);
  process.exit(1);
}

// Determine output format from extension
const outputExt = path.extname(outputPath).toLowerCase().slice(1);
const supportedFormats = ['jpg', 'jpeg', 'png', 'webp', 'avif', 'tiff', 'gif'];

if (!supportedFormats.includes(outputExt)) {
  console.error(`Error: Unsupported output format: ${outputExt}`);
  console.error(`Supported formats: ${supportedFormats.join(', ')}`);
  process.exit(1);
}

// Build sharp pipeline
let pipeline = sharp(inputPath);

// Apply resize if specified
if (options.width || options.height) {
  pipeline = pipeline.resize(options.width, options.height, {
    fit: 'inside',
    withoutEnlargement: true
  });
}

// Apply format conversion
const formatOptions = {};
if (options.quality !== undefined) {
  formatOptions.quality = options.quality;
}

switch (outputExt) {
  case 'jpg':
  case 'jpeg':
    pipeline = pipeline.jpeg(formatOptions);
    break;
  case 'png':
    pipeline = pipeline.png(formatOptions);
    break;
  case 'webp':
    pipeline = pipeline.webp(formatOptions);
    break;
  case 'avif':
    pipeline = pipeline.avif(formatOptions);
    break;
  case 'tiff':
    pipeline = pipeline.tiff(formatOptions);
    break;
  case 'gif':
    pipeline = pipeline.gif(formatOptions);
    break;
}

// Execute conversion
pipeline
  .toFile(outputPath)
  .then(info => {
    console.log(JSON.stringify({
      success: true,
      input: inputPath,
      output: outputPath,
      format: info.format,
      width: info.width,
      height: info.height,
      size: info.size,
      channels: info.channels
    }, null, 2));
  })
  .catch(err => {
    console.error(JSON.stringify({
      success: false,
      error: err.message
    }, null, 2));
    process.exit(1);
  });

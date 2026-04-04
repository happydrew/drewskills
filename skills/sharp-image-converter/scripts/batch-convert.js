#!/usr/bin/env node

/**
 * Batch image conversion script using sharp
 * Usage: node batch-convert.js <input-pattern> <output-dir> <output-format> [options]
 */

const fs = require('fs');
const path = require('path');
const { loadModule } = require('./module-resolver');

let sharp;
let glob;
try {
  sharp = loadModule('sharp');
  ({ glob } = loadModule('glob'));
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}

const args = process.argv.slice(2);

if (args.length < 3) {
  console.error('Usage: node batch-convert.js <input-pattern> <output-dir> <output-format> [--quality=85] [--width=<px>] [--height=<px>]');
  console.error('Example: node batch-convert.js "images/*.png" output webp --quality=90');
  process.exit(1);
}

const inputPattern = args[0];
const outputDir = args[1];
const outputFormat = args[2].toLowerCase();
const options = {};

args.slice(3).forEach(arg => {
  if (arg.startsWith('--quality=')) {
    options.quality = parseInt(arg.split('=')[1], 10);
  } else if (arg.startsWith('--width=')) {
    options.width = parseInt(arg.split('=')[1], 10);
  } else if (arg.startsWith('--height=')) {
    options.height = parseInt(arg.split('=')[1], 10);
  }
});

const supportedFormats = ['jpg', 'jpeg', 'png', 'webp', 'avif', 'tiff', 'gif'];
if (!supportedFormats.includes(outputFormat)) {
  console.error(`Error: Unsupported output format: ${outputFormat}`);
  console.error(`Supported formats: ${supportedFormats.join(', ')}`);
  process.exit(1);
}

if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

glob(inputPattern, { windowsPathsNoEscape: true })
  .then(files => {
    if (files.length === 0) {
      console.error(`No files found matching pattern: ${inputPattern}`);
      process.exit(1);
    }

    console.log(`Found ${files.length} files to convert`);

    const tasks = files.map(async inputPath => {
      const basename = path.basename(inputPath, path.extname(inputPath));
      const outputPath = path.join(outputDir, `${basename}.${outputFormat}`);

      let pipeline = sharp(inputPath);
      if (options.width || options.height) {
        pipeline = pipeline.resize(options.width, options.height, {
          fit: 'inside',
          withoutEnlargement: true
        });
      }

      const formatOptions = {};
      if (options.quality !== undefined) {
        formatOptions.quality = options.quality;
      }

      switch (outputFormat) {
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

      try {
        const info = await pipeline.toFile(outputPath);
        return {
          success: true,
          input: inputPath,
          output: outputPath,
          format: info.format,
          width: info.width,
          height: info.height,
          size: info.size
        };
      } catch (error) {
        return {
          success: false,
          input: inputPath,
          error: error.message
        };
      }
    });

    return Promise.all(tasks);
  })
  .then(printResults)
  .catch(error => {
    console.error(`Error finding files: ${error.message}`);
    process.exit(1);
  });

function printResults(results) {
  const successful = results.filter(result => result.success);
  const failed = results.filter(result => !result.success);

  console.log('\n=== Conversion Results ===');
  console.log(`Total: ${results.length}`);
  console.log(`Successful: ${successful.length}`);
  console.log(`Failed: ${failed.length}`);

  if (successful.length > 0) {
    console.log('\nSuccessful conversions:');
    successful.forEach(result => {
      console.log(`  OK ${result.input} -> ${result.output} (${result.width}x${result.height}, ${(result.size / 1024).toFixed(2)} KB)`);
    });
  }

  if (failed.length > 0) {
    console.log('\nFailed conversions:');
    failed.forEach(result => {
      console.log(`  FAIL ${result.input}: ${result.error}`);
    });
  }

  process.exit(failed.length > 0 ? 1 : 0);
}

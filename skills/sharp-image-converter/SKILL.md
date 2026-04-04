---
name: sharp-image-converter
description: Convert images between formats (PNG, JPEG, WebP, AVIF, TIFF, GIF) and perform batch conversions using the sharp library. Use when users request image format conversion, converting images to WebP/AVIF, batch image processing, or optimizing images for web. Triggers include "convert image to", "change format to", "batch convert images", or "optimize images".
---
# Sharp Image Converter

Convert images between formats using the sharp library, which is commonly available in Node.js projects.

Prefer the bundled scripts over ad-hoc `node -e` snippets when working on Windows or when file paths contain spaces or non-ASCII characters.

## Prerequisites

This skill requires `sharp` to be available globally by default.

The batch script also requires `glob`.

The bundled scripts resolve dependencies in this order:
- global npm modules
- `NODE_PATH`
- current project dependencies
- the skill script's own resolution path

If a package is missing, install it globally:

```bash
npm install -g sharp glob
```

## Preferred Commands

Use the bundled scripts first:

```bash
node <skill-path>/scripts/convert.js <input> <output> [--quality=85] [--width=<px>] [--height=<px>]
node <skill-path>/scripts/convert.js --input-env=IMG_IN --output-env=IMG_OUT [--quality=85] [--width=<px>] [--height=<px>]
node <skill-path>/scripts/batch-convert.js <input-pattern> <output-dir> <output-format> [options]
```

PowerShell example that avoids shell encoding issues for non-ASCII paths:

```powershell
$env:IMG_IN = (Get-Item -LiteralPath "C:\path\to\input.png").FullName
$env:IMG_OUT = [System.IO.Path]::ChangeExtension($env:IMG_IN, "webp")
node C:\Users\zhuge\.agents\skills\sharp-image-converter\scripts\convert.js --input-env=IMG_IN --output-env=IMG_OUT
```

## Single Image Conversion

Use inline Node.js commands only for quick one-off conversions when quoting is simple:

**Basic conversion:**
```bash
node -e "const sharp = require('sharp'); sharp('input.png').webp().toFile('output.webp').then(info => console.log('Converted:', info)).catch(err => console.error('Error:', err));"
```

**With quality setting:**
```bash
node -e "const sharp = require('sharp'); sharp('input.png').webp({ quality: 85 }).toFile('output.webp').then(info => console.log('Converted:', info)).catch(err => console.error('Error:', err));"
```

**With resize:**
```bash
node -e "const sharp = require('sharp'); sharp('input.png').resize(800).webp({ quality: 85 }).toFile('output.webp').then(info => console.log('Converted:', info)).catch(err => console.error('Error:', err));"
```

**Format-specific examples:**

```bash
# PNG to WebP
node -e "const sharp = require('sharp'); sharp('input.png').webp().toFile('output.webp').then(info => console.log('Converted:', info));"

# JPEG to WebP
node -e "const sharp = require('sharp'); sharp('photo.jpg').webp({ quality: 90 }).toFile('photo.webp').then(info => console.log('Converted:', info));"

# PNG to AVIF
node -e "const sharp = require('sharp'); sharp('input.png').avif({ quality: 80 }).toFile('output.avif').then(info => console.log('Converted:', info));"

# WebP to PNG
node -e "const sharp = require('sharp'); sharp('input.webp').png().toFile('output.png').then(info => console.log('Converted:', info));"

# JPEG to PNG
node -e "const sharp = require('sharp'); sharp('photo.jpg').png().toFile('photo.png').then(info => console.log('Converted:', info));"
```

**Supported formats:** jpg, jpeg, png, webp, avif, tiff, gif

## Batch Conversion

For batch operations, use the provided script from the skill's `scripts/` directory:

```bash
node <skill-path>/scripts/batch-convert.js <input-pattern> <output-dir> <output-format> [options]
```

**Options:**
- `--quality=<1-100>`: Set output quality for all images
- `--width=<pixels>`: Resize all images to specific width
- `--height=<pixels>`: Resize all images to specific height

**Examples:**

```bash
# Convert all PNGs in a directory to WebP
node <skill-path>/scripts/batch-convert.js "images/*.png" output webp

# Convert with quality setting
node <skill-path>/scripts/batch-convert.js "photos/**/*.jpg" optimized webp --quality=85

# Convert and resize all images
node <skill-path>/scripts/batch-convert.js "public/imgs/**/*.png" public/imgs/webp webp --width=1920 --quality=90
```

**Pattern syntax:**
- `*.png` - All PNG files in current directory
- `**/*.jpg` - All JPG files in current directory and subdirectories
- `images/*.{png,jpg}` - All PNG and JPG files in images directory

**Note:** The batch script requires the `glob` package. If not available, convert images individually using the inline commands above.

## Format Recommendations

- **WebP**: Best for web use, excellent compression, wide browser support
- **AVIF**: Better compression than WebP, growing browser support
- **PNG**: Lossless, supports transparency, larger file sizes
- **JPEG**: Good for photos, lossy compression, no transparency
- **TIFF**: Archival quality, very large files
- **GIF**: Animations and simple graphics only

## Quality Guidelines

- **WebP/AVIF**: 80-90 for photos, 90-100 for graphics
- **JPEG**: 85-95 for photos
- **PNG**: Quality setting affects compression level, not visual quality

## Common Patterns

**Optimize for web:**
```bash
node -e "const sharp = require('sharp'); sharp('large-image.png').resize(1920).webp({ quality: 85 }).toFile('optimized.webp').then(info => console.log('Optimized:', info));"
```

**Convert with transparency:**
```bash
node -e "const sharp = require('sharp'); sharp('logo.png').webp({ quality: 100, lossless: true }).toFile('logo.webp').then(info => console.log('Converted:', info));"
```

**Generate thumbnail:**
```bash
node -e "const sharp = require('sharp'); sharp('photo.jpg').resize(300, 300, { fit: 'cover' }).webp({ quality: 80 }).toFile('thumb.webp').then(info => console.log('Thumbnail created:', info));"
```

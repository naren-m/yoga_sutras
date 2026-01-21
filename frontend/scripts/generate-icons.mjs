import sharp from 'sharp';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const publicDir = join(__dirname, '..', 'public');

// Create a purple gradient background with Om symbol
// Using a simple SVG since sharp can render SVG to PNG
const createIconSvg = (size) => `
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#7c3aed"/>
      <stop offset="100%" style="stop-color:#5b21b6"/>
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" fill="url(#grad)" rx="${size * 0.1}"/>
  <text
    x="${size / 2}"
    y="${size * 0.65}"
    font-size="${size * 0.55}"
    fill="white"
    text-anchor="middle"
    font-family="serif">ॐ</text>
</svg>`;

// Maskable icon needs safe zone padding (icon content in center 80%)
const createMaskableIconSvg = (size) => {
  const padding = size * 0.1; // 10% padding on each side
  const innerSize = size - (padding * 2);
  return `
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#7c3aed"/>
  <text
    x="${size / 2}"
    y="${size * 0.62}"
    font-size="${innerSize * 0.55}"
    fill="white"
    text-anchor="middle"
    font-family="serif">ॐ</text>
</svg>`;
};

const sizes = [64, 192, 512];

async function generateIcons() {
  for (const size of sizes) {
    const svg = Buffer.from(createIconSvg(size));
    await sharp(svg)
      .resize(size, size)
      .png()
      .toFile(join(publicDir, `pwa-${size}x${size}.png`));
    console.log(`Generated pwa-${size}x${size}.png`);
  }

  // Generate maskable icon
  const maskableSvg = Buffer.from(createMaskableIconSvg(512));
  await sharp(maskableSvg)
    .resize(512, 512)
    .png()
    .toFile(join(publicDir, 'maskable-icon-512x512.png'));
  console.log('Generated maskable-icon-512x512.png');

  // Generate apple-touch-icon (180x180)
  const appleSvg = Buffer.from(createIconSvg(180));
  await sharp(appleSvg)
    .resize(180, 180)
    .png()
    .toFile(join(publicDir, 'apple-touch-icon.png'));
  console.log('Generated apple-touch-icon.png');

  // Generate favicon.ico (use 32x32 as base)
  const faviconSvg = Buffer.from(createIconSvg(32));
  await sharp(faviconSvg)
    .resize(32, 32)
    .png()
    .toFile(join(publicDir, 'favicon.png'));
  console.log('Generated favicon.png');

  console.log('All icons generated successfully!');
}

generateIcons().catch(console.error);

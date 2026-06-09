/**
 * PWA 图标生成脚本
 * 从 SVG 源文件生成不同尺寸的 PNG 图标
 *
 * 运行: npx ts-node scripts/generate-icons.ts
 *
 * 注意：此脚本仅用于开发阶段图标生成。
 * 生产环境建议使用专业设计工具制作高质量图标。
 */

import { createCanvas, loadImage } from 'canvas'
import * as fs from 'fs'
import * as path from 'path'

const ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
const SVG_PATH = path.resolve(__dirname, '../public/favicon.svg')
const OUTPUT_DIR = path.resolve(__dirname, '../public/icons')

async function generateIcons(): Promise<void> {
  // 确保输出目录存在
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true })
  }

  // 读取 SVG
  if (!fs.existsSync(SVG_PATH)) {
    console.error(`SVG file not found: ${SVG_PATH}`)
    console.log('Creating a simple placeholder icon instead...')
    generatePlaceholderIcons()
    return
  }

  try {
    const svgBuffer = fs.readFileSync(SVG_PATH)
    const image = await loadImage(svgBuffer)

    for (const size of ICON_SIZES) {
      const canvas = createCanvas(size, size)
      const ctx = canvas.getContext('2d')
      ctx.drawImage(image, 0, 0, size, size)

      const outputPath = path.join(OUTPUT_DIR, `icon-${size}x${size}.png`)
      const buffer = canvas.toBuffer('image/png')
      fs.writeFileSync(outputPath, buffer)
      console.log(`Generated: ${outputPath}`)
    }

    console.log('All icons generated successfully!')
  } catch {
    console.log('Canvas library not available, generating placeholder icons...')
    generatePlaceholderIcons()
  }
}

/**
 * 生成纯色占位图标（无依赖）
 */
function generatePlaceholderIcons(): void {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true })
  }

  // 生成最小的有效 PNG 占位符
  // 实际项目中请替换为正式设计图标
  const MINIMAL_PNG = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
    'base64'
  )

  for (const size of ICON_SIZES) {
    const outputPath = path.join(OUTPUT_DIR, `icon-${size}x${size}.png`)
    fs.writeFileSync(outputPath, MINIMAL_PNG)
    console.log(`Generated placeholder: ${outputPath}`)
  }

  console.log('Placeholder icons generated. Replace with production icons before deploy!')
}

generateIcons().catch(console.error)

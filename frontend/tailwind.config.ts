import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 场景主题色
        'scene-classroom': '#1976D2',
        'scene-self-study': '#388E3C',
        'scene-exam': '#F57C00',
        'scene-discussion': '#7B1FA2',
        // 品牌色
        primary: '#1976D2',
        'primary-light': '#42A5F5',
        'primary-dark': '#1565C0',
      },
      fontFamily: {
        sans: ['Inter', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  // 与 Element Plus 兼容
  corePlugins: {
    preflight: false,
  },
  plugins: [],
}

export default config

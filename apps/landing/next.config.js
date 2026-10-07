/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**.githubusercontent.com' },
      { protocol: 'https', hostname: '**.github.com' }
    ]
  },
  experimental: {
    serverActions: true
  }
}
module.exports = nextConfig

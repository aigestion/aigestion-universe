import { NextRequest, NextResponse } from 'next/server'
import QRCode from 'qrcode'

export async function GET(request: NextRequest) {
  const url = process.env.APK_URL || 'https://aigestion.net/download/daniela.apk'
  const svg = await QRCode.toDataURL(url, { width: 300, margin: 1 })
  return NextResponse.json({ url, qr: svg })
}

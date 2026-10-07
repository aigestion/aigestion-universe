import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const apkUrl = process.env.APK_URL || 'https://github.com/aigestion/daniela-android/releases/latest/download/daniela.apk'
  return NextResponse.redirect(apkUrl, 302)
}

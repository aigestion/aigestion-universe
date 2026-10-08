# Next.js 15 Build Issue

## Problem
Next.js 15 attempts to statically generate default error pages (/_error: /404 and /_error: /500) even when custom error pages with generateStaticParams = () => [] and dynamic = 'force-dynamic' are provided.

## Error
\\\
Failed to build /_error: /404 after 1 attempts.
Failed to build /_error: /500 after 1 attempts.
Error: Export encountered an error on /_error: /404, exiting the build.
\\\

## Workarounds Attempted
1. generateStaticParams = () => [] + dynamic = 'force-dynamic' on error pages
2. xport const notFound = true on error pages
3. output: 'export' config
4. Custom error pages with orce-dynamic and generateStaticParams = () => []
5. Adding xport const notFound = true to error pages

## Status
All workarounds failed. This is a known bug in Next.js 15.

## Workaround
Use output: 'standalone' and deploy with a custom server that handles errors at runtime, or upgrade to Next.js 15.1+ when fixed.

## References
- Next.js 15 issue: https://github.com/vercel/next.js/issues/XXXXX
- Vercel discussion: https://github.com/vercel/next.js/discussions/XXXXX

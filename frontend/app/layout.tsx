import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'lands.ai',
  description: 'Kenya Land Search & Property Legal AI Agent',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

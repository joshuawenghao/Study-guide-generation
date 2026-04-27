import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Study Guide Generator',
  description: 'Generate comprehensive study guides powered by Gemini AI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">Study Guide Generator</h1>
            <span className="text-sm text-gray-500">Powered by Gemini 2.0</span>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">{children}</main>
      </body>
    </html>
  )
}

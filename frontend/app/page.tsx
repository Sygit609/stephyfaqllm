/**
 * Main Chat Page - OIL Q&A Search Tool
 */

import { SearchInterface } from "@/components/search/SearchInterface"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            OIL Q&A Search
          </h1>
          <p className="text-gray-600">
            AI-powered search for Online Income Lab community questions
          </p>
        </header>

        {/* Main Search Interface */}
        <SearchInterface />
      </div>
    </main>
  )
}

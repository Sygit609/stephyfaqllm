"use client"

/**
 * Web Results Tab Component
 * Displays web search results from Tavily API
 */

import { ExternalLink, Globe } from "lucide-react"

interface WebResult {
  title: string
  url: string
  content: string
  score: number
}

interface WebResultsTabProps {
  results: WebResult[] | undefined
}

export function WebResultsTab({ results }: WebResultsTabProps) {
  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Globe className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No web search results available.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {results.map((result, idx) => (
        <div key={idx} className="border rounded-lg p-4 bg-green-50 hover:shadow-md transition-shadow">
          {/* Header with badge and link */}
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-green-600 text-white text-xs font-bold rounded">
                {idx + 1}
              </span>
              <span className="text-sm text-gray-600">
                {Math.round(result.score * 100)}% relevance
              </span>
            </div>
          </div>

          {/* Title with link */}
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:text-blue-800 hover:underline mb-2 block flex items-center gap-2"
          >
            {result.title}
            <ExternalLink className="w-4 h-4" />
          </a>

          {/* Content snippet */}
          <div className="text-gray-700 text-sm leading-relaxed mb-3">
            {result.content}
          </div>

          {/* URL footer */}
          <div className="flex items-center gap-2 text-xs text-gray-500 border-t pt-2">
            <Globe className="w-3 h-3" />
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline truncate"
            >
              {result.url}
            </a>
          </div>
        </div>
      ))}
    </div>
  )
}

"use client"

/**
 * Facebook Posts Tab Component
 * Displays Facebook community Q&A sources with thread links
 */

import { ExternalLink, MessageCircle } from "lucide-react"
import type { SourceMatch } from "@/lib/api/types"

interface FacebookSourcesTabProps {
  sources: SourceMatch[]
}

export function FacebookSourcesTab({ sources }: FacebookSourcesTabProps) {
  if (sources.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No Facebook community sources found for this query.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sources.map((source, idx) => (
        <div key={source.id} className="border rounded-lg p-4 bg-blue-50 hover:shadow-md transition-shadow">
          {/* Header with badge and thread link */}
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded">
                {idx + 1}
              </span>
              <span className="text-sm text-gray-600">
                {source.match_type} • {Math.round(source.score * 100)}% match
              </span>
            </div>

            {/* Facebook thread link */}
            {source.source_url && (
              <a
                href={source.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1.5 text-sm font-medium"
              >
                <MessageCircle className="w-4 h-4" />
                View Thread
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          {/* Question */}
          <div className="font-medium text-gray-900 mb-2">
            {source.question}
          </div>

          {/* Answer */}
          <div className="text-gray-700 text-sm leading-relaxed mb-3">
            {source.answer}
          </div>

          {/* Tags and metadata footer */}
          <div className="flex items-center justify-between flex-wrap gap-2 border-t pt-2">
            {/* Tags */}
            {source.tags && source.tags.length > 0 && (
              <div className="flex gap-2 flex-wrap">
                {source.tags.slice(0, 3).map((tag, tagIdx) => (
                  <span
                    key={tagIdx}
                    className="px-2 py-1 bg-blue-200 text-blue-800 rounded text-xs font-medium"
                  >
                    {tag}
                  </span>
                ))}
                {source.tags.length > 3 && (
                  <span className="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                    +{source.tags.length - 3} more
                  </span>
                )}
              </div>
            )}

            {/* Date */}
            {source.date && (
              <div className="text-xs text-gray-500">
                Posted: {new Date(source.date).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

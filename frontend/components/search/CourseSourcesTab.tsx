"use client"

/**
 * Course Transcripts Tab Component
 * Displays video transcript sources with timestamp links
 */

import { ExternalLink, Video } from "lucide-react"
import type { SourceMatch } from "@/lib/api/types"

interface CourseSourcesTabProps {
  sources: SourceMatch[]
}

export function CourseSourcesTab({ sources }: CourseSourcesTabProps) {
  const formatTimestamp = (seconds: number | null | undefined): string => {
    if (seconds == null) return "0:00"
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (sources.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Video className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No course transcript sources found for this query.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sources.map((source, idx) => (
        <div key={source.id} className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow">
          {/* Header with badge and video link */}
          <div className="flex justify-between items-start mb-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded">
                {idx + 1}
              </span>
              <span className="text-sm text-gray-600">
                {source.match_type} • {Math.round(source.score * 100)}% match
              </span>
            </div>

            {/* View Source link - Opens in new tab */}
            {source.media_url && source.timecode_start != null && (
              <a
                href={source.media_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1.5 text-sm font-medium"
              >
                <Video className="w-4 h-4" />
                View Source at {formatTimestamp(source.timecode_start)}
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          {/* Question */}
          <div className="font-medium text-gray-900 mb-2">
            {source.question}
          </div>

          {/* Answer/Transcript snippet */}
          <div className="text-gray-700 text-sm leading-relaxed mb-3">
            {source.answer}
          </div>

          {/* Metadata footer */}
          <div className="flex items-center gap-4 text-xs text-gray-500 border-t pt-2">
            {source.timecode_start != null && source.timecode_end != null && (
              <span className="flex items-center gap-1">
                <Video className="w-3 h-3" />
                Timestamp: {formatTimestamp(source.timecode_start)} - {formatTimestamp(source.timecode_end)}
              </span>
            )}
            {source.category && (
              <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-700">
                {source.category}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

"use client"

/**
 * Course Transcripts Tab Component
 * Groups transcript segments by lesson and displays with expand/collapse
 */

import { useState } from "react"
import { ExternalLink, Video, ChevronDown, ChevronRight } from "lucide-react"
import type { SourceMatch } from "@/lib/api/types"

interface CourseSourcesTabProps {
  sources: SourceMatch[]
}

interface LessonGroup {
  lessonId: string
  lessonName: string
  segments: SourceMatch[]
  topScore: number
  allTags: string[]
  mediaUrl: string | null
}

export function CourseSourcesTab({ sources }: CourseSourcesTabProps) {
  const [expandedLessons, setExpandedLessons] = useState<Set<string>>(new Set())

  const formatTimestamp = (seconds: number | null | undefined): string => {
    if (seconds == null) return "0:00"
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Extract lesson name from question (e.g., "Transcript from March 12th - [Mo Smead] All About DM Automation at 5:30")
  const extractLessonName = (question: string): string => {
    // Remove "Transcript from " prefix and timestamp suffix
    let name = question.replace(/^Transcript from /, "")
    name = name.replace(/ at \d+:\d+$/, "")
    return name || question
  }

  // Group sources by lesson_id
  const groupedByLesson = sources.reduce<Record<string, LessonGroup>>((acc, source) => {
    const lessonId = source.lesson_id || source.id // Fallback to source id if no lesson_id

    if (!acc[lessonId]) {
      acc[lessonId] = {
        lessonId,
        lessonName: extractLessonName(source.question),
        segments: [],
        topScore: source.score,
        allTags: [],
        mediaUrl: source.media_url || null
      }
    }

    acc[lessonId].segments.push(source)

    // Track highest score
    if (source.score > acc[lessonId].topScore) {
      acc[lessonId].topScore = source.score
    }

    // Collect unique tags
    if (source.tags) {
      source.tags.forEach(tag => {
        if (!acc[lessonId].allTags.includes(tag)) {
          acc[lessonId].allTags.push(tag)
        }
      })
    }

    return acc
  }, {})

  // Convert to array and sort by top score
  const lessonGroups = Object.values(groupedByLesson).sort((a, b) => b.topScore - a.topScore)

  const toggleLesson = (lessonId: string) => {
    setExpandedLessons(prev => {
      const next = new Set(prev)
      if (next.has(lessonId)) {
        next.delete(lessonId)
      } else {
        next.add(lessonId)
      }
      return next
    })
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
    <div className="space-y-3">
      {lessonGroups.map((group, idx) => {
        const isExpanded = expandedLessons.has(group.lessonId)
        const segmentCount = group.segments.length

        return (
          <div key={group.lessonId} className="border rounded-lg bg-white overflow-hidden">
            {/* Collapsed Header - Always visible */}
            <div
              className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => toggleLesson(group.lessonId)}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-start gap-3 flex-1">
                  {/* Expand/Collapse Icon */}
                  <div className="mt-0.5">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-500" />
                    )}
                  </div>

                  {/* Rank Badge */}
                  <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded flex-shrink-0">
                    {idx + 1}
                  </span>

                  {/* Lesson Info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 mb-1">
                      {group.lessonName}
                    </div>

                    <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                      <span>{segmentCount} matching segment{segmentCount !== 1 ? 's' : ''}</span>
                      <span>•</span>
                      <span>{Math.round(group.topScore * 100)}% best match</span>
                    </div>

                    {/* Tags Summary */}
                    {group.allTags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {group.allTags.slice(0, 6).map((tag, tagIdx) => (
                          <span
                            key={tagIdx}
                            className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                        {group.allTags.length > 6 && (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
                            +{group.allTags.length - 6} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* View Video Link */}
                {group.mediaUrl && (
                  <a
                    href={group.mediaUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1.5 text-sm font-medium flex-shrink-0 ml-4"
                  >
                    <Video className="w-4 h-4" />
                    Watch
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Expanded Content - Individual Segments */}
            {isExpanded && (
              <div className="border-t bg-gray-50">
                <div className="p-4 space-y-3">
                  {group.segments
                    .sort((a, b) => b.score - a.score)
                    .map((source, segIdx) => (
                    <div key={source.id} className="bg-white border rounded-lg p-3">
                      {/* Segment Header */}
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center justify-center w-5 h-5 bg-gray-200 text-gray-700 text-xs font-medium rounded">
                            {segIdx + 1}
                          </span>
                          <span className="text-xs text-gray-500">
                            {source.match_type} • {Math.round(source.score * 100)}% match
                          </span>
                        </div>

                        {source.media_url && source.timecode_start != null && (
                          <a
                            href={source.media_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1 text-xs font-medium"
                          >
                            <Video className="w-3 h-3" />
                            {formatTimestamp(source.timecode_start)}
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </div>

                      {/* Transcript Content */}
                      <div className="text-gray-700 text-sm leading-relaxed">
                        {source.answer}
                      </div>

                      {/* Segment Tags */}
                      {source.tags && source.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {source.tags.slice(0, 4).map((tag, tagIdx) => (
                            <span
                              key={tagIdx}
                              className="px-1.5 py-0.5 bg-purple-50 text-purple-600 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

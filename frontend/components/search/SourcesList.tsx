"use client"

/**
 * Sources List Component with Tabs
 * Separates Course Transcripts, Facebook Posts, and Web Results into tabs
 */

import { useState } from "react"
import { Video, MessageCircle, Globe } from "lucide-react"
import type { SourceMatch, WebResult } from "@/lib/api/types"
import { CourseSourcesTab } from "./CourseSourcesTab"
import { FacebookSourcesTab } from "./FacebookSourcesTab"
import { WebResultsTab } from "./WebResultsTab"

interface SourcesListProps {
  sources: SourceMatch[]
  webResults?: WebResult[] | null
}

type TabType = "course" | "facebook" | "web"

export function SourcesList({ sources, webResults }: SourcesListProps) {
  // Default to Course Transcripts tab
  const [activeTab, setActiveTab] = useState<TabType>("course")

  // Deduplicate sources by content hash (question + answer + timecode)
  // This handles cases where the DB has duplicate content with different IDs
  const uniqueSources = sources.filter((source, index, self) => {
    const contentKey = (s: SourceMatch) => {
      // For video/course content, use question + timecode as unique key
      if (s.timecode_start !== undefined && s.timecode_start !== null) {
        return `${s.question}|${s.timecode_start}|${s.timecode_end || ''}`
      }
      // For non-video content, use question + answer as unique key
      return `${s.question}|${s.answer}`
    }

    return index === self.findIndex((s) => contentKey(s) === contentKey(source))
  })

  // Categorize sources by type
  // Course sources: video or manual content with course_id
  const courseSources = uniqueSources.filter(
    (s) => s.content_type === "video" || s.content_type === "manual" || s.course_id != null
  )

  // Facebook sources: explicitly facebook content, OR content without course association
  const facebookSources = uniqueSources.filter(
    (s) => s.content_type === "facebook" || (s.course_id == null && s.content_type !== "video" && s.content_type !== "manual")
  )

  const webResultsArray = webResults || []

  // Determine which tabs have content
  const hasCourse = courseSources.length > 0
  const hasFacebook = facebookSources.length > 0
  const hasWeb = webResultsArray.length > 0

  // Auto-select first available tab with content
  // This ensures we don't show an empty tab by default
  const effectiveActiveTab =
    activeTab === "course" && !hasCourse
      ? hasFacebook
        ? "facebook"
        : hasWeb
        ? "web"
        : "course"
      : activeTab === "facebook" && !hasFacebook
      ? hasCourse
        ? "course"
        : hasWeb
        ? "web"
        : "facebook"
      : activeTab === "web" && !hasWeb
      ? hasCourse
        ? "course"
        : hasFacebook
        ? "facebook"
        : "web"
      : activeTab

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Tab Header */}
      <div className="border-b border-gray-200 bg-gray-50">
        <div className="flex">
          {/* Course Transcripts Tab */}
          <button
            onClick={() => setActiveTab("course")}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
              effectiveActiveTab === "course"
                ? "bg-white text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            <Video className="w-4 h-4" />
            Course Transcripts ({courseSources.length})
          </button>

          {/* Facebook Posts Tab */}
          <button
            onClick={() => setActiveTab("facebook")}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
              effectiveActiveTab === "facebook"
                ? "bg-white text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            <MessageCircle className="w-4 h-4" />
            Facebook Posts ({facebookSources.length})
          </button>

          {/* Web Results Tab */}
          <button
            onClick={() => setActiveTab("web")}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
              effectiveActiveTab === "web"
                ? "bg-white text-green-600 border-b-2 border-green-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            <Globe className="w-4 h-4" />
            Web Results ({webResultsArray.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {effectiveActiveTab === "course" && <CourseSourcesTab sources={courseSources} />}
        {effectiveActiveTab === "facebook" && <FacebookSourcesTab sources={facebookSources} />}
        {effectiveActiveTab === "web" && <WebResultsTab results={webResultsArray} />}
      </div>
    </div>
  )
}

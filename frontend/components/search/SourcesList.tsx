"use client"

/**
 * Sources List Component with Tabs
 * Separates Course Transcripts, Facebook Posts, and Web Results into tabs
 */

import { useState } from "react"
import { Video, MessageCircle, Globe, Mic } from "lucide-react"
import type { SourceMatch, WebResult } from "@/lib/api/types"
import { CourseSourcesTab } from "./CourseSourcesTab"
import { FacebookSourcesTab } from "./FacebookSourcesTab"
import { WebResultsTab } from "./WebResultsTab"

interface SourcesListProps {
  sources: SourceMatch[]
  webResults?: WebResult[] | null
}

type TabType = "course" | "coaching" | "facebook" | "web"

// Course IDs for categorization
const ONLINE_INCOME_LAB_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"
const COACHING_CALL_REPLAYS_ID = "a75dc54a-da4b-4229-8699-8a46b2132ef7"

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
  // Split course content into main courses vs coaching
  const mainCourseSources = uniqueSources.filter(
    (s) => s.course_id === ONLINE_INCOME_LAB_ID ||
           (s.course_id != null && s.course_id !== COACHING_CALL_REPLAYS_ID &&
            (s.content_type === "video" || s.content_type === "manual"))
  )

  const coachingSources = uniqueSources.filter(
    (s) => s.course_id === COACHING_CALL_REPLAYS_ID
  )

  // Facebook sources: explicitly facebook content, OR content without course association
  const facebookSources = uniqueSources.filter(
    (s) => s.content_type === "facebook" || (s.course_id == null && s.content_type !== "video" && s.content_type !== "manual")
  )

  const webResultsArray = webResults || []

  // Determine which tabs have content
  const hasMainCourse = mainCourseSources.length > 0
  const hasCoaching = coachingSources.length > 0
  const hasFacebook = facebookSources.length > 0
  const hasWeb = webResultsArray.length > 0

  // Auto-select first available tab with content
  // This ensures we don't show an empty tab by default
  const effectiveActiveTab = (() => {
    if (activeTab === "course" && !hasMainCourse) {
      if (hasCoaching) return "coaching"
      if (hasFacebook) return "facebook"
      if (hasWeb) return "web"
    }
    if (activeTab === "coaching" && !hasCoaching) {
      if (hasMainCourse) return "course"
      if (hasFacebook) return "facebook"
      if (hasWeb) return "web"
    }
    if (activeTab === "facebook" && !hasFacebook) {
      if (hasMainCourse) return "course"
      if (hasCoaching) return "coaching"
      if (hasWeb) return "web"
    }
    if (activeTab === "web" && !hasWeb) {
      if (hasMainCourse) return "course"
      if (hasCoaching) return "coaching"
      if (hasFacebook) return "facebook"
    }
    return activeTab
  })()

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Tab Header */}
      <div className="border-b border-gray-200 bg-gray-50">
        <div className="flex">
          {/* Course Tab */}
          <button
            onClick={() => setActiveTab("course")}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
              effectiveActiveTab === "course"
                ? "bg-white text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            <Video className="w-4 h-4" />
            Course ({mainCourseSources.length})
          </button>

          {/* Coaching Tab */}
          <button
            onClick={() => setActiveTab("coaching")}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
              effectiveActiveTab === "coaching"
                ? "bg-white text-purple-600 border-b-2 border-purple-600"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            }`}
          >
            <Mic className="w-4 h-4" />
            Coaching ({coachingSources.length})
          </button>

          {/* Facebook Posts Tab */}
          <button
            onClick={() => setActiveTab("facebook")}
            className={`flex-1 px-6 py-3 font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
              effectiveActiveTab === "facebook"
                ? "bg-white text-green-600 border-b-2 border-green-600"
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
                ? "bg-white text-orange-600 border-b-2 border-orange-600"
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
        {effectiveActiveTab === "course" && <CourseSourcesTab sources={mainCourseSources} />}
        {effectiveActiveTab === "coaching" && <CourseSourcesTab sources={coachingSources} />}
        {effectiveActiveTab === "facebook" && <FacebookSourcesTab sources={facebookSources} />}
        {effectiveActiveTab === "web" && <WebResultsTab results={webResultsArray} />}
      </div>
    </div>
  )
}

"use client"

/**
 * Course Detail Page
 * Shows nested folder tree (Course → Modules → Lessons → Segments)
 */

import { useState, useEffect } from "react"
import Link from "next/link"
import { getCourseTree } from "@/lib/api/courses"
import type { CourseTreeNode } from "@/lib/api/types"
import GoogleDocsTabsView from "@/components/courses/GoogleDocsTabsView"

export default function CourseDetailPage({ params }: { params: Promise<{ courseId: string }> }) {
  const [courseTree, setCourseTree] = useState<CourseTreeNode | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [isCreatingCourse, setIsCreatingCourse] = useState(false)
  const [courseId, setCourseId] = useState<string>("")

  useEffect(() => {
    params.then(p => {
      setCourseId(p.courseId)
      loadCourseTree(p.courseId)
    })
  }, [params])

  const loadCourseTree = async (id: string) => {
    setIsLoading(true)
    setError(null)

    try {
      const tree = await getCourseTree(id)
      setCourseTree(tree)
      // Auto-expand the course node
      setExpandedNodes(new Set([tree.id]))
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to load course")
    } finally {
      setIsLoading(false)
    }
  }

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }

  const handleCreateNewModule = async () => {
    setIsCreatingCourse(true)
    try {
      if (!courseTree || !courseId) return

      // Count existing direct children (modules) of the current course
      const moduleCount = courseTree.children.filter(c => c.type === 'module').length
      const newName = `Module ${moduleCount + 1}`

      // Import createSubfolder
      const { createSubfolder } = await import("@/lib/api/courses")

      await createSubfolder(courseId, {
        name: newName,
        description: "",
        thumbnail_url: null
      })

      // Refresh the tree
      loadCourseTree(courseId)
    } catch (err: any) {
      alert(err.message || "Failed to create module")
    } finally {
      setIsCreatingCourse(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link
              href="/admin/courses"
              className="text-purple-600 hover:text-purple-700 font-medium"
            >
              ← Back to Courses
            </Link>
          </div>

          {courseTree && (
            <>
              <h1 className="text-3xl font-bold text-gray-900">{courseTree.name}</h1>
              <p className="text-gray-600 mt-2">{courseTree.description}</p>
            </>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg
              className="animate-spin h-12 w-12 text-purple-600 mx-auto mb-4"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-gray-600">Loading course...</p>
          </div>
        )}

        {/* Course Tree - Google Docs Style */}
        {!isLoading && courseTree && (
          <GoogleDocsTabsView
            tree={courseTree}
            onRefresh={() => loadCourseTree(courseId)}
            onCreateModule={handleCreateNewModule}
          />
        )}
      </div>
    </div>
  )
}

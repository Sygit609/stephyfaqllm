"use client"

/**
 * Course Grid Page
 * Displays all courses in a grid layout with thumbnails
 */

import { useState, useEffect } from "react"
import Link from "next/link"
import type { Course } from "@/lib/api/types"
import { listCourses, deleteFolder, cloneCourse } from "@/lib/api/courses"
import CourseCard from "@/components/courses/CourseCard"
import CreateCourseModal from "@/components/courses/CreateCourseModal"
import CloneCourseModal from "@/components/courses/CloneCourseModal"
import DeleteConfirmModal from "@/components/admin/DeleteConfirmModal"

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal state
  const [creatingCourse, setCreatingCourse] = useState(false)
  const [cloningCourse, setCloningCourse] = useState<Course | null>(null)
  const [deletingCourse, setDeletingCourse] = useState<Course | null>(null)

  // Load courses
  const loadCourses = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await listCourses()
      setCourses(response.courses)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to load courses")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadCourses()
  }, [])

  // Handlers
  const handleView = (course: Course) => {
    window.location.href = `/admin/courses/${course.id}`
  }

  const handleClone = (course: Course) => {
    setCloningCourse(course)
  }

  const handleDelete = (course: Course) => {
    setDeletingCourse(course)
  }

  const handleConfirmDelete = async () => {
    if (!deletingCourse) return

    try {
      await deleteFolder(deletingCourse.id)
      setDeletingCourse(null)
      loadCourses() // Refresh list
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to delete course")
    }
  }

  const handleConfirmClone = async (newName: string, regenerateEmbeddings: boolean) => {
    if (!cloningCourse) return

    try {
      await cloneCourse(cloningCourse.id, {
        new_name: newName,
        regenerate_embeddings: regenerateEmbeddings
      })
      setCloningCourse(null)
      loadCourses() // Refresh list
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to clone course")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link
              href="/"
              className="text-purple-600 hover:text-purple-700 font-medium"
            >
              ← Back to Search
            </Link>
            <div className="flex gap-3">
              <Link
                href="/admin/content"
                className="px-4 py-2 border-2 border-purple-600 text-purple-600 hover:bg-purple-50 rounded-lg font-medium transition-colors"
              >
                Manage Content
              </Link>
              <button
                onClick={() => setCreatingCourse(true)}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
              >
                + New Course
              </button>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Course Transcripts</h1>
          <p className="text-gray-600 mt-2">
            Manage video course transcripts and enable timestamp-based answers
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right text-red-700 hover:text-red-900 font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* Loading State */}
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
            <p className="text-gray-600">Loading courses...</p>
          </div>
        )}

        {/* Courses Grid */}
        {!isLoading && courses.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {courses.map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                onView={handleView}
                onClone={handleClone}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && courses.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg
              className="mx-auto h-16 w-16 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
              />
            </svg>
            <p className="text-gray-600 text-lg font-semibold mb-2">
              No courses yet
            </p>
            <p className="text-gray-500 text-sm mb-4">
              Create your first course to start organizing video transcripts
            </p>
            <button
              onClick={() => setCreatingCourse(true)}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              Create First Course
            </button>
          </div>
        )}
      </div>

      {/* Modals */}
      {creatingCourse && (
        <CreateCourseModal
          onClose={() => setCreatingCourse(false)}
          onSuccess={() => {
            setCreatingCourse(false)
            loadCourses()
          }}
        />
      )}

      {cloningCourse && (
        <CloneCourseModal
          course={cloningCourse}
          onClose={() => setCloningCourse(null)}
          onConfirm={handleConfirmClone}
        />
      )}

      {deletingCourse && (
        <DeleteConfirmModal
          item={{
            id: deletingCourse.id,
            content_type: "course",
            question: deletingCourse.name,
            answer: deletingCourse.description,
            created_at: deletingCourse.created_at,
            updated_at: deletingCourse.updated_at,
            source_url: null,
            media_url: null,
            tags: null,
            extracted_by: null,
            extraction_confidence: null,
            parent_id: null
          }}
          onClose={() => setDeletingCourse(null)}
          onConfirm={handleConfirmDelete}
          childrenCount={deletingCourse.module_count + deletingCourse.lesson_count + deletingCourse.segment_count}
        />
      )}
    </div>
  )
}

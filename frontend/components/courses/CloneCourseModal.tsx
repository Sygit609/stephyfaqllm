"use client"

/**
 * Clone Course Modal
 * Allows cloning a course with optional embedding regeneration
 */

import { useState } from "react"
import type { Course } from "@/lib/api/types"

interface Props {
  course: Course
  onClose: () => void
  onConfirm: (newName: string, regenerateEmbeddings: boolean) => Promise<void>
}

export default function CloneCourseModal({ course, onClose, onConfirm }: Props) {
  const [newName, setNewName] = useState(`${course.name} (Copy)`)
  const [regenerateEmbeddings, setRegenerateEmbeddings] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Calculate estimated cost
  const embeddingCostPerSegment = 0.0002 // Rough estimate
  const estimatedCost = regenerateEmbeddings
    ? (course.segment_count * embeddingCostPerSegment).toFixed(2)
    : "0.00"

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await onConfirm(newName, regenerateEmbeddings)
    } catch (err) {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Clone Course</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isSubmitting}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Original Course */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <p className="text-sm font-semibold text-gray-700 mb-1">Cloning:</p>
            <p className="text-gray-900 font-medium">{course.name}</p>
            <div className="grid grid-cols-3 gap-2 mt-2 text-xs text-gray-600">
              <div>{course.module_count} modules</div>
              <div>{course.lesson_count} lessons</div>
              <div>{course.segment_count} segments</div>
            </div>
          </div>

          {/* New Name */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              New Course Name <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          {/* Regenerate Embeddings */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={regenerateEmbeddings}
                onChange={(e) => setRegenerateEmbeddings(e.target.checked)}
                className="mt-1"
              />
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900 mb-1">
                  Regenerate embeddings
                </p>
                <p className="text-xs text-gray-600">
                  Generate fresh embeddings for all segments. This is slower and costs more,
                  but ensures the latest embedding model is used.
                </p>
                <p className="text-xs text-gray-900 font-semibold mt-2">
                  Estimated cost: ${estimatedCost}
                  {regenerateEmbeddings && course.segment_count > 0 && (
                    <span className="text-gray-600 font-normal">
                      {" "}({course.segment_count} segments)
                    </span>
                  )}
                </p>
              </div>
            </label>
          </div>

          {/* Info */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <p className="text-xs text-gray-600">
              <strong>Note:</strong> Cloning creates a complete copy of the course structure,
              including all modules, lessons, and transcript segments.
              {!regenerateEmbeddings && " Embeddings will be copied from the original."}
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border-2 border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg font-medium transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Cloning..." : "Clone Course"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

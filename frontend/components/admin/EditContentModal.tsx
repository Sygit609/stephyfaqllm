"use client"

/**
 * Edit Content Modal
 * Allows editing question, answer, tags, and source_url
 */

import { useState } from "react"
import type { ContentItem } from "@/lib/api/types"

interface Props {
  item: ContentItem
  onClose: () => void
  onSave: (updatedItem: ContentItem) => Promise<void>
}

export default function EditContentModal({ item, onClose, onSave }: Props) {
  const [question, setQuestion] = useState(item.question)
  const [answer, setAnswer] = useState(item.answer)
  const [tags, setTags] = useState(item.tags || "")
  const [sourceUrl, setSourceUrl] = useState(item.source_url || "")
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    // Validation
    if (!question.trim()) {
      setError("Question is required")
      return
    }
    if (!answer.trim()) {
      setError("Answer is required")
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      const updatedItem: ContentItem = {
        ...item,
        question: question.trim(),
        answer: answer.trim(),
        tags: tags.trim(),
        source_url: sourceUrl.trim() || null,
        updated_at: new Date().toISOString()
      }

      await onSave(updatedItem)
      onClose()
    } catch (err: any) {
      setError(err.message || "Failed to save changes")
    } finally {
      setIsSaving(false)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isSaving) {
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            {/* Header */}
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-gray-900 mb-1">
                Edit Content
              </h3>
              <p className="text-sm text-gray-600">
                ID: {item.id.slice(0, 8)}... • {item.content_type} •{" "}
                {item.extracted_by || "manual"}
              </p>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
                {error}
              </div>
            )}

            {/* Form */}
            <div className="space-y-4">
              {/* Question */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Question <span className="text-red-600">*</span>
                </label>
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  placeholder="Enter the question..."
                  disabled={isSaving}
                />
              </div>

              {/* Answer */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Answer <span className="text-red-600">*</span>
                </label>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={8}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  placeholder="Enter the answer..."
                  disabled={isSaving}
                />
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Tags
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  placeholder="instagram, follow_block, troubleshooting"
                  disabled={isSaving}
                />
                <p className="text-xs text-gray-600 mt-1">
                  Comma-separated tags for better searchability
                </p>
              </div>

              {/* Source URL */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Source URL
                </label>
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-colors"
                  placeholder="https://facebook.com/groups/oil/posts/..."
                  disabled={isSaving}
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={onClose}
                disabled={isSaving}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving || !question.trim() || !answer.trim()}
                className="px-8 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isSaving ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

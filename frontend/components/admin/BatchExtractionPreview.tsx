"use client"

/**
 * Batch Extraction Preview Component
 * Shows extracted Q&As grouped by screenshot in accordion layout
 */

import { useState } from "react"
import type { BatchUpload } from "@/lib/api/types"

interface Props {
  uploads: BatchUpload[]
  onCancel: () => void
  onSave: (uploads: BatchUpload[]) => Promise<void>
}

export default function BatchExtractionPreview({ uploads, onCancel, onSave }: Props) {
  const [editedUploads, setEditedUploads] = useState<BatchUpload[]>(uploads)
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [isSaving, setIsSaving] = useState(false)

  const successfulUploads = editedUploads.filter(u => u.status === 'success')
  const totalQAPairs = successfulUploads.reduce(
    (sum, u) => sum + (u.extractionResult?.qa_pairs.length || 0),
    0
  )

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const expandAll = () => {
    setExpandedIds(new Set(successfulUploads.map(u => u.id)))
  }

  const collapseAll = () => {
    setExpandedIds(new Set())
  }

  const updateQAPair = (uploadId: string, qaIndex: number, field: string, value: any) => {
    setEditedUploads(prev =>
      prev.map(upload => {
        if (upload.id === uploadId && upload.extractionResult) {
          const updatedQAPairs = [...upload.extractionResult.qa_pairs]
          updatedQAPairs[qaIndex] = {
            ...updatedQAPairs[qaIndex],
            [field]: value
          }
          return {
            ...upload,
            extractionResult: {
              ...upload.extractionResult,
              qa_pairs: updatedQAPairs
            }
          }
        }
        return upload
      })
    )
  }

  const deleteQAPair = (uploadId: string, qaIndex: number) => {
    setEditedUploads(prev =>
      prev.map(upload => {
        if (upload.id === uploadId && upload.extractionResult) {
          const updatedQAPairs = upload.extractionResult.qa_pairs.filter((_, i) => i !== qaIndex)
          return {
            ...upload,
            extractionResult: {
              ...upload.extractionResult,
              qa_pairs: updatedQAPairs
            }
          }
        }
        return upload
      })
    )
  }

  const deleteScreenshot = (uploadId: string) => {
    setEditedUploads(prev => prev.filter(u => u.id !== uploadId))
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(editedUploads.filter(u => u.status === 'success'))
    } finally {
      setIsSaving(false)
    }
  }

  const getConfidenceBadge = (confidence: number) => {
    const percentage = Math.round(confidence * 100)
    let colorClass = 'bg-green-100 text-green-700'
    if (confidence < 0.7) colorClass = 'bg-yellow-100 text-yellow-700'
    if (confidence < 0.5) colorClass = 'bg-red-100 text-red-700'

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
        {percentage}% confidence
      </span>
    )
  }

  if (successfulUploads.length === 0) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
        <h3 className="text-lg font-semibold text-red-900 mb-2">No Successful Extractions</h3>
        <p className="text-red-700 mb-4">
          All screenshot extractions failed. Please check the error messages and try again.
        </p>
        <button
          onClick={onCancel}
          className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors"
        >
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Review Extracted Content</h2>
          <p className="text-gray-600 mt-1">
            {successfulUploads.length} screenshot{successfulUploads.length !== 1 ? 's' : ''} • {totalQAPairs} Q&A pair{totalQAPairs !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={expandAll}
            className="px-3 py-1.5 text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1.5 text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Accordion */}
      <div className="space-y-3">
        {successfulUploads.map((upload) => {
          const isExpanded = expandedIds.has(upload.id)
          const result = upload.extractionResult!
          const qaPairCount = result.qa_pairs.length

          return (
            <div
              key={upload.id}
              className="border-2 border-gray-200 rounded-lg overflow-hidden bg-white"
            >
              {/* Accordion Header */}
              <div className="flex items-center px-4 py-4 hover:bg-gray-50 transition-colors">
                <button
                  onClick={() => toggleExpand(upload.id)}
                  className="flex-1 flex items-center gap-4 text-left"
                >
                  {/* Expand Icon */}
                  <svg
                    className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>

                  {/* Thumbnail */}
                  {upload.preview ? (
                    <img
                      src={upload.preview}
                      alt="Screenshot"
                      className="w-16 h-16 object-cover rounded border border-gray-200"
                    />
                  ) : (
                    <div className="w-16 h-16 bg-gray-100 rounded border border-gray-200 flex items-center justify-center">
                      <svg
                        className="w-8 h-8 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                  )}

                  {/* Info */}
                  <div className="text-left">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-900">
                        {qaPairCount} Q&A pair{qaPairCount !== 1 ? 's' : ''}
                      </span>
                      {getConfidenceBadge(result.confidence)}
                    </div>
                    <p className="text-sm text-gray-600 truncate max-w-md">
                      {upload.sourceUrl}
                    </p>
                  </div>
                </button>

                {/* Delete Button */}
                <button
                  onClick={() => deleteScreenshot(upload.id)}
                  className="text-gray-400 hover:text-red-600 transition-colors p-2"
                  title="Remove this screenshot"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Accordion Content */}
              {isExpanded && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <div className="space-y-4">
                    {result.qa_pairs.map((qaPair, qaIndex) => (
                      <div
                        key={qaIndex}
                        className="bg-white border border-gray-200 rounded-lg p-4"
                      >
                        {/* Q&A Header */}
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-gray-900">Q&A #{qaIndex + 1}</h4>
                          <button
                            onClick={() => deleteQAPair(upload.id, qaIndex)}
                            className="text-gray-400 hover:text-red-600 transition-colors text-sm"
                          >
                            Delete
                          </button>
                        </div>

                        {/* Question */}
                        <div className="mb-3">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Question
                          </label>
                          <textarea
                            value={qaPair.question}
                            onChange={(e) => updateQAPair(upload.id, qaIndex, 'question', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            rows={2}
                          />
                        </div>

                        {/* Answer */}
                        <div className="mb-3">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Answer
                          </label>
                          <textarea
                            value={qaPair.answer}
                            onChange={(e) => updateQAPair(upload.id, qaIndex, 'answer', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            rows={4}
                          />
                        </div>

                        {/* Tags */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Tags (comma-separated)
                          </label>
                          <input
                            type="text"
                            value={qaPair.tags.join(', ')}
                            onChange={(e) =>
                              updateQAPair(
                                upload.id,
                                qaIndex,
                                'tags',
                                e.target.value.split(',').map(t => t.trim()).filter(Boolean)
                              )
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g. facebook, ads, strategy"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <button
          onClick={onCancel}
          disabled={isSaving}
          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving || totalQAPairs === 0}
          className={`px-8 py-3 rounded-lg font-semibold text-white transition-all ${
            isSaving || totalQAPairs === 0
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-700 hover:shadow-lg'
          }`}
        >
          {isSaving ? (
            <span className="flex items-center">
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
            </span>
          ) : (
            `Save All ${totalQAPairs} Q&A Pair${totalQAPairs !== 1 ? 's' : ''}`
          )}
        </button>
      </div>
    </div>
  )
}

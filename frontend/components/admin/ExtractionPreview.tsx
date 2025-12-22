"use client"

/**
 * Extraction Preview Component
 * Shows extracted Q&A pairs with ability to edit before saving
 */

import { useState } from "react"
import { saveContent } from "@/lib/api/admin"
import type { ExtractScreenshotResponse, SaveContentResponse, QAPair } from "@/lib/api/types"

interface Props {
  extractionResult: ExtractScreenshotResponse
  sourceUrl: string
  uploadedImage: string | null
  onSaveComplete: (result: SaveContentResponse) => void
  onCancel: () => void
}

export default function ExtractionPreview({
  extractionResult,
  sourceUrl,
  uploadedImage,
  onSaveComplete,
  onCancel,
}: Props) {
  const [qaPairs, setQaPairs] = useState<QAPair[]>(extractionResult.qa_pairs)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleQuestionChange = (index: number, value: string) => {
    const updated = [...qaPairs]
    updated[index].question = value
    setQaPairs(updated)
  }

  const handleAnswerChange = (index: number, value: string) => {
    const updated = [...qaPairs]
    updated[index].answer = value
    setQaPairs(updated)
  }

  const handleTagsChange = (index: number, value: string) => {
    const updated = [...qaPairs]
    updated[index].tags = value.split(",").map((t) => t.trim()).filter((t) => t)
    setQaPairs(updated)
  }

  const handleDelete = (index: number) => {
    setQaPairs(qaPairs.filter((_, i) => i !== index))
  }

  const handleSave = async () => {
    if (qaPairs.length === 0) {
      setError("No Q&A pairs to save")
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      const result = await saveContent({
        qa_pairs: qaPairs,
        media_url: uploadedImage || "",
        source_url: sourceUrl,
        extracted_by: extractionResult.model_used,
        confidence: extractionResult.confidence,
        raw_extraction: extractionResult.metadata,
        content_type: "screenshot",
      })

      onSaveComplete(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to save content")
    } finally {
      setIsSaving(false)
    }
  }

  const confidenceColor =
    extractionResult.confidence >= 0.8
      ? "text-green-700 bg-green-100"
      : extractionResult.confidence >= 0.6
      ? "text-yellow-700 bg-yellow-100"
      : "text-red-700 bg-red-100"

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Review & Edit</h2>
          <p className="text-gray-600 mt-1">
            Review the extracted Q&A pairs and edit if needed
          </p>
        </div>

        {/* Extraction Metadata */}
        <div className="text-right space-y-1">
          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${confidenceColor}`}>
            {(extractionResult.confidence * 100).toFixed(0)}% Confidence
          </div>
          <p className="text-sm text-gray-600">Model: {extractionResult.model_used}</p>
          {extractionResult.used_fallback && (
            <p className="text-sm text-orange-600 font-medium">Used fallback</p>
          )}
        </div>
      </div>

      {/* Warnings */}
      {extractionResult.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="font-medium text-yellow-800 mb-2">⚠️ Please review carefully:</p>
          <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
            {extractionResult.warnings.map((warning, i) => (
              <li key={i}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Source Reference */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-sm font-medium text-gray-700 mb-1">Source</p>
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-purple-600 hover:text-purple-700 underline text-sm break-all"
        >
          {sourceUrl}
        </a>
      </div>

      {/* Q&A Pairs */}
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">
          Extracted Q&A Pairs ({qaPairs.length})
        </h3>

        {qaPairs.map((qa, index) => (
          <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <span className="inline-block bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-medium">
                Q&A #{index + 1}
              </span>
              <button
                onClick={() => handleDelete(index)}
                className="text-red-600 hover:text-red-700 text-sm font-medium"
              >
                Delete
              </button>
            </div>

            {/* Question */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question
              </label>
              <textarea
                value={qa.question}
                onChange={(e) => handleQuestionChange(index, e.target.value)}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Answer */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Answer</label>
              <textarea
                value={qa.answer}
                onChange={(e) => handleAnswerChange(index, e.target.value)}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={qa.tags.join(", ")}
                onChange={(e) => handleTagsChange(index, e.target.value)}
                placeholder="pricing, business, marketing"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onCancel}
          className="flex-1 py-3 px-6 border-2 border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving || qaPairs.length === 0}
          className={`flex-1 py-3 px-6 rounded-lg font-semibold text-white transition-all ${
            isSaving || qaPairs.length === 0
              ? "bg-gray-300 cursor-not-allowed"
              : "bg-green-600 hover:bg-green-700 hover:shadow-lg"
          }`}
        >
          {isSaving ? (
            <span className="flex items-center justify-center">
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
            `Save ${qaPairs.length} Q&A Pair${qaPairs.length !== 1 ? "s" : ""}`
          )}
        </button>
      </div>

      {/* Metadata Footer */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="font-medium">Extraction Time:</span>{" "}
            {extractionResult.metadata.latency_ms}ms
          </div>
          <div>
            <span className="font-medium">Cost:</span> $
            {extractionResult.metadata.cost_usd.toFixed(4)}
          </div>
        </div>
      </div>
    </div>
  )
}

"use client"

/**
 * Thread Parser Preview Component
 * Shows parsed Q&As with color coding, hierarchy, and tag management
 */

import { useState } from "react"
import type { ParseThreadResponse, ParsedQAPair, SaveContentResponse, SaveContentRequest } from "@/lib/api/types"
import { saveContent } from "@/lib/api/admin"

interface ThreadParserPreviewProps {
  data: ParseThreadResponse
  onSaveComplete: (result: SaveContentResponse) => void
  onCancel: () => void
}

interface EditableQAPair extends ParsedQAPair {
  isSelected: boolean  // For saving (checked = save, unchecked = delete)
  isEditing: boolean   // For inline editing
}

type FilterMode = "all" | "meaningful" | "filler" | "uncertain"

export default function ThreadParserPreview({
  data,
  onSaveComplete,
  onCancel,
}: ThreadParserPreviewProps) {
  const [qaPairs, setQaPairs] = useState<EditableQAPair[]>(
    data.qa_pairs.map(qa => ({
      ...qa,
      isSelected: qa.classification !== "filler",  // Auto-select meaningful for saving
      isEditing: false
    }))
  )
  const [filterMode, setFilterMode] = useState<FilterMode>("all")
  const [isSaving, setIsSaving] = useState(false)

  // Filter Q&As based on mode
  const filteredQAs = qaPairs.filter(qa => {
    if (filterMode === "all") return true
    if (filterMode === "meaningful") return qa.classification === "meaningful"
    if (filterMode === "filler") return qa.classification === "filler"
    if (filterMode === "uncertain") return qa.confidence < 0.7
    return true
  })

  // Counts
  const meaningfulCount = qaPairs.filter(qa => qa.classification === "meaningful").length
  const fillerCount = qaPairs.filter(qa => qa.classification === "filler").length
  const uncertainCount = qaPairs.filter(qa => qa.confidence < 0.7).length
  const selectedCount = qaPairs.filter(qa => qa.isSelected).length

  const handleSelectAll = (selected: boolean) => {
    setQaPairs(qaPairs.map(qa => ({
      ...qa,
      isSelected: selected
    })))
  }

  const handleDeselectAllFiller = () => {
    setQaPairs(qaPairs.map(qa => ({
      ...qa,
      isSelected: qa.classification !== "filler"  // Deselect filler items (won't be saved)
    })))
  }

  const handleToggleSelect = (index: number) => {
    const updated = [...qaPairs]
    updated[index].isSelected = !updated[index].isSelected
    setQaPairs(updated)
  }

  const handleEditQuestion = (index: number, value: string) => {
    const updated = [...qaPairs]
    updated[index].question = value
    setQaPairs(updated)
  }

  const handleEditAnswer = (index: number, value: string) => {
    const updated = [...qaPairs]
    updated[index].answer = value
    setQaPairs(updated)
  }

  const handleAddTag = (index: number, tag: string) => {
    const updated = [...qaPairs]
    if (!updated[index].tags.includes(tag)) {
      updated[index].tags = [...updated[index].tags, tag]
    }
    setQaPairs(updated)
  }

  const handleRemoveTag = (index: number, tag: string) => {
    const updated = [...qaPairs]
    updated[index].tags = updated[index].tags.filter(t => t !== tag)
    setQaPairs(updated)
  }

  const handleSave = async () => {
    setIsSaving(true)

    try {
      // Save selected (checked) Q&As
      const qaPairsToSave = qaPairs
        .filter(qa => qa.isSelected)
        .map(qa => ({
          question: qa.question.trim(),
          answer: qa.answer.trim(),
          tags: qa.tags
        }))

      if (qaPairsToSave.length === 0) {
        alert("No Q&As to save. Please select at least one Q&A.")
        setIsSaving(false)
        return
      }

      // Build save request
      const saveRequest: SaveContentRequest = {
        qa_pairs: qaPairsToSave,
        media_url: "",  // No screenshot
        source_url: data.qa_pairs[0]?.question || "Thread import",  // Use first question as reference
        extracted_by: "manual",  // Use "manual" to satisfy DB constraint (thread-parser info stored in raw_extraction)
        confidence: calculateOverallConfidence(qaPairsToSave),
        raw_extraction: {
          import_method: "thread-parser",
          imported_at: new Date().toISOString(),
          original_count: data.total_parsed,
          filler_filtered: data.filler_count,
          user_deleted: qaPairs.length - selectedCount,
          hierarchy: qaPairs.map(qa => ({
            parent_index: qa.parent_index,
            depth: qa.depth
          })),
          metadata: data.metadata
        },
        content_type: "facebook"
      }

      const result = await saveContent(saveRequest)
      onSaveComplete(result)
    } catch (error) {
      console.error("Failed to save:", error)
      alert("Failed to save content. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  const calculateOverallConfidence = (pairs: any[]) => {
    if (pairs.length === 0) return 0
    const avgConfidence = pairs.reduce((sum, qa) => {
      const original = qaPairs.find(q => q.question === qa.question && q.answer === qa.answer)
      return sum + (original?.confidence || 0.5)
    }, 0) / pairs.length
    return Math.round(avgConfidence * 100) / 100
  }

  const getClassificationColor = (qa: EditableQAPair) => {
    if (qa.classification === "meaningful") return "border-green-300 bg-green-50"
    if (qa.classification === "filler") return "border-red-300 bg-red-50"
    if (qa.confidence < 0.7) return "border-yellow-300 bg-yellow-50"
    return "border-gray-300 bg-white"
  }

  const getClassificationBadge = (qa: EditableQAPair) => {
    if (qa.classification === "meaningful") {
      return <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">✓ MEANINGFUL ({Math.round(qa.confidence * 100)}%)</span>
    }
    if (qa.classification === "filler") {
      return <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">⚠ FILLER ({Math.round(qa.confidence * 100)}%)</span>
    }
    if (qa.confidence < 0.7) {
      return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">? UNCERTAIN ({Math.round(qa.confidence * 100)}%)</span>
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>AI found {data.total_parsed} Q&As:</strong>{" "}
          <span className="text-green-700">{meaningfulCount} meaningful</span>,{" "}
          <span className="text-red-700">{fillerCount} filler</span>
          {uncertainCount > 0 && <>, <span className="text-yellow-700">{uncertainCount} uncertain</span></>}
        </p>
        <p className="text-xs text-blue-600 mt-1">
          Cost: ${data.metadata.cost_usd.toFixed(4)} | Time: {(data.metadata.latency_ms / 1000).toFixed(1)}s | Model: {data.metadata.model}
        </p>
      </div>

      {/* Filters and Bulk Actions */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <select
            value={filterMode}
            onChange={(e) => setFilterMode(e.target.value as FilterMode)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          >
            <option value="all">Show: All ({qaPairs.length})</option>
            <option value="meaningful">Show: Meaningful ({meaningfulCount})</option>
            <option value="filler">Show: Filler ({fillerCount})</option>
            {uncertainCount > 0 && <option value="uncertain">Show: Uncertain ({uncertainCount})</option>}
          </select>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => handleSelectAll(true)}
            className="px-3 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
          >
            ☑ Select all
          </button>
          <button
            onClick={handleDeselectAllFiller}
            className="px-3 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            ☐ Deselect all filler
          </button>
          <button
            onClick={() => handleSelectAll(false)}
            className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            ☐ Deselect all
          </button>
        </div>
      </div>

      {/* Q&A Cards */}
      <div className="space-y-4">
        {filteredQAs.map((qa, index) => {
          const originalIndex = qaPairs.indexOf(qa)
          const indentLevel = Math.min(qa.depth, 3)  // Max 3 levels of indentation

          return (
            <div
              key={originalIndex}
              className={`border rounded-lg p-4 ${getClassificationColor(qa)} ${!qa.isSelected ? "opacity-50" : ""}`}
              style={{ marginLeft: `${indentLevel * 24}px` }}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={qa.isSelected}
                    onChange={() => handleToggleSelect(originalIndex)}
                    className="w-4 h-4"
                  />
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900">
                      {qa.depth === 0 ? "Main Q&A (Parent)" : `Follow-up Q&A #${originalIndex} (depth ${qa.depth})`}
                    </h3>
                    <div className="flex gap-2 mt-1">
                      {getClassificationBadge(qa)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Question */}
              <div className="mb-3">
                <label className="block text-xs font-medium text-gray-700 mb-1">Question</label>
                <textarea
                  value={qa.question}
                  onChange={(e) => handleEditQuestion(originalIndex, e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
                />
              </div>

              {/* Answer */}
              <div className="mb-3">
                <label className="block text-xs font-medium text-gray-700 mb-1">Answer</label>
                <textarea
                  value={qa.answer}
                  onChange={(e) => handleEditAnswer(originalIndex, e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none"
                />
              </div>

              {/* AI Reasoning */}
              {qa.reasoning && (
                <div className="mb-3 text-xs text-gray-600 italic bg-gray-100 p-2 rounded">
                  <strong>AI reasoning:</strong> {qa.reasoning}
                </div>
              )}

              {/* Tags */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Tags</label>
                <div className="flex flex-wrap gap-2">
                  {qa.tags.length === 0 && (
                    <span className="text-xs text-gray-400 italic">No tags</span>
                  )}
                  {qa.tags.map((tag, tagIndex) => (
                    <div
                      key={tagIndex}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                    >
                      <span>{tag}</span>
                      <button
                        onClick={() => handleRemoveTag(originalIndex, tag)}
                        className="hover:text-red-600"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          {selectedCount < qaPairs.length && (
            <span className="text-orange-600 font-medium">
              {qaPairs.length - selectedCount} Q&A{qaPairs.length - selectedCount !== 1 ? "s" : ""} will be discarded
            </span>
          )}
          {selectedCount === qaPairs.length && (
            <span className="text-green-600 font-medium">
              All {qaPairs.length} Q&As will be saved
            </span>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            disabled={isSaving}
            className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || qaPairs.filter(qa => qa.isSelected).length === 0}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? "Saving..." : `Save ${qaPairs.filter(qa => qa.isSelected).length} Q&As`}
          </button>
        </div>
      </div>
    </div>
  )
}

"use client"

/**
 * Text Import Preview Component
 * Shows preview of text-imported Q&As with AI-generated tag suggestions
 */

import { useState, useEffect } from "react"
import type { SaveContentRequest, SaveContentResponse } from "@/lib/api/types"
import { saveContent } from "@/lib/api/admin"

interface TextImportPreviewProps {
  data: SaveContentRequest
  onSaveComplete: (result: SaveContentResponse) => void
  onCancel: () => void
}

interface QAPairWithAITags {
  question: string
  answer: string
  userTags: string[]
  aiTags: string[]
  finalTags: string[]
}

export default function TextImportPreview({
  data,
  onSaveComplete,
  onCancel,
}: TextImportPreviewProps) {
  const [qaPairs, setQaPairs] = useState<QAPairWithAITags[]>([])
  const [isGeneratingTags, setIsGeneratingTags] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    // Initialize Q&A pairs with user tags and generate AI tags
    const initializeAndGenerateTags = async () => {
      const initialized = data.qa_pairs.map(qa => ({
        question: qa.question,
        answer: qa.answer,
        userTags: qa.tags || [],
        aiTags: [],
        finalTags: qa.tags || [],
      }))

      setQaPairs(initialized)

      // Generate AI tags for all Q&As
      await generateAllTags(initialized)
    }

    initializeAndGenerateTags()
  }, [data])

  const generateAllTags = async (pairs: QAPairWithAITags[]) => {
    setIsGeneratingTags(true)

    try {
      const updatedPairs = [...pairs]

      for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i]

        // Call AI tag generation API
        const aiTags = await generateTags(pair.question, pair.answer)

        updatedPairs[i] = {
          ...pair,
          aiTags,
          // If user didn't provide tags, use AI tags as final
          finalTags: pair.userTags.length > 0 ? pair.userTags : aiTags,
        }

        setQaPairs([...updatedPairs])
      }
    } catch (error) {
      console.error("Failed to generate tags:", error)
    } finally {
      setIsGeneratingTags(false)
    }
  }

  const generateTags = async (question: string, answer: string): Promise<string[]> => {
    try {
      const response = await fetch("http://localhost:8001/api/admin/generate-tags", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, answer }),
      })

      if (!response.ok) {
        throw new Error("Failed to generate tags")
      }

      const result = await response.json()
      return result.tags || []
    } catch (error) {
      console.error("Tag generation error:", error)
      return []
    }
  }

  const handleAcceptAITag = (pairIndex: number, tag: string) => {
    const updated = [...qaPairs]
    if (!updated[pairIndex].finalTags.includes(tag)) {
      updated[pairIndex].finalTags = [...updated[pairIndex].finalTags, tag]
    }
    setQaPairs(updated)
  }

  const handleRemoveTag = (pairIndex: number, tag: string) => {
    const updated = [...qaPairs]
    updated[pairIndex].finalTags = updated[pairIndex].finalTags.filter(t => t !== tag)
    setQaPairs(updated)
  }

  const handleSave = async () => {
    setIsSaving(true)

    try {
      // Prepare data with final tags
      const updatedData: SaveContentRequest = {
        ...data,
        qa_pairs: qaPairs.map(pair => ({
          question: pair.question,
          answer: pair.answer,
          tags: pair.finalTags,
        })),
      }

      const result = await saveContent(updatedData)
      onSaveComplete(result)
    } catch (error) {
      console.error("Failed to save:", error)
      alert("Failed to save content. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Review your import:</strong> AI has suggested tags for each Q&A.
          You can accept, reject, or add your own tags before saving.
        </p>
      </div>

      {/* Source URL */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Source URL</label>
        <a
          href={data.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-purple-600 hover:text-purple-700 underline text-sm"
        >
          {data.source_url}
        </a>
      </div>

      {/* Q&A Pairs */}
      {qaPairs.map((pair, index) => (
        <div key={index} className="border border-gray-300 rounded-lg p-6 bg-white">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {index === 0 ? "Main Q&A (Parent)" : `Follow-up #${index}`}
            </h3>
          </div>

          {/* Question */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Question</label>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm whitespace-pre-wrap">
              {pair.question}
            </div>
          </div>

          {/* Answer */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Answer</label>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm whitespace-pre-wrap">
              {pair.answer}
            </div>
          </div>

          {/* Tags Section */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>

            {/* Final Tags (Selected) */}
            <div className="mb-3">
              <div className="text-xs text-gray-600 mb-2">Selected tags:</div>
              <div className="flex flex-wrap gap-2">
                {pair.finalTags.length === 0 && (
                  <span className="text-sm text-gray-400 italic">No tags selected</span>
                )}
                {pair.finalTags.map((tag, tagIndex) => {
                  const isUserTag = pair.userTags.includes(tag)
                  return (
                    <div
                      key={tagIndex}
                      className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                        isUserTag
                          ? "bg-blue-100 text-blue-800 border border-blue-300"
                          : "bg-green-100 text-green-800 border border-green-300"
                      }`}
                    >
                      <span>{tag}</span>
                      {isUserTag && (
                        <span className="text-xs opacity-70">(You)</span>
                      )}
                      {!isUserTag && (
                        <span className="text-xs opacity-70">(AI)</span>
                      )}
                      <button
                        onClick={() => handleRemoveTag(index, tag)}
                        className="hover:text-red-600 ml-1"
                      >
                        ×
                      </button>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* AI Suggested Tags */}
            {isGeneratingTags && pair.aiTags.length === 0 && (
              <div className="text-sm text-gray-500 italic">
                ✨ Generating AI tags...
              </div>
            )}

            {pair.aiTags.length > 0 && (
              <div>
                <div className="text-xs text-gray-600 mb-2">AI suggestions (click to add):</div>
                <div className="flex flex-wrap gap-2">
                  {pair.aiTags
                    .filter(tag => !pair.finalTags.includes(tag))
                    .map((tag, tagIndex) => (
                      <button
                        key={tagIndex}
                        onClick={() => handleAcceptAITag(index, tag)}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm border border-gray-300 hover:bg-green-50 hover:border-green-400 hover:text-green-700 transition-colors"
                      >
                        + {tag}
                      </button>
                    ))}
                  {pair.aiTags.every(tag => pair.finalTags.includes(tag)) && (
                    <span className="text-sm text-gray-400 italic">All suggestions already added</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          onClick={onCancel}
          disabled={isSaving}
          className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving || isGeneratingTags}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSaving ? "Saving..." : isGeneratingTags ? "Generating tags..." : "Save to Knowledge Base"}
        </button>
      </div>
    </div>
  )
}

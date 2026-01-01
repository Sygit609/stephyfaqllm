"use client"

/**
 * Text Import Component
 * Allows direct paste of Facebook post Q&As without screenshot upload
 * Supports main Q&A + optional follow-up questions from comments
 */

import { useState } from "react"
import type { SaveContentRequest } from "@/lib/api/types"

interface QAPair {
  question: string
  answer: string
  tags: string[]
}

interface TextImporterProps {
  onComplete: (data: SaveContentRequest) => void
}

export function TextImporter({ onComplete }: TextImporterProps) {
  const [sourceUrl, setSourceUrl] = useState("")
  const [mainQuestion, setMainQuestion] = useState("")
  const [mainAnswer, setMainAnswer] = useState("")
  const [followUps, setFollowUps] = useState<QAPair[]>([])
  const [tags, setTags] = useState("")

  const addFollowUp = () => {
    setFollowUps([...followUps, { question: "", answer: "", tags: [] }])
  }

  const removeFollowUp = (index: number) => {
    setFollowUps(followUps.filter((_, i) => i !== index))
  }

  const updateFollowUp = (index: number, field: keyof QAPair, value: any) => {
    const updated = [...followUps]
    updated[index] = { ...updated[index], [field]: value }
    setFollowUps(updated)
  }

  const handleClear = () => {
    setSourceUrl("")
    setMainQuestion("")
    setMainAnswer("")
    setFollowUps([])
    setTags("")
  }

  const handleSubmit = () => {
    // Build Q&A pairs array
    const qaPairs: Array<{
      question: string
      answer: string
      tags: string[]
    }> = [
      {
        question: mainQuestion.trim(),
        answer: mainAnswer.trim(),
        tags: tags.split(',').map(t => t.trim()).filter(Boolean)
      },
      ...followUps
        .filter(f => f.question.trim() && f.answer.trim())
        .map(f => ({
          question: f.question.trim(),
          answer: f.answer.trim(),
          tags: f.tags
        }))
    ]

    // Call onComplete with SaveContentRequest format
    onComplete({
      qa_pairs: qaPairs,
      media_url: "",  // No screenshot
      source_url: sourceUrl.trim(),
      extracted_by: "manual",  // Use existing enum value
      confidence: 1.0,
      raw_extraction: {
        import_method: "text",
        imported_at: new Date().toISOString(),
        follow_up_count: followUps.filter(f => f.question.trim() && f.answer.trim()).length
      },
      content_type: "facebook"  // Use existing enum value
    })
  }

  const isValid = sourceUrl.trim() && mainQuestion.trim() && mainAnswer.trim()

  return (
    <div className="space-y-6">
      {/* Helper Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Copy the main question and answer from the Facebook post,
          then add any follow-up Q&As from the comments. This is faster than uploading screenshots
          and works great on mobile!
        </p>
      </div>

      {/* Source URL */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Facebook Post URL <span className="text-red-500">*</span>
        </label>
        <input
          type="url"
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
          placeholder="https://facebook.com/groups/..."
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          required
        />
      </div>

      {/* Main Question */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Main Question <span className="text-red-500">*</span>
        </label>
        <textarea
          value={mainQuestion}
          onChange={(e) => setMainQuestion(e.target.value)}
          rows={3}
          placeholder="Paste the main question from the post..."
          className="w-full px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          {mainQuestion.length} characters (min 10 recommended)
        </p>
      </div>

      {/* Main Answer */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Answer to Main Question <span className="text-red-500">*</span>
        </label>
        <textarea
          value={mainAnswer}
          onChange={(e) => setMainAnswer(e.target.value)}
          rows={5}
          placeholder="Paste the answer..."
          className="w-full px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          required
        />
        <p className="mt-1 text-xs text-gray-500">
          {mainAnswer.length} characters (min 20 recommended)
        </p>
      </div>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tags (comma-separated)
        </label>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="pricing, digital products, business"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-1 text-xs text-gray-500">
          Optional: Add relevant tags to help with searching
        </p>
      </div>

      {/* Follow-up Q&As */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Follow-up Questions (optional)
          </label>
          <button
            type="button"
            onClick={addFollowUp}
            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            + Add Follow-up
          </button>
        </div>

        {followUps.length === 0 && (
          <div className="text-center py-8 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
            <p className="text-sm text-gray-500">
              No follow-up questions yet. Click &quot;Add Follow-up&quot; to add Q&As from comments.
            </p>
          </div>
        )}

        {followUps.map((followUp, index) => (
          <div key={index} className="border border-gray-300 bg-white p-4 mb-3 rounded-lg shadow-sm">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm font-medium text-gray-600">Follow-up #{index + 1}</span>
              <button
                type="button"
                onClick={() => removeFollowUp(index)}
                className="px-2 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
              >
                Remove
              </button>
            </div>

            <div className="space-y-3">
              <textarea
                value={followUp.question}
                onChange={(e) => updateFollowUp(index, 'question', e.target.value)}
                rows={2}
                placeholder="Follow-up question..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none text-sm"
              />

              <textarea
                value={followUp.answer}
                onChange={(e) => updateFollowUp(index, 'answer', e.target.value)}
                rows={3}
                placeholder="Answer to follow-up..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none text-sm"
              />

              <input
                type="text"
                value={followUp.tags.join(', ')}
                onChange={(e) => {
                  const tagArray = e.target.value.split(',').map(t => t.trim()).filter(Boolean)
                  updateFollowUp(index, 'tags', tagArray)
                }}
                placeholder="Tags (comma-separated)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Submit Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={handleClear}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Clear
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!isValid}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Continue to Preview
        </button>
      </div>
    </div>
  )
}

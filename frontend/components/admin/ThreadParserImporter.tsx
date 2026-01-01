"use client"

/**
 * Thread Parser Importer Component
 * Allows pasting full Facebook threads for AI parsing
 */

import { useState } from "react"
import { parseThread } from "@/lib/api/admin"
import type { ParseThreadResponse } from "@/lib/api/types"

interface ThreadParserImporterProps {
  onComplete: (data: ParseThreadResponse) => void
}

export function ThreadParserImporter({ onComplete }: ThreadParserImporterProps) {
  const [sourceUrl, setSourceUrl] = useState("")
  const [threadText, setThreadText] = useState("")
  const [isParsing, setIsParsing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClear = () => {
    setSourceUrl("")
    setThreadText("")
    setError(null)
  }

  const handleParse = async () => {
    setError(null)
    setIsParsing(true)

    try {
      // Validate inputs
      if (!sourceUrl.trim()) {
        throw new Error("Facebook post URL is required")
      }
      if (!threadText.trim()) {
        throw new Error("Thread text is required")
      }
      if (threadText.trim().length < 100) {
        throw new Error("Thread text seems too short. Please paste the full thread including all comments.")
      }

      // Call API
      const result = await parseThread({
        thread_text: threadText.trim(),
        source_url: sourceUrl.trim(),
        provider: "openai"
      })

      // Check if any Q&As were parsed
      if (result.qa_pairs.length === 0) {
        throw new Error("No Q&A pairs found in the thread. Please check the thread format.")
      }

      // Pass to preview
      onComplete(result)
    } catch (err: any) {
      console.error("Thread parsing error:", err)
      setError(err.response?.data?.detail || err.message || "Failed to parse thread. Please try again.")
    } finally {
      setIsParsing(false)
    }
  }

  const isValid = sourceUrl.trim() && threadText.trim().length >= 100

  return (
    <div className="space-y-6">
      {/* Helper Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Copy the entire Facebook post including the main question, answer,
          and all comment replies. AI will automatically extract Q&A pairs, classify them as
          meaningful or filler, and generate tags. This is much faster than manual entry!
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">
            <strong>Error:</strong> {error}
          </p>
        </div>
      )}

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
          disabled={isParsing}
        />
      </div>

      {/* Thread Text */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Paste Entire Thread <span className="text-red-500">*</span>
        </label>
        <textarea
          value={threadText}
          onChange={(e) => setThreadText(e.target.value)}
          rows={15}
          placeholder="Paste the entire Facebook thread here, including:
- Main post question
- Answer to main post
- All comment replies
- Nested discussions

The AI will automatically parse and organize everything for you."
          className="w-full px-4 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
          required
          disabled={isParsing}
        />
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>{threadText.length.toLocaleString()} characters</span>
          <span className={threadText.length < 100 ? "text-orange-600" : "text-green-600"}>
            {threadText.length < 100 ? "Minimum 100 characters recommended" : "Ready to parse"}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={handleClear}
          disabled={isParsing}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Clear
        </button>
        <button
          type="button"
          onClick={handleParse}
          disabled={!isValid || isParsing}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isParsing ? (
            <>
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Parsing with AI...
            </>
          ) : (
            <>
              🤖 Parse with AI
            </>
          )}
        </button>
      </div>

      {/* Parsing in progress message */}
      {isParsing && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>AI is parsing your thread...</strong> This usually takes 5-10 seconds.
            The AI is extracting Q&A pairs, classifying content, and generating tags.
          </p>
        </div>
      )}
    </div>
  )
}

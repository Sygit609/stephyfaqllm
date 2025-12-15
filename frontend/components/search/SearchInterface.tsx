"use client"

/**
 * Main Search Interface Component
 * Handles query input, model selection, and displays results
 */

import { useState } from "react"
import { Search, Loader2 } from "lucide-react"
import { ModelSelector } from "./ModelSelector"
import { AnswerDisplay } from "./AnswerDisplay"
import { SourcesList } from "./SourcesList"
import { useQuery } from "@/lib/hooks/useQuery"
import type { ModelProvider } from "@/lib/api/types"

export function SearchInterface() {
  const [queryText, setQueryText] = useState("")
  const [selectedProvider, setSelectedProvider] = useState<ModelProvider>("openai")

  const { data, isLoading, error, executeQuery } = useQuery()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) return

    await executeQuery({
      query: queryText.trim(),
      provider: selectedProvider,
      search_limit: 5,
      use_web_search: true,
    })
  }

  const handleClear = () => {
    setQueryText("")
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Model Selector */}
          <div className="flex justify-between items-center">
            <label className="text-sm font-medium text-gray-700">
              Model Provider
            </label>
            <ModelSelector
              selected={selectedProvider}
              onChange={setSelectedProvider}
              disabled={isLoading}
            />
          </div>

          {/* Query Input */}
          <div className="relative">
            <textarea
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Ask a question about your community..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
              disabled={isLoading}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end">
            {queryText && (
              <button
                type="button"
                onClick={handleClear}
                disabled={isLoading}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
              >
                Clear
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading || !queryText.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Search
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium mb-1">Error</h3>
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Results */}
      {data && (
        <div className="space-y-6">
          {/* Answer Display */}
          <AnswerDisplay
            query={data.query}
            answer={data.answer}
            provider={data.provider}
            metadata={data.metadata}
            intent={data.intent}
            recencyRequired={data.recency_required}
            webSearchUsed={data.web_search_used}
            queryId={data.query_id}
          />

          {/* Sources */}
          {data.sources && data.sources.length > 0 && (
            <SourcesList
              sources={data.sources}
              webResults={data.web_results}
            />
          )}
        </div>
      )}
    </div>
  )
}

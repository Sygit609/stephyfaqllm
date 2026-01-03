"use client"

/**
 * Main Search Interface Component
 * Handles query input, model selection, admin guidance, and displays results
 * Supports iterative refinement with admin input
 */

import { useState } from "react"
import { Search, Loader2 } from "lucide-react"
import { ModelSelector } from "./ModelSelector"
import { AnswerDisplay } from "./AnswerDisplay"
import { SourcesList } from "./SourcesList"
import { useQuery } from "@/lib/hooks/useQuery"
import type { ModelProvider } from "@/lib/api/types"

export function SearchInterface() {
  const INITIAL_LIMIT = 10  // Increased from 5
  const INCREMENT = 10      // Load +10 more each click

  const [queryText, setQueryText] = useState("")
  const [adminInput, setAdminInput] = useState("")
  const [selectedProvider, setSelectedProvider] = useState<ModelProvider>("openai")
  const [searchState, setSearchState] = useState<"initial" | "answer">("initial")
  const [currentLimit, setCurrentLimit] = useState(INITIAL_LIMIT)
  const [isLoadingMore, setIsLoadingMore] = useState(false)

  const { data, isLoading, error, executeQuery } = useQuery()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) return

    setCurrentLimit(INITIAL_LIMIT)  // Reset to 10 on new search

    await executeQuery({
      query: queryText.trim(),
      provider: selectedProvider,
      search_limit: INITIAL_LIMIT,
      use_web_search: true,
      admin_input: adminInput.trim() || undefined,
    })

    setSearchState("answer")
  }

  const handleNewQuestion = () => {
    setQueryText("")
    setAdminInput("")
    setSearchState("initial")
    setCurrentLimit(INITIAL_LIMIT)
  }

  const handleRefineAnswer = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!queryText.trim()) return

    await executeQuery({
      query: queryText.trim(),
      provider: selectedProvider,
      search_limit: currentLimit,  // Use current limit for refinement
      use_web_search: true,
      admin_input: adminInput.trim() || undefined,
    })
  }

  const handleViewMore = async () => {
    setIsLoadingMore(true)
    const newLimit = currentLimit + INCREMENT

    await executeQuery({
      query: queryText.trim(),
      provider: selectedProvider,
      search_limit: newLimit,
      use_web_search: true,
      admin_input: adminInput.trim() || undefined,
    })

    setCurrentLimit(newLimit)
    setIsLoadingMore(false)
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <form onSubmit={searchState === "initial" ? handleSubmit : handleRefineAnswer} className="space-y-4">

          {/* Model Selector - only show in initial state */}
          {searchState === "initial" && (
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
          )}

          {/* Student Question */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Student's Question {searchState === "answer" && "(read-only)"}
            </label>

            {searchState === "initial" ? (
              <textarea
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                placeholder="Paste the student's question from Facebook..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={4}
                disabled={isLoading}
              />
            ) : (
              <div className="px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-gray-700 whitespace-pre-wrap">
                {queryText}
              </div>
            )}
          </div>

          {/* Admin Input - Always editable */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Admin Input (optional)
            </label>
            <textarea
              value={adminInput}
              onChange={(e) => setAdminInput(e.target.value)}
              placeholder={
                searchState === "initial"
                  ? "Optional: Provide guidance like 'emphasize pricing', 'explain for beginners', 'focus on technical details', etc."
                  : "Refine your guidance to improve the answer..."
              }
              className="w-full px-4 py-3 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              rows={3}
              disabled={isLoading}
            />
            <p className="mt-1 text-xs text-gray-500">
              {searchState === "initial"
                ? "This guidance will influence how the AI generates the answer."
                : "Adjust your guidance and click 'Refine Answer' to regenerate with new direction."}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end">
            {searchState === "answer" && (
              <button
                type="button"
                onClick={handleNewQuestion}
                disabled={isLoading}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                New Question
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
                  {searchState === "initial" ? "Searching..." : "Refining..."}
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  {searchState === "initial" ? "Search" : "Refine Answer"}
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

          {/* View More Button */}
          {data.sources && data.sources.length >= currentLimit && (
            <div className="bg-white rounded-lg shadow-md p-4">
              <button
                onClick={handleViewMore}
                disabled={isLoadingMore || isLoading}
                className="w-full py-3 border-2 border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
              >
                {isLoadingMore ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading more results...
                  </span>
                ) : (
                  `View More Results (+${INCREMENT})`
                )}
              </button>

              <div className="text-sm text-gray-600 mt-3 text-center">
                Showing {data.sources.length} result{data.sources.length !== 1 ? 's' : ''}
                {data.sources.length < currentLimit && ' (all available)'}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

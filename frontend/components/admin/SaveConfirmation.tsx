"use client"

/**
 * Save Confirmation Component
 * Shows success message after content is saved
 */

import Link from "next/link"
import type { SaveContentResponse } from "@/lib/api/types"

interface Props {
  saveResult: SaveContentResponse
  onStartOver: () => void
  batchResults?: SaveContentResponse[]
}

export default function SaveConfirmation({ saveResult, onStartOver, batchResults }: Props) {
  const isBatchMode = batchResults && batchResults.length > 0

  // Calculate batch totals
  const totalQAPairs = isBatchMode
    ? batchResults.reduce((sum, r) => sum + r.total_saved, 0)
    : saveResult.total_saved

  const totalEmbeddings = isBatchMode
    ? batchResults.reduce((sum, r) => sum + r.child_ids.length * 2, 0)
    : saveResult.child_ids.length * 2

  const totalScreenshots = isBatchMode ? batchResults.length : 1
  return (
    <div className="space-y-8 text-center">
      {/* Success Icon */}
      <div className="flex justify-center">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center">
          <svg
            className="w-12 h-12 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
      </div>

      {/* Success Message */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Successfully Saved!</h2>
        <p className="text-gray-600 text-lg">
          {totalQAPairs} Q&A pair{totalQAPairs !== 1 ? "s" : ""} added to
          the knowledge base
          {isBatchMode && ` from ${totalScreenshots} screenshot${totalScreenshots !== 1 ? "s" : ""}`}
        </p>
      </div>

      {/* Details */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-left">
        <h3 className="font-semibold text-green-900 mb-3">Import Details</h3>
        <div className="space-y-2 text-sm">
          {isBatchMode ? (
            <>
              <div className="flex justify-between">
                <span className="text-green-700">Screenshots Saved:</span>
                <span className="text-green-900 font-medium">{totalScreenshots}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Total Q&A Pairs:</span>
                <span className="text-green-900 font-medium">{totalQAPairs}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Parent Entry IDs:</span>
                <span className="text-green-900 font-medium">{batchResults.length} created</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Child Entry IDs:</span>
                <span className="text-green-900 font-medium">
                  {batchResults.reduce((sum, r) => sum + r.child_ids.length, 0)} created
                </span>
              </div>
            </>
          ) : (
            <>
              <div className="flex justify-between">
                <span className="text-green-700">Parent Entry ID:</span>
                <span className="text-green-900 font-mono">{saveResult.parent_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Q&A Pairs Saved:</span>
                <span className="text-green-900 font-medium">{saveResult.total_saved}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Child Entry IDs:</span>
                <span className="text-green-900 font-medium">
                  {saveResult.child_ids.length} created
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-left">
        <h3 className="font-semibold text-blue-900 mb-2">What happens next?</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start">
            <svg
              className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span>All Q&A pairs have been indexed with dual embeddings (OpenAI + Gemini)</span>
          </li>
          <li className="flex items-start">
            <svg
              className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span>Content is immediately searchable in the main Q&A tool</span>
          </li>
          <li className="flex items-start">
            <svg
              className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span>Source screenshot is linked for reference</span>
          </li>
        </ul>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onStartOver}
          className="flex-1 py-3 px-6 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-colors"
        >
          {isBatchMode ? "Import More Screenshots" : "Import Another Screenshot"}
        </button>
        <Link
          href="/"
          className="flex-1 py-3 px-6 bg-white border-2 border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg font-semibold transition-colors text-center"
        >
          Go to Search Tool
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 pt-6 border-t border-gray-200">
        <div>
          <div className="text-2xl font-bold text-gray-900">{totalQAPairs}</div>
          <div className="text-sm text-gray-600">Q&A Pairs</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{totalEmbeddings}</div>
          <div className="text-sm text-gray-600">Embeddings Generated</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-900">{totalScreenshots}</div>
          <div className="text-sm text-gray-600">Screenshot{totalScreenshots !== 1 ? "s" : ""} Saved</div>
        </div>
      </div>
    </div>
  )
}

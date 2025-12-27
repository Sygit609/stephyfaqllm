"use client"

/**
 * Content Table Component
 * Displays content items in a responsive table with edit/delete actions
 */

import type { ContentItem } from "@/lib/api/types"

interface Props {
  items: ContentItem[]
  onEdit: (item: ContentItem) => void
  onDelete: (item: ContentItem) => void
}

export default function ContentTable({ items, onEdit, onDelete }: Props) {
  const getConfidenceBadge = (confidence: number | null) => {
    if (confidence === null) {
      return (
        <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
          N/A
        </span>
      )
    }

    const percentage = Math.round(confidence * 100)
    let colorClass = "bg-green-100 text-green-700"
    if (confidence < 0.7) colorClass = "bg-yellow-100 text-yellow-700"
    if (confidence < 0.5) colorClass = "bg-red-100 text-red-700"

    return (
      <span
        className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}
      >
        {percentage}%
      </span>
    )
  }

  const getTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      screenshot: "bg-purple-100 text-purple-700",
      facebook: "bg-blue-100 text-blue-700",
      manual: "bg-gray-100 text-gray-700",
      csv: "bg-green-100 text-green-700",
      video: "bg-red-100 text-red-700"
    }

    return (
      <span
        className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
          colors[type] || "bg-gray-100 text-gray-700"
        }`}
      >
        {type}
      </span>
    )
  }

  const truncate = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + "..."
  }

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-12 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="text-gray-600 text-lg">No content items found</p>
        <p className="text-gray-500 text-sm mt-2">
          Try adjusting your filters or import new content
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Question
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Answer
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Tags
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {items.map((item) => (
              <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                {/* Question */}
                <td className="px-4 py-4 max-w-xs">
                  <div className="flex items-start">
                    {item.parent_id && (
                      <span
                        className="inline-block mr-2 px-1.5 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700"
                        title={`Child of ${item.parent_id.slice(0, 8)}...`}
                      >
                        ↳
                      </span>
                    )}
                    <p
                      className="text-sm text-gray-900 font-medium"
                      title={item.question}
                    >
                      {truncate(item.question, 60)}
                    </p>
                  </div>
                </td>

                {/* Answer */}
                <td className="px-4 py-4 max-w-md">
                  <p className="text-sm text-gray-700" title={item.answer}>
                    {truncate(item.answer, 80)}
                  </p>
                </td>

                {/* Type */}
                <td className="px-4 py-4 whitespace-nowrap">
                  {getTypeBadge(item.content_type)}
                </td>

                {/* Confidence */}
                <td className="px-4 py-4 whitespace-nowrap">
                  {getConfidenceBadge(item.extraction_confidence)}
                </td>

                {/* Tags */}
                <td className="px-4 py-4">
                  <p className="text-xs text-gray-600" title={item.tags || ""}>
                    {item.tags ? truncate(item.tags, 30) : "—"}
                  </p>
                </td>

                {/* Actions */}
                <td className="px-4 py-4 whitespace-nowrap text-right">
                  <button
                    onClick={() => onEdit(item)}
                    className="text-purple-600 hover:text-purple-700 font-medium text-sm mr-3 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => onDelete(item)}
                    className="text-red-600 hover:text-red-700 font-medium text-sm transition-colors"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden divide-y divide-gray-200">
        {items.map((item) => (
          <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getTypeBadge(item.content_type)}
                  {getConfidenceBadge(item.extraction_confidence)}
                  {item.parent_id && (
                    <span
                      className="inline-block px-1.5 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700"
                      title={`Child of ${item.parent_id.slice(0, 8)}...`}
                    >
                      ↳ Child
                    </span>
                  )}
                </div>
                <p className="text-sm font-semibold text-gray-900 mb-1">
                  {item.question}
                </p>
              </div>
            </div>

            {/* Answer */}
            <p className="text-sm text-gray-700 mb-3">
              {truncate(item.answer, 120)}
            </p>

            {/* Tags */}
            {item.tags && (
              <p className="text-xs text-gray-600 mb-3">
                Tags: {item.tags}
              </p>
            )}

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => onEdit(item)}
                className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => onDelete(item)}
                className="flex-1 px-4 py-2 border-2 border-red-600 text-red-600 hover:bg-red-50 text-sm font-medium rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

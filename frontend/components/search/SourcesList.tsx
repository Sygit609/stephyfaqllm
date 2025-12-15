"use client"

/**
 * Sources List Component
 * Displays internal KB sources and web results
 */

import { ExternalLink, FileText, Globe } from "lucide-react"
import type { SourceMatch, WebResult } from "@/lib/api/types"

interface SourcesListProps {
  sources: SourceMatch[]
  webResults?: WebResult[] | null
}

export function SourcesList({ sources, webResults }: SourcesListProps) {
  return (
    <div className="space-y-4">
      {/* Internal Sources */}
      {sources.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-gray-600" />
              <h3 className="font-medium text-gray-900">
                Knowledge Base Sources ({sources.length})
              </h3>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {sources.map((source, idx) => (
              <div key={source.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                {/* Source Header */}
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                        {idx + 1}
                      </span>
                      <span className="text-xs text-gray-500">
                        {source.match_type} · {(source.score * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <h4 className="font-medium text-gray-900 leading-snug">
                      {source.question}
                    </h4>
                  </div>
                </div>

                {/* Answer */}
                <p className="text-gray-700 text-sm leading-relaxed mb-3">
                  {source.answer}
                </p>

                {/* Metadata */}
                <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
                  {/* Category */}
                  {source.category && (
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {source.category}
                    </span>
                  )}

                  {/* Tags */}
                  {source.tags && source.tags.length > 0 && (
                    <div className="flex gap-1">
                      {source.tags.slice(0, 3).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-blue-50 text-blue-700 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {source.tags.length > 3 && (
                        <span className="px-2 py-1 text-gray-400">
                          +{source.tags.length - 3}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Date */}
                  {source.date && (
                    <span>{new Date(source.date).toLocaleDateString()}</span>
                  )}

                  {/* Source Link */}
                  {source.source_url && (
                    <a
                      href={source.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      View source
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Web Results */}
      {webResults && webResults.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-gray-600" />
              <h3 className="font-medium text-gray-900">
                Web Search Results ({webResults.length})
              </h3>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {webResults.map((result, idx) => (
              <div key={idx} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group"
                >
                  <div className="flex items-start gap-3">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-green-100 text-green-700 text-xs font-medium flex-shrink-0">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <h4 className="font-medium text-blue-600 group-hover:text-blue-700 group-hover:underline mb-1">
                        {result.title}
                      </h4>
                      <p className="text-gray-700 text-sm leading-relaxed mb-2">
                        {result.content}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span className="truncate">{result.url}</span>
                        <span>·</span>
                        <span>{(result.score * 100).toFixed(0)}% relevance</span>
                      </div>
                    </div>
                  </div>
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

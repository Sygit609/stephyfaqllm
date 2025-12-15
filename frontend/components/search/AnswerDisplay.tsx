"use client"

/**
 * Answer Display Component
 * Shows the generated answer with metadata
 */

import { Clock, DollarSign, MessageSquare, Zap, Globe, Calendar } from "lucide-react"
import type { AnswerMetadata } from "@/lib/api/types"

interface AnswerDisplayProps {
  query: string
  answer: string
  provider: string
  metadata: AnswerMetadata
  intent: string
  recencyRequired: boolean
  webSearchUsed: boolean
  queryId: string
}

export function AnswerDisplay({
  query,
  answer,
  provider,
  metadata,
  intent,
  recencyRequired,
  webSearchUsed,
  queryId,
}: AnswerDisplayProps) {
  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4">
        <h2 className="text-white font-medium text-lg">Answer</h2>
        <p className="text-blue-100 text-sm mt-1">{query}</p>
      </div>

      {/* Answer Content */}
      <div className="px-6 py-5">
        <div className="prose max-w-none">
          <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
            {answer}
          </p>
        </div>
      </div>

      {/* Metadata Footer */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          {/* Provider */}
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4" />
            <span className="font-medium">{provider.toUpperCase()}</span>
            <span className="text-gray-400">({metadata.model})</span>
          </div>

          {/* Intent */}
          <div className="flex items-center gap-1.5">
            <Zap className="w-4 h-4" />
            <span>{intent}</span>
          </div>

          {/* Web Search */}
          {webSearchUsed && (
            <div className="flex items-center gap-1.5 text-green-600">
              <Globe className="w-4 h-4" />
              <span>Web Search Used</span>
            </div>
          )}

          {/* Recency */}
          {recencyRequired && (
            <div className="flex items-center gap-1.5 text-orange-600">
              <Calendar className="w-4 h-4" />
              <span>Time-sensitive</span>
            </div>
          )}

          {/* Latency */}
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            <span>{(metadata.latency_ms / 1000).toFixed(2)}s</span>
          </div>

          {/* Cost */}
          <div className="flex items-center gap-1.5">
            <DollarSign className="w-4 h-4" />
            <span>${metadata.cost_usd.toFixed(4)}</span>
          </div>

          {/* Tokens */}
          <div className="flex items-center gap-1.5 text-gray-500">
            <span className="text-xs">
              {metadata.tokens_input + metadata.tokens_output} tokens
            </span>
          </div>
        </div>

        {/* Query ID (for debugging) */}
        <div className="mt-2 text-xs text-gray-400">
          ID: {queryId}
        </div>
      </div>
    </div>
  )
}

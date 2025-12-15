"use client"

/**
 * Model Provider Selector Component
 * Toggle between OpenAI and Gemini
 */

import type { ModelProvider } from "@/lib/api/types"

interface ModelSelectorProps {
  selected: ModelProvider
  onChange: (provider: ModelProvider) => void
  disabled?: boolean
}

export function ModelSelector({ selected, onChange, disabled }: ModelSelectorProps) {
  return (
    <div className="inline-flex rounded-lg border border-gray-300 bg-white p-1">
      <button
        type="button"
        onClick={() => onChange("openai")}
        disabled={disabled}
        className={`
          px-4 py-1.5 rounded-md text-sm font-medium transition-colors
          ${selected === "openai"
            ? "bg-blue-600 text-white"
            : "text-gray-700 hover:bg-gray-100"
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        OpenAI
      </button>
      <button
        type="button"
        onClick={() => onChange("gemini")}
        disabled={disabled}
        className={`
          px-4 py-1.5 rounded-md text-sm font-medium transition-colors
          ${selected === "gemini"
            ? "bg-blue-600 text-white"
            : "text-gray-700 hover:bg-gray-100"
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        Gemini
      </button>
    </div>
  )
}

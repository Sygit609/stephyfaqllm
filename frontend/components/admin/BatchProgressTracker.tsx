"use client"

/**
 * Batch Progress Tracker Component
 * Shows extraction progress with statistics
 */

interface Props {
  total: number
  current: number
  successCount: number
  failedCount: number
}

export default function BatchProgressTracker({ total, current, successCount, failedCount }: Props) {
  const percentage = Math.round((current / total) * 100)
  const remaining = total - current

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-blue-900">
            Extracting Screenshots
          </h3>
          <span className="text-sm text-blue-700 font-medium">
            {current}/{total} ({percentage}%)
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-blue-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-blue-600 h-full transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-white rounded-lg p-3">
            <div className="text-2xl font-bold text-green-600">{successCount}</div>
            <div className="text-xs text-gray-600 mt-1">Success</div>
          </div>
          <div className="bg-white rounded-lg p-3">
            <div className="text-2xl font-bold text-red-600">{failedCount}</div>
            <div className="text-xs text-gray-600 mt-1">Failed</div>
          </div>
          <div className="bg-white rounded-lg p-3">
            <div className="text-2xl font-bold text-gray-600">{remaining}</div>
            <div className="text-xs text-gray-600 mt-1">Remaining</div>
          </div>
        </div>

        {/* Status Message */}
        <p className="text-sm text-blue-700 text-center">
          {current < total ? (
            <>Processing screenshots using Gemini Vision with GPT-4 fallback...</>
          ) : (
            <>Extraction complete! Review your results below.</>
          )}
        </p>
      </div>
    </div>
  )
}

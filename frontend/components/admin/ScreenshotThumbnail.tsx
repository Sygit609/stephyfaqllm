"use client"

/**
 * Screenshot Thumbnail Component
 * Displays a single screenshot with URL input and status
 */

import type { BatchUpload } from "@/lib/api/types"

interface Props {
  upload: BatchUpload
  onRemove: () => void
  onUrlChange: (url: string) => void
}

export default function ScreenshotThumbnail({ upload, onRemove, onUrlChange }: Props) {
  const getStatusColor = () => {
    switch (upload.status) {
      case 'pending':
        return 'border-gray-300 bg-white'
      case 'extracting':
        return 'border-blue-500 bg-blue-50'
      case 'success':
        return 'border-green-500 bg-green-50'
      case 'failed':
        return 'border-red-500 bg-red-50'
      default:
        return 'border-gray-300 bg-white'
    }
  }

  const getStatusBadge = () => {
    switch (upload.status) {
      case 'pending':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
            Pending
          </span>
        )
      case 'extracting':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
            <svg className="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Extracting
          </span>
        )
      case 'success':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            Success
          </span>
        )
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            Failed
          </span>
        )
    }
  }

  return (
    <div className={`border-2 rounded-lg p-3 transition-all ${getStatusColor()}`}>
      {/* Status Badge and Remove Button */}
      <div className="flex items-center justify-between mb-2">
        {getStatusBadge()}
        <button
          onClick={onRemove}
          className="text-gray-400 hover:text-red-600 transition-colors"
          title="Remove"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Image Preview */}
      <div className="relative aspect-square mb-2 rounded overflow-hidden bg-gray-100">
        {upload.preview ? (
          <img
            src={upload.preview}
            alt="Screenshot preview"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <svg
              className="w-12 h-12 text-gray-400 animate-pulse"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* File Info */}
      <p className="text-xs text-gray-600 mb-2 truncate" title={upload.file.name}>
        {upload.file.name}
      </p>
      <p className="text-xs text-gray-500 mb-2">
        {(upload.file.size / 1024).toFixed(1)} KB
      </p>

      {/* URL Input */}
      <input
        type="url"
        value={upload.sourceUrl}
        onChange={(e) => onUrlChange(e.target.value)}
        placeholder="Facebook post URL..."
        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        disabled={upload.status === 'extracting'}
      />

      {/* Error Message */}
      {upload.error && (
        <p className="text-xs text-red-600 mt-2">
          {upload.error}
        </p>
      )}

      {/* Success Info */}
      {upload.status === 'success' && upload.extractionResult && (
        <p className="text-xs text-green-600 mt-2">
          {upload.extractionResult.qa_pairs.length} Q&A pair(s) extracted
        </p>
      )}
    </div>
  )
}

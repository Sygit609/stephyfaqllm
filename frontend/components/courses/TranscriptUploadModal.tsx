"use client"

/**
 * Transcript Upload Modal
 * Upload .srt or .vtt transcript files
 */

import { useState } from "react"
import { uploadTranscript } from "@/lib/api/courses"

interface Props {
  lessonId: string
  lessonName: string
  onClose: () => void
  onSuccess: () => void
}

export default function TranscriptUploadModal({
  lessonId,
  lessonName,
  onClose,
  onSuccess
}: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{
    segments_created: number
    format: string
  } | null>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile && (droppedFile.name.endsWith('.srt') || droppedFile.name.endsWith('.vtt'))) {
      setFile(droppedFile)
      setError(null)
    } else {
      setError("Please upload a .srt or .vtt file")
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setIsUploading(true)
    setError(null)

    try {
      const response = await uploadTranscript(lessonId, file)
      setResult(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Upload failed")
    } finally {
      setIsUploading(false)
    }
  }

  const handleFinish = () => {
    onSuccess()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Upload Transcript</h2>
            <p className="text-sm text-gray-600 mt-1">{lessonName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!result ? (
            <>
              {/* Error */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
                  {error}
                </div>
              )}

              {/* File Selection */}
              {file ? (
                <div className="border-2 border-green-500 bg-green-50 rounded-lg p-6 mb-4">
                  <div className="flex items-center gap-3">
                    <svg className="w-10 h-10 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                      <p className="text-xs text-gray-600">
                        {(file.size / 1024).toFixed(1)} KB · {file.name.endsWith('.srt') ? 'SRT' : 'VTT'} format
                      </p>
                    </div>
                    <button
                      onClick={() => setFile(null)}
                      className="flex-shrink-0 text-gray-400 hover:text-gray-600"
                      title="Remove file"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center mb-6">
                  <input
                    type="file"
                    accept=".srt,.vtt"
                    onChange={handleFileInput}
                    className="hidden"
                    id="transcript-file"
                  />
                  <label
                    htmlFor="transcript-file"
                    className="inline-block px-8 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 cursor-pointer font-medium text-lg"
                  >
                    Choose Transcript File
                  </label>
                  <p className="text-sm text-gray-500 mt-3">
                    .srt or .vtt format
                  </p>
                </div>
              )}

              {/* Info */}
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <p className="text-sm text-gray-700">
                  <strong>Supported formats:</strong> .srt (SubRip) and .vtt (WebVTT)
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  The transcript will be parsed into searchable segments with timestamps.
                  Each segment will be embedded for semantic search.
                </p>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 mt-6">
                <button
                  onClick={onClose}
                  className="px-4 py-2 border-2 border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg font-medium"
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? "Uploading..." : "Upload & Process"}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Success Result */}
              <div className="text-center py-8">
                <svg
                  className="mx-auto h-16 w-16 text-green-500 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <h3 className="text-xl font-bold text-gray-900 mb-2">Upload Successful!</h3>
                <p className="text-gray-600 mb-6">
                  Created <strong>{result.segments_created} transcript segments</strong> from {result.format.toUpperCase()} file
                </p>

                <div className="bg-green-50 rounded-lg p-4 border border-green-200 mb-6">
                  <p className="text-sm text-gray-700">
                    ✓ Transcript parsed and segmented<br />
                    ✓ Dual embeddings generated (OpenAI + Gemini)<br />
                    ✓ Segments are now searchable with timestamp citations
                  </p>
                </div>

                <button
                  onClick={handleFinish}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium"
                >
                  Done
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

"use client"

/**
 * Batch Screenshot Uploader Component
 * Supports clipboard paste, drag-drop, and file input for multiple screenshots
 */

import { useState, useRef, useEffect } from "react"
import { extractScreenshot, fileToBase64 } from "@/lib/api/admin"
import { extractImagesFromClipboard } from "@/lib/utils/clipboard"
import { validateFiles } from "@/lib/utils/file-validation"
import ScreenshotThumbnail from "./ScreenshotThumbnail"
import BatchProgressTracker from "./BatchProgressTracker"
import type { BatchUpload, ExtractScreenshotResponse } from "@/lib/api/types"

interface Props {
  onExtractionComplete: (uploads: BatchUpload[]) => void
}

export default function BatchScreenshotUploader({ onExtractionComplete }: Props) {
  const [uploads, setUploads] = useState<BatchUpload[]>([])
  const [isExtracting, setIsExtracting] = useState(false)
  const [currentExtractionIndex, setCurrentExtractionIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Clipboard paste handler
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      e.preventDefault()
      const files = extractImagesFromClipboard(e)
      if (files.length > 0) {
        addFiles(files)
      }
    }

    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [uploads])

  const addFiles = async (files: File[]) => {
    const { valid, invalid } = validateFiles(files)

    if (invalid.length > 0) {
      setError(`${invalid.length} file(s) rejected: ${invalid[0].error}`)
      setTimeout(() => setError(null), 5000)
    }

    if (valid.length === 0) return

    // Generate previews synchronously before adding to state
    const newUploads: BatchUpload[] = await Promise.all(
      valid.map(async (file, index) => {
        const id = `${Date.now()}-${index}`

        // Generate preview immediately
        const preview = await new Promise<string>((resolve) => {
          const reader = new FileReader()
          reader.onload = (e) => resolve(e.target?.result as string)
          reader.readAsDataURL(file)
        })

        return {
          id,
          file,
          preview,
          sourceUrl: '',
          status: 'pending' as const,
          order: uploads.length + index,
        }
      })
    )

    setUploads(prev => [...prev, ...newUploads])
  }

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      addFiles(files)
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      addFiles(Array.from(files))
    }
  }

  const removeUpload = (id: string) => {
    setUploads(prev => prev.filter(u => u.id !== id))
  }

  const updateSourceUrl = (id: string, url: string) => {
    setUploads(prev =>
      prev.map(u => (u.id === id ? { ...u, sourceUrl: url } : u))
    )
  }

  const extractAllSequentially = async () => {
    // Validate all have URLs
    const missingUrls = uploads.filter(u => !u.sourceUrl.trim())
    if (missingUrls.length > 0) {
      setError(`Please add Facebook URLs to all ${missingUrls.length} screenshot(s)`)
      return
    }

    setIsExtracting(true)
    setError(null)
    const updatedUploads = [...uploads]

    for (let i = 0; i < updatedUploads.length; i++) {
      const upload = updatedUploads[i]

      // Update status to extracting
      upload.status = 'extracting'
      setUploads([...updatedUploads])
      setCurrentExtractionIndex(i + 1)

      try {
        const base64Image = await fileToBase64(upload.file)
        const result: ExtractScreenshotResponse = await extractScreenshot({
          image_data: base64Image,
          source_url: upload.sourceUrl.trim(),
          provider: "gemini",
          use_fallback: true,
        })

        upload.status = 'success'
        upload.extractionResult = result
      } catch (error: any) {
        upload.status = 'failed'
        upload.error = error.response?.data?.detail || error.message || 'Extraction failed'
      }

      setUploads([...updatedUploads])

      // Add delay to prevent rate limiting
      if (i < updatedUploads.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }

    setIsExtracting(false)

    // Pass successful uploads to parent
    const successfulUploads = updatedUploads.filter(u => u.status === 'success')
    if (successfulUploads.length > 0) {
      onExtractionComplete(updatedUploads)
    } else {
      setError('All extractions failed. Please retry or check your screenshots.')
    }
  }

  const successCount = uploads.filter(u => u.status === 'success').length
  const failedCount = uploads.filter(u => u.status === 'failed').length
  const canExtract = uploads.length > 0 && !isExtracting && uploads.every(u => u.sourceUrl.trim())

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Upload Screenshots</h2>
        <p className="text-gray-600 mt-1">
          Paste screenshots with <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">Cmd+V</kbd> or{' '}
          <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm font-mono">Ctrl+V</kbd>,
          or drag & drop multiple files
        </p>
      </div>

      {/* Upload Area */}
      {uploads.length === 0 && (
        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-purple-500 bg-purple-50'
              : 'border-gray-300 hover:border-gray-400 bg-gray-50'
          }`}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={handleFileInputChange}
          />

          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-4"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="text-gray-700 font-medium mb-2">
            Paste screenshots, drag & drop, or click to browse
          </p>
          <p className="text-gray-500 text-sm">
            Supports JPG, PNG (max 10MB each)
          </p>
        </div>
      )}

      {/* Thumbnail Grid */}
      {uploads.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {uploads.length} screenshot(s) uploaded
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              disabled={isExtracting}
            >
              + Add More
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleFileInputChange}
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {uploads.map((upload) => (
              <ScreenshotThumbnail
                key={upload.id}
                upload={upload}
                onRemove={() => removeUpload(upload.id)}
                onUrlChange={(url) => updateSourceUrl(upload.id, url)}
              />
            ))}
          </div>
        </>
      )}

      {/* Progress Tracker */}
      {isExtracting && (
        <BatchProgressTracker
          total={uploads.length}
          current={currentExtractionIndex}
          successCount={successCount}
          failedCount={failedCount}
        />
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Extract Button */}
      {uploads.length > 0 && (
        <button
          onClick={extractAllSequentially}
          disabled={!canExtract}
          className={`w-full py-4 px-6 rounded-lg font-semibold text-white transition-all ${
            !canExtract
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-purple-600 hover:bg-purple-700 hover:shadow-lg'
          }`}
        >
          {isExtracting ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Extracting {currentExtractionIndex}/{uploads.length}...
            </span>
          ) : (
            `Extract All ${uploads.length} Screenshot${uploads.length !== 1 ? 's' : ''}`
          )}
        </button>
      )}

      <p className="text-gray-500 text-sm text-center">
        Gemini Vision (free) with GPT-4 Vision fallback • ~$0.02-0.05 per screenshot
      </p>
    </div>
  )
}

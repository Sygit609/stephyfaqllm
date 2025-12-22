"use client"

/**
 * Screenshot Uploader Component
 * Handles drag-drop file upload and extraction
 */

import { useState, useRef } from "react"
import { extractScreenshot, fileToBase64 } from "@/lib/api/admin"
import type { ExtractScreenshotResponse } from "@/lib/api/types"

interface Props {
  onExtractionComplete: (
    result: ExtractScreenshotResponse,
    sourceUrl: string,
    imageDataUrl: string
  ) => void
}

export default function ScreenshotUploader({ onExtractionComplete }: Props) {
  const [sourceUrl, setSourceUrl] = useState<string>("")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [isExtracting, setIsExtracting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (file: File) => {
    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file (JPG, PNG, etc.)")
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError("Image file is too large (max 10MB)")
      return
    }

    setSelectedFile(file)
    setError(null)

    // Create preview
    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)
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

    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleExtract = async () => {
    if (!selectedFile || !sourceUrl.trim()) {
      setError("Please select an image and enter the source URL")
      return
    }

    setIsExtracting(true)
    setError(null)

    try {
      // Convert image to base64
      const base64Image = await fileToBase64(selectedFile)

      // Call extraction API
      const result = await extractScreenshot({
        image_data: base64Image,
        source_url: sourceUrl.trim(),
        provider: "gemini", // Try Gemini first (free)
        use_fallback: true, // Enable GPT-4 fallback
      })

      // Pass result to parent
      onExtractionComplete(result, sourceUrl.trim(), imagePreview!)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Extraction failed")
    } finally {
      setIsExtracting(false)
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Upload Screenshot</h2>
      <p className="text-gray-600">
        Upload a Facebook post screenshot and we'll extract the Q&A pairs automatically
      </p>

      {/* File Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? "border-purple-500 bg-purple-50"
            : imagePreview
            ? "border-green-500 bg-green-50"
            : "border-gray-300 hover:border-gray-400 bg-gray-50"
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
          className="hidden"
          onChange={handleFileInputChange}
        />

        {imagePreview ? (
          <div className="space-y-4">
            <img
              src={imagePreview}
              alt="Preview"
              className="max-h-96 mx-auto rounded-lg shadow-lg"
            />
            <p className="text-green-700 font-medium">
              ✓ {selectedFile?.name} ({(selectedFile?.size! / 1024).toFixed(1)} KB)
            </p>
            <button
              type="button"
              className="text-purple-600 hover:text-purple-700 underline text-sm"
              onClick={(e) => {
                e.stopPropagation()
                setSelectedFile(null)
                setImagePreview(null)
              }}
            >
              Choose different image
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
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
            <p className="text-gray-700 font-medium">
              Drag and drop your screenshot here, or click to browse
            </p>
            <p className="text-gray-500 text-sm">Supports JPG, PNG (max 10MB)</p>
          </div>
        )}
      </div>

      {/* Source URL Input */}
      <div>
        <label htmlFor="source_url" className="block text-sm font-medium text-gray-700 mb-2">
          Facebook Post URL
        </label>
        <input
          id="source_url"
          type="url"
          value={sourceUrl}
          onChange={(e) => setSourceUrl(e.target.value)}
          placeholder="https://facebook.com/groups/..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
        <p className="text-gray-500 text-sm mt-1">
          The URL will be saved as a reference source
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Extract Button */}
      <button
        onClick={handleExtract}
        disabled={!selectedFile || !sourceUrl.trim() || isExtracting}
        className={`w-full py-4 px-6 rounded-lg font-semibold text-white transition-all ${
          !selectedFile || !sourceUrl.trim() || isExtracting
            ? "bg-gray-300 cursor-not-allowed"
            : "bg-purple-600 hover:bg-purple-700 hover:shadow-lg"
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
            Extracting Q&A pairs...
          </span>
        ) : (
          "Extract Q&A Pairs"
        )}
      </button>

      <p className="text-gray-500 text-sm text-center">
        We'll use Gemini Vision API (free) with GPT-4 Vision fallback for best results
      </p>
    </div>
  )
}

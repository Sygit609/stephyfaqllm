"use client"

/**
 * Admin Import Page
 * 3-step workflow: Upload → Preview/Edit → Save
 */

import { useState } from "react"
import Link from "next/link"
import ScreenshotUploader from "@/components/admin/ScreenshotUploader"
import ExtractionPreview from "@/components/admin/ExtractionPreview"
import SaveConfirmation from "@/components/admin/SaveConfirmation"
import type { ExtractScreenshotResponse, SaveContentResponse } from "@/lib/api/types"

type Step = "upload" | "preview" | "saved"

export default function AdminImportPage() {
  const [currentStep, setCurrentStep] = useState<Step>("upload")
  const [extractionResult, setExtractionResult] = useState<ExtractScreenshotResponse | null>(null)
  const [saveResult, setSaveResult] = useState<SaveContentResponse | null>(null)
  const [sourceUrl, setSourceUrl] = useState<string>("")
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)

  const handleExtractionComplete = (
    result: ExtractScreenshotResponse,
    url: string,
    imageDataUrl: string
  ) => {
    setExtractionResult(result)
    setSourceUrl(url)
    setUploadedImage(imageDataUrl)
    setCurrentStep("preview")
  }

  const handleSaveComplete = (result: SaveContentResponse) => {
    setSaveResult(result)
    setCurrentStep("saved")
  }

  const handleStartOver = () => {
    setCurrentStep("upload")
    setExtractionResult(null)
    setSaveResult(null)
    setSourceUrl("")
    setUploadedImage(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-purple-600 hover:text-purple-700 font-medium mb-4 inline-block"
          >
            ← Back to Search
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Import Content</h1>
          <p className="text-gray-600 mt-2">
            Upload Facebook screenshots to extract Q&A pairs automatically
          </p>
        </div>

        {/* Progress Steps */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            {/* Step 1: Upload */}
            <div className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  currentStep === "upload"
                    ? "bg-purple-600 text-white"
                    : currentStep === "preview" || currentStep === "saved"
                    ? "bg-green-500 text-white"
                    : "bg-gray-200 text-gray-600"
                }`}
              >
                {currentStep === "preview" || currentStep === "saved" ? "✓" : "1"}
              </div>
              <span
                className={`ml-3 font-medium ${
                  currentStep === "upload" ? "text-purple-600" : "text-gray-700"
                }`}
              >
                Upload Screenshot
              </span>
            </div>

            <div className="flex-1 h-1 mx-4 bg-gray-200">
              <div
                className={`h-full transition-all ${
                  currentStep === "preview" || currentStep === "saved"
                    ? "bg-green-500 w-full"
                    : "bg-gray-200 w-0"
                }`}
              />
            </div>

            {/* Step 2: Preview */}
            <div className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  currentStep === "preview"
                    ? "bg-purple-600 text-white"
                    : currentStep === "saved"
                    ? "bg-green-500 text-white"
                    : "bg-gray-200 text-gray-600"
                }`}
              >
                {currentStep === "saved" ? "✓" : "2"}
              </div>
              <span
                className={`ml-3 font-medium ${
                  currentStep === "preview" ? "text-purple-600" : "text-gray-700"
                }`}
              >
                Review & Edit
              </span>
            </div>

            <div className="flex-1 h-1 mx-4 bg-gray-200">
              <div
                className={`h-full transition-all ${
                  currentStep === "saved" ? "bg-green-500 w-full" : "bg-gray-200 w-0"
                }`}
              />
            </div>

            {/* Step 3: Saved */}
            <div className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  currentStep === "saved"
                    ? "bg-green-500 text-white"
                    : "bg-gray-200 text-gray-600"
                }`}
              >
                {currentStep === "saved" ? "✓" : "3"}
              </div>
              <span
                className={`ml-3 font-medium ${
                  currentStep === "saved" ? "text-green-600" : "text-gray-700"
                }`}
              >
                Saved
              </span>
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          {currentStep === "upload" && (
            <ScreenshotUploader onExtractionComplete={handleExtractionComplete} />
          )}

          {currentStep === "preview" && extractionResult && (
            <ExtractionPreview
              extractionResult={extractionResult}
              sourceUrl={sourceUrl}
              uploadedImage={uploadedImage}
              onSaveComplete={handleSaveComplete}
              onCancel={handleStartOver}
            />
          )}

          {currentStep === "saved" && saveResult && (
            <SaveConfirmation saveResult={saveResult} onStartOver={handleStartOver} />
          )}
        </div>
      </div>
    </div>
  )
}

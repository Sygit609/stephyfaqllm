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
import BatchScreenshotUploader from "@/components/admin/BatchScreenshotUploader"
import BatchExtractionPreview from "@/components/admin/BatchExtractionPreview"
import { TextImporter } from "@/components/admin/TextImporter"
import TextImportPreview from "@/components/admin/TextImportPreview"
import { ThreadParserImporter } from "@/components/admin/ThreadParserImporter"
import ThreadParserPreview from "@/components/admin/ThreadParserPreview"
import { saveContent } from "@/lib/api/admin"
import type {
  ExtractScreenshotResponse,
  SaveContentResponse,
  BatchUpload,
  SaveContentRequest,
  ParseThreadResponse
} from "@/lib/api/types"

type Step = "upload" | "preview" | "saved"
type ImportMethod = "screenshot" | "text" | "thread-parser"

export default function AdminImportPage() {
  const [currentStep, setCurrentStep] = useState<Step>("upload")
  const [mode, setMode] = useState<"single" | "batch">("single")
  const [importMethod, setImportMethod] = useState<ImportMethod>("screenshot")

  // Single mode state
  const [extractionResult, setExtractionResult] = useState<ExtractScreenshotResponse | null>(null)
  const [saveResult, setSaveResult] = useState<SaveContentResponse | null>(null)
  const [sourceUrl, setSourceUrl] = useState<string>("")
  const [uploadedImage, setUploadedImage] = useState<string | null>(null)

  // Batch mode state
  const [batchUploads, setBatchUploads] = useState<BatchUpload[]>([])
  const [batchSaveResults, setBatchSaveResults] = useState<SaveContentResponse[]>([])

  // Text import state
  const [textImportData, setTextImportData] = useState<SaveContentRequest | null>(null)

  // Thread parser state
  const [threadParserData, setThreadParserData] = useState<ParseThreadResponse | null>(null)

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

  const handleBatchExtractionComplete = (uploads: BatchUpload[]) => {
    setBatchUploads(uploads)
    setCurrentStep("preview")
  }

  const handleTextImportComplete = (data: SaveContentRequest) => {
    setTextImportData(data)
    setCurrentStep("preview")
  }

  const handleThreadParserComplete = (data: ParseThreadResponse) => {
    setThreadParserData(data)
    setCurrentStep("preview")
  }

  const handleSaveComplete = (result: SaveContentResponse) => {
    setSaveResult(result)
    setCurrentStep("saved")
  }

  const handleBatchSave = async (uploads: BatchUpload[]) => {
    const results: SaveContentResponse[] = []

    for (const upload of uploads) {
      if (upload.status === 'success' && upload.extractionResult) {
        try {
          const result = await saveContent({
            qa_pairs: upload.extractionResult.qa_pairs,
            media_url: upload.sourceUrl || 'screenshot-' + upload.id, // Use source URL as media reference
            source_url: upload.sourceUrl,
            extracted_by: upload.extractionResult.metadata.model,
            confidence: upload.extractionResult.confidence,
            raw_extraction: upload.extractionResult.metadata,
            content_type: "screenshot"
          })
          results.push(result)
        } catch (error) {
          console.error(`Failed to save ${upload.sourceUrl}:`, error)
        }
      }
    }

    setBatchSaveResults(results)
    setCurrentStep("saved")
  }

  const handleStartOver = () => {
    setCurrentStep("upload")
    setMode("single")
    setImportMethod("screenshot")
    setExtractionResult(null)
    setSaveResult(null)
    setSourceUrl("")
    setUploadedImage(null)
    setBatchUploads([])
    setBatchSaveResults([])
    setTextImportData(null)
    setThreadParserData(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link
              href="/"
              className="text-purple-600 hover:text-purple-700 font-medium inline-block"
            >
              ← Back to Search
            </Link>
            {currentStep === "upload" && (
              <div className="flex flex-col gap-2">
                {/* Import Method Toggle */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setImportMethod("screenshot")}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      importMethod === "screenshot"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    }`}
                  >
                    📸 Screenshot
                  </button>
                  <button
                    onClick={() => setImportMethod("text")}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      importMethod === "text"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    }`}
                  >
                    📝 Text/Paste
                  </button>
                  <button
                    onClick={() => setImportMethod("thread-parser")}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      importMethod === "thread-parser"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    }`}
                  >
                    🧵 Thread Parser
                  </button>
                </div>

                {/* Screenshot Mode Toggle (only show for screenshot import) */}
                {importMethod === "screenshot" && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setMode("single")}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        mode === "single"
                          ? "bg-purple-600 text-white"
                          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                    >
                      Single Upload
                    </button>
                    <button
                      onClick={() => setMode("batch")}
                      className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        mode === "batch"
                          ? "bg-purple-600 text-white"
                          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                    >
                      Batch Upload
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Import Content</h1>
          <p className="text-gray-600 mt-2">
            {importMethod === "thread-parser"
              ? "Paste entire Facebook threads for AI-powered parsing and classification"
              : importMethod === "text"
              ? "Paste Facebook post content directly for faster import"
              : mode === "batch"
              ? "Upload multiple Facebook screenshots at once for bulk extraction"
              : "Upload Facebook screenshots to extract Q&A pairs automatically"}
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
          {currentStep === "upload" && importMethod === "text" && (
            <TextImporter onComplete={handleTextImportComplete} />
          )}

          {currentStep === "upload" && importMethod === "thread-parser" && (
            <ThreadParserImporter onComplete={handleThreadParserComplete} />
          )}

          {currentStep === "upload" && importMethod === "screenshot" && mode === "single" && (
            <ScreenshotUploader onExtractionComplete={handleExtractionComplete} />
          )}

          {currentStep === "upload" && importMethod === "screenshot" && mode === "batch" && (
            <BatchScreenshotUploader onExtractionComplete={handleBatchExtractionComplete} />
          )}

          {currentStep === "preview" && mode === "single" && extractionResult && (
            <ExtractionPreview
              extractionResult={extractionResult}
              sourceUrl={sourceUrl}
              uploadedImage={uploadedImage}
              onSaveComplete={handleSaveComplete}
              onCancel={handleStartOver}
            />
          )}

          {currentStep === "preview" && mode === "batch" && batchUploads.length > 0 && (
            <BatchExtractionPreview
              uploads={batchUploads}
              onCancel={handleStartOver}
              onSave={handleBatchSave}
            />
          )}

          {currentStep === "preview" && importMethod === "text" && textImportData && (
            <TextImportPreview
              data={textImportData}
              onSaveComplete={handleSaveComplete}
              onCancel={handleStartOver}
            />
          )}

          {currentStep === "preview" && importMethod === "thread-parser" && threadParserData && (
            <ThreadParserPreview
              data={threadParserData}
              onSaveComplete={handleSaveComplete}
              onCancel={handleStartOver}
            />
          )}

          {currentStep === "saved" && mode === "single" && saveResult && (
            <SaveConfirmation saveResult={saveResult} onStartOver={handleStartOver} />
          )}

          {currentStep === "saved" && mode === "batch" && batchSaveResults.length > 0 && (
            <SaveConfirmation
              saveResult={batchSaveResults[0]}
              batchResults={batchSaveResults}
              onStartOver={handleStartOver}
            />
          )}
        </div>
      </div>
    </div>
  )
}

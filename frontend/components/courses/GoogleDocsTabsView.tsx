"use client"

/**
 * Google Docs-style Tabs View
 * Horizontal tab layout similar to Google Docs
 */

import { useState, useRef, useEffect } from "react"
import type { CourseTreeNode } from "@/lib/api/types"
import { deleteFolder, createSubfolder, uploadTranscript, updateFolder } from "@/lib/api/courses"

interface Props {
  tree: CourseTreeNode
  onRefresh: () => void
  onCreateModule?: () => void
}

export default function GoogleDocsTabsView({ tree, onRefresh, onCreateModule }: Props) {
  const [selectedTab, setSelectedTab] = useState<string | null>(null)
  const [expandedTabs, setExpandedTabs] = useState<Set<string>>(new Set())
  const [showMenu, setShowMenu] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [currentUploadFolderId, setCurrentUploadFolderId] = useState<string | null>(null)
  const [isEditingMetadata, setIsEditingMetadata] = useState(false)
  const [videoUrl, setVideoUrl] = useState("")
  const [description, setDescription] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load metadata when tab is selected
  useEffect(() => {
    if (selectedTab) {
      const node = findNodeById(tree, selectedTab)
      if (node) {
        setVideoUrl(node.metadata?.media_url || "")
        setDescription(node.description || "")
        setIsEditingMetadata(false)
      }
    }
  }, [selectedTab, tree])

  const handleAddSubtab = async (parentId: string, parentNode: CourseTreeNode) => {
    try {
      const subfolderCount = parentNode.children.filter(c => !c.is_leaf).length
      const newName = `Tab ${subfolderCount + 1}`

      await createSubfolder(parentId, {
        name: newName,
        description: "",
        thumbnail_url: null
      })
      onRefresh()
    } catch (err: any) {
      alert(err.message || "Failed to create subtab")
    }
    setShowMenu(null)
  }

  const handleDelete = async (folderId: string) => {
    if (!confirm("Delete this tab? This will also delete all nested tabs.")) return

    try {
      await deleteFolder(folderId)
      onRefresh()
    } catch (err) {
      alert("Failed to delete")
    }
    setShowMenu(null)
  }

  const handleDeleteTranscript = async (segmentId: string) => {
    if (!confirm("Delete this transcript segment?")) return

    try {
      await deleteFolder(segmentId)  // Segments are also knowledge_items, same endpoint
      onRefresh()
    } catch (err) {
      alert("Failed to delete transcript")
    }
  }

  const handleSaveMetadata = async () => {
    if (!selectedTab) return

    try {
      await updateFolder(selectedTab, {
        video_url: videoUrl || null,
        description: description || null
      })
      setIsEditingMetadata(false)
      onRefresh()
    } catch (err) {
      alert("Failed to save metadata")
    }
  }

  const handleUpload = (folderId: string) => {
    setCurrentUploadFolderId(folderId)
    setShowMenu(null)
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!currentUploadFolderId) return

    await processFileUpload(file)
  }

  const handleDrop = async (e: React.DragEvent, folderId: string) => {
    e.preventDefault()
    e.stopPropagation()

    const file = e.dataTransfer.files[0]
    if (!file) return

    // Check file type
    if (!file.name.endsWith('.srt') && !file.name.endsWith('.vtt')) {
      setUploadError("Please upload a .srt or .vtt file")
      return
    }

    // Set folder ID and upload directly
    setIsUploading(true)
    setUploadError(null)

    try {
      await uploadTranscript(folderId, file)
      onRefresh()
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || err.message || "Upload failed")
    } finally {
      setIsUploading(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const processFileUpload = async (file: File) => {
    if (!currentUploadFolderId) return

    setIsUploading(true)
    setUploadError(null)

    try {
      await uploadTranscript(currentUploadFolderId, file)
      onRefresh()
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || err.message || "Upload failed")
    } finally {
      setIsUploading(false)
      setCurrentUploadFolderId(null)
    }
  }

  const renderTab = (node: CourseTreeNode, level: number = 0) => {
    // NEVER render transcript segments in sidebar (they should only appear in content area)
    if (node.is_leaf || node.metadata?.timecode_start != null) {
      return null
    }

    const isSelected = selectedTab === node.id
    const isExpanded = expandedTabs.has(node.id)
    const hasChildren = node.children.filter(c => !c.is_leaf && c.metadata?.timecode_start == null).length > 0
    const canAddSubtab = node.hierarchy_level < 4

    return (
      <div key={node.id} className={`${level > 0 ? 'ml-8' : ''}`}>
        {/* Tab Row */}
        <div
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg group relative
            ${isSelected ? 'bg-blue-100' : 'hover:bg-gray-100'}
            ${level === 0 ? 'font-medium' : ''}
          `}
        >
          {/* Expand/Collapse Icon */}
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                const next = new Set(expandedTabs)
                if (next.has(node.id)) {
                  next.delete(node.id)
                } else {
                  next.add(node.id)
                }
                setExpandedTabs(next)
              }}
              className="flex-shrink-0"
            >
              <svg
                className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}
          {!hasChildren && <div className="w-4" />}

          {/* Tab Icon */}
          <div onClick={() => setSelectedTab(node.id)} className="flex items-center gap-2 flex-1 cursor-pointer">
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>

            {/* Tab Name */}
            <span className="flex-1">{node.name}</span>
          </div>

          {/* 3-dot Menu */}
          <button
            onClick={(e) => {
              e.stopPropagation()
              setShowMenu(showMenu === node.id ? null : node.id)
            }}
            className="p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-200 rounded"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
            </svg>
          </button>

          {/* Dropdown Menu */}
          {showMenu === node.id && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowMenu(null)} />
              <div className="absolute right-0 top-10 z-50 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                {canAddSubtab && (
                  <button
                    onClick={() => handleAddSubtab(node.id, node)}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add subtab
                  </button>
                )}
                <button
                  onClick={() => handleUpload(node.id)}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload transcript
                </button>
                <button
                  onClick={() => alert("Duplicate coming soon")}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Duplicate
                </button>
                <button
                  onClick={() => alert("Rename coming soon")}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Rename
                </button>
                <div className="border-t border-gray-200 my-1"></div>
                <button
                  onClick={() => handleDelete(node.id)}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 text-red-600 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Delete
                </button>
              </div>
            </>
          )}
        </div>

        {/* Nested Children (when expanded) */}
        {isExpanded && hasChildren && (
          <div className="mt-1">
            {node.children
              .filter(c => !c.is_leaf && c.metadata?.timecode_start == null)
              .map(child => renderTab(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      {/* Sidebar with tabs */}
      <div className="flex">
        {/* Left sidebar with tabs */}
        <div className="w-80 border-r border-gray-200 p-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          {/* Header with + button */}
          <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700">Modules</h3>
            {onCreateModule && (
              <button
                onClick={onCreateModule}
                className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                title="Add new module"
              >
                <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            )}
          </div>

          {/* Tabs list */}
          <div className="space-y-1">
            {tree.children
              .filter(c => !c.is_leaf && c.metadata?.timecode_start == null)
              .map(child => renderTab(child))}
          </div>
        </div>

        {/* Right content area */}
        <div className="flex-1 p-8">
          {selectedTab ? (
            <div>
              <h2 className="text-xl font-semibold mb-2">
                {findNodeById(tree, selectedTab)?.name || 'Tab Content'}
              </h2>
              <p className="text-gray-600 mb-6">
                Add transcripts to this {findNodeById(tree, selectedTab)?.type || 'folder'}
              </p>

              {/* Video URL and Description Metadata */}
              <div className="mb-6 space-y-4">
                {/* Video URL Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Video URL
                  </label>
                  {isEditingMetadata ? (
                    <input
                      type="url"
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                      placeholder="https://www.youtube.com/watch?v=..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  ) : (
                    <div className="flex items-center gap-2">
                      {videoUrl ? (
                        <a
                          href={videoUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-purple-600 hover:text-purple-700 hover:underline text-sm"
                        >
                          {videoUrl}
                        </a>
                      ) : (
                        <span className="text-gray-400 text-sm">No video URL set</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Description Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  {isEditingMetadata ? (
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Add description, links, and additional information..."
                      rows={4}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  ) : (
                    <div className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded-lg border border-gray-200">
                      {description || <span className="text-gray-400">No description set</span>}
                    </div>
                  )}
                </div>

                {/* Edit/Save Buttons */}
                <div className="flex gap-2">
                  {isEditingMetadata ? (
                    <>
                      <button
                        onClick={handleSaveMetadata}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setIsEditingMetadata(false)
                          // Reset to original values
                          const node = findNodeById(tree, selectedTab)
                          if (node) {
                            setVideoUrl(node.metadata?.media_url || "")
                            setDescription(node.description || "")
                          }
                        }}
                        className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm font-medium"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setIsEditingMetadata(true)}
                      className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm font-medium"
                    >
                      Edit Metadata
                    </button>
                  )}
                </div>
              </div>

              {/* Transcript Segments List */}
              {(() => {
                const node = findNodeById(tree, selectedTab)
                const transcripts = node?.children.filter(c => c.is_leaf || c.metadata?.timecode_start != null) || []

                return transcripts.length > 0 ? (
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">
                      Transcript Segments ({transcripts.length})
                    </h3>
                    <div className="space-y-2 max-h-96 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50">
                      {transcripts.map((segment) => (
                        <div
                          key={segment.id}
                          className="p-4 bg-white rounded-lg border border-gray-200 hover:border-purple-300 transition-colors"
                        >
                          <div className="flex items-start gap-3">
                            {/* Timecode Badge */}
                            <div className="flex-shrink-0 bg-purple-100 text-purple-700 px-3 py-1 rounded-md text-xs font-mono">
                              {segment.metadata?.timecode_start || '00:00'}
                            </div>

                            {/* Transcript Content */}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
                                {segment.description || segment.name}
                              </p>

                              {/* Metadata */}
                              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                                <span>
                                  Duration: {segment.metadata?.timecode_start} → {segment.metadata?.timecode_end}
                                </span>
                                {segment.metadata?.extraction_confidence && (
                                  <span>
                                    Confidence: {Math.round(segment.metadata.extraction_confidence * 100)}%
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Delete Button */}
                            <button
                              onClick={() => handleDeleteTranscript(segment.id)}
                              className="flex-shrink-0 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Delete transcript"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null
              })()}

              {/* Upload Area - Only show if no transcripts exist */}
              {(() => {
                const node = findNodeById(tree, selectedTab)
                const transcripts = node?.children.filter(c => c.is_leaf || c.metadata?.timecode_start != null) || []

                // Only show upload area if there are no transcripts
                if (transcripts.length > 0) return null

                return (
                  <div
                    onClick={() => {
                      const node = findNodeById(tree, selectedTab)
                      if (node && !isUploading) handleUpload(node.id)
                    }}
                    onDrop={(e) => {
                      const node = findNodeById(tree, selectedTab)
                      if (node && !isUploading) handleDrop(e, node.id)
                    }}
                    onDragOver={handleDragOver}
                    className={`p-8 border-2 border-dashed rounded-lg transition-colors ${
                      isUploading
                        ? 'border-purple-400 bg-purple-50 cursor-wait'
                        : 'border-gray-300 hover:border-purple-400 hover:bg-purple-50 cursor-pointer'
                    }`}
                  >
                    <div className="text-center">
                      {isUploading ? (
                        <>
                          <svg
                            className="animate-spin h-12 w-12 text-purple-600 mx-auto mb-2"
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
                          <p className="mt-2 text-sm text-gray-600 font-semibold">Uploading and processing...</p>
                        </>
                      ) : (
                        <>
                          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                          </svg>
                          <p className="mt-2 text-sm text-gray-600">
                            <span className="font-semibold">Add course transcripts here</span>
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            Drop .srt or .vtt files here or click to upload
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                )
              })()}

              {/* Error Message */}
              {uploadError && (
                <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {uploadError}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-12">
              Select a tab to view its content
            </div>
          )}
        </div>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".srt,.vtt"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  )
}

// Helper function to find node by ID
function findNodeById(node: CourseTreeNode, id: string): CourseTreeNode | null {
  if (node.id === id) return node
  for (const child of node.children) {
    const found = findNodeById(child, id)
    if (found) return found
  }
  return null
}

"use client"

/**
 * Folder Tree Node Component
 * Recursive component for individual nodes in the tree
 */

import { useState } from "react"
import type { CourseTreeNode } from "@/lib/api/types"
import { deleteFolder, createSubfolder } from "@/lib/api/courses"
import AddContentDropdown from "./AddContentDropdown"
import TranscriptUploadModal from "./TranscriptUploadModal"

interface Props {
  node: CourseTreeNode
  level: number
  isExpanded: boolean
  onToggle: (nodeId: string) => void
  expandedNodes: Set<string>
  onRefresh: () => void
}

export default function FolderTreeNode({
  node,
  level,
  isExpanded,
  onToggle,
  expandedNodes,
  onRefresh
}: Props) {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isCreatingSubfolder, setIsCreatingSubfolder] = useState(false)

  // Max depth is 4 levels (1, 2, 3, 4)
  const canAddSubfolder = node.hierarchy_level < 4

  const getIcon = () => {
    switch (node.type) {
      case "course":
        return (
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        )
      case "module":
        return (
          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        )
      case "lesson":
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        )
      default:
        return null
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Delete this ${node.type}? This will also delete all children.`)) return

    setIsDeleting(true)
    try {
      await deleteFolder(node.id)
      onRefresh()
    } catch (err) {
      alert("Failed to delete")
      setIsDeleting(false)
    }
  }

  const handleAddSubfolder = async () => {
    setIsCreatingSubfolder(true)
    setShowMenu(false)
    try {
      // Count existing subfolders to generate name (exclude segment transcripts)
      const subfolderCount = node.children.filter(c => c.type !== 'segment').length
      const newName = `Subfolder ${subfolderCount + 1}`

      await createSubfolder(node.id, {
        name: newName,
        description: "",
        thumbnail_url: null
      })
      onRefresh()
    } catch (err: any) {
      alert(err.message || "Failed to create subfolder")
    } finally {
      setIsCreatingSubfolder(false)
    }
  }

  const handleDuplicate = async () => {
    setShowMenu(false)
    // TODO: Implement duplicate functionality
    alert("Duplicate functionality coming soon")
  }

  const handleRename = () => {
    setShowMenu(false)
    // TODO: Implement rename functionality
    alert("Rename functionality coming soon")
  }

  const indentClass = `ml-${level * 6}`

  return (
    <div>
      {/* Node Row */}
      <div className={`flex items-center gap-2 py-2 px-3 hover:bg-gray-50 rounded-lg group ${level > 0 ? 'ml-6' : ''}`}>
        {/* Expand/Collapse */}
        {node.children.length > 0 && (
          <button
            onClick={() => onToggle(node.id)}
            className="flex-shrink-0 w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600"
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
        {node.children.length === 0 && <div className="w-5" />}

        {/* Icon */}
        {getIcon()}

        {/* Name */}
        <span className="flex-1 font-medium text-gray-900">{node.name}</span>

        {/* 3-dot menu (always visible like Google Docs) */}
        <div className="relative flex items-center gap-2">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
            title="More options"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
            </svg>
          </button>

          {/* Dropdown Menu */}
          {showMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-8 z-50 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                {canAddSubfolder && (
                  <button
                    onClick={handleAddSubfolder}
                    disabled={isCreatingSubfolder}
                    className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2 disabled:opacity-50"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    {isCreatingSubfolder ? "Creating..." : "Add subtab"}
                  </button>
                )}
                <button
                  onClick={handleDuplicate}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Duplicate
                </button>
                <button
                  onClick={handleRename}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  Rename
                </button>
                <div className="border-t border-gray-200 my-1"></div>
                <button
                  onClick={() => {
                    handleDelete()
                    setShowMenu(false)
                  }}
                  disabled={isDeleting}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 text-red-600 flex items-center gap-2 disabled:opacity-50"
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
      </div>

      {/* Children (recursive) AND Empty State */}
      {isExpanded && (
        <div className="ml-6">
          {/* Show existing children */}
          {node.children.map((child) => (
            <FolderTreeNode
              key={child.id}
              node={child}
              level={level + 1}
              isExpanded={expandedNodes.has(child.id)}
              onToggle={onToggle}
              expandedNodes={expandedNodes}
              onRefresh={onRefresh}
            />
          ))}

          {/* Always show empty state for uploading transcripts */}
          <div
            onClick={() => setShowUploadModal(true)}
            className="mt-2 mb-4 p-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors cursor-pointer"
          >
            <div className="text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                <span className="font-semibold">Add course transcripts here</span>
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Drop .srt, .vtt, .txt, .mp4, .mov files here or click to upload
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <TranscriptUploadModal
          lessonId={node.id}
          lessonName={node.name}
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false)
            onRefresh()
          }}
        />
      )}
    </div>
  )
}

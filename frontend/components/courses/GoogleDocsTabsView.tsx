"use client"

/**
 * Google Docs-style Tabs View
 * Horizontal tab layout similar to Google Docs
 */

import { useState } from "react"
import type { CourseTreeNode } from "@/lib/api/types"
import { deleteFolder, createSubfolder } from "@/lib/api/courses"
import TranscriptUploadModal from "./TranscriptUploadModal"

interface Props {
  tree: CourseTreeNode
  onRefresh: () => void
  onCreateModule?: () => void
}

export default function GoogleDocsTabsView({ tree, onRefresh, onCreateModule }: Props) {
  const [selectedTab, setSelectedTab] = useState<string | null>(null)
  const [expandedTabs, setExpandedTabs] = useState<Set<string>>(new Set())
  const [showMenu, setShowMenu] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadFolderId, setUploadFolderId] = useState<string | null>(null)
  const [uploadFolderName, setUploadFolderName] = useState<string>("")

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

  const handleUpload = (folderId: string, folderName: string) => {
    setUploadFolderId(folderId)
    setUploadFolderName(folderName)
    setShowUploadModal(true)
    setShowMenu(null)
  }

  const renderTab = (node: CourseTreeNode, level: number = 0) => {
    const isSelected = selectedTab === node.id
    const isExpanded = expandedTabs.has(node.id)
    const hasChildren = node.children.length > 0
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
                  onClick={() => handleUpload(node.id, node.name)}
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
            {node.children.filter(c => !c.is_leaf).map(child => renderTab(child, level + 1))}
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
            {tree.children.filter(c => !c.is_leaf).map(child => renderTab(child))}
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

              {/* Upload Area */}
              <div
                onClick={() => {
                  const node = findNodeById(tree, selectedTab)
                  if (node) handleUpload(node.id, node.name)
                }}
                className="p-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition-colors cursor-pointer"
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
          ) : (
            <div className="text-center text-gray-500 py-12">
              Select a tab to view its content
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && uploadFolderId && (
        <TranscriptUploadModal
          lessonId={uploadFolderId}
          lessonName={uploadFolderName}
          onClose={() => {
            setShowUploadModal(false)
            setUploadFolderId(null)
          }}
          onSuccess={() => {
            setShowUploadModal(false)
            setUploadFolderId(null)
            onRefresh()
          }}
        />
      )}
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

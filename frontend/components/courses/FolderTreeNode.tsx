"use client"

/**
 * Folder Tree Node Component
 * Recursive component for individual nodes in the tree
 */

import { useState } from "react"
import type { CourseTreeNode } from "@/lib/api/types"
import { deleteFolder } from "@/lib/api/courses"
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
  const [isDeleting, setIsDeleting] = useState(false)

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

        {/* Actions (show on hover) */}
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {/* Add Content (for course, module) */}
          {(node.type === "course" || node.type === "module") && (
            <AddContentDropdown node={node} onRefresh={onRefresh} />
          )}

          {/* Upload Transcript (for lesson) */}
          {node.type === "lesson" && (
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
              title="Upload transcript"
            >
              + Transcript
            </button>
          )}

          {/* View */}
          <button
            onClick={() => onToggle(node.id)}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Toggle view"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>

          {/* Delete */}
          {node.type !== "course" && (
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="p-1 text-red-400 hover:text-red-600 disabled:opacity-50"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Children (recursive) */}
      {isExpanded && node.children.length > 0 && (
        <div className="ml-6">
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

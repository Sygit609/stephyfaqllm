"use client"

/**
 * Add Content Dropdown
 * Dropdown menu to add modules or lessons
 */

import { useState } from "react"
import type { CourseTreeNode } from "@/lib/api/types"
import { createModule, createLesson } from "@/lib/api/courses"

interface Props {
  node: CourseTreeNode
  onRefresh: () => void
}

export default function AddContentDropdown({ node, onRefresh }: Props) {
  const [isOpen, setIsOpen] = useState(false)
  const [showModuleForm, setShowModuleForm] = useState(false)
  const [showLessonForm, setShowLessonForm] = useState(false)

  const [moduleName, setModuleName] = useState("")
  const [moduleDesc, setModuleDesc] = useState("")
  const [lessonName, setLessonName] = useState("")
  const [lessonDesc, setLessonDesc] = useState("")
  const [lessonUrl, setLessonUrl] = useState("")

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleCreateModule = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await createModule(node.id, {
        name: moduleName,
        description: moduleDesc
      })
      setShowModuleForm(false)
      setModuleName("")
      setModuleDesc("")
      onRefresh()
    } catch (err) {
      alert("Failed to create module")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCreateLesson = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await createLesson(node.id, {
        name: lessonName,
        description: lessonDesc,
        video_url: lessonUrl || null
      })
      setShowLessonForm(false)
      setLessonName("")
      setLessonDesc("")
      setLessonUrl("")
      onRefresh()
    } catch (err) {
      alert("Failed to create lesson")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="relative">
      {/* Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
      >
        + Add
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 z-20 min-w-[150px]">
            {node.type === "course" && (
              <button
                onClick={() => {
                  setIsOpen(false)
                  setShowModuleForm(true)
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm"
              >
                Add Module
              </button>
            )}
            {node.type === "module" && (
              <button
                onClick={() => {
                  setIsOpen(false)
                  setShowLessonForm(true)
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 text-sm"
              >
                Add Lesson
              </button>
            )}
          </div>
        </>
      )}

      {/* Module Form Modal */}
      {showModuleForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="border-b border-gray-200 px-6 py-4">
              <h3 className="text-lg font-bold">Add Module</h3>
            </div>
            <form onSubmit={handleCreateModule} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Name</label>
                <input
                  type="text"
                  value={moduleName}
                  onChange={(e) => setModuleName(e.target.value)}
                  required
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2">Description</label>
                <textarea
                  value={moduleDesc}
                  onChange={(e) => setModuleDesc(e.target.value)}
                  required
                  rows={3}
                  className="w-full px-4 py-2 border rounded-lg resize-none"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModuleForm(false)}
                  className="px-4 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:opacity-50"
                >
                  {isSubmitting ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lesson Form Modal */}
      {showLessonForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="border-b border-gray-200 px-6 py-4">
              <h3 className="text-lg font-bold">Add Lesson</h3>
            </div>
            <form onSubmit={handleCreateLesson} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Name</label>
                <input
                  type="text"
                  value={lessonName}
                  onChange={(e) => setLessonName(e.target.value)}
                  required
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2">Description</label>
                <textarea
                  value={lessonDesc}
                  onChange={(e) => setLessonDesc(e.target.value)}
                  required
                  rows={3}
                  className="w-full px-4 py-2 border rounded-lg resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-2">Video URL (optional)</label>
                <input
                  type="url"
                  value={lessonUrl}
                  onChange={(e) => setLessonUrl(e.target.value)}
                  placeholder="https://vimeo.com/..."
                  className="w-full px-4 py-2 border rounded-lg"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowLessonForm(false)}
                  className="px-4 py-2 border rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg disabled:opacity-50"
                >
                  {isSubmitting ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

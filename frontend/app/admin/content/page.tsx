"use client"

/**
 * Admin Content Management Page
 * View, edit, and delete knowledge base entries
 */

import { useState, useEffect } from "react"
import Link from "next/link"
import type { ContentItem, ContentListResponse } from "@/lib/api/types"
import { listContent, deleteContent, updateContent } from "@/lib/api/admin"
import ContentTable from "@/components/admin/ContentTable"
import ContentFiltersBar from "@/components/admin/ContentFiltersBar"
import EditContentModal from "@/components/admin/EditContentModal"
import DeleteConfirmModal from "@/components/admin/DeleteConfirmModal"

interface ContentFilters {
  contentType?: string
  extractedBy?: string
  minConfidence?: number
  showParentsOnly?: boolean
  showChildrenOnly?: boolean
}

export default function AdminContentPage() {
  // Data state
  const [data, setData] = useState<ContentListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter and pagination state
  const [filters, setFilters] = useState<ContentFilters>({})
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Modal state
  const [editingItem, setEditingItem] = useState<ContentItem | null>(null)
  const [deletingItem, setDeletingItem] = useState<ContentItem | null>(null)

  // Load data from API
  const loadData = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await listContent({
        content_type: filters.contentType,
        extracted_by: filters.extractedBy,
        min_confidence: filters.minConfidence,
        has_parent: filters.showParentsOnly
          ? false
          : filters.showChildrenOnly
          ? true
          : undefined,
        page,
        page_size: pageSize,
      })
      setData(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to load content")
    } finally {
      setIsLoading(false)
    }
  }

  // Load on mount and when filters/page change
  useEffect(() => {
    loadData()
  }, [filters, page])

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1)
  }, [filters.contentType, filters.extractedBy, filters.minConfidence, filters.showParentsOnly, filters.showChildrenOnly])

  // Handlers
  const handleEdit = (item: ContentItem) => {
    setEditingItem(item)
  }

  const handleDelete = (item: ContentItem) => {
    setDeletingItem(item)
  }

  const handleSaveEdit = async (updatedItem: ContentItem) => {
    try {
      await updateContent(updatedItem.id, {
        question: updatedItem.question,
        answer: updatedItem.answer,
        tags: updatedItem.tags || undefined,
        source_url: updatedItem.source_url || undefined,
      })
      setEditingItem(null)
      loadData() // Refresh the list
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || err.message || "Failed to update")
    }
  }

  const handleConfirmDelete = async () => {
    if (!deletingItem) return

    try {
      await deleteContent(deletingItem.id)
      setDeletingItem(null)
      loadData() // Refresh the list
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to delete")
    }
  }

  // Count children for delete warning (from current data)
  const getChildrenCount = (itemId: string) => {
    if (!data) return 0
    return data.items.filter((item) => item.parent_id === itemId).length
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link
              href="/"
              className="text-purple-600 hover:text-purple-700 font-medium"
            >
              ← Back to Search
            </Link>
            <Link
              href="/admin/import"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              + Import Content
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Content Management</h1>
          <p className="text-gray-600 mt-2">
            View, edit, and manage all knowledge base entries
          </p>
        </div>

        {/* Filters */}
        <ContentFiltersBar filters={filters} onFiltersChange={setFilters} />

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg
              className="animate-spin h-12 w-12 text-purple-600 mx-auto mb-4"
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
            <p className="text-gray-600">Loading content...</p>
          </div>
        )}

        {/* Stats Summary */}
        {!isLoading && data && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold text-gray-900">{data.total_count}</div>
                <div className="text-sm text-gray-600 mt-1">Total Items</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600">{data.page}</div>
                <div className="text-sm text-gray-600 mt-1">Current Page</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600">{data.total_pages}</div>
                <div className="text-sm text-gray-600 mt-1">Total Pages</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600">{data.items.length}</div>
                <div className="text-sm text-gray-600 mt-1">Showing</div>
              </div>
            </div>
          </div>
        )}

        {/* Content Table */}
        {!isLoading && data && data.items.length > 0 && (
          <>
            <ContentTable
              items={data.items}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="bg-white rounded-lg shadow-sm p-4 mt-6">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    ← Previous
                  </button>
                  <span className="text-gray-700 font-medium">
                    Page {page} of {data.total_pages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {!isLoading && data && data.items.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <svg
              className="mx-auto h-16 w-16 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-gray-600 text-lg font-semibold mb-2">
              No content found
            </p>
            <p className="text-gray-500 text-sm mb-4">
              {Object.values(filters).some(v => v !== undefined)
                ? "Try adjusting your filters"
                : "Import your first content to get started"}
            </p>
            {Object.values(filters).some(v => v !== undefined) ? (
              <button
                onClick={() => setFilters({})}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
              >
                Clear All Filters
              </button>
            ) : (
              <Link
                href="/admin/import"
                className="inline-block px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
              >
                Import Content
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {editingItem && (
        <EditContentModal
          item={editingItem}
          onClose={() => setEditingItem(null)}
          onSave={handleSaveEdit}
        />
      )}

      {deletingItem && (
        <DeleteConfirmModal
          item={deletingItem}
          onClose={() => setDeletingItem(null)}
          onConfirm={handleConfirmDelete}
          childrenCount={
            !deletingItem.parent_id ? getChildrenCount(deletingItem.id) : 0
          }
        />
      )}
    </div>
  )
}

/**
 * Admin API Client Functions
 * Handles screenshot extraction and content management
 */

import { apiClient } from "./client"
import type {
  ExtractScreenshotRequest,
  ExtractScreenshotResponse,
  SaveContentRequest,
  SaveContentResponse,
  ContentListResponse,
} from "./types"

/**
 * Extract Q&A pairs from screenshot using vision API
 */
export async function extractScreenshot(
  request: ExtractScreenshotRequest
): Promise<ExtractScreenshotResponse> {
  const response = await apiClient.post<ExtractScreenshotResponse>(
    "/api/admin/extract-screenshot",
    request
  )
  return response.data
}

/**
 * Save extracted (and possibly edited) content to knowledge base
 */
export async function saveContent(
  request: SaveContentRequest
): Promise<SaveContentResponse> {
  const response = await apiClient.post<SaveContentResponse>(
    "/api/admin/save-content",
    request
  )
  return response.data
}

/**
 * List content items with filters and pagination
 */
export async function listContent(params?: {
  content_type?: string
  extracted_by?: string
  min_confidence?: number
  has_parent?: boolean
  parent_id?: string
  page?: number
  page_size?: number
}): Promise<ContentListResponse> {
  const response = await apiClient.get<ContentListResponse>(
    "/api/admin/content-list",
    { params }
  )
  return response.data
}

/**
 * Delete a content item
 */
export async function deleteContent(
  itemId: string
): Promise<{ success: boolean; message: string; deleted_count: number }> {
  const response = await apiClient.delete(`/api/admin/content/${itemId}`)
  return response.data
}

/**
 * Convert file to base64 string
 * Helper function for image upload
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      const result = reader.result as string
      // Remove data:image/...;base64, prefix
      const base64 = result.split(",")[1]
      resolve(base64)
    }
    reader.onerror = (error) => reject(error)
  })
}

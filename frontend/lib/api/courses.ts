/**
 * Course Transcript Management API Client
 */

import axios from 'axios'
import type {
  Course,
  CourseListResponse,
  CourseTreeNode,
  CreateCourseRequest,
  CreateModuleRequest,
  CreateLessonRequest,
  TranscribeRequest,
  TranscriptionResponse,
  UploadTranscriptResponse,
  Segment,
  UpdateSegmentRequest,
  CloneCourseRequest,
  CloneCourseResponse,
  Folder,
  UpdateFolderRequest,
  DeleteFolderResponse,
  CourseStatsResponse
} from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

// ============================================================
// Course CRUD
// ============================================================

export async function listCourses(): Promise<CourseListResponse> {
  const response = await axios.get(`${API_URL}/api/admin/courses`)
  return response.data
}

export async function createCourse(data: CreateCourseRequest): Promise<Course> {
  const response = await axios.post(`${API_URL}/api/admin/courses`, data)
  return response.data
}

export async function getCourseTree(courseId: string): Promise<CourseTreeNode> {
  const response = await axios.get(`${API_URL}/api/admin/courses/${courseId}/tree`)
  return response.data.course
}

export async function getCourseStats(courseId: string): Promise<CourseStatsResponse> {
  const response = await axios.get(`${API_URL}/api/admin/courses/${courseId}/stats`)
  return response.data
}

// ============================================================
// Module & Lesson CRUD
// ============================================================

export async function createModule(
  courseId: string,
  data: CreateModuleRequest
): Promise<Folder> {
  const response = await axios.post(
    `${API_URL}/api/admin/courses/${courseId}/modules`,
    data
  )
  return response.data
}

export async function createLesson(
  moduleId: string,
  data: CreateLessonRequest
): Promise<Folder> {
  const response = await axios.post(
    `${API_URL}/api/admin/modules/${moduleId}/lessons`,
    data
  )
  return response.data
}

// ============================================================
// Folder Operations (Create/Update/Delete)
// ============================================================

export async function createSubfolder(
  parentId: string,
  data: {
    name: string
    description: string
    thumbnail_url: string | null
  }
): Promise<Folder> {
  const response = await axios.post(
    `${API_URL}/api/admin/folders/${parentId}/subfolder`,
    data
  )
  return response.data
}

export async function updateFolder(
  folderId: string,
  data: UpdateFolderRequest
): Promise<Folder> {
  const response = await axios.put(`${API_URL}/api/admin/folders/${folderId}`, data)
  return response.data
}

export async function deleteFolder(folderId: string): Promise<DeleteFolderResponse> {
  const response = await axios.delete(`${API_URL}/api/admin/folders/${folderId}`)
  return response.data
}

// ============================================================
// Video & Transcription
// ============================================================

export async function uploadTranscript(
  lessonId: string,
  file: File
): Promise<UploadTranscriptResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(
    `${API_URL}/api/admin/lessons/${lessonId}/upload-transcript`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  )
  return response.data
}

export async function transcribeLesson(
  lessonId: string,
  options: TranscribeRequest
): Promise<TranscriptionResponse> {
  const response = await axios.post(
    `${API_URL}/api/admin/lessons/${lessonId}/transcribe`,
    options
  )
  return response.data
}

// ============================================================
// Segment Management
// ============================================================

export async function getLessonSegments(lessonId: string): Promise<Segment[]> {
  const response = await axios.get(`${API_URL}/api/admin/lessons/${lessonId}/segments`)
  return response.data
}

export async function updateSegment(
  segmentId: string,
  data: UpdateSegmentRequest
): Promise<Segment> {
  const response = await axios.put(`${API_URL}/api/admin/segments/${segmentId}`, data)
  return response.data
}

// ============================================================
// Course Operations
// ============================================================

export async function cloneCourse(
  courseId: string,
  options: CloneCourseRequest
): Promise<CloneCourseResponse> {
  const response = await axios.post(
    `${API_URL}/api/admin/courses/${courseId}/clone`,
    options
  )
  return response.data
}

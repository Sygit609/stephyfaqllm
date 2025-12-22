/**
 * File validation utilities
 * Shared validation logic for file uploads
 */

export interface FileValidationResult {
  valid: boolean
  error?: string
}

/**
 * Validate an image file
 */
export function validateImageFile(file: File): FileValidationResult {
  // Check file type
  if (!file.type.startsWith('image/')) {
    return {
      valid: false,
      error: 'Must be an image file (JPG, PNG, etc.)',
    }
  }

  // Check file size (max 10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large (max 10MB). File size: ${(file.size / 1024 / 1024).toFixed(1)}MB`,
    }
  }

  return { valid: true }
}

/**
 * Validate multiple files
 */
export function validateFiles(files: File[]): { valid: File[]; invalid: Array<{ file: File; error: string }> } {
  const valid: File[] = []
  const invalid: Array<{ file: File; error: string }> = []

  for (const file of files) {
    const result = validateImageFile(file)
    if (result.valid) {
      valid.push(file)
    } else {
      invalid.push({ file, error: result.error || 'Invalid file' })
    }
  }

  return { valid, invalid }
}

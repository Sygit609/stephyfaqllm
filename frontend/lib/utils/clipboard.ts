/**
 * Clipboard utility functions
 * Handles clipboard paste events and blob-to-file conversion
 */

/**
 * Convert a clipboard blob to a File object
 */
export function clipboardBlobToFile(blob: Blob, index: number = 0): File {
  const timestamp = Date.now()
  const filename = `pasted-screenshot-${timestamp}-${index}.png`

  return new File([blob], filename, {
    type: blob.type,
    lastModified: timestamp,
  })
}

/**
 * Extract image files from clipboard event
 */
export function extractImagesFromClipboard(event: ClipboardEvent): File[] {
  const files: File[] = []
  const items = event.clipboardData?.items

  if (!items) return files

  let imageIndex = 0
  for (const item of Array.from(items)) {
    if (item.type.startsWith('image/')) {
      const blob = item.getAsFile()
      if (blob) {
        const file = clipboardBlobToFile(blob, imageIndex)
        files.push(file)
        imageIndex++
      }
    }
  }

  return files
}

"use client"

/**
 * Content Filters Bar
 * Provides dropdown and slider controls for filtering content
 */

interface ContentFilters {
  contentType?: string
  extractedBy?: string
  minConfidence?: number
  showParentsOnly?: boolean
  showChildrenOnly?: boolean
}

interface Props {
  filters: ContentFilters
  onFiltersChange: (filters: ContentFilters) => void
}

export default function ContentFiltersBar({ filters, onFiltersChange }: Props) {
  const handleContentTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFiltersChange({
      ...filters,
      contentType: e.target.value || undefined
    })
  }

  const handleExtractedByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFiltersChange({
      ...filters,
      extractedBy: e.target.value || undefined
    })
  }

  const handleConfidenceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      minConfidence: parseFloat(e.target.value)
    })
  }

  const handleParentChildChange = (value: string) => {
    if (value === 'all') {
      onFiltersChange({
        ...filters,
        showParentsOnly: undefined,
        showChildrenOnly: undefined
      })
    } else if (value === 'parents') {
      onFiltersChange({
        ...filters,
        showParentsOnly: true,
        showChildrenOnly: undefined
      })
    } else if (value === 'children') {
      onFiltersChange({
        ...filters,
        showParentsOnly: undefined,
        showChildrenOnly: true
      })
    }
  }

  const handleClearFilters = () => {
    onFiltersChange({})
  }

  const hasActiveFilters = Object.values(filters).some(v => v !== undefined)

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex flex-wrap items-center gap-4">
        {/* Content Type */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Content Type
          </label>
          <select
            value={filters.contentType || ''}
            onChange={handleContentTypeChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
          >
            <option value="">All Types</option>
            <option value="screenshot">Screenshot</option>
            <option value="facebook">Facebook</option>
            <option value="manual">Manual</option>
            <option value="csv">CSV</option>
            <option value="video">Video</option>
          </select>
        </div>

        {/* Extracted By */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Extracted By
          </label>
          <select
            value={filters.extractedBy || ''}
            onChange={handleExtractedByChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
          >
            <option value="">All Methods</option>
            <option value="gemini-vision">Gemini Vision</option>
            <option value="gpt4-vision">GPT-4 Vision</option>
            <option value="manual">Manual</option>
          </select>
        </div>

        {/* Parent/Child Filter */}
        <div className="flex-1 min-w-[150px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Relationship
          </label>
          <select
            value={
              filters.showParentsOnly
                ? 'parents'
                : filters.showChildrenOnly
                ? 'children'
                : 'all'
            }
            onChange={(e) => handleParentChildChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
          >
            <option value="all">All Items</option>
            <option value="parents">Parents Only</option>
            <option value="children">Children Only</option>
          </select>
        </div>

        {/* Confidence Slider */}
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min. Confidence: {((filters.minConfidence || 0) * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={filters.minConfidence || 0}
            onChange={handleConfidenceChange}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <div className="flex items-end">
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 text-sm text-purple-600 hover:text-purple-700 font-medium hover:bg-purple-50 rounded-lg transition-colors"
            >
              Clear Filters
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

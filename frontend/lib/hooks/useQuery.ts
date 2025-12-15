"use client"

/**
 * Custom React Hook for Query API
 * Handles search + answer generation
 */

import { useState } from "react"
import { apiClient } from "../api/client"
import type { QueryRequest, QueryResponse } from "../api/types"

export function useQuery() {
  const [data, setData] = useState<QueryResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const executeQuery = async (request: QueryRequest) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await apiClient.post<QueryResponse>("/api/query", request)
      setData(response.data)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || "Failed to execute query"
      setError(errorMessage)
      console.error("Query error:", err)
    } finally {
      setIsLoading(false)
    }
  }

  const reset = () => {
    setData(null)
    setError(null)
  }

  return {
    data,
    isLoading,
    error,
    executeQuery,
    reset,
  }
}
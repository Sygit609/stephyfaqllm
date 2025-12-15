/**
 * Axios HTTP client configuration
 * Handles API communication with the FastAPI backend
 */

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios"
import type { APIError } from "./types"

// Base URL from environment variable
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Create axios instance
export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Log request in development
    if (process.env.NODE_ENV === "development") {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => {
    console.error("[API Request Error]", error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response in development
    if (process.env.NODE_ENV === "development") {
      console.log(`[API Response] ${response.config.url}`, response.status)
    }
    return response
  },
  (error: AxiosError<APIError>) => {
    // Handle different error types
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const message = error.response.data?.detail || error.message

      console.error(`[API Error ${status}]`, message)

      // Handle specific status codes
      switch (status) {
        case 400:
          console.error("Bad Request:", message)
          break
        case 401:
          console.error("Unauthorized:", message)
          break
        case 404:
          console.error("Not Found:", message)
          break
        case 422:
          console.error("Validation Error:", message)
          break
        case 500:
          console.error("Server Error:", message)
          break
        case 503:
          console.error("Service Unavailable:", message)
          break
        default:
          console.error("API Error:", message)
      }
    } else if (error.request) {
      // Request made but no response received
      console.error("[API Network Error] No response received from server")
    } else {
      // Error in request setup
      console.error("[API Error]", error.message)
    }

    return Promise.reject(error)
  }
)

// Export types for convenience
export type { AxiosError, AxiosResponse }

import axios, { AxiosError } from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  timeout: 15_000,
})

interface ApiErrorBody {
  detail?: string | { msg: string }[]
}

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    const detail = error.response?.data?.detail
    let message = error.message
    if (typeof detail === 'string') {
      message = detail
    } else if (Array.isArray(detail)) {
      message = detail.map((item) => item.msg).join('; ')
    }
    return Promise.reject(new Error(message))
  },
)

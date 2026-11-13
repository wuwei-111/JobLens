import { http } from './http'
import type { JobListResponse, JobOut, JobQuery } from '@/types/api'

export async function fetchJobs(query: JobQuery = {}): Promise<JobListResponse> {
  const { data } = await http.get<JobListResponse>('/jobs', { params: query })
  return data
}

export async function fetchJob(jobId: string): Promise<JobOut> {
  const { data } = await http.get<JobOut>(`/jobs/${encodeURIComponent(jobId)}`)
  return data
}
